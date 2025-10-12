import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import * as SecureStore from 'expo-secure-store';
import axios from 'axios';
import Constants from 'expo-constants';

const BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface User {
  employee_id: string;
  name: string;
  role: 'admin' | 'plant_manager' | 'supervisor';
  plant_id?: string;
  assigned_areas?: string[];
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (employeeId: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadStoredAuth();
  }, []);

  // Configure axios interceptor for auth token
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  const loadStoredAuth = async () => {
    try {
      const storedToken = await SecureStore.getItemAsync('auth_token');
      const storedUser = await SecureStore.getItemAsync('user_data');

      if (storedToken && storedUser) {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
        
        // Verify token is still valid
        try {
          const response = await axios.get(`${BACKEND_URL}/api/auth/me`, {
            headers: { Authorization: `Bearer ${storedToken}` }
          });
          setUser(response.data);
        } catch (error) {
          // Token invalid, clear storage
          await clearAuth();
        }
      }
    } catch (error) {
      console.error('Error loading stored auth:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (employeeId: string, password: string) => {
    try {
      console.log('AuthContext: Starting login for', employeeId);
      console.log('AuthContext: Backend URL:', BACKEND_URL);
      
      const response = await axios.post(`${BACKEND_URL}/api/auth/login`, {
        employee_id: employeeId,
        password: password,
      });

      console.log('AuthContext: Login response received');
      const { access_token, user: userData } = response.data;

      // Store credentials securely
      console.log('AuthContext: Storing credentials...');
      await SecureStore.setItemAsync('auth_token', access_token);
      await SecureStore.setItemAsync('user_data', JSON.stringify(userData));

      console.log('AuthContext: Setting state...');
      setToken(access_token);
      setUser(userData);
      console.log('AuthContext: Login complete!');
    } catch (error: any) {
      console.error('AuthContext: Login error:', error);
      console.error('AuthContext: Error response:', error.response?.data);
      throw new Error(
        error.response?.data?.detail || 'Login failed. Please check your credentials.'
      );
    }
  };

  const clearAuth = async () => {
    await SecureStore.deleteItemAsync('auth_token');
    await SecureStore.deleteItemAsync('user_data');
    setToken(null);
    setUser(null);
  };

  const logout = async () => {
    await clearAuth();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        logout,
        isAuthenticated: !!user && !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
