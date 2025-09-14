import { useState, useEffect } from 'react';
import { api } from '../utils/api';
import { ApiResponse } from '../types';

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export const useApi = <T>(url: string, dependencies: any[] = []) => {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setState(prev => ({ ...prev, loading: true, error: null }));
        const response: ApiResponse<T> = await api.get(url);
        setState({
          data: response.data || null,
          loading: false,
          error: null,
        });
      } catch (error: any) {
        setState({
          data: null,
          loading: false,
          error: error.message || 'An error occurred',
        });
      }
    };

    fetchData();
  }, dependencies);

  return state;
};
