from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from bson import ObjectId
from emergentintegrations.llm.chat import LlmChat, UserMessage
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

logger = logging.getLogger(__name__)

# Pydantic Models
class Material(BaseModel):
    id: Optional[str] = None
    name: str
    type: str
    unit: str
    wagon_types: List[str]
    
class MaterialResponse(Material):
    id: str

class Stockyard(BaseModel):
    id: Optional[str] = None
    name: str
    location: str
    capacity: float
    
class StockyardResponse(Stockyard):
    id: str

class Inventory(BaseModel):
    id: Optional[str] = None
    stockyard_id: str
    material_id: str
    quantity: float
    cost_per_unit: float
    last_updated: Optional[datetime] = None
    
class InventoryResponse(Inventory):
    id: str
    stockyard_name: Optional[str] = None
    material_name: Optional[str] = None

class Order(BaseModel):
    id: Optional[str] = None
    customer_name: str
    material_id: str
    quantity: float
    destination: str
    priority: str  # high, medium, low
    deadline: datetime
    status: str = "pending"  # pending, assigned, shipped, delivered
    penalty_per_day: float = 0
    
class OrderResponse(Order):
    id: str
    material_name: Optional[str] = None
    days_until_deadline: Optional[int] = None

class Wagon(BaseModel):
    id: Optional[str] = None
    wagon_number: str
    type: str
    capacity: float
    status: str = "available"  # available, in_use, maintenance
    
class WagonResponse(Wagon):
    id: str

class LoadingPoint(BaseModel):
    id: Optional[str] = None
    name: str
    capacity: float
    current_utilization: float = 0
    stockyard_id: str
    
class LoadingPointResponse(LoadingPoint):
    id: str
    stockyard_name: Optional[str] = None

class RakeFormation(BaseModel):
    id: Optional[str] = None
    rake_number: str
    wagon_ids: List[str]
    order_ids: List[str]
    loading_point_id: str
    route: str
    total_cost: float
    transport_cost: float
    loading_cost: float
    estimated_penalty: float
    status: str = "planned"  # planned, loading, in_transit, delivered
    formation_date: datetime
    dispatch_date: Optional[datetime] = None
    ai_recommendation: Optional[str] = None
    
class RakeFormationResponse(RakeFormation):
    id: str
    wagon_count: int
    order_count: int
    loading_point_name: Optional[str] = None

class AIOptimizationRequest(BaseModel):
    order_ids: List[str]
    max_cost: Optional[float] = None
    priority_weight: float = 0.5  # 0-1, higher means prioritize deadlines

class AIOptimizationResponse(BaseModel):
    recommended_rakes: List[Dict]
    total_cost: float
    explanation: str
    potential_savings: float

class DashboardStats(BaseModel):
    pending_orders: int
    active_rakes: int
    available_wagons: int
    total_inventory_value: float
    urgent_orders: int
    avg_utilization: float

# Helper function to convert ObjectId to string
def obj_to_dict(obj):
    if isinstance(obj, dict):
        obj['id'] = str(obj.pop('_id', ''))
    return obj

# Materials endpoints
@api_router.post("/materials", response_model=MaterialResponse)
async def create_material(material: Material):
    material_dict = material.dict(exclude={'id'})
    result = await db.materials.insert_one(material_dict)
    material_dict['id'] = str(result.inserted_id)
    return MaterialResponse(**material_dict)

@api_router.get("/materials", response_model=List[MaterialResponse])
async def get_materials():
    materials = await db.materials.find().to_list(1000)
    return [MaterialResponse(**obj_to_dict(m)) for m in materials]

# Stockyards endpoints
@api_router.post("/stockyards", response_model=StockyardResponse)
async def create_stockyard(stockyard: Stockyard):
    stockyard_dict = stockyard.dict(exclude={'id'})
    result = await db.stockyards.insert_one(stockyard_dict)
    stockyard_dict['id'] = str(result.inserted_id)
    return StockyardResponse(**stockyard_dict)

@api_router.get("/stockyards", response_model=List[StockyardResponse])
async def get_stockyards():
    stockyards = await db.stockyards.find().to_list(1000)
    return [StockyardResponse(**obj_to_dict(s)) for s in stockyards]

