import axios from 'axios';
import { ApiResponse } from '../types';

// Create axios instance with default configuration
export const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Include cookies for session management
});

// Fetch CSRF token on initialization
let csrfToken: string | null = null;

const fetchCsrfToken = async () => {
  try {
    const apiUrl = process.env.REACT_APP_API_URL || '/api';
    const response = await axios.get(`${apiUrl}/auth/csrf-token`, { withCredentials: true });
    csrfToken = response.data.csrfToken;
  } catch (error) {
    console.error('Failed to fetch CSRF token:', error);
  }
};

// Initialize CSRF token
fetchCsrfToken();

// Request interceptor to add CSRF token and tenant header
apiClient.interceptors.request.use(
  async (config) => {
    // Extract tenant subdomain from current hostname
    const hostname = window.location.hostname;
    const parts = hostname.split('.');
    if (parts.length > 2 && parts[0] !== 'www') {
      // Send subdomain as header for cross-domain API calls
      config.headers['X-Tenant-Subdomain'] = parts[0];
    }
    
    // Add CSRF token for unsafe methods
    if (config.method && ['post', 'put', 'delete', 'patch'].includes(config.method.toLowerCase())) {
      if (!csrfToken) {
        await fetchCsrfToken();
      }
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle common errors
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    // Retry CSRF token fetch on 400 CSRF errors
    if (error.response?.status === 400 && error.response?.data?.error?.includes('CSRF')) {
      await fetchCsrfToken();
      // Retry the request
      const config = error.config;
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
      }
      return apiClient.request(config);
    }
    
    if (error.response?.status === 401) {
      // Redirect to login on unauthorized
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Generic API functions
export const api = {
  get: <T>(url: string): Promise<ApiResponse<T>> =>
    apiClient.get(url).then(response => response.data),
  
  post: <T>(url: string, data?: any): Promise<ApiResponse<T>> =>
    apiClient.post(url, data).then(response => response.data),
  
  put: <T>(url: string, data?: any): Promise<ApiResponse<T>> =>
    apiClient.put(url, data).then(response => response.data),
  
  delete: <T>(url: string): Promise<ApiResponse<T>> =>
    apiClient.delete(url).then(response => response.data),
  
  upload: <T>(url: string, formData: FormData): Promise<ApiResponse<T>> =>
    apiClient.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }).then(response => response.data),
};