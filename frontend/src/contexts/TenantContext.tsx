import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Tenant } from '../types';
import { useAuth } from './AuthContext';

interface TenantContextType {
  tenant: Tenant | null;
  setTenant: (tenant: Tenant | null) => void;
  loading: boolean;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

interface TenantProviderProps {
  children: ReactNode;
}

export const TenantProvider: React.FC<TenantProviderProps> = ({ children }) => {
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    const fetchTenant = async () => {
      if (user && user.tenant_id) {
        try {
          // Fetch actual tenant data from the backend
          const response = await fetch('/api/tenant/', {
            credentials: 'include'
          });
          
          if (response.ok) {
            const data = await response.json();
            setTenant(data.tenant);
          } else {
            // Fallback to basic tenant if fetch fails
            setTenant({
              id: user.tenant_id,
              name: 'Default Tenant',
              slug: 'default',
              is_active: true,
              position_mode: 'three_position',
              team_name_1: 'Team 1',
              team_name_2: 'Team 2',
              team_color_1: 'blue',
              team_color_2: 'red',
              assignment_mode: 'manual',
              default_goaltenders: 2,
              default_defence: 4,
              default_forwards: 6,
              default_skaters: 10,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            });
          }
        } catch (error) {
          console.error('Failed to fetch tenant:', error);
        }
      } else {
        setTenant(null);
      }
      setLoading(false);
    };
  
    fetchTenant();
  }, [user]);

  const value: TenantContextType = {
    tenant,
    setTenant,
    loading,
  };

  return (
    <TenantContext.Provider value={value}>
      {children}
    </TenantContext.Provider>
  );
};

export const useTenant = (): TenantContextType => {
  const context = useContext(TenantContext);
  if (context === undefined) {
    throw new Error('useTenant must be used within a TenantProvider');
  }
  return context;
};
