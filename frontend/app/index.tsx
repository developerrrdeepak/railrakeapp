import React, { useEffect } from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import axios from 'axios';
import Constants from 'expo-constants';

const BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

export default function IndexScreen() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();
  const { theme } = useTheme();

  useEffect(() => {
    if (!isLoading) {
      initializeApp();
    }
  }, [isLoading, isAuthenticated]);

  const initializeApp = async () => {
    try {
      // Initialize sample data and users
      await Promise.allSettled([
        axios.post(`${BACKEND_URL}/api/initialize-sample-data`),
        axios.post(`${BACKEND_URL}/api/auth/initialize-users`),
      ]);
    } catch (err) {
      console.error('Initialization error:', err);
    }

    // Navigate based on auth status
    if (isAuthenticated) {
      router.replace('/(tabs)');
    } else {
      router.replace('/login');
    }
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <ActivityIndicator size="large" color={theme.primary} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});