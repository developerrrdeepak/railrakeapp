from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
from emergentintegrations.llm.chat import LlmChat, UserMessage
import json
import asyncio
import csv
import io
import random
from enum import Enum

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

# Enhanced Models for Advanced Control Room Features

class WagonStatus(str, Enum):
    AVAILABLE = "available"
    LOADED = "loaded"
    IN_TRANSIT = "in_transit"
    MAINTENANCE = "maintenance"
    EMPTY_RETURNING = "empty_returning"

class RakeStatus(str, Enum):
    PLANNED = "planned"
    LOADING = "loading"
    IN_TRANSIT = "in_transit"
    UNLOADING = "unloading"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

# Real-time Tracking Models
class WagonTracking(BaseModel):
    id: Optional[str] = None
    wagon_id: str
    current_location: str
    destination: Optional[str] = None
    status: WagonStatus
    load_percentage: float = 0.0
    estimated_arrival: Optional[datetime] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    gps_coordinates: Optional[Dict[str, float]] = None  # {"lat": 0.0, "lng": 0.0}

class WagonTrackingResponse(WagonTracking):
    id: str
    wagon_number: Optional[str] = None
    wagon_type: Optional[str] = None

# Compatibility Matrix
class CompatibilityRule(BaseModel):
    id: Optional[str] = None
    material_type: str
    wagon_type: str
    compatibility_score: float  # 0.0 to 1.0
    restrictions: List[str] = []
    loading_efficiency: float = 1.0

class CompatibilityRuleResponse(CompatibilityRule):
    id: str

# Route Management
class Route(BaseModel):
    id: Optional[str] = None
    name: str
    origin: str
    destination: str
    distance_km: float
    estimated_time_hours: float
    restrictions: List[str] = []
    cost_per_km: float
    is_active: bool = True

class RouteResponse(Route):
    id: str

# Multi-destination Rake Formation
class MultiDestinationRake(BaseModel):
    id: Optional[str] = None
    rake_number: str
    destinations: List[Dict[str, Any]]  # [{"destination": "City", "wagon_ids": [], "order_ids": []}]
    total_wagons: int
    formation_date: datetime
    status: RakeStatus
    route_plan: List[str]  # Sequence of destinations
    total_distance: float
    estimated_completion: datetime
    ai_recommendation: Optional[str] = None

class MultiDestinationRakeResponse(MultiDestinationRake):
    id: str

# Capacity Monitoring
class CapacityMonitor(BaseModel):
    id: Optional[str] = None
    loading_point_id: str
    timestamp: datetime
    current_utilization: float  # 0.0 to 1.0
    planned_utilization: float
    available_capacity: float
    queued_rakes: int
    estimated_wait_time: float  # in hours

class CapacityMonitorResponse(CapacityMonitor):
    id: str
    loading_point_name: Optional[str] = None

# ERP Integration
class ERPSync(BaseModel):
    id: Optional[str] = None
    system_name: str  # "SAP", "Oracle", etc.
    last_sync: datetime
    sync_status: str  # "success", "failed", "in_progress"
    records_synced: int
    error_message: Optional[str] = None

class ERPSyncResponse(ERPSync):
    id: str

# Workflow Management
class WorkflowApproval(BaseModel):
    id: Optional[str] = None
    entity_type: str  # "rake", "order", "allocation"
    entity_id: str
    approver_id: str
    approval_status: ApprovalStatus
    comments: Optional[str] = None
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None

class WorkflowApprovalResponse(WorkflowApproval):
    id: str
    entity_details: Optional[Dict] = None

# Advanced Analytics
class PerformanceMetrics(BaseModel):
    id: Optional[str] = None
    date: datetime
    total_rakes_dispatched: int
    average_loading_time: float
    on_time_delivery_rate: float
    cost_efficiency: float
    wagon_utilization_rate: float
    customer_satisfaction_score: float

class PerformanceMetricsResponse(PerformanceMetrics):
    id: str

# Real-time Dashboard Data
class ControlRoomDashboard(BaseModel):
    timestamp: datetime
    active_rakes: Dict[str, int]  # {"loading": 5, "in_transit": 10, "unloading": 3}
    wagon_status_summary: Dict[str, int]  # {"available": 50, "loaded": 30, "maintenance": 5}
    stockyard_utilization: Dict[str, float]  # {"Stockyard A": 0.75, "Stockyard B": 0.60}
    urgent_alerts: List[Dict[str, Any]]
    performance_kpis: Dict[str, float]
    live_tracking_count: int

# Report Generation
class ReportRequest(BaseModel):
    report_type: str  # "daily_plan", "performance", "inventory", "utilization"
    start_date: datetime
    end_date: datetime
    format: str = "pdf"  # "pdf", "excel", "csv"
    include_charts: bool = True
    email_recipients: List[str] = []