# Inventory endpoints
@api_router.post("/inventory", response_model=InventoryResponse)
async def create_inventory(inventory: Inventory):
    inventory_dict = inventory.dict(exclude={'id'})
    inventory_dict['last_updated'] = datetime.utcnow()
    result = await db.inventory.insert_one(inventory_dict)
    
    # Get related data
    inv = await db.inventory.find_one({'_id': result.inserted_id})
    stockyard = await db.stockyards.find_one({'_id': ObjectId(inv['stockyard_id'])})
    material = await db.materials.find_one({'_id': ObjectId(inv['material_id'])})
    
    inv = obj_to_dict(inv)
    inv['stockyard_name'] = stockyard['name'] if stockyard else None
    inv['material_name'] = material['name'] if material else None
    return InventoryResponse(**inv)

@api_router.get("/inventory", response_model=List[InventoryResponse])
async def get_inventory():
    inventories = await db.inventory.find().to_list(1000)
    result = []
    for inv in inventories:
        inv = obj_to_dict(inv)
        stockyard = await db.stockyards.find_one({'_id': ObjectId(inv['stockyard_id'])})
        material = await db.materials.find_one({'_id': ObjectId(inv['material_id'])})
        inv['stockyard_name'] = stockyard['name'] if stockyard else None
        inv['material_name'] = material['name'] if material else None
        result.append(InventoryResponse(**inv))
    return result

# Orders endpoints
@api_router.post("/orders", response_model=OrderResponse)
async def create_order(order: Order):
    order_dict = order.dict(exclude={'id'})
    result = await db.orders.insert_one(order_dict)
    
    order_obj = await db.orders.find_one({'_id': result.inserted_id})
    order_obj = obj_to_dict(order_obj)
    material = await db.materials.find_one({'_id': ObjectId(order_obj['material_id'])})
    order_obj['material_name'] = material['name'] if material else None
    order_obj['days_until_deadline'] = (order_obj['deadline'] - datetime.utcnow()).days
    return OrderResponse(**order_obj)

@api_router.get("/orders", response_model=List[OrderResponse])
async def get_orders():
    orders = await db.orders.find().to_list(1000)
    result = []
    for order in orders:
        order = obj_to_dict(order)
        material = await db.materials.find_one({'_id': ObjectId(order['material_id'])})
        order['material_name'] = material['name'] if material else None
        order['days_until_deadline'] = (order['deadline'] - datetime.utcnow()).days
        result.append(OrderResponse(**order))
    return result

@api_router.put("/orders/{order_id}", response_model=OrderResponse)
async def update_order(order_id: str, order: Order):
    order_dict = order.dict(exclude={'id'})
    await db.orders.update_one({'_id': ObjectId(order_id)}, {'$set': order_dict})
    
    order_obj = await db.orders.find_one({'_id': ObjectId(order_id)})
    order_obj = obj_to_dict(order_obj)
    material = await db.materials.find_one({'_id': ObjectId(order_obj['material_id'])})
    order_obj['material_name'] = material['name'] if material else None
    order_obj['days_until_deadline'] = (order_obj['deadline'] - datetime.utcnow()).days
    return OrderResponse(**order_obj)

# Wagons endpoints
@api_router.post("/wagons", response_model=WagonResponse)
async def create_wagon(wagon: Wagon):
    wagon_dict = wagon.dict(exclude={'id'})
    result = await db.wagons.insert_one(wagon_dict)
    wagon_dict['id'] = str(result.inserted_id)
    return WagonResponse(**wagon_dict)

@api_router.get("/wagons", response_model=List[WagonResponse])
async def get_wagons():
    wagons = await db.wagons.find().to_list(1000)
    return [WagonResponse(**obj_to_dict(w)) for w in wagons]

# Loading Points endpoints
@api_router.post("/loading-points", response_model=LoadingPointResponse)
async def create_loading_point(loading_point: LoadingPoint):
    lp_dict = loading_point.dict(exclude={'id'})
    result = await db.loading_points.insert_one(lp_dict)
    
    lp = await db.loading_points.find_one({'_id': result.inserted_id})
    lp = obj_to_dict(lp)
    stockyard = await db.stockyards.find_one({'_id': ObjectId(lp['stockyard_id'])})
    lp['stockyard_name'] = stockyard['name'] if stockyard else None
    return LoadingPointResponse(**lp)

