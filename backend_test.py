#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Advanced Rake Formation Control Room
Tests all new advanced control room features and endpoints
"""

import requests
import json
import asyncio
import websockets
from datetime import datetime, timedelta
import random
import time

# Backend URL from environment
BACKEND_URL = "https://freight-genius-2.preview.emergentagent.com/api"

class AdvancedBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.test_results = []
        self.sample_data_ids = {}
        
    def log_test(self, test_name, success, message="", response_data=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        
    def test_basic_connectivity(self):
        """Test basic API connectivity"""
        try:
            response = self.session.get(f"{BACKEND_URL}/")
            if response.status_code == 200:
                self.log_test("Basic Connectivity", True, "API is accessible")
                return True
            else:
                self.log_test("Basic Connectivity", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Basic Connectivity", False, f"Connection error: {str(e)}")
            return False
    
    def test_sample_data_initialization(self):
        """Test sample data initialization with advanced features"""
        try:
            response = self.session.post(f"{BACKEND_URL}/initialize-sample-data")
            if response.status_code == 200:
                data = response.json()
                self.log_test("Sample Data Initialization", True, data.get('message', 'Success'))
                return True
            else:
                self.log_test("Sample Data Initialization", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Sample Data Initialization", False, f"Error: {str(e)}")
            return False
    
    def test_real_time_wagon_tracking(self):
        """Test real-time wagon tracking endpoints"""
        try:
            # Test get wagon tracking
            response = self.session.get(f"{BACKEND_URL}/wagon-tracking")
            if response.status_code == 200:
                tracking_data = response.json()
                self.log_test("Get Wagon Tracking", True, f"Retrieved {len(tracking_data)} tracking records")
            else:
                self.log_test("Get Wagon Tracking", False, f"Status: {response.status_code}")
                return False
            
            # Test real-time tracking endpoint
            response = self.session.get(f"{BACKEND_URL}/wagon-tracking/real-time")
            if response.status_code == 200:
                real_time_data = response.json()
                wagon_count = len(real_time_data.get('wagons', []))
                self.log_test("Real-time Wagon Tracking", True, f"Retrieved real-time data for {wagon_count} wagons")
                return True
            else:
                self.log_test("Real-time Wagon Tracking", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Real-time Wagon Tracking", False, f"Error: {str(e)}")
            return False
    
    def test_compatibility_matrix(self):
        """Test compatibility matrix management"""
        try:
            # Test get compatibility rules
            response = self.session.get(f"{BACKEND_URL}/compatibility-rules")
            if response.status_code == 200:
                rules = response.json()
                self.log_test("Get Compatibility Rules", True, f"Retrieved {len(rules)} compatibility rules")
            else:
                self.log_test("Get Compatibility Rules", False, f"Status: {response.status_code}")
                return False
            
            # Test compatibility matrix for specific material type
            response = self.session.get(f"{BACKEND_URL}/compatibility-matrix/Bulk")
            if response.status_code == 200:
                matrix = response.json()
                material_type = matrix.get('material_type')
                matrix_data = matrix.get('compatibility_matrix', {})
                self.log_test("Compatibility Matrix", True, f"Retrieved matrix for {material_type} with {len(matrix_data)} wagon types")
                return True
            else:
                self.log_test("Compatibility Matrix", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Compatibility Matrix", False, f"Error: {str(e)}")
            return False
    
    def test_route_validation(self):
        """Test route validation system"""
        try:
            # Test get routes
            response = self.session.get(f"{BACKEND_URL}/routes")
            if response.status_code == 200:
                routes = response.json()
                self.log_test("Get Routes", True, f"Retrieved {len(routes)} routes")
            else:
                self.log_test("Get Routes", False, f"Status: {response.status_code}")
                return False
            
            # Test route validation
            validation_data = {
                "origin": "Plant North",
                "destination": "Mumbai",
                "wagon_type": "BOXN"
            }
            response = self.session.post(f"{BACKEND_URL}/routes/validate", json=validation_data)
            if response.status_code == 200:
                validation_result = response.json()
                is_valid = validation_result.get('valid', False)
                message = validation_result.get('message', '')
                self.log_test("Route Validation", True, f"Validation result: {is_valid} - {message}")
                return True
            else:
                self.log_test("Route Validation", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Route Validation", False, f"Error: {str(e)}")
            return False
    
    def test_multi_destination_rake(self):
        """Test multi-destination rake formation"""
        try:
            # Test get multi-destination rakes
            response = self.session.get(f"{BACKEND_URL}/multi-destination-rakes")
            if response.status_code == 200:
                rakes = response.json()
                self.log_test("Get Multi-destination Rakes", True, f"Retrieved {len(rakes)} multi-destination rakes")
            else:
                self.log_test("Get Multi-destination Rakes", False, f"Status: {response.status_code}")
                return False
            
            # Test multi-destination optimization
            optimization_data = {
                "destinations": ["Mumbai", "Delhi"],
                "max_wagons": 30
            }
            response = self.session.post(f"{BACKEND_URL}/optimize-multi-destination", json=optimization_data)
            if response.status_code == 200:
                optimization_result = response.json()
                destinations = optimization_result.get('destinations', [])
                self.log_test("Multi-destination Optimization", True, f"AI optimization completed for {len(destinations)} destinations")
                return True
            else:
                self.log_test("Multi-destination Optimization", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Multi-destination Rake Formation", False, f"Error: {str(e)}")
            return False
    
    def test_capacity_monitoring(self):
        """Test capacity monitoring with real-time data"""
        try:
            # Test real-time capacity monitoring
            response = self.session.get(f"{BACKEND_URL}/capacity-monitoring/real-time")
            if response.status_code == 200:
                capacity_data = response.json()
                loading_points = capacity_data.get('loading_points', [])
                overall_util = capacity_data.get('overall_utilization', 0)
                self.log_test("Real-time Capacity Monitoring", True, f"Retrieved capacity data for {len(loading_points)} loading points, overall utilization: {overall_util:.2f}")
                return True
            else:
                self.log_test("Real-time Capacity Monitoring", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Capacity Monitoring", False, f"Error: {str(e)}")
            return False
    
    def test_erp_integration(self):
        """Test ERP integration framework"""
        try:
            # Test ERP sync status
            response = self.session.get(f"{BACKEND_URL}/erp-sync/status")
            if response.status_code == 200:
                sync_status = response.json()
                recent_syncs = sync_status.get('recent_syncs', [])
                systems_status = sync_status.get('systems_status', {})
                self.log_test("ERP Sync Status", True, f"Retrieved {len(recent_syncs)} recent syncs, systems: {list(systems_status.keys())}")
            else:
                self.log_test("ERP Sync Status", False, f"Status: {response.status_code}")
                return False
            
            # Test trigger ERP sync
            sync_data = {"system_name": "SAP"}
            response = self.session.post(f"{BACKEND_URL}/erp-sync/trigger", json=sync_data)
            if response.status_code == 200:
                trigger_result = response.json()
                message = trigger_result.get('message', '')
                self.log_test("ERP Sync Trigger", True, message)
                return True
            else:
                self.log_test("ERP Sync Trigger", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("ERP Integration", False, f"Error: {str(e)}")
            return False
    
    def test_workflow_management(self):
        """Test workflow management with approvals"""
        try:
            # Test get pending approvals
            response = self.session.get(f"{BACKEND_URL}/workflow/approvals/pending")
            if response.status_code == 200:
                pending_approvals = response.json()
                self.log_test("Get Pending Approvals", True, f"Retrieved {len(pending_approvals)} pending approvals")
                
                # If there are pending approvals, test updating one
                if pending_approvals:
                    approval_id = pending_approvals[0].get('id')
                    if approval_id:
                        update_data = {
                            "status": "approved",
                            "comments": "Approved via automated testing"
                        }
                        response = self.session.put(f"{BACKEND_URL}/workflow/approvals/{approval_id}", json=update_data)
                        if response.status_code == 200:
                            self.log_test("Update Approval Status", True, "Successfully updated approval status")
                        else:
                            self.log_test("Update Approval Status", False, f"Status: {response.status_code}")
                
                return True
            else:
                self.log_test("Workflow Management", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Workflow Management", False, f"Error: {str(e)}")
            return False
    
    def test_advanced_analytics(self):
        """Test advanced analytics and performance metrics"""
        try:
            # Test performance analytics
            response = self.session.get(f"{BACKEND_URL}/analytics/performance")
            if response.status_code == 200:
                analytics = response.json()
                kpis = analytics.get('kpis', {})
                trends = analytics.get('trends', {})
                self.log_test("Performance Analytics", True, f"Retrieved analytics with {len(kpis)} KPIs and {len(trends)} trend datasets")
                return True
            else:
                self.log_test("Performance Analytics", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Advanced Analytics", False, f"Error: {str(e)}")
            return False
    
    def test_control_room_dashboard(self):
        """Test control room dashboard with comprehensive data"""
        try:
            # Test control room dashboard
            response = self.session.get(f"{BACKEND_URL}/control-room/dashboard")
            if response.status_code == 200:
                dashboard_data = response.json()
                active_rakes = dashboard_data.get('active_rakes', {})
                wagon_status = dashboard_data.get('wagon_status_summary', {})
                stockyard_util = dashboard_data.get('stockyard_utilization', {})
                alerts = dashboard_data.get('urgent_alerts', [])
                kpis = dashboard_data.get('performance_kpis', {})
                
                self.log_test("Control Room Dashboard", True, 
                    f"Dashboard loaded: {len(active_rakes)} rake statuses, {len(wagon_status)} wagon statuses, "
                    f"{len(stockyard_util)} stockyards, {len(alerts)} alerts, {len(kpis)} KPIs")
                return True
            else:
                self.log_test("Control Room Dashboard", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Control Room Dashboard", False, f"Error: {str(e)}")
            return False
    
    def test_report_generation(self):
        """Test report generation system"""
        try:
            # Test report generation
            report_request = {
                "report_type": "performance",
                "start_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "format": "csv",
                "include_charts": True,
                "email_recipients": []
            }
            
            response = self.session.post(f"{BACKEND_URL}/reports/generate", json=report_request)
            if response.status_code == 200:
                report_response = response.json()
                report_id = report_response.get('report_id')
                download_url = report_response.get('download_url')
                self.log_test("Report Generation", True, f"Report generated: {report_id}")
                
                # Test report download
                if download_url:
                    download_response = self.session.get(f"{BACKEND_URL.replace('/api', '')}{download_url}")
                    if download_response.status_code == 200:
                        self.log_test("Report Download", True, f"Report downloaded successfully, size: {len(download_response.content)} bytes")
                    else:
                        self.log_test("Report Download", False, f"Download status: {download_response.status_code}")
                
                return True
            else:
                self.log_test("Report Generation", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Report Generation", False, f"Error: {str(e)}")
            return False
    
    def test_ai_optimization(self):
        """Test AI optimization for multi-destination works"""
        try:
            # First get some orders to optimize
            response = self.session.get(f"{BACKEND_URL}/orders")
            if response.status_code != 200:
                self.log_test("AI Optimization - Get Orders", False, f"Status: {response.status_code}")
                return False
            
            orders = response.json()
            if not orders:
                self.log_test("AI Optimization", False, "No orders available for optimization")
                return False
            
            # Test AI optimization with first few orders
            order_ids = [order['id'] for order in orders[:3]]
            optimization_request = {
                "order_ids": order_ids,
                "max_cost": 100000,
                "priority_weight": 0.7
            }
            
            response = self.session.post(f"{BACKEND_URL}/optimize-rake", json=optimization_request)
            if response.status_code == 200:
                optimization_result = response.json()
                recommended_rakes = optimization_result.get('recommended_rakes', [])
                total_cost = optimization_result.get('total_cost', 0)
                explanation = optimization_result.get('explanation', '')
                
                self.log_test("AI Optimization", True, 
                    f"AI optimization completed: {len(recommended_rakes)} recommended rakes, "
                    f"total cost: {total_cost}, explanation length: {len(explanation)} chars")
                return True
            else:
                self.log_test("AI Optimization", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("AI Optimization", False, f"Error: {str(e)}")
            return False
    
    async def test_websocket_real_time_updates(self):
        """Test WebSocket real-time updates"""
        try:
            websocket_url = BACKEND_URL.replace('https://', 'wss://').replace('/api', '/ws/real-time-updates')
            
            async with websockets.connect(websocket_url) as websocket:
                # Wait for a few updates
                updates_received = 0
                timeout = 15  # 15 seconds timeout
                start_time = time.time()
                
                while updates_received < 3 and (time.time() - start_time) < timeout:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5)
                        update_data = json.loads(message)
                        updates_received += 1
                        
                        update_type = update_data.get('type', 'unknown')
                        timestamp = update_data.get('timestamp', '')
                        
                    except asyncio.TimeoutError:
                        break
                
                if updates_received > 0:
                    self.log_test("WebSocket Real-time Updates", True, f"Received {updates_received} real-time updates")
                    return True
                else:
                    self.log_test("WebSocket Real-time Updates", False, "No updates received within timeout")
                    return False
                    
        except Exception as e:
            self.log_test("WebSocket Real-time Updates", False, f"Error: {str(e)}")
            return False
    
    def test_all_basic_endpoints(self):
        """Test all basic CRUD endpoints are still working"""
        try:
            endpoints_to_test = [
                ("materials", "Materials"),
                ("stockyards", "Stockyards"), 
                ("inventory", "Inventory"),
                ("orders", "Orders"),
                ("wagons", "Wagons"),
                ("loading-points", "Loading Points"),
                ("rakes", "Rakes")
            ]
            
            all_passed = True
            for endpoint, name in endpoints_to_test:
                response = self.session.get(f"{BACKEND_URL}/{endpoint}")
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(f"Get {name}", True, f"Retrieved {len(data)} records")
                else:
                    self.log_test(f"Get {name}", False, f"Status: {response.status_code}")
                    all_passed = False
            
            # Test dashboard stats
            response = self.session.get(f"{BACKEND_URL}/dashboard/stats")
            if response.status_code == 200:
                stats = response.json()
                self.log_test("Dashboard Stats", True, f"Retrieved dashboard statistics")
            else:
                self.log_test("Dashboard Stats", False, f"Status: {response.status_code}")
                all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.log_test("Basic Endpoints", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests systematically"""
        print("🚀 Starting Comprehensive Advanced Backend Testing...")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Test in priority order
        tests = [
            ("Basic Connectivity", self.test_basic_connectivity),
            ("Sample Data Initialization", self.test_sample_data_initialization),
            ("All Basic Endpoints", self.test_all_basic_endpoints),
            ("Real-time Wagon Tracking", self.test_real_time_wagon_tracking),
            ("Compatibility Matrix", self.test_compatibility_matrix),
            ("Route Validation", self.test_route_validation),
            ("Multi-destination Rake", self.test_multi_destination_rake),
            ("Capacity Monitoring", self.test_capacity_monitoring),
            ("ERP Integration", self.test_erp_integration),
            ("Workflow Management", self.test_workflow_management),
            ("Advanced Analytics", self.test_advanced_analytics),
            ("Control Room Dashboard", self.test_control_room_dashboard),
            ("Report Generation", self.test_report_generation),
            ("AI Optimization", self.test_ai_optimization),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Testing: {test_name}")
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.log_test(test_name, False, f"Unexpected error: {str(e)}")
        
        # Test WebSocket separately (async)
        print(f"\n🔍 Testing: WebSocket Real-time Updates")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            websocket_result = loop.run_until_complete(self.test_websocket_real_time_updates())
            if websocket_result:
                passed_tests += 1
            total_tests += 1
            loop.close()
        except Exception as e:
            self.log_test("WebSocket Real-time Updates", False, f"Unexpected error: {str(e)}")
            total_tests += 1
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Print failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['message']}")
        
        print("\n✅ All advanced control room features tested!")
        return passed_tests, total_tests, failed_tests

if __name__ == "__main__":
    tester = AdvancedBackendTester()
    passed, total, failed = tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if len(failed) == 0 else 1)