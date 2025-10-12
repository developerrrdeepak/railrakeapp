import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useColorScheme } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

type ThemeMode = 'light' | 'dark' | 'auto';
type ActiveTheme = 'light' | 'dark';

interface Theme {
  background: string;
  surface: string;
  card: string;
  text: string;
  textSecondary: string;
  primary: string;
  primaryDark: string;
  success: string;
  warning: string;
  error: string;
  border: string;
  shadow: string;
  tabBarBackground: string;
  tabBarActive: string;
  tabBarInactive: string;
}

interface ThemeContextType {
  theme: Theme;
  themeMode: ThemeMode;
  activeTheme: ActiveTheme;
  setThemeMode: (mode: ThemeMode) => void;
}

const lightTheme: Theme = {
  background: '#f5f7fa',
  surface: '#ffffff',
  card: '#ffffff',
  text: '#1a1a2e',
  textSecondary: '#6b7280',
  primary: '#3b82f6',
  primaryDark: '#2563eb',
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  border: '#e5e7eb',
  shadow: '#00000015',
  tabBarBackground: '#ffffff',
  tabBarActive: '#3b82f6',
  tabBarInactive: '#9ca3af',
};

const darkTheme: Theme = {
  background: '#0f0f23',
  surface: '#1a1a2e',
  card: '#16213e',
  text: '#ffffff',
  textSecondary: '#a0a0a0',
  primary: '#4a90e2',
  primaryDark: '#357abd',
  success: '#10b981',
  warning: '#fbbf24',
  error: '#f87171',
  border: '#2d3748',
  shadow: '#00000050',
  tabBarBackground: '#1a1a2e',
  tabBarActive: '#4a90e2',
  tabBarInactive: '#6b7280',
};

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider = ({ children }: { children: ReactNode }) => {
  const systemColorScheme = useColorScheme();
  const [themeMode, setThemeModeState] = useState<ThemeMode>('auto');
  const [activeTheme, setActiveTheme] = useState<ActiveTheme>('dark');

  useEffect(() => {
    loadThemePreference();
  }, []);

  useEffect(() => {
    const newActiveTheme = 
      themeMode === 'auto' 
        ? (systemColorScheme === 'dark' ? 'dark' : 'light')
        : themeMode;
    setActiveTheme(newActiveTheme);
  }, [themeMode, systemColorScheme]);

  const loadThemePreference = async () => {
    try {
      const savedTheme = await AsyncStorage.getItem('themeMode');
      if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark' || savedTheme === 'auto')) {
        setThemeModeState(savedTheme as ThemeMode);
      }
    } catch (error) {
      console.error('Error loading theme preference:', error);
    }
  };

  const setThemeMode = async (mode: ThemeMode) => {
    try {
      await AsyncStorage.setItem('themeMode', mode);
      setThemeModeState(mode);
    } catch (error) {
      console.error('Error saving theme preference:', error);
    }
  };

  const theme = activeTheme === 'dark' ? darkTheme : lightTheme;

  return (
    <ThemeContext.Provider value={{ theme, themeMode, activeTheme, setThemeMode }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
