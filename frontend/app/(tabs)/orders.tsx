import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl, ActivityIndicator, Modal, TextInput, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import Constants from 'expo-constants';
import { format } from 'date-fns';

const BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface Order {
  id: string;
  customer_name: string;
  material_id: string;
  material_name?: string;
  quantity: number;
  destination: string;
  priority: string;
  deadline: string;
  status: string;
  penalty_per_day: number;
  days_until_deadline?: number;
}

interface Material {
  id: string;
  name: string;
  type: string;
  unit: string;
}

export default function OrdersScreen() {
  const queryClient = useQueryClient();
  const [showAddModal, setShowAddModal] = useState(false);
  const [newOrder, setNewOrder] = useState({
    customer_name: '',
    material_id: '',
    quantity: '',
    destination: '',
    priority: 'medium',
    deadline_days: '7',
    penalty_per_day: '5000',
  });

  const { data: orders, isLoading, refetch, isRefetching } = useQuery<Order[]>({
    queryKey: ['orders'],
    queryFn: async () => {
      const response = await axios.get(`${BACKEND_URL}/api/orders`);
      return response.data;
    },
  });

  const { data: materials } = useQuery<Material[]>({
    queryKey: ['materials'],
    queryFn: async () => {
      const response = await axios.get(`${BACKEND_URL}/api/materials`);
      return response.data;
    },
  });

  const handleAddOrder = async () => {
    try {
      const deadlineDate = new Date();
      deadlineDate.setDate(deadlineDate.getDate() + parseInt(newOrder.deadline_days || '7'));

      await axios.post(`${BACKEND_URL}/api/orders`, {
        customer_name: newOrder.customer_name,
        material_id: newOrder.material_id,
        quantity: parseFloat(newOrder.quantity),
        destination: newOrder.destination,
        priority: newOrder.priority,
        deadline: deadlineDate.toISOString(),
        status: 'pending',
        penalty_per_day: parseFloat(newOrder.penalty_per_day),
      });

      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardStats'] });
      setShowAddModal(false);
      setNewOrder({
        customer_name: '',
        material_id: '',
        quantity: '',
        destination: '',
        priority: 'medium',
        deadline_days: '7',
        penalty_per_day: '5000',
      });
    } catch (error) {
      console.error('Error adding order:', error);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return '#ff6b6b';
      case 'medium':
        return '#ffd93d';
      case 'low':
        return '#51cf66';
      default:
        return '#888';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return '#ffd93d';
      case 'assigned':
        return '#38bdf8';
      case 'shipped':
        return '#a78bfa';
      case 'delivered':
        return '#51cf66';
      default:
        return '#888';
    }
  };

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <ActivityIndicator size="large" color="#4a90e2" style={{ marginTop: 100 }} />
      </SafeAreaView>
    );
  }

  const pendingOrders = orders?.filter(o => o.status === 'pending') || [];
  const activeOrders = orders?.filter(o => ['assigned', 'shipped'].includes(o.status)) || [];
  const completedOrders = orders?.filter(o => o.status === 'delivered') || [];

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.addButton}
          onPress={() => setShowAddModal(true)}
        >
          <Ionicons name="add-circle" size={24} color="#4a90e2" />
          <Text style={styles.addButtonText}>New Order</Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor="#4a90e2" />
        }
      >
        <View style={styles.statsRow}>
          <View style={styles.miniStat}>
            <Text style={styles.miniStatValue}>{pendingOrders.length}</Text>
            <Text style={styles.miniStatLabel}>Pending</Text>
          </View>
          <View style={styles.miniStat}>
            <Text style={styles.miniStatValue}>{activeOrders.length}</Text>
            <Text style={styles.miniStatLabel}>Active</Text>
          </View>
          <View style={styles.miniStat}>
            <Text style={styles.miniStatValue}>{completedOrders.length}</Text>
            <Text style={styles.miniStatLabel}>Completed</Text>
          </View>
        </View>

        {pendingOrders.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Pending Orders</Text>
            {pendingOrders.map((order) => (
              <View key={order.id} style={styles.orderCard}>
                <View style={styles.orderHeader}>
                  <Text style={styles.customerName}>{order.customer_name}</Text>
                  <View style={[styles.priorityBadge, { backgroundColor: getPriorityColor(order.priority) }]}>
                    <Text style={styles.badgeText}>{order.priority.toUpperCase()}</Text>
                  </View>
                </View>
                
                <View style={styles.orderDetail}>
                  <Ionicons name="cube" size={16} color="#888" />
                  <Text style={styles.detailText}>{order.material_name} - {order.quantity} MT</Text>
                </View>
                
                <View style={styles.orderDetail}>
                  <Ionicons name="location" size={16} color="#888" />
                  <Text style={styles.detailText}>{order.destination}</Text>
                </View>
                
                <View style={styles.orderFooter}>
                  <View style={styles.orderDetail}>
                    <Ionicons
                      name="time"
                      size={16}
                      color={order.days_until_deadline && order.days_until_deadline < 3 ? '#ff6b6b' : '#888'}
                    />
                    <Text style={[styles.detailText, order.days_until_deadline && order.days_until_deadline < 3 && { color: '#ff6b6b' }]}>
                      {order.days_until_deadline} days left
                    </Text>
                  </View>
                  <View style={[styles.statusBadge, { backgroundColor: getStatusColor(order.status) }]}>
                    <Text style={styles.badgeText}>{order.status.toUpperCase()}</Text>
                  </View>
                </View>
              </View>
            ))}
          </View>
        )}

        {activeOrders.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Active Orders</Text>
            {activeOrders.map((order) => (
              <View key={order.id} style={styles.orderCard}>
                <View style={styles.orderHeader}>
                  <Text style={styles.customerName}>{order.customer_name}</Text>
                  <View style={[styles.statusBadge, { backgroundColor: getStatusColor(order.status) }]}>
                    <Text style={styles.badgeText}>{order.status.toUpperCase()}</Text>
                  </View>
                </View>
                
                <View style={styles.orderDetail}>
                  <Ionicons name="cube" size={16} color="#888" />
                  <Text style={styles.detailText}>{order.material_name} - {order.quantity} MT</Text>
                </View>
                
                <View style={styles.orderDetail}>
                  <Ionicons name="location" size={16} color="#888" />
                  <Text style={styles.detailText}>{order.destination}</Text>
                </View>
              </View>
            ))}
          </View>
        )}
      </ScrollView>

      <Modal
        visible={showAddModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowAddModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>New Order</Text>
              <TouchableOpacity onPress={() => setShowAddModal(false)}>
                <Ionicons name="close" size={24} color="#fff" />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalScroll}>
              <Text style={styles.label}>Customer Name</Text>
              <TextInput
                style={styles.input}
                value={newOrder.customer_name}
                onChangeText={(text) => setNewOrder({ ...newOrder, customer_name: text })}
                placeholder="Enter customer name"
                placeholderTextColor="#666"
              />

              <Text style={styles.label}>Material</Text>
              <View style={styles.pickerContainer}>
                {materials?.map((material) => (
                  <TouchableOpacity
                    key={material.id}
                    style={[
                      styles.pickerOption,
                      newOrder.material_id === material.id && styles.pickerOptionSelected,
                    ]}
                    onPress={() => setNewOrder({ ...newOrder, material_id: material.id })}
                  >
                    <Text
                      style={[
                        styles.pickerOptionText,
                        newOrder.material_id === material.id && styles.pickerOptionTextSelected,
                      ]}
                    >
                      {material.name}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={styles.label}>Quantity (MT)</Text>
              <TextInput
                style={styles.input}
                value={newOrder.quantity}
                onChangeText={(text) => setNewOrder({ ...newOrder, quantity: text })}
                placeholder="Enter quantity"
                placeholderTextColor="#666"
                keyboardType="numeric"
              />

              <Text style={styles.label}>Destination</Text>
              <TextInput
                style={styles.input}
                value={newOrder.destination}
                onChangeText={(text) => setNewOrder({ ...newOrder, destination: text })}
                placeholder="Enter destination"
                placeholderTextColor="#666"
              />

              <Text style={styles.label}>Priority</Text>
              <View style={styles.pickerContainer}>
                {['high', 'medium', 'low'].map((priority) => (
                  <TouchableOpacity
                    key={priority}
                    style={[
                      styles.pickerOption,
                      newOrder.priority === priority && styles.pickerOptionSelected,
                    ]}
                    onPress={() => setNewOrder({ ...newOrder, priority })}
                  >
                    <Text
                      style={[
                        styles.pickerOptionText,
                        newOrder.priority === priority && styles.pickerOptionTextSelected,
                      ]}
                    >
                      {priority.toUpperCase()}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={styles.label}>Deadline (Days from now)</Text>
              <TextInput
                style={styles.input}
                value={newOrder.deadline_days}
                onChangeText={(text) => setNewOrder({ ...newOrder, deadline_days: text })}
                placeholder="Enter days"
                placeholderTextColor="#666"
                keyboardType="numeric"
              />

              <Text style={styles.label}>Penalty per Day (₹)</Text>
              <TextInput
                style={styles.input}
                value={newOrder.penalty_per_day}
                onChangeText={(text) => setNewOrder({ ...newOrder, penalty_per_day: text })}
                placeholder="Enter penalty amount"
                placeholderTextColor="#666"
                keyboardType="numeric"
              />

              <TouchableOpacity style={styles.submitButton} onPress={handleAddOrder}>
                <Text style={styles.submitButtonText}>Create Order</Text>
              </TouchableOpacity>
            </ScrollView>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f0f23',
  },
  header: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a3e',
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1a1a2e',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#4a90e2',
  },
  addButtonText: {
    color: '#4a90e2',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  scrollContent: {
    padding: 16,
  },
  statsRow: {
    flexDirection: 'row',
    marginBottom: 24,
    gap: 12,
  },
  miniStat: {
    flex: 1,
    backgroundColor: '#1a1a2e',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  miniStatValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  miniStatLabel: {
    fontSize: 12,
    color: '#888',
    marginTop: 4,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 12,
  },
  orderCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  orderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  customerName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
    flex: 1,
  },
  priorityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#000',
  },
  orderDetail: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  detailText: {
    fontSize: 14,
    color: '#a0a0a0',
    marginLeft: 8,
  },
  orderFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1a1a2e',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '90%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a3e',
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  modalScroll: {
    padding: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#a0a0a0',
    marginBottom: 8,
    marginTop: 16,
  },
  input: {
    backgroundColor: '#0f0f23',
    borderWidth: 1,
    borderColor: '#2a2a3e',
    borderRadius: 8,
    padding: 12,
    color: '#ffffff',
    fontSize: 16,
  },
  pickerContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  pickerOption: {
    backgroundColor: '#0f0f23',
    borderWidth: 1,
    borderColor: '#2a2a3e',
    borderRadius: 8,
    padding: 12,
  },
  pickerOptionSelected: {
    backgroundColor: '#4a90e2',
    borderColor: '#4a90e2',
  },
  pickerOptionText: {
    color: '#a0a0a0',
    fontSize: 14,
  },
  pickerOptionTextSelected: {
    color: '#ffffff',
    fontWeight: 'bold',
  },
  submitButton: {
    backgroundColor: '#4a90e2',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 24,
    marginBottom: 32,
  },
  submitButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});