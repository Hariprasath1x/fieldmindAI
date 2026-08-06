import apiClient from './api';

export const getWorkers = async () => {
  const res = await apiClient.get('/api/marketplace/workers');
  return res.data;
};

export const createWorker = async (data) => {
  const res = await apiClient.post('/api/marketplace/workers', data);
  return res.data;
};

export const deleteWorker = async (id) => {
  const res = await apiClient.delete(`/api/marketplace/workers/${id}`);
  return res.data;
};
