import React from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import Constants from 'expo-constants';

const BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface Rake {
  id: string;
  rake_number: string;
  wagon_count: number;
  order_count: number;
  loading_point_name?: string;
  route: string;
  total_cost: number;
  status: string;
  ai_recommendation?: string;
}

export default function RakesScreen() {
  const { data: rakes, isLoading, refetch, isRefetching } = useQuery<Rake[]>({
    queryKey: ['rakes'],
    queryFn: async () => {
      const response = await axios.get(`${BACKEND_URL}/api/rakes`);
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

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor="#4a90e2" />
        }
      >
        <Text style={styles.header}>Rake Management</Text>
        
        {!rakes || rakes.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="train-outline" size={64} color="#2a2a3e" />
            <Text style={styles.emptyText}>No rakes yet</Text>
            <Text style={styles.emptySubtext}>Use AI Optimize to create rake formations</Text>
          </View>
        ) : (
          rakes.map((rake) => (
            <View key={rake.id} style={styles.rakeCard}>
              <View style={styles.rakeHeader}>
                <Ionicons name="train" size={20} color="#4a90e2" />
                <Text style={styles.rakeNumber}>{rake.rake_number}</Text>
              </View>
              
              <Text style={styles.routeText}>{rake.route}</Text>
              
              <View style={styles.statsRow}>
                <View style={styles.stat}>
                  <Text style={styles.statLabel}>Wagons</Text>
                  <Text style={styles.statValue}>{rake.wagon_count}</Text>
                </View>
                <View style={styles.stat}>
                  <Text style={styles.statLabel}>Orders</Text>
                  <Text style={styles.statValue}>{rake.order_count}</Text>
                </View>
                <View style={styles.stat}>
                  <Text style={styles.statLabel}>Cost</Text>
                  <Text style={styles.statValue}>₹{(rake.total_cost / 1000).toFixed(0)}K</Text>
                </View>
              </View>

              {rake.ai_recommendation && (
                <View style={styles.aiBox}>
                  <Ionicons name="sparkles" size={14} color="#51cf66" />
                  <Text style={styles.aiText} numberOfLines={2}>{rake.ai_recommendation}</Text>
                </View>
              )}
            </View>
          ))
        )}
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
    marginBottom: 20,
  },
  rakeCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  rakeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  rakeNumber: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
    marginLeft: 8,
  },
  routeText: {
    fontSize: 14,
    color: '#a0a0a0',
    marginBottom: 12,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  stat: {
    flex: 1,
    backgroundColor: '#0f0f23',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 12,
    color: '#888',
    marginBottom: 4,
  },
  statValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  aiBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(81, 207, 102, 0.1)',
    padding: 8,
    borderRadius: 6,
    borderLeftWidth: 3,
    borderLeftColor: '#51cf66',
  },
  aiText: {
    fontSize: 12,
    color: '#a0a0a0',
    marginLeft: 8,
    flex: 1,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#888',
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#666',
    marginTop: 8,
  },
});
