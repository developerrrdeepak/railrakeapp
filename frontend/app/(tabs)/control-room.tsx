import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl, ActivityIndicator, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import Constants from 'expo-constants';

const BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface WorkflowApproval {
  id: string;
  entity_type: string;
  entity_id: string;
  approver_id: string;
  approval_status: string;
  comments?: string;
  requested_at: string;
  entity_details?: any;
}

interface ERPSync {
  recent_syncs: Array<{
    id?: string;
    system_name: string;
    last_sync: string;
    sync_status: string;
    records_synced: number;
    error_message?: string;
  }>;
  systems_status: {
    SAP: string;
    Oracle: string;
  };
}

interface CompatibilityRule {
  id: string;
  material_type: string;
  wagon_type: string;
  compatibility_score: number;
  restrictions: string[];
  loading_efficiency: number;
}

export default function ControlRoomScreen() {
  const [activeSection, setActiveSection] = useState<'approvals' | 'erp' | 'compatibility' | 'analytics'>('approvals');
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Workflow Approvals
  const { data: approvals, isLoading: approvalsLoading, refetch: refetchApprovals } = useQuery<WorkflowApproval[]>({
    queryKey: ['workflowApprovals'],
    queryFn: async () => {
      const response = await axios.get(`${BACKEND_URL}/api/workflow/approvals/pending`);
      return response.data;
    },
    refetchInterval: 30000,
  });

  // ERP Sync Status
  const { data: erpStatus, isLoading: erpLoading, refetch: refetchERP } = useQuery<ERPSync>({
    queryKey: ['erpStatus'],
    queryFn: async () => {
      const response = await axios.get(`${BACKEND_URL}/api/erp-sync/status`);
      return response.data;
    },
    refetchInterval: 60000,
  });

  // Compatibility Rules
  const { data: compatibilityRules, isLoading: compatibilityLoading, refetch: refetchCompatibility } = useQuery<CompatibilityRule[]>({
    queryKey: ['compatibilityRules'],
    queryFn: async () => {
      const response = await axios.get(`${BACKEND_URL}/api/compatibility-rules`);
      return response.data;
    },
  });

  // Analytics
  const { data: analytics, isLoading: analyticsLoading, refetch: refetchAnalytics } = useQuery({
    queryKey: ['performanceAnalytics'],
    queryFn: async () => {
      const response = await axios.get(`${BACKEND_URL}/api/analytics/performance`);
      return response.data;
    },
    refetchInterval: 300000, // 5 minutes
  });

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([refetchApprovals(), refetchERP(), refetchCompatibility(), refetchAnalytics()]);
    setIsRefreshing(false);
  };

  const handleApproval = async (approvalId: string, status: 'approved' | 'rejected', comments?: string) => {
    try {
      await axios.put(`${BACKEND_URL}/api/workflow/approvals/${approvalId}`, {
        status,
        comments: comments || ''
      });
      Alert.alert('Success', `Request ${status} successfully`);
      refetchApprovals();
    } catch (error) {
      Alert.alert('Error', 'Failed to update approval status');
    }
  };

  const triggerERPSync = async (systemName: string) => {
    try {
      await axios.post(`${BACKEND_URL}/api/erp-sync/trigger`, { system_name: systemName });
      Alert.alert('Success', `${systemName} synchronization triggered`);
      setTimeout(() => refetchERP(), 2000);
    } catch (error) {
      Alert.alert('Error', `Failed to trigger ${systemName} sync`);
    }
  };

  if (approvalsLoading && erpLoading) {
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
        <Text style={styles.headerTitle}>Advanced Control Room</Text>
        <Text style={styles.headerSubtitle}>System Management & Monitoring</Text>
      </View>

      {/* Section Navigation */}
      <View style={styles.sectionNav}>
        {[
          { key: 'approvals', title: 'Approvals', icon: 'checkmark-circle' },
          { key: 'erp', title: 'ERP Sync', icon: 'sync' },
          { key: 'compatibility', title: 'Compatibility', icon: 'grid' },
          { key: 'analytics', title: 'Analytics', icon: 'analytics' },
        ].map((section) => (
          <TouchableOpacity
            key={section.key}
            style={[styles.navButton, activeSection === section.key && styles.activeNavButton]}
            onPress={() => setActiveSection(section.key as any)}
          >
            <Ionicons 
              name={section.icon as any} 
              size={16} 
              color={activeSection === section.key ? '#fff' : '#666'} 
            />
            <Text style={[styles.navText, activeSection === section.key && styles.activeNavText]}>
              {section.title}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={isRefreshing} onRefresh={handleRefresh} tintColor="#4a90e2" />
        }
      >
        {activeSection === 'approvals' && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Pending Workflow Approvals</Text>
            {approvals && approvals.length > 0 ? (
              approvals.map((approval) => (
                <View key={approval.id} style={styles.approvalCard}>
                  <View style={styles.approvalHeader}>
                    <View style={styles.approvalInfo}>
                      <Text style={styles.approvalType}>{approval.entity_type.toUpperCase()}</Text>
                      <Text style={styles.approvalTime}>
                        {new Date(approval.requested_at).toLocaleDateString()}
                      </Text>
                    </View>
                    <View style={[styles.statusBadge, {
                      backgroundColor: approval.approval_status === 'pending' ? '#ffd93d' : 
                                     approval.approval_status === 'approved' ? '#51cf66' : '#ff6b6b'
                    }]}>
                      <Text style={styles.statusText}>{approval.approval_status.toUpperCase()}</Text>
                    </View>
                  </View>
                  
                  {approval.comments && (
                    <Text style={styles.approvalComments}>{approval.comments}</Text>
                  )}
                  
                  {approval.approval_status === 'pending' && (
                    <View style={styles.approvalActions}>
                      <TouchableOpacity
                        style={[styles.actionButton, styles.approveButton]}
                        onPress={() => handleApproval(approval.id, 'approved', 'Approved from control room')}
                      >
                        <Ionicons name="checkmark" size={16} color="#fff" />
                        <Text style={styles.actionText}>Approve</Text>
                      </TouchableOpacity>
                      
                      <TouchableOpacity
                        style={[styles.actionButton, styles.rejectButton]}
                        onPress={() => handleApproval(approval.id, 'rejected', 'Rejected from control room')}
                      >
                        <Ionicons name="close" size={16} color="#fff" />
                        <Text style={styles.actionText}>Reject</Text>
                      </TouchableOpacity>
                    </View>
                  )}
                </View>
              ))
            ) : (
              <Text style={styles.emptyText}>No pending approvals</Text>
            )}
          </View>
        )}

        {activeSection === 'erp' && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>ERP System Integration</Text>
            
            <View style={styles.erpStatusCard}>
              <Text style={styles.cardTitle}>System Status</Text>
              <View style={styles.erpSystems}>
                {Object.entries(erpStatus?.systems_status || {}).map(([system, status]) => (
                  <View key={system} style={styles.erpSystem}>
                    <View style={styles.systemInfo}>
                      <Text style={styles.systemName}>{system}</Text>
                      <View style={[styles.systemStatus, {
                        backgroundColor: status === 'connected' ? '#51cf66' : '#ff6b6b'
                      }]}>
                        <Text style={styles.systemStatusText}>{status.toUpperCase()}</Text>
                      </View>
                    </View>
                    <TouchableOpacity
                      style={styles.syncButton}
                      onPress={() => triggerERPSync(system)}
                    >
                      <Ionicons name="sync" size={16} color="#4a90e2" />
                      <Text style={styles.syncText}>Sync Now</Text>
                    </TouchableOpacity>
                  </View>
                ))}
              </View>
            </View>

            <Text style={styles.cardTitle}>Recent Sync History</Text>
            {erpStatus?.recent_syncs?.map((sync, index) => (
              <View key={index} style={styles.syncCard}>
                <View style={styles.syncHeader}>
                  <Text style={styles.syncSystem}>{sync.system_name}</Text>
                  <Text style={styles.syncTime}>
                    {new Date(sync.last_sync).toLocaleString()}
                  </Text>
                </View>
                <View style={styles.syncDetails}>
                  <Text style={[styles.syncStatus, {
                    color: sync.sync_status === 'success' ? '#51cf66' : '#ff6b6b'
                  }]}>
                    {sync.sync_status.toUpperCase()}
                  </Text>
                  <Text style={styles.syncRecords}>
                    {sync.records_synced} records
                  </Text>
                </View>
                {sync.error_message && (
                  <Text style={styles.errorMessage}>{sync.error_message}</Text>
                )}
              </View>
            ))}
          </View>
        )}

        {activeSection === 'compatibility' && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Material-Wagon Compatibility Matrix</Text>
            {compatibilityRules?.map((rule) => (
              <View key={rule.id} style={styles.compatibilityCard}>
                <View style={styles.compatibilityHeader}>
                  <Text style={styles.materialType}>{rule.material_type}</Text>
                  <Text style={styles.wagonType}>{rule.wagon_type}</Text>
                </View>
                <View style={styles.compatibilityMetrics}>
                  <View style={styles.metric}>
                    <Text style={styles.metricValue}>
                      {(rule.compatibility_score * 100).toFixed(0)}%
                    </Text>
                    <Text style={styles.metricLabel}>Compatibility</Text>
                  </View>
                  <View style={styles.metric}>
                    <Text style={styles.metricValue}>
                      {(rule.loading_efficiency * 100).toFixed(0)}%
                    </Text>
                    <Text style={styles.metricLabel}>Efficiency</Text>
                  </View>
                </View>
                {rule.restrictions.length > 0 && (
                  <View style={styles.restrictions}>
                    <Text style={styles.restrictionsTitle}>Restrictions:</Text>
                    {rule.restrictions.map((restriction, index) => (
                      <Text key={index} style={styles.restriction}>• {restriction}</Text>
                    ))}
                  </View>
                )}
              </View>
            ))}
          </View>
        )}

        {activeSection === 'analytics' && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Performance Analytics</Text>
            {analytics && (
              <>
                <View style={styles.kpiGrid}>
                  {Object.entries(analytics.kpis || {}).map(([key, value]) => (
                    <View key={key} style={styles.kpiCard}>
                      <Text style={styles.kpiValue}>
                        {typeof value === 'number' ? value.toFixed(1) : value}
                        {key.includes('rate') || key.includes('efficiency') ? '%' : ''}
                      </Text>
                      <Text style={styles.kpiLabel}>
                        {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </Text>
                    </View>
                  ))}
                </View>
                
                <View style={styles.trendsSection}>
                  <Text style={styles.cardTitle}>30-Day Trends</Text>
                  <Text style={styles.trendInfo}>
                    Average Daily Dispatches: {
                      analytics.trends?.daily_dispatches ? 
                      (analytics.trends.daily_dispatches.reduce((a: number, b: number) => a + b, 0) / 
                       analytics.trends.daily_dispatches.length).toFixed(1) : 'N/A'
                    }
                  </Text>
                  <Text style={styles.trendInfo}>
                    Average Utilization: {
                      analytics.trends?.utilization_trend ? 
                      ((analytics.trends.utilization_trend.reduce((a: number, b: number) => a + b, 0) / 
                        analytics.trends.utilization_trend.length) * 100).toFixed(1) : 'N/A'
                    }%
                  </Text>
                </View>
              </>
            )}
          </View>
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
  },
  loadingText: {
    color: '#ffffff',
    marginTop: 16,
    fontSize: 16,
    textAlign: 'center',
  },
  sectionNav: {
    flexDirection: 'row',
    backgroundColor: '#1a1a2e',
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  navButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    marginHorizontal: 2,
    borderRadius: 8,
    backgroundColor: '#2a2a3e',
  },
  activeNavButton: {
    backgroundColor: '#4a90e2',
  },
  navText: {
    fontSize: 11,
    color: '#666',
    marginLeft: 4,
    fontWeight: '500',
  },
  activeNavText: {
    color: '#ffffff',
  },
  scrollContent: {
    padding: 16,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 16,
  },
  emptyText: {
    color: '#888',
    textAlign: 'center',
    marginTop: 24,
    fontSize: 16,
  },
  // Approval Styles
  approvalCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  approvalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  approvalInfo: {
    flex: 1,
  },
  approvalType: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  approvalTime: {
    fontSize: 12,
    color: '#888',
    marginTop: 2,
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
  approvalComments: {
    fontSize: 14,
    color: '#a0a0a0',
    marginBottom: 12,
    lineHeight: 20,
  },
  approvalActions: {
    flexDirection: 'row',
    gap: 8,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    borderRadius: 8,
  },
  approveButton: {
    backgroundColor: '#51cf66',
  },
  rejectButton: {
    backgroundColor: '#ff6b6b',
  },
  actionText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: 'bold',
    marginLeft: 4,
  },
  // ERP Styles
  erpStatusCard: {
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
  erpSystems: {
    gap: 12,
  },
  erpSystem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  systemInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  systemName: {
    fontSize: 16,
    color: '#ffffff',
    fontWeight: '600',
    marginRight: 12,
  },
  systemStatus: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  systemStatusText: {
    fontSize: 10,
    color: '#ffffff',
    fontWeight: 'bold',
  },
  syncButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#4a90e2',
  },
  syncText: {
    fontSize: 12,
    color: '#4a90e2',
    fontWeight: '500',
    marginLeft: 4,
  },
  syncCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  syncHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  syncSystem: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  syncTime: {
    fontSize: 12,
    color: '#888',
  },
  syncDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  syncStatus: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  syncRecords: {
    fontSize: 14,
    color: '#a0a0a0',
  },
  errorMessage: {
    fontSize: 12,
    color: '#ff6b6b',
    marginTop: 8,
    lineHeight: 16,
  },
  // Compatibility Styles
  compatibilityCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  compatibilityHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  materialType: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  wagonType: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#4a90e2',
  },
  compatibilityMetrics: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  metric: {
    flex: 1,
    alignItems: 'center',
  },
  metricValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#51cf66',
  },
  metricLabel: {
    fontSize: 12,
    color: '#a0a0a0',
    marginTop: 4,
  },
  restrictions: {
    marginTop: 8,
  },
  restrictionsTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#ffd93d',
    marginBottom: 4,
  },
  restriction: {
    fontSize: 12,
    color: '#ff6b6b',
    lineHeight: 16,
  },
  // Analytics Styles
  kpiGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -6,
    marginBottom: 16,
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
  trendsSection: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  trendInfo: {
    fontSize: 14,
    color: '#ffffff',
    marginBottom: 8,
    lineHeight: 20,
  },
});