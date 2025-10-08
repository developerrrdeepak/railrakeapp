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
  
  const { data: stats, isLoading, refetch, isRefetching } = useQuery<DashboardStats>({
    queryKey: ['dashboardStats'],
    queryFn: async () => {
      const response = await axios.get(`${BACKEND_URL}/api/dashboard/stats`);
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <ActivityIndicator size="large" color="#4a90e2" style={{ marginTop: 100 }} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor="#4a90e2" />
        }
      >
        <Text style={styles.header}>Operations Dashboard</Text>
        <Text style={styles.subtitle}>Real-time logistics overview</Text>

        <View style={styles.statsGrid}>
          <View style={[styles.statCard, styles.primaryCard]}>
            <Ionicons name="alert-circle" size={32} color="#ff6b6b" />
            <Text style={styles.statValue}>{stats?.urgent_orders || 0}</Text>
            <Text style={styles.statLabel}>Urgent Orders</Text>
            <Text style={styles.statSubtext}>{'<'}3 days deadline</Text>
          </View>

          <View style={[styles.statCard, styles.secondaryCard]}>
            <Ionicons name="list" size={32} color="#4a90e2" />
            <Text style={styles.statValue}>{stats?.pending_orders || 0}</Text>
            <Text style={styles.statLabel}>Pending Orders</Text>
          </View>

          <View style={[styles.statCard, styles.secondaryCard]}>
            <Ionicons name="train" size={32} color="#51cf66" />
            <Text style={styles.statValue}>{stats?.active_rakes || 0}</Text>
            <Text style={styles.statLabel}>Active Rakes</Text>
          </View>

          <View style={[styles.statCard, styles.secondaryCard]}>
            <Ionicons name="cart" size={32} color="#ffd93d" />
            <Text style={styles.statValue}>{stats?.available_wagons || 0}</Text>
            <Text style={styles.statLabel}>Available Wagons</Text>
          </View>

          <View style={[styles.statCard, styles.fullWidth]}>
            <View style={styles.cardHeader}>
              <Ionicons name="cube" size={28} color="#a78bfa" />
              <Text style={styles.cardTitle}>Inventory Value</Text>
            </View>
            <Text style={styles.valueAmount}>
              ₹{((stats?.total_inventory_value || 0) / 1000000).toFixed(2)}M
            </Text>
          </View>

          <View style={[styles.statCard, styles.fullWidth]}>
            <View style={styles.cardHeader}>
              <Ionicons name="analytics" size={28} color="#38bdf8" />
              <Text style={styles.cardTitle}>Avg. Loading Utilization</Text>
            </View>
            <View style={styles.progressBar}>
              <View
                style={[
                  styles.progressFill,
                  { width: `${(stats?.avg_utilization || 0) * 100}%` },
                ]}
              />
            </View>
            <Text style={styles.percentText}>
              {((stats?.avg_utilization || 0) * 100).toFixed(1)}%
            </Text>
          </View>
        </View>

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
            <Text style={styles.actionText}>AI Rake Optimization</Text>
            <Ionicons name="chevron-forward" size={20} color="#666" />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => router.push('/(tabs)/rakes')}
          >
            <Ionicons name="train" size={24} color="#ffd93d" />
            <Text style={styles.actionText}>View Rakes</Text>
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
    padding: 16,
  },
  header: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#888',
    marginBottom: 24,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -8,
  },
  statCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    margin: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  primaryCard: {
    width: '100%',
    borderColor: '#ff6b6b',
    borderWidth: 2,
  },
  secondaryCard: {
    width: '45%',
  },
  fullWidth: {
    width: '100%',
    alignItems: 'stretch',
  },
  statValue: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#ffffff',
    marginTop: 8,
  },
  statLabel: {
    fontSize: 14,
    color: '#a0a0a0',
    marginTop: 4,
  },
  statSubtext: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginLeft: 12,
  },
  valueAmount: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#ffffff',
    marginLeft: 40,
  },
  progressBar: {
    height: 8,
    backgroundColor: '#2a2a3e',
    borderRadius: 4,
    overflow: 'hidden',
    marginVertical: 12,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#38bdf8',
  },
  percentText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ffffff',
    textAlign: 'center',
  },
  actionsSection: {
    marginTop: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 16,
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