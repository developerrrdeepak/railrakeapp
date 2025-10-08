import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl, ActivityIndicator, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import Constants from 'expo-constants';
import { useRouter } from 'expo-router';

const BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface DashboardStats {
  pending_orders: number;
  active_rakes: number;
  available_wagons: number;
  total_inventory_value: number;
  urgent_orders: number;
  avg_utilization: number;
}

interface ControlRoomDashboard {
  timestamp: string;
  active_rakes: {
    planned: number;
    loading: number;
    in_transit: number;
    unloading: number;
  };
  wagon_status_summary: {
    available: number;
    loaded: number;
    in_transit: number;
    maintenance: number;
  };
  stockyard_utilization: Record<string, number>;
  urgent_alerts: Array<{
    type: string;
    message: string;
    priority: string;
  }>;
  performance_kpis: {
    efficiency: number;
    utilization: number;
    on_time_delivery: number;
    cost_optimization: number;
  };
  live_tracking_count: number;
}

interface RealTimeTracking {
  timestamp: string;
  wagons: Array<{
    wagon_id: string;
    wagon_number: string;
    status: string;
    current_location: string;
    load_percentage: number;
    last_updated: string;
  }>;
}

interface CapacityData {
  timestamp: string;
  loading_points: Array<{
    loading_point_id: string;
    loading_point_name: string;
    current_utilization: number;
    available_capacity: number;
    queued_rakes: number;
    estimated_wait_time: number;
    status: string;
  }>;
  overall_utilization: number;
}

