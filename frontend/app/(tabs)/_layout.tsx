import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: '#4a90e2',
        tabBarInactiveTintColor: '#666',
        tabBarStyle: {
          backgroundColor: '#1a1a2e',
          borderTopColor: '#2a2a3e',
          height: 60,
          paddingBottom: 8,
        },
        headerStyle: {
          backgroundColor: '#1a1a2e',
        },
        headerTintColor: '#fff',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      }}>
      <Tabs.Screen
        name="index"
        options={{
          title: 'Dashboard',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="orders"
        options={{
          title: 'Orders',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="list" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="inventory"
        options={{
          title: 'Inventory',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="cube" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="rakes"
        options={{
          title: 'Rakes',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="train" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="optimize"
        options={{
          title: 'AI Optimize',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="sparkles" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="control-room"
        options={{
          title: 'Control Room',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="desktop" size={size} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}