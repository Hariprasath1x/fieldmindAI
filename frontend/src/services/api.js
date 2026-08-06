import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds timeout
});

export const verifyLeaf = async (imageFile) => {
  const formData = new FormData();
  formData.append('file', imageFile);
  // Example endpoint, update to match FastAPI
  const response = await apiClient.post('/verify-leaf', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const detectDisease = async (imageFile) => {
  const formData = new FormData();
  formData.append('file', imageFile);
  // Example endpoint
  const response = await apiClient.post('/detect-disease', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const recommendCrop = async (data) => {
  const response = await apiClient.post('/recommend-crop', data);
  return response.data;
};

export const getSystemStatus = async () => {
  try {
    const response = await apiClient.get('/status');
    return response.data;
  } catch (error) {
    throw new Error('Backend is unavailable');
  }
};

export default apiClient;