class ReportResponse(BaseModel):
    report_id: str
    status: str
    download_url: Optional[str] = None
    generated_at: datetime

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
        lp_result = await db.loading_points.insert_many(loading_points)
        lp_ids = [str(id) for id in lp_result.inserted_ids]
        
        # Create advanced control room sample data
        
        # Create compatibility rules
        compatibility_rules = [
            {"material_type": "Bulk", "wagon_type": "BOXN", "compatibility_score": 0.95, "restrictions": [], "loading_efficiency": 0.9},
            {"material_type": "Bulk", "wagon_type": "BCN", "compatibility_score": 0.85, "restrictions": ["no_heavy_loads"], "loading_efficiency": 0.8},
            {"material_type": "Finished", "wagon_type": "BRN", "compatibility_score": 0.9, "restrictions": [], "loading_efficiency": 0.85},
            {"material_type": "Finished", "wagon_type": "BOST", "compatibility_score": 0.95, "restrictions": [], "loading_efficiency": 0.9},
        ]
        await db.compatibility_rules.insert_many(compatibility_rules)
        
        # Create routes
        routes = [
            {"name": "Plant-Mumbai", "origin": "Plant North", "destination": "Mumbai", "distance_km": 1200, "estimated_time_hours": 24, "restrictions": [], "cost_per_km": 5.0, "is_active": True},
            {"name": "Plant-Delhi", "origin": "Plant South", "destination": "Delhi", "distance_km": 800, "estimated_time_hours": 18, "restrictions": ["no_hazardous"], "cost_per_km": 6.0, "is_active": True},
            {"name": "Plant-Kolkata", "origin": "Plant East", "destination": "Kolkata", "distance_km": 600, "estimated_time_hours": 14, "restrictions": [], "cost_per_km": 4.5, "is_active": True},
            {"name": "Plant-Chennai", "origin": "Plant North", "destination": "Chennai", "distance_km": 1500, "estimated_time_hours": 30, "restrictions": [], "cost_per_km": 5.5, "is_active": True},
        ]
        await db.routes.insert_many(routes)
        
        # Create wagon tracking data
        wagon_ids = []
        for i in range(1, 51):
            wagon_id = f"{i:03d}"
            wagon_ids.append(wagon_id)
        
        wagon_tracking = []
        for i, wagon_id in enumerate(wagon_ids[:10]):  # Track first 10 wagons
            tracking = {
                "wagon_id": wagon_id,
                "current_location": f"Location-{(i % 3) + 1}",
                "destination": random.choice(["Mumbai", "Delhi", "Kolkata", "Chennai"]) if i < 5 else None,
                "status": random.choice(["available", "loaded", "in_transit", "maintenance"]),
                "load_percentage": random.uniform(0, 100),
                "estimated_arrival": datetime.utcnow() + timedelta(hours=random.randint(2, 48)) if i < 5 else None,
                "last_updated": datetime.utcnow(),
                "gps_coordinates": {"lat": 19.0760 + random.uniform(-1, 1), "lng": 72.8777 + random.uniform(-1, 1)}
            }
            wagon_tracking.append(tracking)
        await db.wagon_tracking.insert_many(wagon_tracking)
        
        # Create capacity monitoring data
        capacity_monitors = []
        for lp_id in lp_ids:
            for hour in range(24):
                monitor = {
                    "loading_point_id": lp_id,
                    "timestamp": datetime.utcnow() - timedelta(hours=hour),
                    "current_utilization": random.uniform(0.2, 0.9),
                    "planned_utilization": random.uniform(0.5, 1.0),
                    "available_capacity": random.uniform(2, 8),
                    "queued_rakes": random.randint(0, 3),
                    "estimated_wait_time": random.uniform(0.5, 4)
                }
                capacity_monitors.append(monitor)
        await db.capacity_monitoring.insert_many(capacity_monitors)
        
        # Create multi-destination rake
        multi_dest_rake = {
            "rake_number": "MDR-001",
            "destinations": [
                {"destination": "Mumbai", "wagon_ids": wagon_ids[:10], "order_ids": []},
                {"destination": "Delhi", "wagon_ids": wagon_ids[10:20], "order_ids": []},
            ],
            "total_wagons": 20,
            "formation_date": datetime.utcnow(),
            "status": "planned",
            "route_plan": ["Plant North", "Mumbai", "Delhi"],
            "total_distance": 2000,
            "estimated_completion": datetime.utcnow() + timedelta(days=3),
            "ai_recommendation": "Optimized for multi-destination efficiency with cost savings of 15%"
        }
        await db.multi_destination_rakes.insert_one(multi_dest_rake)
        
        # Create workflow approvals
        workflow_approvals = [
            {
                "entity_type": "rake",
                "entity_id": "sample_rake_id",
                "approver_id": "operator_001",
                "approval_status": "pending",
                "comments": "Pending review for high priority order",
                "requested_at": datetime.utcnow()
            },
            {
                "entity_type": "order",
                "entity_id": "sample_order_id", 
                "approver_id": "supervisor_001",
                "approval_status": "approved",
                "comments": "Approved for immediate dispatch",
                "requested_at": datetime.utcnow() - timedelta(hours=2),
                "processed_at": datetime.utcnow() - timedelta(hours=1)
            }
        ]
        await db.workflow_approvals.insert_many(workflow_approvals)
        
        # Create ERP sync records
        erp_syncs = [
            {
                "system_name": "SAP",
                "last_sync": datetime.utcnow() - timedelta(minutes=30),
                "sync_status": "success",
                "records_synced": 1250,
                "error_message": None
            },
            {
                "system_name": "Oracle",
                "last_sync": datetime.utcnow() - timedelta(hours=2),
                "sync_status": "success", 
                "records_synced": 890,
                "error_message": None
            }
        ]
        await db.erp_sync.insert_many(erp_syncs)
        
        # Create performance metrics
        performance_metrics = []
        for day in range(7):
            metrics = {
                "date": datetime.utcnow() - timedelta(days=day),
                "total_rakes_dispatched": random.randint(8, 15),
                "average_loading_time": random.uniform(2.5, 4.5),
                "on_time_delivery_rate": random.uniform(0.85, 0.95),
                "cost_efficiency": random.uniform(0.8, 0.92),
                "wagon_utilization_rate": random.uniform(0.75, 0.9),
                "customer_satisfaction_score": random.uniform(4.2, 4.8)
            }
            performance_metrics.append(metrics)
        await db.performance_metrics.insert_many(performance_metrics)
        
        return {"message": "Advanced control room sample data initialized successfully"}
    except Exception as e:
        logger.error(f"Error initializing data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================
# ADVANCED CONTROL ROOM FEATURES API ENDPOINTS
# =====================================================

# Real-time Wagon Tracking
@api_router.post("/wagon-tracking", response_model=WagonTrackingResponse)
async def create_wagon_tracking(tracking: WagonTracking):
    tracking_dict = tracking.dict(exclude={'id'})
    result = await db.wagon_tracking.insert_one(tracking_dict)
    
    # Get wagon details
    tracking_obj = await db.wagon_tracking.find_one({'_id': result.inserted_id})
    tracking_obj = obj_to_dict(tracking_obj)
    wagon = await db.wagons.find_one({'_id': ObjectId(tracking_obj['wagon_id'])})
    tracking_obj['wagon_number'] = wagon['wagon_number'] if wagon else None
    tracking_obj['wagon_type'] = wagon['type'] if wagon else None
    
    return WagonTrackingResponse(**tracking_obj)

@api_router.get("/wagon-tracking", response_model=List[WagonTrackingResponse])
async def get_wagon_tracking():
    trackings = await db.wagon_tracking.find().sort('last_updated', -1).to_list(1000)
    result = []
    for tracking in trackings:
        tracking = obj_to_dict(tracking)
        # Try to find wagon by ObjectId first, then by wagon_number if that fails
        wagon = None
        try:
            wagon = await db.wagons.find_one({'_id': ObjectId(tracking['wagon_id'])})
        except:
            # If ObjectId fails, try to find by wagon_number (for string IDs like "001")
            wagon_number = f"W{tracking['wagon_id']}"
            wagon = await db.wagons.find_one({'wagon_number': wagon_number})
        
        tracking['wagon_number'] = wagon['wagon_number'] if wagon else None
        tracking['wagon_type'] = wagon['type'] if wagon else None
        result.append(WagonTrackingResponse(**tracking))
    return result

@api_router.get("/wagon-tracking/real-time")
async def get_real_time_tracking():
    """Get real-time status of all wagons"""
    # Simulate real-time data updates
    wagons = await db.wagons.find().to_list(1000)
    tracking_data = []
    
    for wagon in wagons:
        wagon = obj_to_dict(wagon)
        # Simulate real-time position and status
        tracking_data.append({
            "wagon_id": wagon['id'],
            "wagon_number": wagon['wagon_number'],
            "status": wagon['status'],
            "current_location": f"Location-{random.randint(1, 10)}",
            "load_percentage": random.uniform(0, 100),
            "last_updated": datetime.utcnow().isoformat()
        })
    
    return {"timestamp": datetime.utcnow(), "wagons": tracking_data}

# Compatibility Matrix Management
@api_router.post("/compatibility-rules", response_model=CompatibilityRuleResponse)
async def create_compatibility_rule(rule: CompatibilityRule):
    rule_dict = rule.dict(exclude={'id'})
    result = await db.compatibility_rules.insert_one(rule_dict)
    rule_dict['id'] = str(result.inserted_id)
    return CompatibilityRuleResponse(**rule_dict)

@api_router.get("/compatibility-rules", response_model=List[CompatibilityRuleResponse])
async def get_compatibility_rules():
    rules = await db.compatibility_rules.find().to_list(1000)
    return [CompatibilityRuleResponse(**obj_to_dict(rule)) for rule in rules]

@api_router.get("/compatibility-matrix/{material_type}")
async def get_compatibility_matrix(material_type: str):
    """Get compatibility matrix for a specific material type"""
    rules = await db.compatibility_rules.find({"material_type": material_type}).to_list(100)
    matrix = {}
    for rule in rules:
        rule = obj_to_dict(rule)
        matrix[rule['wagon_type']] = {
            "compatibility_score": rule['compatibility_score'],
            "restrictions": rule['restrictions'],
            "loading_efficiency": rule['loading_efficiency']
        }
    return {"material_type": material_type, "compatibility_matrix": matrix}

# Route Management
@api_router.post("/routes", response_model=RouteResponse)
async def create_route(route: Route):
    route_dict = route.dict(exclude={'id'})
    result = await db.routes.insert_one(route_dict)
    route_dict['id'] = str(result.inserted_id)
    return RouteResponse(**route_dict)

@api_router.get("/routes", response_model=List[RouteResponse])
async def get_routes():
    routes = await db.routes.find().to_list(1000)
    return [RouteResponse(**obj_to_dict(route)) for route in routes]

@api_router.post("/routes/validate")
async def validate_route(route_data: Dict[str, Any]):
    """Validate route feasibility and restrictions"""
    origin = route_data.get('origin')
    destination = route_data.get('destination')
    wagon_type = route_data.get('wagon_type')
    
    # Check for existing routes
    route = await db.routes.find_one({
        "origin": origin, 
        "destination": destination,
        "is_active": True
    })
    
    if not route:
        return {
            "valid": False,
            "message": "No active route found between specified locations",
            "restrictions": []
        }
    
    route = obj_to_dict(route)
    
    # Check wagon type restrictions
    wagon_restrictions = []
    if wagon_type in route.get('restrictions', []):
        wagon_restrictions.append(f"Wagon type {wagon_type} not allowed on this route")
    
    return {
        "valid": len(wagon_restrictions) == 0,
        "route_id": route['id'],
        "distance_km": route['distance_km'],
        "estimated_time_hours": route['estimated_time_hours'],
        "cost_per_km": route['cost_per_km'],
        "restrictions": wagon_restrictions,
        "message": "Route validated successfully" if len(wagon_restrictions) == 0 else "Route has restrictions"
    }

# Multi-destination Rake Formation
@api_router.post("/multi-destination-rakes", response_model=MultiDestinationRakeResponse)
async def create_multi_destination_rake(rake: MultiDestinationRake):
    rake_dict = rake.dict(exclude={'id'})
    result = await db.multi_destination_rakes.insert_one(rake_dict)
    rake_dict['id'] = str(result.inserted_id)
    return MultiDestinationRakeResponse(**rake_dict)

@api_router.get("/multi-destination-rakes", response_model=List[MultiDestinationRakeResponse])
async def get_multi_destination_rakes():
    rakes = await db.multi_destination_rakes.find().to_list(1000)
    return [MultiDestinationRakeResponse(**obj_to_dict(rake)) for rake in rakes]

@api_router.post("/optimize-multi-destination")
async def optimize_multi_destination_rake(request: Dict[str, Any]):
    """AI optimization for multi-destination rake formation"""
    try:
        destinations = request.get('destinations', [])
        max_wagons = request.get('max_wagons', 50)
        
        # Fetch relevant data
        orders_by_dest = {}
        for dest in destinations:
            orders = await db.orders.find({"destination": dest, "status": "pending"}).to_list(100)
            orders_by_dest[dest] = [obj_to_dict(order) for order in orders]
        
        # Create AI prompt for multi-destination optimization
        prompt = f"""
        Optimize multi-destination rake formation for destinations: {destinations}
        
        Available orders by destination:
        {json.dumps(orders_by_dest, indent=2, default=str)}
        
        Constraints:
        - Maximum {max_wagons} wagons per rake
        - Minimize total route distance
        - Optimize loading sequence
        - Consider destination proximity
        
        Provide optimal sequence and wagon allocation.
        """
        
        # Initialize AI chat
        llm_chat = LlmChat(
            api_key=os.environ['EMERGENT_LLM_KEY'],
            session_id=f"multi_dest_optimization_{datetime.utcnow().timestamp()}",
            system_message="You are an expert in multi-destination railway logistics optimization."
        ).with_model("openai", "gpt-4o")
        
        user_message = UserMessage(text=prompt)
        response = await llm_chat.send_message(user_message)
        
        return {
            "optimization_result": response,
            "destinations": destinations,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Multi-destination optimization error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Capacity Monitoring
@api_router.post("/capacity-monitoring", response_model=CapacityMonitorResponse)
async def create_capacity_monitor(monitor: CapacityMonitor):
    monitor_dict = monitor.dict(exclude={'id'})
    result = await db.capacity_monitoring.insert_one(monitor_dict)
    
    monitor_obj = await db.capacity_monitoring.find_one({'_id': result.inserted_id})
    monitor_obj = obj_to_dict(monitor_obj)
    loading_point = await db.loading_points.find_one({'_id': ObjectId(monitor_obj['loading_point_id'])})
    monitor_obj['loading_point_name'] = loading_point['name'] if loading_point else None
    
    return CapacityMonitorResponse(**monitor_obj)

@api_router.get("/capacity-monitoring/real-time")
async def get_real_time_capacity():
    """Get real-time capacity utilization across all loading points"""
    loading_points = await db.loading_points.find().to_list(1000)
    capacity_data = []
    
    for lp in loading_points:
        lp = obj_to_dict(lp)
        # Simulate real-time capacity data
        utilization = random.uniform(0.2, 0.9)
        capacity_data.append({
            "loading_point_id": lp['id'],
            "loading_point_name": lp['name'],
            "current_utilization": utilization,
            "available_capacity": lp['capacity'] * (1 - utilization),
            "queued_rakes": random.randint(0, 5),
            "estimated_wait_time": utilization * 2,  # Hours
            "status": "critical" if utilization > 0.8 else "warning" if utilization > 0.6 else "normal"
        })
    
    return {
        "timestamp": datetime.utcnow(),
        "loading_points": capacity_data,
        "overall_utilization": sum(lp['current_utilization'] for lp in capacity_data) / len(capacity_data)
    }

# ERP Integration
@api_router.post("/erp-sync", response_model=ERPSyncResponse)
async def create_erp_sync(sync: ERPSync):
    sync_dict = sync.dict(exclude={'id'})
    result = await db.erp_sync.insert_one(sync_dict)
    sync_dict['id'] = str(result.inserted_id)
    return ERPSyncResponse(**sync_dict)

@api_router.get("/erp-sync/status")
async def get_erp_sync_status():
    """Get latest ERP synchronization status"""
    syncs = await db.erp_sync.find().sort('last_sync', -1).to_list(10)
    return {
        "timestamp": datetime.utcnow(),
        "recent_syncs": [obj_to_dict(sync) for sync in syncs],
        "systems_status": {
            "SAP": "connected" if syncs and syncs[0].get('system_name') == 'SAP' else "disconnected",
            "Oracle": "connected" if syncs and syncs[0].get('system_name') == 'Oracle' else "disconnected"
        }
    }

@api_router.post("/erp-sync/trigger")
async def trigger_erp_sync(system_data: Dict[str, Any]):
    """Trigger manual ERP synchronization"""
    system_name = system_data.get('system_name')
    
    # Simulate ERP sync process
    sync_record = {
        "system_name": system_name,
        "last_sync": datetime.utcnow(),
        "sync_status": "success",
        "records_synced": random.randint(100, 1000),
        "error_message": None
    }
    
    await db.erp_sync.insert_one(sync_record)
    
    return {
        "message": f"ERP sync triggered for {system_name}",
        "sync_id": str(sync_record.get('_id')),
        "estimated_completion": datetime.utcnow() + timedelta(minutes=5)
    }

# Workflow Management
@api_router.post("/workflow/approvals", response_model=WorkflowApprovalResponse)
async def create_workflow_approval(approval: WorkflowApproval):
    approval_dict = approval.dict(exclude={'id'})
    result = await db.workflow_approvals.insert_one(approval_dict)
    
    approval_obj = await db.workflow_approvals.find_one({'_id': result.inserted_id})
    approval_obj = obj_to_dict(approval_obj)
    
    # Get entity details based on type
    entity_details = None
    if approval_obj['entity_type'] == 'rake':
        entity = await db.rakes.find_one({'_id': ObjectId(approval_obj['entity_id'])})
        entity_details = obj_to_dict(entity) if entity else None
    elif approval_obj['entity_type'] == 'order':
        entity = await db.orders.find_one({'_id': ObjectId(approval_obj['entity_id'])})
        entity_details = obj_to_dict(entity) if entity else None
    
    approval_obj['entity_details'] = entity_details
    return WorkflowApprovalResponse(**approval_obj)

@api_router.get("/workflow/approvals/pending")
async def get_pending_approvals():
    """Get all pending workflow approvals"""
    approvals = await db.workflow_approvals.find({"approval_status": "pending"}).sort('requested_at', -1).to_list(100)
    result = []
    
    for approval in approvals:
        approval = obj_to_dict(approval)
        # Get entity details
        entity_details = None
        try:
            if approval['entity_type'] == 'rake':
                entity = await db.rakes.find_one({'_id': ObjectId(approval['entity_id'])})
                entity_details = obj_to_dict(entity) if entity else None
            elif approval['entity_type'] == 'order':
                entity = await db.orders.find_one({'_id': ObjectId(approval['entity_id'])})
                entity_details = obj_to_dict(entity) if entity else None
        except:
            # If ObjectId is invalid, set entity_details to None
            entity_details = None
            
        approval['entity_details'] = entity_details
        result.append(WorkflowApprovalResponse(**approval))
    
    return result

@api_router.put("/workflow/approvals/{approval_id}")
async def update_approval_status(approval_id: str, update_data: Dict[str, Any]):
    """Update approval status (approve/reject)"""
    update_dict = {
        "approval_status": update_data.get('status'),
        "comments": update_data.get('comments'),
        "processed_at": datetime.utcnow()
    }
    
    await db.workflow_approvals.update_one(
        {'_id': ObjectId(approval_id)}, 
        {'$set': update_dict}
    )
    
    # Get updated approval
    approval = await db.workflow_approvals.find_one({'_id': ObjectId(approval_id)})
    return obj_to_dict(approval) if approval else None

# Advanced Analytics and Performance
@api_router.get("/analytics/performance")
async def get_performance_analytics():
    """Get comprehensive performance analytics"""
    # Simulate performance data
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    # Calculate metrics from existing data
    total_orders = await db.orders.count_documents({})
    completed_orders = await db.orders.count_documents({"status": "delivered"})
    total_rakes = await db.rakes.count_documents({})
    active_rakes = await db.rakes.count_documents({"status": {"$in": ["planned", "loading", "in_transit"]}})
    
    analytics = {
        "period": {"start": start_date, "end": end_date},
        "kpis": {
            "order_completion_rate": (completed_orders / total_orders * 100) if total_orders > 0 else 0,
            "rake_utilization_rate": (active_rakes / total_rakes * 100) if total_rakes > 0 else 0,
            "on_time_delivery_rate": random.uniform(85, 95),
            "cost_efficiency": random.uniform(88, 92),
            "customer_satisfaction": random.uniform(4.2, 4.8)
        },
        "trends": {
            "daily_dispatches": [random.randint(5, 15) for _ in range(30)],
            "utilization_trend": [random.uniform(0.6, 0.9) for _ in range(30)],
            "cost_trend": [random.uniform(1000, 2000) for _ in range(30)]
        }
    }
    
    return analytics

# Control Room Dashboard
@api_router.get("/control-room/dashboard")
async def get_control_room_dashboard():
    """Get comprehensive control room dashboard data"""
    # Real-time stats
    active_rakes_stats = {}
    for status in ["planned", "loading", "in_transit", "unloading"]:
        count = await db.rakes.count_documents({"status": status})
        active_rakes_stats[status] = count
    
    wagon_status_stats = {}
    for status in ["available", "loaded", "in_transit", "maintenance"]:
        count = await db.wagons.count_documents({"status": status})
        wagon_status_stats[status] = count
    
    # Stockyard utilization (simulated)
    stockyards = await db.stockyards.find().to_list(100)
    stockyard_util = {}
    for sy in stockyards:
        sy = obj_to_dict(sy)
        stockyard_util[sy['name']] = random.uniform(0.4, 0.9)
    
    # Urgent alerts (simulated)
    urgent_alerts = [
        {"type": "delay", "message": "Rake R001 delayed by 2 hours", "priority": "high"},
        {"type": "capacity", "message": "Loading Point LP-1 at 95% capacity", "priority": "medium"},
        {"type": "maintenance", "message": "5 wagons due for maintenance", "priority": "low"}
    ]
    
    # Performance KPIs
    kpis = {
        "efficiency": random.uniform(0.85, 0.95),
        "utilization": random.uniform(0.75, 0.85),
        "on_time_delivery": random.uniform(0.88, 0.96),
        "cost_optimization": random.uniform(0.82, 0.92)
    }
    
    dashboard_data = ControlRoomDashboard(
        timestamp=datetime.utcnow(),
        active_rakes=active_rakes_stats,
        wagon_status_summary=wagon_status_stats,
        stockyard_utilization=stockyard_util,
        urgent_alerts=urgent_alerts,
        performance_kpis=kpis,
        live_tracking_count=sum(wagon_status_stats.values())
    )
    
    return dashboard_data

# Report Generation
@api_router.post("/reports/generate")
async def generate_report(request: ReportRequest):
    """Generate various types of reports"""
    report_id = f"RPT_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    # Simulate report generation process
    report_data = {
        "report_id": report_id,
        "type": request.report_type,
        "period": {"start": request.start_date, "end": request.end_date},
        "generated_at": datetime.utcnow(),
        "format": request.format
    }
    
    # Store report metadata
    await db.reports.insert_one(report_data)
    
    return ReportResponse(
        report_id=report_id,
        status="generated",
        download_url=f"/api/reports/download/{report_id}",
        generated_at=datetime.utcnow()
    )

@api_router.get("/reports/download/{report_id}")
async def download_report(report_id: str):
    """Download generated report"""
    # Simulate CSV report generation
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Sample report data
    writer.writerow(["Date", "Rakes Dispatched", "On-Time Delivery", "Cost Efficiency"])
    for i in range(10):
        writer.writerow([
            (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d'),
            random.randint(5, 15),
            f"{random.uniform(85, 95):.1f}%",
            f"{random.uniform(1000, 2000):.2f}"
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={report_id}.csv"}
    )

# Cost Optimization Models
class CostOptimizationRequest(BaseModel):
    order_ids: List[str]
    max_budget: Optional[float] = None
    optimization_type: str = "minimize_total_cost"  # minimize_total_cost, minimize_transport, minimize_penalties

class CostBreakdown(BaseModel):
    loading_cost: float
    transport_cost: float
    demurrage_cost: float
    penalty_cost: float
    total_cost: float

class StockyardRecommendation(BaseModel):
    id: str
    name: str
    location: str

class CostAnalysis(BaseModel):
    order_id: str
    customer_name: str
    material_name: str
    quantity: float
    destination: str
    best_stockyard: StockyardRecommendation
    cost_breakdown: CostBreakdown
    cost_savings: float
    efficiency_score: float

class CostOptimizationResult(BaseModel):
    total_orders: int
    total_savings: float
    average_efficiency: float
    cost_analyses: List[CostAnalysis]
    recommended_actions: List[str]

# Cost Optimization Engine
@api_router.post("/cost-optimization", response_model=CostOptimizationResult)
async def optimize_costs(request: CostOptimizationRequest):
    try:
        cost_analyses = []
        total_savings = 0
        
        for order_id in request.order_ids:
            order = await db.orders.find_one({'_id': ObjectId(order_id)})
            if not order:
                continue
            
            order = obj_to_dict(order)
            material = await db.materials.find_one({'_id': ObjectId(order['material_id'])})
            
            # Get all stockyards with this material
            inventories = await db.inventory.find({
                'material_id': order['material_id'],
                'quantity': {'$gte': order['quantity']}
            }).to_list(100)
            
            best_cost = float('inf')
            best_stockyard_data = None
            best_breakdown = None
            
            for inventory in inventories:
                inventory = obj_to_dict(inventory)
                stockyard = await db.stockyards.find_one({'_id': ObjectId(inventory['stockyard_id'])})
                if not stockyard:
                    continue
                stockyard = obj_to_dict(stockyard)
                
                # Calculate cost breakdown
                loading_cost = order['quantity'] * 25  # ₹25 per MT loading cost
                
                # Simplified distance calculation (in real app, use actual distance)
                distance_km = 500 + (hash(stockyard['location'] + order['destination']) % 1000)
                transport_cost = distance_km * 5.5 * order['quantity'] / 60  # ₹5.5 per km per wagon
                
                # Demurrage cost (based on loading point capacity and queue)
                loading_points = await db.loading_points.find({'stockyard_id': inventory['stockyard_id']}).to_list(10)
                avg_utilization = sum(lp.get('current_utilization', 0.5) for lp in loading_points) / len(loading_points) if loading_points else 0.5
                demurrage_days = max(1, avg_utilization * 3)  # More utilization = more wait time
                demurrage_cost = demurrage_days * 2000 * (order['quantity'] / 60)  # ₹2000 per day per wagon
                
                # Penalty cost (based on deadline proximity)
                days_to_deadline = order.get('days_until_deadline', 7)
                transport_days = distance_km / 400  # Assume 400km per day
                total_days = demurrage_days + transport_days
                
                penalty_cost = 0
                if total_days > days_to_deadline:
                    delay_days = total_days - days_to_deadline
                    penalty_cost = delay_days * order.get('penalty_per_day', 5000)
                
                total_cost = loading_cost + transport_cost + demurrage_cost + penalty_cost
                
                if total_cost < best_cost:
                    best_cost = total_cost
                    best_stockyard_data = stockyard
                    best_breakdown = {
                        'loading_cost': loading_cost,
                        'transport_cost': transport_cost,
                        'demurrage_cost': demurrage_cost,
                        'penalty_cost': penalty_cost,
                        'total_cost': total_cost
                    }
            
            if best_stockyard_data and best_breakdown:
                # Calculate savings (compared to average cost)
                average_cost = best_cost * 1.3  # Assume 30% higher without optimization
                cost_savings = average_cost - best_cost
                efficiency_score = min(95, (average_cost - best_cost) / average_cost * 100)
                
                total_savings += cost_savings
                
                cost_analyses.append(CostAnalysis(
                    order_id=order_id,
                    customer_name=order['customer_name'],
                    material_name=material['name'] if material else 'Unknown',
                    quantity=order['quantity'],
                    destination=order['destination'],
                    best_stockyard=StockyardRecommendation(
                        id=best_stockyard_data['id'],
                        name=best_stockyard_data['name'],
                        location=best_stockyard_data['location']
                    ),
                    cost_breakdown=CostBreakdown(**best_breakdown),
                    cost_savings=cost_savings,
                    efficiency_score=efficiency_score
                ))
        
        average_efficiency = sum(analysis.efficiency_score for analysis in cost_analyses) / len(cost_analyses) if cost_analyses else 0
        
        recommended_actions = [
            f"Switch {len([a for a in cost_analyses if a.cost_savings > 10000])} high-impact orders to optimized stockyards",
            f"Prioritize orders with penalty risks to avoid ₹{sum(a.cost_breakdown.penalty_cost for a in cost_analyses):,.0f} in penalties",
            f"Coordinate loading schedules to reduce ₹{sum(a.cost_breakdown.demurrage_cost for a in cost_analyses):,.0f} in demurrage costs"
        ]
        
        return CostOptimizationResult(
            total_orders=len(cost_analyses),
            total_savings=total_savings,
            average_efficiency=average_efficiency,
            cost_analyses=cost_analyses,
            recommended_actions=recommended_actions
        )
        
    except Exception as e:
        logger.error(f"Cost optimization error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/implement-cost-optimization")
async def implement_cost_optimization(data: Dict[str, Any]):
    try:
        cost_analyses = data.get('cost_analyses', [])
        
        for analysis in cost_analyses:
            order_id = analysis['order_id']
            best_stockyard_id = analysis['best_stockyard']['id']
            
            # Update order with recommended stockyard assignment
            await db.orders.update_one(
                {'_id': ObjectId(order_id)},
                {'$set': {
                    'assigned_stockyard_id': best_stockyard_id,
                    'cost_optimized': True,
                    'optimization_date': datetime.utcnow(),
                    'estimated_total_cost': analysis['cost_breakdown']['total_cost'],
                    'cost_savings': analysis['cost_savings']
                }}
            )
        
        return {
            "message": f"Cost optimization implemented for {len(cost_analyses)} orders",
            "total_orders_optimized": len(cost_analyses),
            "implementation_date": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Implementation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced stockyard selection endpoint
@api_router.get("/stockyard-selection/{order_id}")
async def get_optimal_stockyard_selection(order_id: str):
    try:
        order = await db.orders.find_one({'_id': ObjectId(order_id)})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order = obj_to_dict(order)
        
        # Get all available stockyards with the required material
        inventories = await db.inventory.find({
            'material_id': order['material_id'],
            'quantity': {'$gte': order['quantity']}
        }).to_list(100)
        
        stockyard_options = []
        
        for inventory in inventories:
            inventory = obj_to_dict(inventory)
            stockyard = await db.stockyards.find_one({'_id': ObjectId(inventory['stockyard_id'])})
            
            if stockyard:
                stockyard = obj_to_dict(stockyard)
                
                # Calculate comprehensive cost analysis
                loading_cost = order['quantity'] * 25
                distance_km = 500 + (hash(stockyard['location'] + order['destination']) % 1000)
                transport_cost = distance_km * 5.5 * order['quantity'] / 60
                
                loading_points = await db.loading_points.find({'stockyard_id': ObjectId(inventory['stockyard_id'])}).to_list(10)
                avg_utilization = sum(lp.get('current_utilization', 0.5) for lp in loading_points) / len(loading_points) if loading_points else 0.5
                
                demurrage_cost = max(1, avg_utilization * 3) * 2000 * (order['quantity'] / 60)
                
                total_cost = loading_cost + transport_cost + demurrage_cost
                
                stockyard_options.append({
                    'stockyard_id': stockyard['id'],
                    'stockyard_name': stockyard['name'],
                    'location': stockyard['location'],
                    'available_quantity': inventory['quantity'],
                    'cost_per_unit': inventory['cost_per_unit'],
                    'distance_km': distance_km,
                    'loading_cost': loading_cost,
                    'transport_cost': transport_cost,
                    'demurrage_cost': demurrage_cost,
                    'total_logistics_cost': total_cost,
                    'loading_point_utilization': avg_utilization,
                    'efficiency_score': max(50, 100 - (avg_utilization * 50))
                })
        
        # Sort by total cost
        stockyard_options.sort(key=lambda x: x['total_logistics_cost'])
        
        return {
            'order_id': order_id,
            'order_details': {
                'customer_name': order['customer_name'],
                'quantity': order['quantity'],
                'destination': order['destination']
            },
            'stockyard_options': stockyard_options,
            'recommendation': stockyard_options[0] if stockyard_options else None
        }
        
    except Exception as e:
        logger.error(f"Stockyard selection error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket for Real-time Updates
websocket_connections = []

@app.websocket("/ws/real-time-updates")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_connections.append(websocket)
    try:
        while True:
            # Send real-time updates every 5 seconds
            await asyncio.sleep(5)
            
            # Generate random update
            update_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "type": random.choice(["wagon_update", "rake_status", "capacity_alert"]),
                "data": {
                    "message": f"Update at {datetime.utcnow().strftime('%H:%M:%S')}",
                    "value": random.randint(1, 100)
                }
            }
            
            await websocket.send_json(update_data)
            
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)

@api_router.get("/")
async def root():
    return {"message": "Advanced Rake Formation Control Room API is running"}

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
