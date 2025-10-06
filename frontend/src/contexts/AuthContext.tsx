import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, Tenant, AuthContextType } from '../types';
import { apiClient } from '../utils/api';
import { API_ENDPOINTS } from '../utils/constants';

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await apiClient.get(API_ENDPOINTS.AUTH.ME);
      if (response.data.user) {
        setUser(response.data.user);
        // Set tenant from response
        if (response.data.tenant) {
          setTenant(response.data.tenant);
        }
      }
    } catch (error) {
      // User not authenticated
      setUser(null);
      setTenant(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const response = await apiClient.post(API_ENDPOINTS.AUTH.LOGIN, { email, password });
      if (response.data.user) {
        setUser(response.data.user);
        // Set tenant from login response
        if (response.data.tenant) {
          setTenant(response.data.tenant);
        }
        return true;
      }
      return false;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };

  const logout = async () => {
    try {
      await apiClient.post(API_ENDPOINTS.AUTH.LOGOUT);
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setTenant(null);
    }
  };

  const value: AuthContextType = {
    user,
    tenant,
    login,
    logout,
    loading,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
