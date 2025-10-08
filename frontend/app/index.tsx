import React, { useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import axios from 'axios';
import Constants from 'expo-constants';

const BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

export default function WelcomeScreen() {
  const router = useRouter();
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState('');

  useEffect(() => {
    checkBackend();
  }, []);

  const checkBackend = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api`);
      console.log('Backend connected:', response.data);
      setLoading(false);
    } catch (err) {
      console.error('Backend error:', err);
      setError('Unable to connect to backend');
      setLoading(false);
    }
  };

  const handleGetStarted = async () => {
    try {
      // Initialize sample data
      await axios.post(`${BACKEND_URL}/api/initialize-sample-data`);
      router.replace('/(tabs)');
    } catch (err: any) {
      console.error('Initialization error:', err);
      // Navigate anyway if data already exists
      if (err.response?.data?.message?.includes('already exists')) {
        router.replace('/(tabs)');
      }
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <ActivityIndicator size="large" color="#4a90e2" />
        <Text style={styles.loadingText}>Connecting...</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>AI-Powered Rake Formation System</Text>
        <Text style={styles.subtitle}>Optimize your logistics operations with intelligent rake planning</Text>
        
        <View style={styles.features}>
          <Text style={styles.feature}>• Dynamic rake formation</Text>
          <Text style={styles.feature}>• AI-powered optimization</Text>
          <Text style={styles.feature}>• Real-time cost analysis</Text>
          <Text style={styles.feature}>• Smart resource allocation</Text>
        </View>

        {error ? <Text style={styles.error}>{error}</Text> : null}

        <TouchableOpacity style={styles.button} onPress={handleGetStarted}>
          <Text style={styles.buttonText}>Get Started</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f0f23',
  },
  content: {
    flex: 1,
    padding: 24,
    justifyContent: 'center',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 16,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#a0a0a0',
    marginBottom: 48,
    textAlign: 'center',
    lineHeight: 24,
  },
  features: {
    marginBottom: 48,
  },
  feature: {
    fontSize: 16,
    color: '#4a90e2',
    marginBottom: 12,
    paddingLeft: 8,
  },
  button: {
    backgroundColor: '#4a90e2',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  loadingText: {
    color: '#ffffff',
    marginTop: 16,
    fontSize: 16,
  },
  error: {
    color: '#ff6b6b',
    marginBottom: 16,
    textAlign: 'center',
  },
});