export default function DashboardScreen() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'overview' | 'tracking' | 'capacity' | 'alerts'>('overview');
  
  // Basic dashboard stats
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery<DashboardStats>({
    queryKey: ['dashboardStats'],
    queryFn: async () => {
      const response = await axios.get(`${BACKEND_URL}/api/dashboard/stats`);
      return response.data;
    },
    refetchInterval: 30000,
  });

  // Enhanced control room dashboard
  const { data: controlRoom, isLoading: controlLoading, refetch: refetchControl } = useQuery<ControlRoomDashboard>({
    queryKey: ['controlRoomDashboard'],
    queryFn: async () => {
      const response = await axios.get(`${BACKEND_URL}/api/control-room/dashboard`);
      return response.data;
    },
    refetchInterval: 10000, // More frequent updates for control room
  });

  // Real-time wagon tracking
  const { data: tracking, refetch: refetchTracking } = useQuery<RealTimeTracking>({
    queryKey: ['realTimeTracking'],
    queryFn: async () => {
      const response = await axios.get(`${BACKEND_URL}/api/wagon-tracking/real-time`);
      return response.data;
    },
    refetchInterval: 15000,
    enabled: activeTab === 'tracking',
  });

  // Capacity monitoring
  const { data: capacity, refetch: refetchCapacity } = useQuery<CapacityData>({
    queryKey: ['capacityMonitoring'],
    queryFn: async () => {
      const response = await axios.get(`${BACKEND_URL}/api/capacity-monitoring/real-time`);
      return response.data;
    },
    refetchInterval: 20000,
    enabled: activeTab === 'capacity',
  });

  const handleRefresh = async () => {
    await Promise.all([refetchStats(), refetchControl(), refetchTracking(), refetchCapacity()]);
  };

  const generateReport = async () => {
    try {
      const response = await axios.post(`${BACKEND_URL}/api/reports/generate`, {
        report_type: 'daily_plan',
        start_date: new Date().toISOString(),
        end_date: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        format: 'csv'
      });
      Alert.alert('Success', `Report generated: ${response.data.report_id}`);
    } catch (error) {
      Alert.alert('Error', 'Failed to generate report');
    }
  };

  if (statsLoading || controlLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <ActivityIndicator size="large" color="#4a90e2" style={{ marginTop: 100 }} />
        <Text style={styles.loadingText}>Loading Control Room...</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Control Room Dashboard</Text>
        <Text style={styles.headerSubtitle}>Real-time Railway Operations Center</Text>
        <TouchableOpacity style={styles.liveIndicator}>
          <View style={styles.liveIcon} />
          <Text style={styles.liveText}>LIVE</Text>
        </TouchableOpacity>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabContainer}>
        {[
          { key: 'overview', title: 'Overview', icon: 'grid' },
          { key: 'tracking', title: 'Tracking', icon: 'location' },
          { key: 'capacity', title: 'Capacity', icon: 'analytics' },
          { key: 'alerts', title: 'Alerts', icon: 'warning' },
        ].map((tab) => (
          <TouchableOpacity
            key={tab.key}
            style={[styles.tab, activeTab === tab.key && styles.activeTab]}
            onPress={() => setActiveTab(tab.key as any)}
          >
            <Ionicons 
              name={tab.icon as any} 
              size={18} 
              color={activeTab === tab.key ? '#4a90e2' : '#666'} 
            />
            <Text style={[styles.tabText, activeTab === tab.key && styles.activeTabText]}>
              {tab.title}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={false} onRefresh={handleRefresh} tintColor="#4a90e2" />
        }
      >
        {activeTab === 'overview' && (
          <>
            {/* KPI Cards */}
            <View style={styles.kpiSection}>
              <Text style={styles.sectionTitle}>Performance KPIs</Text>
              <View style={styles.kpiGrid}>
                <View style={styles.kpiCard}>
                  <Text style={styles.kpiValue}>
                    {((controlRoom?.performance_kpis?.efficiency || 0) * 100).toFixed(1)}%
                  </Text>
                  <Text style={styles.kpiLabel}>Efficiency</Text>
                </View>
                <View style={styles.kpiCard}>
                  <Text style={styles.kpiValue}>
                    {((controlRoom?.performance_kpis?.on_time_delivery || 0) * 100).toFixed(1)}%
                  </Text>
                  <Text style={styles.kpiLabel}>On-Time Delivery</Text>
                </View>
                <View style={styles.kpiCard}>
                  <Text style={styles.kpiValue}>
                    {((controlRoom?.performance_kpis?.utilization || 0) * 100).toFixed(1)}%
                  </Text>
                  <Text style={styles.kpiLabel}>Utilization</Text>
                </View>
                <View style={styles.kpiCard}>
                  <Text style={styles.kpiValue}>
                    {((controlRoom?.performance_kpis?.cost_optimization || 0) * 100).toFixed(1)}%
                  </Text>
                  <Text style={styles.kpiLabel}>Cost Efficiency</Text>
                </View>
              </View>
            </View>

            {/* Active Operations */}
            <View style={styles.operationsSection}>
              <Text style={styles.sectionTitle}>Active Operations</Text>
              <View style={styles.operationsGrid}>
                <View style={styles.operationCard}>
                  <Ionicons name="train" size={24} color="#51cf66" />
                  <Text style={styles.operationValue}>
                    {(controlRoom?.active_rakes?.planned || 0) + 
                     (controlRoom?.active_rakes?.loading || 0) + 
                     (controlRoom?.active_rakes?.in_transit || 0)}
                  </Text>
                  <Text style={styles.operationLabel}>Active Rakes</Text>
                  <Text style={styles.operationDetail}>
                    {controlRoom?.active_rakes?.in_transit || 0} in transit
                  </Text>
                </View>
                <View style={styles.operationCard}>
                  <Ionicons name="cube" size={24} color="#ffd93d" />
                  <Text style={styles.operationValue}>
                    {(controlRoom?.wagon_status_summary?.loaded || 0) + 
                     (controlRoom?.wagon_status_summary?.in_transit || 0)}
                  </Text>
                  <Text style={styles.operationLabel}>Loaded Wagons</Text>
                  <Text style={styles.operationDetail}>
                    {controlRoom?.wagon_status_summary?.available || 0} available
                  </Text>
                </View>
              </View>
            </View>

            {/* Stockyard Status */}
            <View style={styles.stockyardSection}>
              <Text style={styles.sectionTitle}>Stockyard Utilization</Text>
              {Object.entries(controlRoom?.stockyard_utilization || {}).map(([name, utilization]) => (
                <View key={name} style={styles.stockyardItem}>
                  <View style={styles.stockyardHeader}>
                    <Text style={styles.stockyardName}>{name}</Text>
                    <Text style={styles.stockyardPercent}>{(utilization * 100).toFixed(1)}%</Text>
                  </View>
                  <View style={styles.progressBar}>
                    <View 
                      style={[
                        styles.progressFill, 
                        { 
                          width: `${utilization * 100}%`,
                          backgroundColor: utilization > 0.8 ? '#ff6b6b' : utilization > 0.6 ? '#ffd93d' : '#51cf66'
                        }
                      ]} 
                    />
                  </View>
                </View>
              ))}
            </View>
          </>
        )}

        {activeTab === 'tracking' && (
          <View style={styles.trackingSection}>
            <Text style={styles.sectionTitle}>Real-time Wagon Tracking</Text>
            <Text style={styles.trackingCount}>
              {tracking?.wagons?.length || 0} wagons tracked
            </Text>
            {tracking?.wagons?.slice(0, 8).map((wagon) => (
              <View key={wagon.wagon_id} style={styles.wagonCard}>
                <View style={styles.wagonHeader}>
                  <Text style={styles.wagonNumber}>{wagon.wagon_number}</Text>
                  <View style={[styles.statusBadge, { 
                    backgroundColor: wagon.status === 'available' ? '#51cf66' : 
                                   wagon.status === 'loaded' ? '#ffd93d' : 
                                   wagon.status === 'in_transit' ? '#4a90e2' : '#ff6b6b'
                  }]}>
                    <Text style={styles.statusText}>{wagon.status.toUpperCase()}</Text>
                  </View>
                </View>
                <Text style={styles.wagonLocation}>📍 {wagon.current_location}</Text>
                <View style={styles.loadContainer}>
                  <Text style={styles.loadLabel}>Load: {wagon.load_percentage.toFixed(1)}%</Text>
                  <View style={styles.loadBar}>
                    <View style={[styles.loadFill, { width: `${wagon.load_percentage}%` }]} />
                  </View>
                </View>
              </View>
            ))}
          </View>
        )}

        {activeTab === 'capacity' && (
          <View style={styles.capacitySection}>
            <Text style={styles.sectionTitle}>Loading Point Capacity</Text>
            <Text style={styles.capacityOverall}>
              Overall Utilization: {((capacity?.overall_utilization || 0) * 100).toFixed(1)}%
            </Text>
            {capacity?.loading_points?.map((lp) => (
              <View key={lp.loading_point_id} style={styles.capacityCard}>
                <View style={styles.capacityHeader}>
                  <Text style={styles.capacityName}>{lp.loading_point_name}</Text>
                  <View style={[styles.statusIndicator, {
                    backgroundColor: lp.status === 'normal' ? '#51cf66' :
                                   lp.status === 'warning' ? '#ffd93d' : '#ff6b6b'
                  }]}>
                    <Text style={styles.statusIndicatorText}>{lp.status.toUpperCase()}</Text>
                  </View>
                </View>
                <View style={styles.capacityMetrics}>
                  <View style={styles.capacityMetric}>
                    <Text style={styles.metricValue}>{(lp.current_utilization * 100).toFixed(1)}%</Text>
                    <Text style={styles.metricLabel}>Utilization</Text>
                  </View>
                  <View style={styles.capacityMetric}>
                    <Text style={styles.metricValue}>{lp.queued_rakes}</Text>
                    <Text style={styles.metricLabel}>Queued</Text>
                  </View>
                  <View style={styles.capacityMetric}>
                    <Text style={styles.metricValue}>{lp.estimated_wait_time.toFixed(1)}h</Text>
                    <Text style={styles.metricLabel}>Wait Time</Text>
                  </View>
                </View>
              </View>
            ))}
          </View>
        )}

        {activeTab === 'alerts' && (
          <View style={styles.alertsSection}>
            <Text style={styles.sectionTitle}>System Alerts</Text>
            {controlRoom?.urgent_alerts?.map((alert, index) => (
              <View key={index} style={[styles.alertCard, {
                borderLeftColor: alert.priority === 'high' ? '#ff6b6b' :
                               alert.priority === 'medium' ? '#ffd93d' : '#4a90e2'
              }]}>
                <View style={styles.alertHeader}>
                  <Ionicons 
                    name={alert.type === 'delay' ? 'time' : 
                         alert.type === 'capacity' ? 'warning' : 'build'} 
                    size={20} 
                    color={alert.priority === 'high' ? '#ff6b6b' : 
                          alert.priority === 'medium' ? '#ffd93d' : '#4a90e2'} 
                  />
                  <Text style={[styles.alertPriority, {
                    color: alert.priority === 'high' ? '#ff6b6b' :
                          alert.priority === 'medium' ? '#ffd93d' : '#4a90e2'
                  }]}>
                    {alert.priority.toUpperCase()}
                  </Text>
                </View>
                <Text style={styles.alertMessage}>{alert.message}</Text>
              </View>
            ))}
            
            <TouchableOpacity style={styles.reportButton} onPress={generateReport}>
              <Ionicons name="document" size={20} color="#fff" />
              <Text style={styles.reportButtonText}>Generate Daily Report</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Quick Actions */}
        <View style={styles.actionsSection}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => router.push('/(tabs)/orders')}
          >
            <Ionicons name="add-circle" size={24} color="#4a90e2" />
            <Text style={styles.actionText}>Create Order</Text>
            <Ionicons name="chevron-forward" size={20} color="#666" />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => router.push('/(tabs)/optimize')}
          >
            <Ionicons name="sparkles" size={24} color="#51cf66" />
            <Text style={styles.actionText}>AI Multi-Destination Optimization</Text>
            <Ionicons name="chevron-forward" size={20} color="#666" />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => router.push('/(tabs)/rakes')}
          >
            <Ionicons name="train" size={24} color="#ffd93d" />
            <Text style={styles.actionText}>Rake Formation Planning</Text>
            <Ionicons name="chevron-forward" size={20} color="#666" />
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f0f23',
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingBottom: 24,
  },
  header: {
    backgroundColor: '#1a1a2e',
    paddingHorizontal: 16,
    paddingVertical: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a3e',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#888',
    marginBottom: 12,
  },
  liveIndicator: {
    position: 'absolute',
    top: 20,
    right: 16,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e7e34',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  liveIcon: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#51cf66',
    marginRight: 6,
  },
  liveText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#1a1a2e',
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    marginHorizontal: 4,
    borderRadius: 8,
    backgroundColor: '#2a2a3e',
  },
  activeTab: {
    backgroundColor: '#4a90e2',
  },
  tabText: {
    fontSize: 12,
    color: '#666',
    marginLeft: 6,
    fontWeight: '500',
  },
  activeTabText: {
    color: '#ffffff',
  },
  loadingText: {
    color: '#ffffff',
    marginTop: 16,
    fontSize: 16,
    textAlign: 'center',
  },
  // KPI Section
  kpiSection: {
    marginTop: 16,
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 16,
  },
  kpiGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -6,
  },
  kpiCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    margin: 6,
    width: '45%',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  kpiValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#4a90e2',
    marginBottom: 4,
  },
  kpiLabel: {
    fontSize: 12,
    color: '#a0a0a0',
    textAlign: 'center',
  },
  // Operations Section
  operationsSection: {
    marginBottom: 24,
  },
  operationsGrid: {
    flexDirection: 'row',
    marginHorizontal: -8,
  },
  operationCard: {
    flex: 1,
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    margin: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  operationValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#ffffff',
    marginVertical: 8,
  },
  operationLabel: {
    fontSize: 14,
    color: '#a0a0a0',
    marginBottom: 4,
  },
  operationDetail: {
    fontSize: 12,
    color: '#666',
  },
  // Stockyard Section
  stockyardSection: {
    marginBottom: 24,
  },
  stockyardItem: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  stockyardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  stockyardName: {
    fontSize: 16,
    color: '#ffffff',
    fontWeight: '600',
  },
  stockyardPercent: {
    fontSize: 16,
    color: '#4a90e2',
    fontWeight: 'bold',
  },
  progressBar: {
    height: 8,
    backgroundColor: '#2a2a3e',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#38bdf8',
  },
  // Tracking Section
  trackingSection: {
    marginTop: 16,
  },
  trackingCount: {
    fontSize: 14,
    color: '#888',
    marginBottom: 16,
  },
  wagonCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  wagonHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  wagonNumber: {
    fontSize: 16,
    color: '#ffffff',
    fontWeight: 'bold',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 10,
    color: '#ffffff',
    fontWeight: 'bold',
  },
  wagonLocation: {
    fontSize: 14,
    color: '#a0a0a0',
    marginBottom: 12,
  },
  loadContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  loadLabel: {
    fontSize: 12,
    color: '#666',
    marginRight: 12,
    width: 80,
  },
  loadBar: {
    flex: 1,
    height: 6,
    backgroundColor: '#2a2a3e',
    borderRadius: 3,
    overflow: 'hidden',
  },
  loadFill: {
    height: '100%',
    backgroundColor: '#ffd93d',
  },
  // Capacity Section
  capacitySection: {
    marginTop: 16,
  },
  capacityOverall: {
    fontSize: 16,
    color: '#4a90e2',
    fontWeight: 'bold',
    marginBottom: 16,
    textAlign: 'center',
  },
  capacityCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  capacityHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  capacityName: {
    fontSize: 16,
    color: '#ffffff',
    fontWeight: '600',
  },
  statusIndicator: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusIndicatorText: {
    fontSize: 10,
    color: '#ffffff',
    fontWeight: 'bold',
  },
  capacityMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  capacityMetric: {
    alignItems: 'center',
  },
  metricValue: {
    fontSize: 18,
    color: '#ffffff',
    fontWeight: 'bold',
  },
  metricLabel: {
    fontSize: 12,
    color: '#a0a0a0',
    marginTop: 4,
  },
  // Alerts Section
  alertsSection: {
    marginTop: 16,
  },
  alertCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 4,
    borderTopWidth: 1,
    borderRightWidth: 1,
    borderBottomWidth: 1,
    borderTopColor: '#2a2a3e',
    borderRightColor: '#2a2a3e',
    borderBottomColor: '#2a2a3e',
  },
  alertHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  alertPriority: {
    fontSize: 12,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  alertMessage: {
    fontSize: 14,
    color: '#ffffff',
    lineHeight: 20,
  },
  reportButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#4a90e2',
    padding: 16,
    borderRadius: 12,
    marginTop: 16,
  },
  reportButtonText: {
    fontSize: 16,
    color: '#ffffff',
    fontWeight: 'bold',
    marginLeft: 8,
  },
  // Actions Section
  actionsSection: {
    marginTop: 24,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1a1a2e',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  actionText: {
    flex: 1,
    fontSize: 16,
    color: '#ffffff',
    marginLeft: 12,
  },
});