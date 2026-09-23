import apiClient from './api';

export const getEquipment = async () => {
  const res = await apiClient.get('/api/marketplace/equipment');
  return res.data;
};

export const getEquipmentById = async (id) => {
  const res = await apiClient.get(`/api/marketplace/equipment/${id}`);
  return res.data;
};

export const createEquipment = async (data) => {
  const res = await apiClient.post('/api/marketplace/equipment', data);
  return res.data;
};

export const updateEquipment = async (id, data) => {
  const res = await apiClient.put(`/api/marketplace/equipment/${id}`, data);
  return res.data;
};

export const deleteEquipment = async (id) => {
  const res = await apiClient.delete(`/api/marketplace/equipment/${id}`);
  return res.data;
};

export const getOwnerEquipment = async (uid) => {
  const res = await apiClient.get(`/api/marketplace/equipment/owner/${uid}`);
  return res.data;
};


