import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '../../contexts/ThemeContext';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import Constants from 'expo-constants';

const BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface Alert {
  _id: string;
  type: string;
  message: string;
  severity: string;
  entity_type: string;
  entity_id: string;
  created_at: string;
  acknowledged: boolean;
}

export default function AlertsScreen() {
  const { theme } = useTheme();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<'all' | 'critical' | 'warning'>('all');

  useEffect(() => {
    fetchAlerts();
  }, [filter]);

  const fetchAlerts = async () => {
    try {
      const params: any = {};
      if (filter !== 'all') {
        params.severity = filter;
      }
      const response = await axios.get(`${BACKEND_URL}/api/alerts`, { params });
      setAlerts(response.data.alerts || []);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    fetchAlerts();
  };

  const acknowledgeAlert = async (alertId: string) => {
    try {
      await axios.put(`${BACKEND_URL}/api/alerts/${alertId}/acknowledge`);
      fetchAlerts();
    } catch (error) {
      console.error('Error acknowledging alert:', error);
    }
  };

  const getAlertIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'alert-circle';
      case 'warning':
        return 'warning';
      case 'info':
        return 'information-circle';
      default:
        return 'notifications';
    }
  };

  const getAlertColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return theme.error;
      case 'warning':
        return theme.warning;
      case 'info':
        return theme.primary;
      default:
        return theme.textSecondary;
    }
  };

  const renderAlert = ({ item }: { item: Alert }) => (
    <View style={[styles.alertCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      <View style={styles.alertHeader}>
        <Ionicons
          name={getAlertIcon(item.severity) as any}
          size={24}
          color={getAlertColor(item.severity)}
        />
        <View style={styles.alertHeaderText}>
          <Text style={[styles.alertType, { color: theme.text }]}>{item.type}</Text>
          <Text style={[styles.alertTime, { color: theme.textSecondary }]}>
            {new Date(item.created_at).toLocaleString()}
          </Text>
        </View>
        {!item.acknowledged && (
          <View style={[styles.badge, { backgroundColor: getAlertColor(item.severity) + '20' }]}>
            <Text style={[styles.badgeText, { color: getAlertColor(item.severity) }]}>
              {item.severity}
            </Text>
          </View>
        )}
      </View>

      <Text style={[styles.alertMessage, { color: theme.text }]}>{item.message}</Text>

      {!item.acknowledged && (
        <TouchableOpacity
          style={[styles.acknowledgeButton, { borderColor: theme.primary }]}
          onPress={() => acknowledgeAlert(item._id)}
        >
          <Text style={[styles.acknowledgeText, { color: theme.primary }]}>Acknowledge</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.centerContent}>
          <ActivityIndicator size="large" color={theme.primary} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      {/* Filter Tabs */}
      <View style={[styles.filterContainer, { backgroundColor: theme.surface, borderBottomColor: theme.border }]}>
        {['all', 'critical', 'warning'].map((filterOption) => (
          <TouchableOpacity
            key={filterOption}
            style={[
              styles.filterTab,
              filter === filterOption && [styles.activeFilterTab, { borderBottomColor: theme.primary }],
            ]}
            onPress={() => setFilter(filterOption as any)}
          >
            <Text
              style={[
                styles.filterText,
                { color: theme.textSecondary },
                filter === filterOption && { color: theme.primary, fontWeight: '600' },
              ]}
            >
              {filterOption.charAt(0).toUpperCase() + filterOption.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <FlatList
        data={alerts}
        renderItem={renderAlert}
        keyExtractor={(item) => item._id}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={theme.primary}
          />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Ionicons name="notifications-off-outline" size={64} color={theme.textSecondary} />
            <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
              No alerts to display
            </Text>
          </View>
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  filterContainer: {
    flexDirection: 'row',
    borderBottomWidth: 1,
  },
  filterTab: {
    flex: 1,
    paddingVertical: 16,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  activeFilterTab: {
    borderBottomWidth: 2,
  },
  filterText: {
    fontSize: 14,
  },
  listContent: {
    padding: 16,
  },
  alertCard: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
  },
  alertHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  alertHeaderText: {
    flex: 1,
    marginLeft: 12,
  },
  alertType: {
    fontSize: 16,
    fontWeight: '600',
  },
  alertTime: {
    fontSize: 12,
    marginTop: 2,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  alertMessage: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
  },
  acknowledgeButton: {
    borderWidth: 1,
    borderRadius: 8,
    paddingVertical: 8,
    alignItems: 'center',
  },
  acknowledgeText: {
    fontSize: 14,
    fontWeight: '600',
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 48,
  },
  emptyText: {
    fontSize: 16,
    marginTop: 16,
  },
});