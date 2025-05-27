import axios from 'axios';
import config from '../config';
import { getIdToken } from './auth';

// Create axios instance with base URL
const api = axios.create({
  baseURL: config.apiUrl
});

// Add authorization header to all requests
api.interceptors.request.use(
  async (config) => {
    try {
      const token = await getIdToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    } catch (error) {
      console.error('Error getting token:', error);
      return config;
    }
  },
  (error) => {
    return Promise.reject(error);
  }
);

// API functions
export const getTelemetryData = async (deviceId, startTime, endTime) => {
  try {
    const params = { deviceId };
    
    if (startTime) {
      params.startTime = startTime;
    }
    
    if (endTime) {
      params.endTime = endTime;
    }
    
    const response = await api.get('/telemetry', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching telemetry data:', error);
    throw error;
  }
};

export const getAllDevices = async (companyId) => {
  try {
    const params = {};
    
    if (companyId) {
      params.companyId = companyId;
    }
    
    const response = await api.get('/devices', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching devices:', error);
    throw error;
  }
};

export const getUserCompanies = async () => {
  try {
    const response = await api.get('/user-company');
    return response.data;
  } catch (error) {
    console.error('Error fetching user companies:', error);
    throw error;
  }
};

export const sendTelemetryData = async (telemetryData) => {
  try {
    const response = await api.post('/telemetry', telemetryData);
    return response.data;
  } catch (error) {
    console.error('Error sending telemetry data:', error);
    throw error;
  }
};

export const registerCompany = async (companyData) => {
  try {
    const response = await api.post('/company', companyData);
    return response.data;
  } catch (error) {
    console.error('Error registering company:', error);
    throw error;
  }
};

export default api;
