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
  penalty_per_day: number;
}

interface CostAnalysis {
  order_id: string;
  customer_name: string;
  material_name: string;
  quantity: number;
  destination: string;
  best_stockyard: {
    id: string;
    name: string;
    location: string;
  };
  cost_breakdown: {
    loading_cost: number;
    transport_cost: number;
    demurrage_cost: number;
    penalty_cost: number;
    total_cost: number;
  };
  cost_savings: number;
  efficiency_score: number;
}

interface CostOptimizationResult {
  total_orders: number;
  total_savings: number;
  average_efficiency: number;
  cost_analyses: CostAnalysis[];
  recommended_actions: string[];
}

export default function CostOptimizeScreen() {
  const queryClient = useQueryClient();
  const [selectedOrders, setSelectedOrders] = useState<string[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [costResult, setCostResult] = useState<CostOptimizationResult | null>(null);
  const [maxCostBudget, setMaxCostBudget] = useState<string>('');

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

  const handleCostAnalysis = async () => {
    if (selectedOrders.length === 0) {
      Alert.alert('No Orders Selected', 'Please select at least one order to analyze');
      return;
    }

    setAnalyzing(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/api/cost-optimization`, {
        order_ids: selectedOrders,
        max_budget: maxCostBudget ? parseFloat(maxCostBudget) : null,
        optimization_type: 'minimize_total_cost'
      });
      
      setCostResult(response.data);
      Alert.alert('Cost Analysis Complete', `Analyzed ${response.data.total_orders} orders with potential savings of ₹${response.data.total_savings.toLocaleString()}`);
    } catch (error: any) {
      console.error('Cost analysis error:', error);
      Alert.alert('Analysis Failed', error.response?.data?.detail || 'An error occurred');
    } finally {
      setAnalyzing(false);
    }
  };

  const implementOptimization = async () => {
    if (!costResult) return;

    try {
      await axios.post(`${BACKEND_URL}/api/implement-cost-optimization`, {
        cost_analyses: costResult.cost_analyses
      });

      Alert.alert('Success', 'Cost optimization implemented! Orders have been assigned optimal stockyards.');
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      setCostResult(null);
      setSelectedOrders([]);
    } catch (error: any) {
      Alert.alert('Implementation Failed', error.response?.data?.detail || 'Failed to implement optimization');
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
          <Ionicons name="calculator" size={32} color="#f39c12" />
          <Text style={styles.title}>Cost & Efficiency Optimization</Text>
          <Text style={styles.subtitle}>Minimize logistics costs across loading, transport, demurrage & penalties</Text>
        </View>

        {/* Budget Input */}
        <View style={styles.budgetCard}>
          <Text style={styles.budgetLabel}>Maximum Cost Budget (Optional)</Text>
          <TextInput
            style={styles.budgetInput}
            placeholder="Enter max budget in ₹"
            placeholderTextColor="#666"
            value={maxCostBudget}
            onChangeText={setMaxCostBudget}
            keyboardType="numeric"
          />
        </View>

        {/* Results Section */}
        {costResult && (
          <View style={styles.resultsSection}>
            <Text style={styles.sectionTitle}>Cost Analysis Results</Text>
            
            <View style={styles.summaryCards}>
              <View style={styles.summaryCard}>
                <Text style={styles.summaryValue}>₹{costResult.total_savings.toLocaleString()}</Text>
                <Text style={styles.summaryLabel}>Total Savings</Text>
              </View>
              <View style={styles.summaryCard}>
                <Text style={styles.summaryValue}>{costResult.average_efficiency.toFixed(1)}%</Text>
                <Text style={styles.summaryLabel}>Avg Efficiency</Text>
              </View>
            </View>

            {/* Recommended Actions */}
            <View style={styles.actionsCard}>
              <Text style={styles.cardTitle}>Recommended Actions</Text>
              {costResult.recommended_actions.map((action, index) => (
                <View key={index} style={styles.actionItem}>
                  <Ionicons name="arrow-forward" size={16} color="#51cf66" />
                  <Text style={styles.actionText}>{action}</Text>
                </View>
              ))}
            </View>

            {/* Detailed Analysis */}
            <View style={styles.analysisSection}>
              <Text style={styles.cardTitle}>Detailed Cost Analysis</Text>
              {costResult.cost_analyses.map((analysis) => (
                <View key={analysis.order_id} style={styles.analysisCard}>
                  <View style={styles.analysisHeader}>
                    <Text style={styles.customerName}>{analysis.customer_name}</Text>
                    <View style={styles.savingsBadge}>
                      <Text style={styles.savingsText}>Save ₹{analysis.cost_savings.toLocaleString()}</Text>
                    </View>
                  </View>
                  
                  <Text style={styles.analysisDetail}>{analysis.material_name} - {analysis.quantity} MT → {analysis.destination}</Text>
                  <Text style={styles.stockyardRecommendation}>
                    Best Source: {analysis.best_stockyard.name} ({analysis.best_stockyard.location})
                  </Text>
                  
                  <View style={styles.costBreakdown}>
                    <View style={styles.costRow}>
                      <Text style={styles.costLabel}>Loading:</Text>
                      <Text style={styles.costValue}>₹{analysis.cost_breakdown.loading_cost.toLocaleString()}</Text>
                    </View>
                    <View style={styles.costRow}>
                      <Text style={styles.costLabel}>Transport:</Text>
                      <Text style={styles.costValue}>₹{analysis.cost_breakdown.transport_cost.toLocaleString()}</Text>
                    </View>
                    <View style={styles.costRow}>
                      <Text style={styles.costLabel}>Demurrage:</Text>
                      <Text style={styles.costValue}>₹{analysis.cost_breakdown.demurrage_cost.toLocaleString()}</Text>
                    </View>
                    <View style={styles.costRow}>
                      <Text style={styles.costLabel}>Penalty Risk:</Text>
                      <Text style={styles.costValue}>₹{analysis.cost_breakdown.penalty_cost.toLocaleString()}</Text>
                    </View>
                    <View style={[styles.costRow, styles.totalCostRow]}>
                      <Text style={styles.totalLabel}>Total Cost:</Text>
                      <Text style={styles.totalValue}>₹{analysis.cost_breakdown.total_cost.toLocaleString()}</Text>
                    </View>
                  </View>
                  
                  <View style={styles.efficiencyBar}>
                    <View style={[styles.efficiencyFill, { width: `${analysis.efficiency_score}%` }]} />
                    <Text style={styles.efficiencyText}>{analysis.efficiency_score.toFixed(1)}% Efficient</Text>
                  </View>
                </View>
              ))}
            </View>

            <TouchableOpacity style={styles.implementButton} onPress={implementOptimization}>
              <Ionicons name="checkmark-circle" size={20} color="#fff" />
              <Text style={styles.implementButtonText}>Implement Optimization</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Order Selection */}
        <View style={styles.ordersSection}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Select Orders for Cost Analysis</Text>
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
                <Text style={styles.penaltyText}>₹{order.penalty_per_day}/day</Text>
              </View>

              <View style={styles.orderDetails}>
                <Text style={styles.orderDetailText}>{order.material_name} - {order.quantity} MT</Text>
                <Text style={styles.orderDetailText}>Destination: {order.destination}</Text>
                <Text style={[styles.orderDetailText, { color: order.days_until_deadline && order.days_until_deadline < 3 ? '#ff6b6b' : '#51cf66' }]}>
                  Due in {order.days_until_deadline} days
                </Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>

        <TouchableOpacity
          style={[styles.analyzeButton, selectedOrders.length === 0 && styles.analyzeButtonDisabled]}
          onPress={handleCostAnalysis}
          disabled={analyzing || selectedOrders.length === 0}
        >
          {analyzing ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <>
              <Ionicons name="analytics" size={20} color="#fff" />
              <Text style={styles.analyzeButtonText}>Analyze Costs & Optimize</Text>
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
    fontSize: 26,
    fontWeight: 'bold',
    color: '#ffffff',
    marginTop: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 14,
    color: '#888',
    marginTop: 4,
    textAlign: 'center',
    lineHeight: 20,
  },
  budgetCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  budgetLabel: {
    fontSize: 14,
    color: '#ffffff',
    marginBottom: 8,
    fontWeight: '600',
  },
  budgetInput: {
    backgroundColor: '#2a2a3e',
    borderRadius: 8,
    padding: 12,
    color: '#ffffff',
    fontSize: 16,
  },
  resultsSection: {
    marginBottom: 24,
  },
  summaryCards: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  summaryCard: {
    flex: 1,
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  summaryValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#f39c12',
    marginBottom: 4,
  },
  summaryLabel: {
    fontSize: 12,
    color: '#888',
  },
  actionsCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 12,
  },
  actionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  actionText: {
    fontSize: 14,
    color: '#a0a0a0',
    marginLeft: 8,
    lineHeight: 20,
  },
  analysisSection: {
    marginBottom: 16,
  },
  analysisCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  analysisHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  savingsBadge: {
    backgroundColor: '#51cf66',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  savingsText: {
    fontSize: 12,
    color: '#ffffff',
    fontWeight: 'bold',
  },
  analysisDetail: {
    fontSize: 14,
    color: '#a0a0a0',
    marginBottom: 4,
  },
  stockyardRecommendation: {
    fontSize: 14,
    color: '#4a90e2',
    fontWeight: '600',
    marginBottom: 12,
  },
  costBreakdown: {
    backgroundColor: '#2a2a3e',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  costRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  costLabel: {
    fontSize: 13,
    color: '#a0a0a0',
  },
  costValue: {
    fontSize: 13,
    color: '#ffffff',
    fontWeight: '500',
  },
  totalCostRow: {
    borderTopWidth: 1,
    borderTopColor: '#4a4a5e',
    paddingTop: 4,
    marginTop: 4,
  },
  totalLabel: {
    fontSize: 14,
    color: '#ffffff',
    fontWeight: 'bold',
  },
  totalValue: {
    fontSize: 14,
    color: '#f39c12',
    fontWeight: 'bold',
  },
  efficiencyBar: {
    height: 20,
    backgroundColor: '#2a2a3e',
    borderRadius: 10,
    position: 'relative',
    justifyContent: 'center',
  },
  efficiencyFill: {
    position: 'absolute',
    height: '100%',
    backgroundColor: '#51cf66',
    borderRadius: 10,
  },
  efficiencyText: {
    fontSize: 12,
    color: '#ffffff',
    fontWeight: 'bold',
    textAlign: 'center',
    zIndex: 1,
  },
  implementButton: {
    backgroundColor: '#51cf66',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 8,
    gap: 8,
    marginBottom: 24,
  },
  implementButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
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
    borderColor: '#f39c12',
    backgroundColor: 'rgba(243, 156, 18, 0.1)',
  },
  orderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
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
    borderColor: '#f39c12',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  checkboxChecked: {
    backgroundColor: '#f39c12',
  },
  customerName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  penaltyText: {
    fontSize: 12,
    color: '#ff6b6b',
    fontWeight: '600',
  },
  orderDetails: {
    gap: 4,
  },
  orderDetailText: {
    fontSize: 14,
    color: '#a0a0a0',
  },
  analyzeButton: {
    backgroundColor: '#f39c12',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 8,
    gap: 8,
  },
  analyzeButtonDisabled: {
    backgroundColor: '#2a2a3e',
  },
  analyzeButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});