@api_router.get("/loading-points", response_model=List[LoadingPointResponse])
async def get_loading_points():
    loading_points = await db.loading_points.find().to_list(1000)
    result = []
    for lp in loading_points:
        lp = obj_to_dict(lp)
        stockyard = await db.stockyards.find_one({'_id': ObjectId(lp['stockyard_id'])})
        lp['stockyard_name'] = stockyard['name'] if stockyard else None
        result.append(LoadingPointResponse(**lp))
    return result

# Rake Formation endpoints
@api_router.post("/rakes", response_model=RakeFormationResponse)
async def create_rake(rake: RakeFormation):
    rake_dict = rake.dict(exclude={'id'})
    result = await db.rakes.insert_one(rake_dict)
    
    rake_obj = await db.rakes.find_one({'_id': result.inserted_id})
    rake_obj = obj_to_dict(rake_obj)
    loading_point = await db.loading_points.find_one({'_id': ObjectId(rake_obj['loading_point_id'])})
    rake_obj['loading_point_name'] = loading_point['name'] if loading_point else None
    rake_obj['wagon_count'] = len(rake_obj['wagon_ids'])
    rake_obj['order_count'] = len(rake_obj['order_ids'])
    return RakeFormationResponse(**rake_obj)

@api_router.get("/rakes", response_model=List[RakeFormationResponse])
async def get_rakes():
    rakes = await db.rakes.find().to_list(1000)
    result = []
    for rake in rakes:
        rake = obj_to_dict(rake)
        loading_point = await db.loading_points.find_one({'_id': ObjectId(rake['loading_point_id'])})
        rake['loading_point_name'] = loading_point['name'] if loading_point else None
        rake['wagon_count'] = len(rake['wagon_ids'])
        rake['order_count'] = len(rake['order_ids'])
        result.append(RakeFormationResponse(**rake))
    return result

