import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, Alert, TextInput } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import Constants from 'expo-constants';

const BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface Order {
  id: string;
  customer_name: string;
  material_name?: string;
  quantity: number;
  destination: string;
  priority: string;
  status: string;
  days_until_deadline?: number;
}

export default function OptimizeScreen() {
  const queryClient = useQueryClient();
  const [selectedOrders, setSelectedOrders] = useState<string[]>([]);
  const [optimizing, setOptimizing] = useState(false);

  const { data: orders, isLoading } = useQuery<Order[]>({
    queryKey: ['orders'],
    queryFn: async () => {
      const response = await axios.get(`${BACKEND_URL}/api/orders`);
      return response.data.filter((o: Order) => o.status === 'pending');
    },
  });

  const toggleOrder = (orderId: string) => {
    if (selectedOrders.includes(orderId)) {
      setSelectedOrders(selectedOrders.filter(id => id !== orderId));
    } else {
      setSelectedOrders([...selectedOrders, orderId]);
    }
  };

  const handleOptimize = async () => {
    if (selectedOrders.length === 0) {
      Alert.alert('No Orders Selected', 'Please select at least one order to optimize');
      return;
    }

    setOptimizing(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/api/optimize-rake`, {
        order_ids: selectedOrders,
        priority_weight: 0.5,
      });
      
      const result = response.data;
      Alert.alert('Optimization Complete', `AI has generated ${result.recommended_rakes.length} rake recommendations!`);
      
      // Create rakes automatically
      for (const rake of result.recommended_rakes) {
        await axios.post(`${BACKEND_URL}/api/rakes`, {
          rake_number: rake.rake_number,
          wagon_ids: rake.wagons,
          order_ids: rake.orders,
          loading_point_id: rake.loading_point_id,
          route: rake.route,
          total_cost: rake.total_cost,
          transport_cost: rake.transport_cost,
          loading_cost: rake.loading_cost,
          estimated_penalty: rake.estimated_penalty,
          status: 'planned',
          formation_date: new Date().toISOString(),
          ai_recommendation: rake.reasoning,
        });
      }

      queryClient.invalidateQueries({ queryKey: ['rakes'] });
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
      
      setSelectedOrders([]);
    } catch (error: any) {
      console.error('Optimization error:', error);
      Alert.alert('Optimization Failed', error.response?.data?.detail || 'An error occurred');
    } finally {
      setOptimizing(false);
    }
  };

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <ActivityIndicator size="large" color="#4a90e2" style={{ marginTop: 100 }} />
      </SafeAreaView>
    );
  }

  const pendingOrders = orders || [];

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Ionicons name="sparkles" size={32} color="#51cf66" />
          <Text style={styles.title}>AI Rake Optimization</Text>
          <Text style={styles.subtitle}>Select orders to optimize rake formation</Text>
        </View>

        <View style={styles.statsCard}>
          <Text style={styles.statsLabel}>Selected Orders</Text>
          <Text style={styles.statsValue}>{selectedOrders.length}</Text>
        </View>

        <View style={styles.ordersSection}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Available Orders</Text>
            {selectedOrders.length > 0 && (
              <TouchableOpacity onPress={() => setSelectedOrders([])}>
                <Text style={styles.clearText}>Clear All</Text>
              </TouchableOpacity>
            )}
          </View>

          {pendingOrders.map((order) => (
            <TouchableOpacity
              key={order.id}
              style={[
                styles.orderCard,
                selectedOrders.includes(order.id) && styles.orderCardSelected,
              ]}
              onPress={() => toggleOrder(order.id)}
            >
              <View style={styles.orderHeader}>
                <View style={styles.checkboxContainer}>
                  <View style={[
                    styles.checkbox,
                    selectedOrders.includes(order.id) && styles.checkboxChecked,
                  ]}>
                    {selectedOrders.includes(order.id) && (
                      <Ionicons name="checkmark" size={16} color="#fff" />
                    )}
                  </View>
                  <Text style={styles.customerName}>{order.customer_name}</Text>
                </View>
              </View>

              <View style={styles.orderDetails}>
                <Text style={styles.orderDetailText}>{order.material_name} - {order.quantity} MT</Text>
                <Text style={styles.orderDetailText}>{order.destination}</Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>

        <TouchableOpacity
          style={[styles.optimizeButton, selectedOrders.length === 0 && styles.optimizeButtonDisabled]}
          onPress={handleOptimize}
          disabled={optimizing || selectedOrders.length === 0}
        >
          {optimizing ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <>
              <Ionicons name="flash" size={20} color="#fff" />
              <Text style={styles.optimizeButtonText}>Optimize with AI</Text>
            </>
          )}
        </TouchableOpacity>
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
    alignItems: 'center',
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
    marginTop: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#888',
    marginTop: 4,
  },
  statsCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  statsLabel: {
    fontSize: 12,
    color: '#888',
    marginBottom: 4,
  },
  statsValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  ordersSection: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  clearText: {
    fontSize: 14,
    color: '#4a90e2',
  },
  orderCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 2,
    borderColor: '#2a2a3e',
  },
  orderCardSelected: {
    borderColor: '#4a90e2',
    backgroundColor: 'rgba(74, 144, 226, 0.1)',
  },
  orderHeader: {
    marginBottom: 12,
  },
  checkboxContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: '#4a90e2',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  checkboxChecked: {
    backgroundColor: '#4a90e2',
  },
  customerName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  orderDetails: {
    gap: 4,
  },
  orderDetailText: {
    fontSize: 14,
    color: '#a0a0a0',
  },
  optimizeButton: {
    backgroundColor: '#51cf66',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 8,
    gap: 8,
  },
  optimizeButtonDisabled: {
    backgroundColor: '#2a2a3e',
  },
  optimizeButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
