#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Rake Formation API - Operational & Real-Time Features
Testing all newly implemented operational features as specified in the review request.
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random

# Backend URL from frontend .env
BACKEND_URL = "https://trackflow-ui.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.existing_ids = {}
        
    def log_result(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if response_data:
            result["response_data"] = response_data
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()

    def get_existing_ids(self):
        """Get existing IDs from database for testing"""
        try:
            # Get existing rakes
            response = self.session.get(f"{self.base_url}/rakes")
            if response.status_code == 200:
                rakes = response.json()
                if rakes:
                    self.existing_ids['rake_id'] = rakes[0]['id']
            
            # Get existing wagons
            response = self.session.get(f"{self.base_url}/wagons")
            if response.status_code == 200:
                wagons = response.json()
                if wagons:
                    self.existing_ids['wagon_id'] = wagons[0]['id']
            
            # Get existing loading points
            response = self.session.get(f"{self.base_url}/loading-points")
            if response.status_code == 200:
                loading_points = response.json()
                if loading_points:
                    self.existing_ids['loading_point_id'] = loading_points[0]['id']
                    
            print(f"Retrieved existing IDs: {self.existing_ids}")
            
        except Exception as e:
            print(f"Warning: Could not retrieve existing IDs: {e}")

    def test_iot_sensors_integration(self):
        """Test IoT Sensors Integration endpoints"""
        print("=== Testing IoT Sensors Integration ===")
        
        # Test 1: Create IoT sensor data with different sensor types and statuses
        sensor_data_tests = [
            {
                "sensor_id": "TEMP_001",
                "sensor_type": "temperature",
                "loading_point_id": self.existing_ids.get('loading_point_id', 'test_lp_id'),
                "value": 45.5,
                "unit": "celsius",
                "status": "normal",
                "threshold_min": 0,
                "threshold_max": 50,
                "location": {"lat": 19.0760, "lng": 72.8777}
            },
            {
                "sensor_id": "WEIGHT_001", 
                "sensor_type": "weight",
                "loading_point_id": self.existing_ids.get('loading_point_id', 'test_lp_id'),
                "value": 58.2,
                "unit": "tons",
                "status": "warning",
                "threshold_min": 0,
                "threshold_max": 60,
                "location": {"lat": 19.0760, "lng": 72.8777}
            },
            {
                "sensor_id": "VIB_001",
                "sensor_type": "vibration", 
                "loading_point_id": self.existing_ids.get('loading_point_id', 'test_lp_id'),
                "value": 8.5,
                "unit": "mm/s",
                "status": "critical",
                "threshold_min": 0,
                "threshold_max": 5,
                "location": {"lat": 19.0760, "lng": 72.8777}
            },
            {
                "sensor_id": "LOAD_001",
                "sensor_type": "load_status",
                "loading_point_id": self.existing_ids.get('loading_point_id', 'test_lp_id'), 
                "value": 1,
                "unit": "boolean",
                "status": "normal",
                "threshold_min": 0,
                "threshold_max": 1,
                "location": {"lat": 19.0760, "lng": 72.8777}
            }
        ]
        
        for i, sensor_data in enumerate(sensor_data_tests):
            try:
                response = self.session.post(f"{self.base_url}/iot/sensors", json=sensor_data)
                if response.status_code == 200:
                    result = response.json()
                    self.log_result(f"IoT Sensor Creation - {sensor_data['sensor_type']} ({sensor_data['status']})", 
                                  True, f"Sensor created with ID: {result.get('id')}")
                else:
                    self.log_result(f"IoT Sensor Creation - {sensor_data['sensor_type']}", 
                                  False, f"Status: {response.status_code}", response.text)
            except Exception as e:
                self.log_result(f"IoT Sensor Creation - {sensor_data['sensor_type']}", 
                              False, f"Exception: {str(e)}")

        # Test 2: Get real-time sensor data
        try:
            response = self.session.get(f"{self.base_url}/iot/sensors/real-time")
            if response.status_code == 200:
                result = response.json()
                self.log_result("IoT Real-time Data Retrieval", True, 
                              f"Retrieved {len(result.get('sensors', []))} sensors")
            else:
                self.log_result("IoT Real-time Data Retrieval", False, 
                              f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("IoT Real-time Data Retrieval", False, f"Exception: {str(e)}")

        # Test 3: Get real-time sensor data with loading point filter
        if self.existing_ids.get('loading_point_id'):
            try:
                response = self.session.get(f"{self.base_url}/iot/sensors/real-time", 
                                          params={"loading_point_id": self.existing_ids['loading_point_id']})
                if response.status_code == 200:
                    result = response.json()
                    self.log_result("IoT Real-time Data with Filter", True, 
                                  f"Filtered data for loading point: {self.existing_ids['loading_point_id']}")
                else:
                    self.log_result("IoT Real-time Data with Filter", False, 
                                  f"Status: {response.status_code}", response.text)
            except Exception as e:
                self.log_result("IoT Real-time Data with Filter", False, f"Exception: {str(e)}")

    def test_smart_weighbridge_integration(self):
        """Test Smart Weighbridge Integration endpoints"""
        print("=== Testing Smart Weighbridge Integration ===")
        
        # Test 1: Create weighbridge readings with different statuses
        weighbridge_tests = [
            {
                "wagon_id": self.existing_ids.get('wagon_id', 'test_wagon_id'),
                "gross_weight": 58.5,
                "tare_weight": 18.5,
                "net_weight": 40.0,
                "expected_weight": 40.0,
                "variance_percentage": 0.0,
                "status": "verified",
                "operator_id": "OP001",
                "weighbridge_id": "WB001"
            },
            {
                "wagon_id": self.existing_ids.get('wagon_id', 'test_wagon_id'),
                "gross_weight": 85.0,
                "tare_weight": 18.5,
                "net_weight": 66.5,
                "expected_weight": 60.0,
                "variance_percentage": 10.8,
                "status": "overload",
                "operator_id": "OP002", 
                "weighbridge_id": "WB002"
            },
            {
                "wagon_id": self.existing_ids.get('wagon_id', 'test_wagon_id'),
                "gross_weight": 48.0,
                "tare_weight": 18.5,
                "net_weight": 29.5,
                "expected_weight": 40.0,
                "variance_percentage": -26.25,
                "status": "underload",
                "operator_id": "OP003",
                "weighbridge_id": "WB003"
            },
            {
                "wagon_id": self.existing_ids.get('wagon_id', 'test_wagon_id'),
                "gross_weight": 72.0,
                "tare_weight": 18.5,
                "net_weight": 53.5,
                "expected_weight": 40.0,
                "variance_percentage": 33.75,
                "status": "suspicious",
                "operator_id": "OP004",
                "weighbridge_id": "WB004"
            }
        ]
        
        for weighbridge_data in weighbridge_tests:
            try:
                response = self.session.post(f"{self.base_url}/weighbridge/reading", json=weighbridge_data)
                if response.status_code == 200:
                    result = response.json()
                    self.log_result(f"Weighbridge Reading - {weighbridge_data['status']}", True, 
                                  f"Reading created with variance: {weighbridge_data['variance_percentage']}%")
                else:
                    self.log_result(f"Weighbridge Reading - {weighbridge_data['status']}", False, 
                                  f"Status: {response.status_code}", response.text)
            except Exception as e:
                self.log_result(f"Weighbridge Reading - {weighbridge_data['status']}", False, 
                              f"Exception: {str(e)}")

        # Test 2: Get weighbridge readings
        try:
            response = self.session.get(f"{self.base_url}/weighbridge/readings")
            if response.status_code == 200:
                result = response.json()
                self.log_result("Weighbridge Readings Retrieval", True, 
                              f"Retrieved {len(result.get('readings', []))} readings")
            else:
                self.log_result("Weighbridge Readings Retrieval", False, 
                              f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Weighbridge Readings Retrieval", False, f"Exception: {str(e)}")

        # Test 3: Get weighbridge readings with filters
        if self.existing_ids.get('wagon_id'):
            try:
                response = self.session.get(f"{self.base_url}/weighbridge/readings", 
                                          params={"wagon_id": self.existing_ids['wagon_id']})
                if response.status_code == 200:
                    result = response.json()
                    self.log_result("Weighbridge Readings with Wagon Filter", True, 
                                  f"Filtered readings for wagon: {self.existing_ids['wagon_id']}")
                else:
                    self.log_result("Weighbridge Readings with Wagon Filter", False, 
                                  f"Status: {response.status_code}", response.text)
            except Exception as e:
                self.log_result("Weighbridge Readings with Wagon Filter", False, f"Exception: {str(e)}")

        # Test 4: Get weighbridge readings with status filter
        try:
            response = self.session.get(f"{self.base_url}/weighbridge/readings", 
                                      params={"status": "overload"})
            if response.status_code == 200:
                result = response.json()
                self.log_result("Weighbridge Readings with Status Filter", True, 
                              "Filtered readings by overload status")
            else:
                self.log_result("Weighbridge Readings with Status Filter", False, 
                              f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Weighbridge Readings with Status Filter", False, f"Exception: {str(e)}")

    def test_gps_tracking_enhancement(self):
        """Test GPS Tracking Enhancement endpoints"""
        print("=== Testing GPS Tracking Enhancement ===")
        
        # Test 1: Create GPS route progress updates
        gps_progress_tests = [
            {
                "rake_id": self.existing_ids.get('rake_id', 'test_rake_id'),
                "current_location": {"lat": 19.0760, "lng": 72.8777, "address": "Mumbai Central"},
                "destination": {"lat": 28.6139, "lng": 77.2090, "address": "New Delhi"},
                "progress_percentage": 25.5,
                "estimated_arrival": (datetime.utcnow() + timedelta(hours=18)).isoformat(),
                "speed_kmh": 45.2,
                "distance_remaining_km": 850.5,
                "route_status": "on_track"
            },
            {
                "rake_id": self.existing_ids.get('rake_id', 'test_rake_id_2'),
                "current_location": {"lat": 22.5726, "lng": 88.3639, "address": "Kolkata Junction"},
                "destination": {"lat": 13.0827, "lng": 80.2707, "address": "Chennai Central"},
                "progress_percentage": 60.0,
                "estimated_arrival": (datetime.utcnow() + timedelta(hours=12)).isoformat(),
                "speed_kmh": 52.8,
                "distance_remaining_km": 420.0,
                "route_status": "delayed"
            }
        ]
        
        for gps_data in gps_progress_tests:
            try:
                response = self.session.post(f"{self.base_url}/gps/route-progress", json=gps_data)
                if response.status_code == 200:
                    result = response.json()
                    self.log_result(f"GPS Route Progress - {gps_data['route_status']}", True, 
                                  f"Progress: {gps_data['progress_percentage']}%, Speed: {gps_data['speed_kmh']} km/h")
                else:
                    self.log_result(f"GPS Route Progress - {gps_data['route_status']}", False, 
                                  f"Status: {response.status_code}", response.text)
            except Exception as e:
                self.log_result(f"GPS Route Progress - {gps_data['route_status']}", False, 
                              f"Exception: {str(e)}")

        # Test 2: Get specific rake progress
        if self.existing_ids.get('rake_id'):
            try:
                response = self.session.get(f"{self.base_url}/gps/route-progress/{self.existing_ids['rake_id']}")
                if response.status_code == 200:
                    result = response.json()
                    self.log_result("GPS Specific Rake Progress", True, 
                                  f"Retrieved progress for rake: {self.existing_ids['rake_id']}")
                else:
                    self.log_result("GPS Specific Rake Progress", False, 
                                  f"Status: {response.status_code}", response.text)
            except Exception as e:
                self.log_result("GPS Specific Rake Progress", False, f"Exception: {str(e)}")

        # Test 3: Get all active rakes tracking data
        try:
            response = self.session.get(f"{self.base_url}/gps/all-active-rakes")
            if response.status_code == 200:
                result = response.json()
                self.log_result("GPS All Active Rakes", True, 
                              f"Retrieved tracking data for {len(result.get('active_rakes', []))} rakes")
            else:
                self.log_result("GPS All Active Rakes", False, 
                              f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("GPS All Active Rakes", False, f"Exception: {str(e)}")

    def test_smart_alert_system(self):
        """Test Smart Alert System endpoints"""
        print("=== Testing Smart Alert System ===")
        
        # Test 1: Create alerts with different priorities and channels
        alert_tests = [
            {
                "title": "Critical Temperature Alert",
                "message": "Temperature sensor reading critical levels at Loading Point LP-1",
                "priority": "critical",
                "category": "safety",
                "source": "iot_sensor",
                "source_id": "TEMP_001",
                "channels": ["sms", "email", "app"],
                "recipients": ["operator@plant.com", "+919876543210"],
                "metadata": {"sensor_type": "temperature", "value": 85.5, "threshold": 50}
            },
            {
                "title": "Weighbridge Overload Alert",
                "message": "Wagon W001 detected with 15% overload at Weighbridge WB-2",
                "priority": "high",
                "category": "operational",
                "source": "weighbridge",
                "source_id": "WB002",
                "channels": ["email", "app"],
                "recipients": ["supervisor@plant.com"],
                "metadata": {"wagon_id": "W001", "overload_percentage": 15}
            },
            {
                "title": "Route Delay Notification",
                "message": "Rake R001 delayed by 2 hours due to signal issues",
                "priority": "medium",
                "category": "logistics",
                "source": "gps_tracking",
                "source_id": "R001",
                "channels": ["app"],
                "recipients": ["dispatcher@plant.com"],
                "metadata": {"delay_hours": 2, "reason": "signal_issues"}
            },
            {
                "title": "Maintenance Reminder",
                "message": "Scheduled maintenance due for Loading Point LP-3",
                "priority": "low",
                "category": "maintenance",
                "source": "maintenance_system",
                "source_id": "LP003",
                "channels": ["email"],
                "recipients": ["maintenance@plant.com"],
                "metadata": {"maintenance_type": "scheduled", "due_date": "2024-01-15"}
            }
        ]
        
        created_alert_ids = []
        for alert_data in alert_tests:
            try:
                response = self.session.post(f"{self.base_url}/alerts", json=alert_data)
                if response.status_code == 200:
                    result = response.json()
                    alert_id = result.get('id')
                    created_alert_ids.append(alert_id)
                    self.log_result(f"Alert Creation - {alert_data['priority']}", True, 
                                  f"Alert created: {alert_data['title']}")
                else:
                    self.log_result(f"Alert Creation - {alert_data['priority']}", False, 
                                  f"Status: {response.status_code}", response.text)
            except Exception as e:
                self.log_result(f"Alert Creation - {alert_data['priority']}", False, 
                              f"Exception: {str(e)}")

        # Test 2: Get alerts
        try:
            response = self.session.get(f"{self.base_url}/alerts")
            if response.status_code == 200:
                result = response.json()
                self.log_result("Alert Retrieval", True, 
                              f"Retrieved {len(result.get('alerts', []))} alerts")
            else:
                self.log_result("Alert Retrieval", False, 
                              f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Alert Retrieval", False, f"Exception: {str(e)}")

        # Test 3: Get alerts with priority filter
        try:
            response = self.session.get(f"{self.base_url}/alerts", params={"priority": "critical"})
            if response.status_code == 200:
                result = response.json()
                self.log_result("Alert Retrieval with Priority Filter", True, 
                              "Filtered alerts by critical priority")
            else:
                self.log_result("Alert Retrieval with Priority Filter", False, 
                              f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Alert Retrieval with Priority Filter", False, f"Exception: {str(e)}")

        # Test 4: Get alerts with status filter
        try:
            response = self.session.get(f"{self.base_url}/alerts", params={"status": "active"})
            if response.status_code == 200:
                result = response.json()
                self.log_result("Alert Retrieval with Status Filter", True, 
                              "Filtered alerts by active status")
            else:
                self.log_result("Alert Retrieval with Status Filter", False, 
                              f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Alert Retrieval with Status Filter", False, f"Exception: {str(e)}")

        # Test 5: Acknowledge alert
        if created_alert_ids:
            try:
                alert_id = created_alert_ids[0]
                acknowledge_data = {
                    "acknowledged_by": "operator_001",
                    "acknowledgment_note": "Alert reviewed and action taken"
                }
                response = self.session.put(f"{self.base_url}/alerts/{alert_id}/acknowledge", 
                                          json=acknowledge_data)
                if response.status_code == 200:
                    result = response.json()
                    self.log_result("Alert Acknowledgment", True, 
                                  f"Alert {alert_id} acknowledged successfully")
                else:
                    self.log_result("Alert Acknowledgment", False, 
                                  f"Status: {response.status_code}", response.text)
            except Exception as e:
                self.log_result("Alert Acknowledgment", False, f"Exception: {str(e)}")

    def test_idle_rake_detection_rescheduling(self):
        """Test Idle Rake Detection & Rescheduling endpoints"""
        print("=== Testing Idle Rake Detection & Rescheduling ===")
        
        # Test 1: Detect idle rakes
        try:
            response = self.session.get(f"{self.base_url}/idle-rakes/detect")
            if response.status_code == 200:
                result = response.json()
                idle_rakes = result.get('idle_rakes', [])
                self.log_result("Idle Rake Detection", True, 
                              f"Detected {len(idle_rakes)} idle rakes with AI suggestions")
            else:
                self.log_result("Idle Rake Detection", False, 
                              f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Idle Rake Detection", False, f"Exception: {str(e)}")

        # Test 2: Get list of detected idle rakes
        try:
            response = self.session.get(f"{self.base_url}/idle-rakes")
            if response.status_code == 200:
                result = response.json()
                self.log_result("Idle Rakes List", True, 
                              f"Retrieved idle rakes list with {len(result.get('idle_rakes', []))} entries")
            else:
                self.log_result("Idle Rakes List", False, 
                              f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Idle Rakes List", False, f"Exception: {str(e)}")

    def test_predictive_maintenance_alerts(self):
        """Test Predictive Maintenance Alerts endpoints"""
        print("=== Testing Predictive Maintenance Alerts ===")
        
        # Test 1: Run AI-based predictive maintenance analysis
        maintenance_data = {
            "entity_type": "wagon",
            "entity_ids": [self.existing_ids.get('wagon_id', 'test_wagon_id')],
            "analysis_type": "comprehensive",
            "include_loading_points": True
        }
        
        try:
            response = self.session.post(f"{self.base_url}/maintenance/predict", json=maintenance_data)
            if response.status_code == 200:
                result = response.json()
                predictions = result.get('predictions', [])
                self.log_result("Predictive Maintenance Analysis", True, 
                              f"Generated {len(predictions)} maintenance predictions")
            else:
                self.log_result("Predictive Maintenance Analysis", False, 
                              f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Predictive Maintenance Analysis", False, f"Exception: {str(e)}")

        # Test 2: Get maintenance alerts
        try:
            response = self.session.get(f"{self.base_url}/maintenance/alerts")
            if response.status_code == 200:
                result = response.json()
                alerts = result.get('alerts', [])
                self.log_result("Maintenance Alerts Retrieval", True, 
                              f"Retrieved {len(alerts)} maintenance alerts")
            else:
                self.log_result("Maintenance Alerts Retrieval", False, 
                              f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Maintenance Alerts Retrieval", False, f"Exception: {str(e)}")

        # Test 3: Get maintenance alerts with severity filter
        try:
            response = self.session.get(f"{self.base_url}/maintenance/alerts", 
                                      params={"severity": "high"})
            if response.status_code == 200:
                result = response.json()
                self.log_result("Maintenance Alerts with Severity Filter", True, 
                              "Filtered maintenance alerts by high severity")
            else:
                self.log_result("Maintenance Alerts with Severity Filter", False, 
                              f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Maintenance Alerts with Severity Filter", False, f"Exception: {str(e)}")

    def test_auto_rescheduling_engine(self):
        """Test Auto Rescheduling Engine endpoints"""
        print("=== Testing Auto Rescheduling Engine ===")
        
        # Test 1: Auto reschedule a rake
        reschedule_data = {
            "rake_id": self.existing_ids.get('rake_id', 'test_rake_id'),
            "reason": "route_closure",
            "priority": "high",
            "constraints": {
                "max_delay_hours": 24,
                "preferred_routes": ["alternate_route_1", "alternate_route_2"],
                "cost_limit": 50000
            }
        }
        
        try:
            response = self.session.post(f"{self.base_url}/rescheduling/auto-reschedule", 
                                       json=reschedule_data)
            if response.status_code == 200:
                result = response.json()
                self.log_result("Auto Rescheduling", True, 
                              f"Rake rescheduled with AI recommendations")
            else:
                self.log_result("Auto Rescheduling", False, 
                              f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Auto Rescheduling", False, f"Exception: {str(e)}")

        # Test 2: Report route disruptions
        disruption_data = {
            "route_id": "route_001",
            "disruption_type": "signal_failure",
            "severity": "high",
            "estimated_duration_hours": 6,
            "affected_area": "Mumbai-Pune section",
            "alternative_routes": ["route_002", "route_003"],
            "reported_by": "control_room_operator"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/route-disruptions", json=disruption_data)
            if response.status_code == 200:
                result = response.json()
                self.log_result("Route Disruption Reporting", True, 
                              f"Disruption reported: {disruption_data['disruption_type']}")
            else:
                self.log_result("Route Disruption Reporting", False, 
                              f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Route Disruption Reporting", False, f"Exception: {str(e)}")

    def test_realtime_collaboration_panel(self):
        """Test Real-time Collaboration Panel endpoints"""
        print("=== Testing Real-time Collaboration Panel ===")
        
        # Test 1: Post team messages with different teams and urgency levels
        message_tests = [
            {
                "team": "plant",
                "sender_id": "plant_manager_001",
                "sender_name": "Plant Manager",
                "message": "Loading Point LP-1 maintenance scheduled for tomorrow 6 AM",
                "urgency": "normal",
                "related_entity_type": "loading_point",
                "related_entity_id": self.existing_ids.get('loading_point_id', 'test_lp_id'),
                "tags": ["maintenance", "schedule"]
            },
            {
                "team": "rail",
                "sender_id": "rail_coordinator_001", 
                "sender_name": "Rail Coordinator",
                "message": "URGENT: Signal failure on Mumbai-Pune route, expect 4-hour delays",
                "urgency": "urgent",
                "related_entity_type": "route",
                "related_entity_id": "route_001",
                "tags": ["urgent", "delay", "signal_failure"]
            },
            {
                "team": "marketing",
                "sender_id": "marketing_head_001",
                "sender_name": "Marketing Head", 
                "message": "Customer ABC Steel requesting priority dispatch for Order #12345",
                "urgency": "high",
                "related_entity_type": "order",
                "related_entity_id": "order_12345",
                "tags": ["customer_request", "priority"]
            },
            {
                "team": "operations",
                "sender_id": "ops_supervisor_001",
                "sender_name": "Operations Supervisor",
                "message": "Rake R001 loaded and ready for dispatch from Stockyard A",
                "urgency": "normal",
                "related_entity_type": "rake",
                "related_entity_id": self.existing_ids.get('rake_id', 'test_rake_id'),
                "tags": ["dispatch", "ready"]
            }
        ]
        
        for message_data in message_tests:
            try:
                response = self.session.post(f"{self.base_url}/collaboration/message", json=message_data)
                if response.status_code == 200:
                    result = response.json()
                    self.log_result(f"Collaboration Message - {message_data['team']} ({message_data['urgency']})", 
                                  True, f"Message posted by {message_data['sender_name']}")
                else:
                    self.log_result(f"Collaboration Message - {message_data['team']}", False, 
                                  f"Status: {response.status_code}", response.text)
            except Exception as e:
                self.log_result(f"Collaboration Message - {message_data['team']}", False, 
                              f"Exception: {str(e)}")

        # Test 2: Get messages
        try:
            response = self.session.get(f"{self.base_url}/collaboration/messages")
            if response.status_code == 200:
                result = response.json()
                messages = result.get('messages', [])
                self.log_result("Collaboration Messages Retrieval", True, 
                              f"Retrieved {len(messages)} messages")
            else:
                self.log_result("Collaboration Messages Retrieval", False, 
                              f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Collaboration Messages Retrieval", False, f"Exception: {str(e)}")

        # Test 3: Get messages with team filter
        try:
            response = self.session.get(f"{self.base_url}/collaboration/messages", 
                                      params={"team": "rail"})
            if response.status_code == 200:
                result = response.json()
                self.log_result("Collaboration Messages with Team Filter", True, 
                              "Filtered messages by rail team")
            else:
                self.log_result("Collaboration Messages with Team Filter", False, 
                              f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Collaboration Messages with Team Filter", False, f"Exception: {str(e)}")

        # Test 4: Get messages with related entity filter
        if self.existing_ids.get('rake_id'):
            try:
                response = self.session.get(f"{self.base_url}/collaboration/messages", 
                                          params={"related_entity_id": self.existing_ids['rake_id']})
                if response.status_code == 200:
                    result = response.json()
                    self.log_result("Collaboration Messages with Entity Filter", True, 
                                  f"Filtered messages by entity: {self.existing_ids['rake_id']}")
                else:
                    self.log_result("Collaboration Messages with Entity Filter", False, 
                                  f"Status: {response.status_code}", response.text)
            except Exception as e:
                self.log_result("Collaboration Messages with Entity Filter", False, f"Exception: {str(e)}")

    def test_historical_data_archive_system(self):
        """Test Historical Data Archive System endpoints"""
        print("=== Testing Historical Data Archive System ===")
        
        # Test 1: Query historical data for different entity types
        archive_queries = [
            {
                "entity_type": "rakes",
                "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "filters": {"status": "delivered"},
                "include_related_data": True
            },
            {
                "entity_type": "orders", 
                "start_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "filters": {"priority": "high"},
                "include_related_data": False
            },
            {
                "entity_type": "wagons",
                "start_date": (datetime.utcnow() - timedelta(days=15)).isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "filters": {"status": "maintenance"},
                "include_related_data": True
            },
            {
                "entity_type": "alerts",
                "start_date": (datetime.utcnow() - timedelta(days=3)).isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "filters": {"priority": "critical"},
                "include_related_data": False
            },
            {
                "entity_type": "weighbridge",
                "start_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "filters": {"status": "overload"},
                "include_related_data": True
            },
            {
                "entity_type": "gps_tracking",
                "start_date": (datetime.utcnow() - timedelta(hours=12)).isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "filters": {"route_status": "delayed"},
                "include_related_data": False
            }
        ]
        
        for query_data in archive_queries:
            try:
                response = self.session.post(f"{self.base_url}/archive/query", json=query_data)
                if response.status_code == 200:
                    result = response.json()
                    records = result.get('records', [])
                    self.log_result(f"Archive Query - {query_data['entity_type']}", True, 
                                  f"Retrieved {len(records)} historical records")
                else:
                    self.log_result(f"Archive Query - {query_data['entity_type']}", False, 
                                  f"Status: {response.status_code}", response.text)
            except Exception as e:
                self.log_result(f"Archive Query - {query_data['entity_type']}", False, 
                              f"Exception: {str(e)}")

        # Test 2: Get archive summary statistics
        try:
            response = self.session.get(f"{self.base_url}/archive/summary")
            if response.status_code == 200:
                result = response.json()
                self.log_result("Archive Summary Statistics", True, 
                              f"Retrieved archive statistics for {len(result.get('entity_counts', {}))} entity types")
            else:
                self.log_result("Archive Summary Statistics", False, 
                              f"Status: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Archive Summary Statistics", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all operational feature tests"""
        print("🚀 Starting Comprehensive Backend Testing for Operational & Real-Time Features")
        print("=" * 80)
        
        # Initialize sample data first
        try:
            response = self.session.post(f"{self.base_url}/initialize-sample-data")
            if response.status_code == 200:
                print("✅ Sample data initialized successfully")
            else:
                print(f"⚠️  Sample data initialization: {response.status_code}")
        except Exception as e:
            print(f"⚠️  Sample data initialization failed: {e}")
        
        # Get existing IDs for testing
        self.get_existing_ids()
        
        # Run all operational feature tests
        self.test_iot_sensors_integration()
        self.test_smart_weighbridge_integration()
        self.test_gps_tracking_enhancement()
        self.test_smart_alert_system()
        self.test_idle_rake_detection_rescheduling()
        self.test_predictive_maintenance_alerts()
        self.test_auto_rescheduling_engine()
        self.test_realtime_collaboration_panel()
        self.test_historical_data_archive_system()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("=" * 80)
        print("🏁 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    tester = BackendTester()
    tester.run_all_tests()