# AI Optimization endpoint
@api_router.post("/optimize-rake", response_model=AIOptimizationResponse)
async def optimize_rake(request: AIOptimizationRequest):
    try:
        # Fetch orders
        orders = []
        for order_id in request.order_ids:
            order = await db.orders.find_one({'_id': ObjectId(order_id)})
            if order:
                order = obj_to_dict(order)
                material = await db.materials.find_one({'_id': ObjectId(order['material_id'])})
                order['material_name'] = material['name'] if material else None
                order['material_type'] = material['type'] if material else None
                order['wagon_types'] = material['wagon_types'] if material else []
                orders.append(order)
        
        # Fetch available inventory
        inventories = await db.inventory.find().to_list(1000)
        inventory_data = []
        for inv in inventories:
            inv = obj_to_dict(inv)
            stockyard = await db.stockyards.find_one({'_id': ObjectId(inv['stockyard_id'])})
            material = await db.materials.find_one({'_id': ObjectId(inv['material_id'])})
            inv['stockyard_name'] = stockyard['name'] if stockyard else None
            inv['stockyard_location'] = stockyard['location'] if stockyard else None
            inv['material_name'] = material['name'] if material else None
            inventory_data.append(inv)
        
        # Fetch available wagons
        wagons = await db.wagons.find({'status': 'available'}).to_list(1000)
        wagon_data = [obj_to_dict(w) for w in wagons]
        
        # Fetch loading points
        loading_points = await db.loading_points.find().to_list(1000)
        lp_data = []
        for lp in loading_points:
            lp = obj_to_dict(lp)
            stockyard = await db.stockyards.find_one({'_id': ObjectId(lp['stockyard_id'])})
            lp['stockyard_name'] = stockyard['name'] if stockyard else None
            lp_data.append(lp)
        
        # Create AI prompt for optimization
        prompt = f"""
You are an AI optimization expert for railway logistics. Analyze the following data and provide optimal rake formation recommendations.

**Orders to fulfill:**
{json.dumps(orders, indent=2, default=str)}

**Available Inventory:**
{json.dumps(inventory_data, indent=2, default=str)}

**Available Wagons:**
{json.dumps(wagon_data, indent=2, default=str)}

**Loading Points:**
{json.dumps(lp_data, indent=2, default=str)}

**Optimization Criteria:**
- Priority weight: {request.priority_weight} (0=cost focused, 1=deadline focused)
- Max cost constraint: {request.max_cost if request.max_cost else 'No limit'}

**Requirements:**
1. Match orders with available inventory from stockyards
2. Assign appropriate wagon types based on material compatibility
3. Select optimal loading points based on proximity and capacity
4. Minimize total cost (transport + loading + potential penalties)
5. Respect wagon capacity constraints
6. Prioritize orders based on deadlines and priority levels
7. Aim for full rake utilization

**Provide a JSON response with:**
{{
  "recommended_rakes": [
    {{
      "rake_number": "RAKE-XXX",
      "orders": ["order_id1", "order_id2"],
      "wagons": ["wagon_id1", "wagon_id2"],
      "loading_point_id": "lp_id",
      "route": "Stockyard -> Destination",
      "total_cost": 0,
      "transport_cost": 0,
      "loading_cost": 0,
      "estimated_penalty": 0,
      "reasoning": "Why this configuration"
    }}
  ],
  "total_cost": 0,
  "potential_savings": 0,
  "explanation": "Overall strategy and key decisions"
}}
"""
        
        # Initialize AI chat
        llm_chat = LlmChat(
            api_key=os.environ['EMERGENT_LLM_KEY'],
            session_id=f"rake_optimization_{datetime.utcnow().timestamp()}",
            system_message="You are an expert logistics optimization AI. Provide practical, cost-effective recommendations."
        ).with_model("openai", "gpt-4o")
        
        user_message = UserMessage(text=prompt)
        response = await llm_chat.send_message(user_message)
        
        # Parse AI response
        try:
            # Extract JSON from response
            response_text = response.strip()
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            ai_result = json.loads(response_text)
            
            return AIOptimizationResponse(
                recommended_rakes=ai_result.get('recommended_rakes', []),
                total_cost=ai_result.get('total_cost', 0),
                explanation=ai_result.get('explanation', response),
                potential_savings=ai_result.get('potential_savings', 0)
            )
        except json.JSONDecodeError:
            # If JSON parsing fails, return a structured response with the explanation
            return AIOptimizationResponse(
                recommended_rakes=[],
                total_cost=0,
                explanation=response,
                potential_savings=0
            )
    
    except Exception as e:
        logger.error(f"Optimization error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

# Dashboard stats endpoint
@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    pending_orders = await db.orders.count_documents({'status': 'pending'})
    active_rakes = await db.rakes.count_documents({'status': {'$in': ['planned', 'loading', 'in_transit']}})
    available_wagons = await db.wagons.count_documents({'status': 'available'})
    
    # Calculate total inventory value
    inventories = await db.inventory.find().to_list(1000)
    total_value = sum(inv['quantity'] * inv['cost_per_unit'] for inv in inventories)
    
    # Count urgent orders (deadline within 3 days)
    urgent_date = datetime.utcnow() + timedelta(days=3)
    urgent_orders = await db.orders.count_documents({
        'status': 'pending',
        'deadline': {'$lte': urgent_date}
    })
    
    # Calculate average loading point utilization
    loading_points = await db.loading_points.find().to_list(1000)
    avg_utilization = sum(lp['current_utilization'] for lp in loading_points) / len(loading_points) if loading_points else 0
    
    return DashboardStats(
        pending_orders=pending_orders,
        active_rakes=active_rakes,
        available_wagons=available_wagons,
        total_inventory_value=total_value,
        urgent_orders=urgent_orders,
        avg_utilization=avg_utilization
    )

# Initialize sample data endpoint
@api_router.post("/initialize-sample-data")
async def initialize_sample_data():
    try:
        # Check if data already exists
        existing_materials = await db.materials.count_documents({})
        if existing_materials > 0:
            return {"message": "Sample data already exists"}
        
        # Create materials
        materials = [
            {"name": "Coal", "type": "Bulk", "unit": "MT", "wagon_types": ["BOXN", "BCN"]},
            {"name": "Iron Ore", "type": "Bulk", "unit": "MT", "wagon_types": ["BOXN", "BCN"]},
            {"name": "Steel Coils", "type": "Finished", "unit": "MT", "wagon_types": ["BRN", "BOST"]},
            {"name": "Limestone", "type": "Bulk", "unit": "MT", "wagon_types": ["BOXN", "BCN"]},
        ]
        material_result = await db.materials.insert_many(materials)
        material_ids = [str(id) for id in material_result.inserted_ids]
        
        # Create stockyards
        stockyards = [
            {"name": "Stockyard A", "location": "Plant North", "capacity": 50000},
            {"name": "Stockyard B", "location": "Plant South", "capacity": 40000},
            {"name": "Stockyard C", "location": "Plant East", "capacity": 60000},
        ]
        stockyard_result = await db.stockyards.insert_many(stockyards)
        stockyard_ids = [str(id) for id in stockyard_result.inserted_ids]
        
        # Create inventory
        inventories = [
            {"stockyard_id": stockyard_ids[0], "material_id": material_ids[0], "quantity": 15000, "cost_per_unit": 50, "last_updated": datetime.utcnow()},
            {"stockyard_id": stockyard_ids[0], "material_id": material_ids[1], "quantity": 20000, "cost_per_unit": 80, "last_updated": datetime.utcnow()},
            {"stockyard_id": stockyard_ids[1], "material_id": material_ids[2], "quantity": 8000, "cost_per_unit": 500, "last_updated": datetime.utcnow()},
            {"stockyard_id": stockyard_ids[2], "material_id": material_ids[3], "quantity": 25000, "cost_per_unit": 30, "last_updated": datetime.utcnow()},
        ]
        await db.inventory.insert_many(inventories)
        
        # Create orders
        orders = [
            {"customer_name": "ABC Steel Ltd", "material_id": material_ids[0], "quantity": 5000, "destination": "Mumbai", "priority": "high", "deadline": datetime.utcnow() + timedelta(days=2), "status": "pending", "penalty_per_day": 10000},
            {"customer_name": "XYZ Industries", "material_id": material_ids[2], "quantity": 3000, "destination": "Delhi", "priority": "medium", "deadline": datetime.utcnow() + timedelta(days=5), "status": "pending", "penalty_per_day": 5000},
            {"customer_name": "PQR Corp", "material_id": material_ids[1], "quantity": 8000, "destination": "Kolkata", "priority": "high", "deadline": datetime.utcnow() + timedelta(days=3), "status": "pending", "penalty_per_day": 8000},
            {"customer_name": "LMN Ltd", "material_id": material_ids[3], "quantity": 4000, "destination": "Chennai", "priority": "low", "deadline": datetime.utcnow() + timedelta(days=10), "status": "pending", "penalty_per_day": 2000},
        ]
        await db.orders.insert_many(orders)
        
        # Create wagons
        wagons = []
        for i in range(1, 51):
            wagon_type = "BOXN" if i <= 25 else "BRN" if i <= 40 else "BCN"
            capacity = 60 if wagon_type == "BOXN" else 50 if wagon_type == "BRN" else 55
            wagons.append({"wagon_number": f"W{i:03d}", "type": wagon_type, "capacity": capacity, "status": "available"})
        await db.wagons.insert_many(wagons)
        
        # Create loading points
        loading_points = [
            {"name": "LP-North-1", "capacity": 10, "current_utilization": 0.3, "stockyard_id": stockyard_ids[0]},
            {"name": "LP-South-1", "capacity": 8, "current_utilization": 0.5, "stockyard_id": stockyard_ids[1]},
            {"name": "LP-East-1", "capacity": 12, "current_utilization": 0.2, "stockyard_id": stockyard_ids[2]},
        ]
        await db.loading_points.insert_many(loading_points)
        
        return {"message": "Sample data initialized successfully"}
    except Exception as e:
        logger.error(f"Error initializing data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/")
async def root():
    return {"message": "Rake Formation API is running"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
