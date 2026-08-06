import apiClient from './api';

export const getFarmerBookings = async (uid) => {
  const res = await apiClient.get(`/api/marketplace/bookings/farmer/${uid}`);
  return res.data;
};

export const getOwnerBookings = async (uid) => {
  const res = await apiClient.get(`/api/marketplace/bookings/owner/${uid}`);
  return res.data;
};

export const createBooking = async (data) => {
  const res = await apiClient.post('/api/marketplace/bookings', data);
  return res.data;
};

export const updateBookingStatus = async (id, status) => {
  const res = await apiClient.put(`/api/marketplace/bookings/${id}/status?status=${status}`);
  return res.data;
};
