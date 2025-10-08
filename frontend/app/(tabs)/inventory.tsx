import React from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import Constants from 'expo-constants';

const BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface Inventory {
  id: string;
  stockyard_id: string;
  stockyard_name?: string;
  material_id: string;
  material_name?: string;
  quantity: number;
  cost_per_unit: number;
  last_updated?: string;
}

export default function InventoryScreen() {
  const { data: inventory, isLoading, refetch, isRefetching } = useQuery<Inventory[]>({
    queryKey: ['inventory'],
    queryFn: async () => {
      const response = await axios.get(`${BACKEND_URL}/api/inventory`);
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <ActivityIndicator size="large" color="#4a90e2" style={{ marginTop: 100 }} />
      </SafeAreaView>
    );
  }

  const totalValue = inventory?.reduce((sum, item) => sum + (item.quantity * item.cost_per_unit), 0) || 0;
  const totalQuantity = inventory?.reduce((sum, item) => sum + item.quantity, 0) || 0;

  // Group by stockyard
  const groupedInventory = inventory?.reduce((acc, item) => {
    const stockyard = item.stockyard_name || 'Unknown';
    if (!acc[stockyard]) {
      acc[stockyard] = [];
    }
    acc[stockyard].push(item);
    return acc;
  }, {} as Record<string, Inventory[]>) || {};

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.summaryCard}>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryLabel}>Total Quantity</Text>
            <Text style={styles.summaryValue}>{(totalQuantity / 1000).toFixed(1)}K MT</Text>
          </View>
          <View style={styles.divider} />
          <View style={styles.summaryItem}>
            <Text style={styles.summaryLabel}>Total Value</Text>
            <Text style={styles.summaryValue}>₹{(totalValue / 10000000).toFixed(2)}Cr</Text>
          </View>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor="#4a90e2" />
        }
      >
        {Object.entries(groupedInventory).map(([stockyard, items]) => {
          const stockyardValue = items.reduce((sum, item) => sum + (item.quantity * item.cost_per_unit), 0);
          
          return (
            <View key={stockyard} style={styles.section}>
              <View style={styles.sectionHeader}>
                <View style={styles.sectionTitleRow}>
                  <Ionicons name="business" size={20} color="#4a90e2" />
                  <Text style={styles.sectionTitle}>{stockyard}</Text>
                </View>
                <Text style={styles.sectionValue}>₹{(stockyardValue / 1000000).toFixed(2)}M</Text>
              </View>

              {items.map((item) => (
                <View key={item.id} style={styles.inventoryCard}>
                  <View style={styles.cardHeader}>
                    <View style={styles.materialInfo}>
                      <Text style={styles.materialName}>{item.material_name}</Text>
                      <Text style={styles.materialQuantity}>{item.quantity.toLocaleString()} MT</Text>
                    </View>
                    <View style={styles.valueInfo}>
                      <Text style={styles.costLabel}>₹{item.cost_per_unit}/MT</Text>
                      <Text style={styles.totalValue}>
                        ₹{((item.quantity * item.cost_per_unit) / 1000000).toFixed(2)}M
                      </Text>
                    </View>
                  </View>

                  <View style={styles.progressBar}>
                    <View
                      style={[
                        styles.progressFill,
                        { width: `${Math.min((item.quantity / 30000) * 100, 100)}%` },
                      ]}
                    />
                  </View>
                  
                  <View style={styles.cardFooter}>
                    <View style={styles.footerItem}>
                      <Ionicons name="cube-outline" size={14} color="#888" />
                      <Text style={styles.footerText}>Stock Level</Text>
                    </View>
                    <Text style={[
                      styles.stockStatus,
                      { color: item.quantity > 20000 ? '#51cf66' : item.quantity > 10000 ? '#ffd93d' : '#ff6b6b' }
                    ]}>
                      {item.quantity > 20000 ? 'High' : item.quantity > 10000 ? 'Medium' : 'Low'}
                    </Text>
                  </View>
                </View>
              ))}
            </View>
          );
        })}
      </ScrollView>
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
  summaryCard: {
    flexDirection: 'row',
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  summaryItem: {
    flex: 1,
    alignItems: 'center',
  },
  summaryLabel: {
    fontSize: 12,
    color: '#888',
    marginBottom: 4,
  },
  summaryValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  divider: {
    width: 1,
    backgroundColor: '#2a2a3e',
    marginHorizontal: 16,
  },
  scrollContent: {
    padding: 16,
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
    marginLeft: 8,
  },
  sectionValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#4a90e2',
  },
  inventoryCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  materialInfo: {
    flex: 1,
  },
  materialName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 4,
  },
  materialQuantity: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#4a90e2',
  },
  valueInfo: {
    alignItems: 'flex-end',
  },
  costLabel: {
    fontSize: 12,
    color: '#888',
    marginBottom: 4,
  },
  totalValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  progressBar: {
    height: 6,
    backgroundColor: '#2a2a3e',
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: 12,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#4a90e2',
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  footerItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: '#888',
    marginLeft: 4,
  },
  stockStatus: {
    fontSize: 12,
    fontWeight: 'bold',
  },
});
