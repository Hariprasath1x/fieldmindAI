import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import apiClient from '../services/api';

export default function MobileNumber() {
  const { user, profile } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // The intended destination if redirected from a protected route
  const from = location.state?.from?.pathname || '/';

  // If we already have a phone number on the profile, just go to the destination
  if (profile && profile.phone) {
    navigate(from, { replace: true });
    return null;
  }

  const handleSavePhone = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await apiClient.post('/api/marketplace/users/sync', {
        uid: user.uid,
        phone: phone
      });
      // Once saved, force a refresh or navigate so the app updates its state
      window.location.href = from;
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save mobile number. Please try again.');
    }
    setLoading(false);
  };

  return (
    <div className="flex items-center justify-center min-h-[75vh] py-8">
      <div className="bg-card p-8 rounded-2xl shadow-lg border border-border w-full max-w-md">
        <div className="text-center mb-7">
          <div className="text-4xl mb-2">📱</div>
          <h1 className="text-2xl font-bold text-primary">Enter your mobile number</h1>
          <p className="text-text-secondary text-sm mt-1">
            We use your mobile number for rental, booking, and contact purposes.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm mb-4 font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleSavePhone} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Mobile Number</label>
            <input
              type="tel"
              placeholder="+919876543210"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="w-full px-4 py-2.5 border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary bg-background-app"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading || !user}
            className="w-full bg-primary text-white py-2.5 rounded-xl font-semibold hover:bg-green-800 transition-all disabled:opacity-60"
          >
            {loading ? 'Saving…' : 'Save & Continue'}
          </button>
        </form>
      </div>
    </div>
  );
}
