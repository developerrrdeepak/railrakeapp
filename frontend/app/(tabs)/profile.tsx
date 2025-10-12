import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { Ionicons } from '@expo/vector-icons';

export default function ProfileScreen() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const { theme, themeMode, setThemeMode } = useTheme();

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            await logout();
            router.replace('/login');
          },
        },
      ]
    );
  };

  const getThemeIcon = () => {
    if (themeMode === 'auto') return 'phone-portrait-outline';
    if (themeMode === 'light') return 'sunny-outline';
    return 'moon-outline';
  };

  const getRoleDisplayName = (role: string) => {
    const roleNames: Record<string, string> = {
      admin: 'Administrator',
      plant_manager: 'Plant Manager',
      supervisor: 'Supervisor',
    };
    return roleNames[role] || role;
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <ScrollView style={styles.scrollView}>
        {/* Profile Header */}
        <View style={[styles.header, { backgroundColor: theme.surface }]}>
          <View style={[styles.avatarContainer, { backgroundColor: theme.primary }]}>
            <Ionicons name="person" size={48} color="#ffffff" />
          </View>
          <Text style={[styles.name, { color: theme.text }]}>{user?.name}</Text>
          <Text style={[styles.employeeId, { color: theme.textSecondary }]}>
            {user?.employee_id}
          </Text>
          <View style={[styles.roleBadge, { backgroundColor: theme.primary + '20' }]}>
            <Text style={[styles.roleText, { color: theme.primary }]}>
              {getRoleDisplayName(user?.role || '')}
            </Text>
          </View>
        </View>

        {/* Settings */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
            APPEARANCE
          </Text>

          {/* Theme Selector */}
          <View style={[styles.card, { backgroundColor: theme.surface }]}>
            <View style={styles.settingRow}>
              <Ionicons name={getThemeIcon()} size={24} color={theme.text} />
              <Text style={[styles.settingLabel, { color: theme.text }]}>Theme</Text>
            </View>
            <View style={styles.themeButtons}>
              {['light', 'dark', 'auto'].map((mode) => (
                <TouchableOpacity
                  key={mode}
                  style={[
                    styles.themeButton,
                    { borderColor: theme.border },
                    themeMode === mode && {
                      backgroundColor: theme.primary,
                      borderColor: theme.primary,
                    },
                  ]}
                  onPress={() => setThemeMode(mode as any)}
                >
                  <Text
                    style={[
                      styles.themeButtonText,
                      { color: theme.text },
                      themeMode === mode && { color: '#ffffff' },
                    ]}
                  >
                    {mode.charAt(0).toUpperCase() + mode.slice(1)}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        </View>

        {/* Account Info */}
        {user?.plant_id && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
              ACCOUNT INFO
            </Text>
            <View style={[styles.card, { backgroundColor: theme.surface }]}>
              <View style={styles.infoRow}>
                <Ionicons name="business-outline" size={20} color={theme.textSecondary} />
                <Text style={[styles.infoLabel, { color: theme.textSecondary }]}>
                  Plant ID:
                </Text>
                <Text style={[styles.infoValue, { color: theme.text }]}>
                  {user.plant_id}
                </Text>
              </View>
            </View>
          </View>
        )}

        {/* Actions */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
            ACTIONS
          </Text>

          <TouchableOpacity
            style={[styles.card, { backgroundColor: theme.surface }]}
            onPress={() => Alert.alert('Info', 'Password change functionality coming soon')}
          >
            <View style={styles.actionRow}>
              <Ionicons name="key-outline" size={24} color={theme.text} />
              <Text style={[styles.actionLabel, { color: theme.text }]}>Change Password</Text>
              <Ionicons name="chevron-forward" size={20} color={theme.textSecondary} />
            </View>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.card, { backgroundColor: theme.surface, marginTop: 12 }]}
            onPress={handleLogout}
          >
            <View style={styles.actionRow}>
              <Ionicons name="log-out-outline" size={24} color={theme.error} />
              <Text style={[styles.actionLabel, { color: theme.error }]}>Logout</Text>
              <Ionicons name="chevron-forward" size={20} color={theme.error} />
            </View>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  header: {
    alignItems: 'center',
    padding: 24,
    marginBottom: 8,
  },
  avatarContainer: {
    width: 96,
    height: 96,
    borderRadius: 48,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  name: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  employeeId: {
    fontSize: 14,
    marginBottom: 12,
  },
  roleBadge: {
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 16,
  },
  roleText: {
    fontSize: 12,
    fontWeight: '600',
  },
  section: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '700',
    marginBottom: 12,
    letterSpacing: 0.5,
  },
  card: {
    borderRadius: 12,
    padding: 16,
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  settingLabel: {
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 12,
  },
  themeButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  themeButton: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
  },
  themeButtonText: {
    fontSize: 14,
    fontWeight: '600',
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  infoLabel: {
    fontSize: 14,
    marginLeft: 8,
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 8,
  },
  actionRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  actionLabel: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 12,
  },
});