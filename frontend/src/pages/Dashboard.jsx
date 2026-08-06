import { useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { useNavigate } from 'react-router-dom';
import { getFarmerBookings, getOwnerBookings, updateBookingStatus } from '../services/bookingApi';
import { auth } from '../services/firebase';

import EquipmentForm from '../components/marketplace/EquipmentForm';
import WorkerForm from '../components/marketplace/WorkerForm';

export default function Dashboard() {
  const { user, profile, loading } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [farmerBookings, setFarmerBookings] = useState([]);
  const [ownerBookings, setOwnerBookings] = useState([]);
  const [showEquipmentForm, setShowEquipmentForm] = useState(false);
  const [showWorkerForm, setShowWorkerForm] = useState(false);

  useEffect(() => {
    if (!loading && !user) {
      navigate('/login');
    } else if (user && profile) {
      fetchData();
    }
  }, [user, profile, loading, navigate]);

  const fetchData = async () => {
    try {
      const oRes = await getOwnerBookings(user.uid);
      setOwnerBookings(oRes);
      
      const fRes = await getFarmerBookings(user.uid);
      setFarmerBookings(fRes);
    } catch (e) {
      console.error(e);
    }
  };

  const handleStatusChange = async (id, status) => {
    try {
      await updateBookingStatus(id, status);
      fetchData(); // refresh
    } catch (e) {
      alert("Failed to update status");
    }
  };

  if (loading || !profile) return <div className="text-center py-10">Loading...</div>;

  return (
    <div className="max-w-5xl mx-auto py-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 bg-card p-6 rounded-xl border border-border shadow-sm gap-4">
        <div>
          <h1 className="text-3xl font-bold text-primary mb-1">Welcome, {profile.displayName}</h1>
          <p className="text-text-secondary">Manage your farm rentals and workforce.</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <button 
            onClick={() => setShowEquipmentForm(true)}
            className="px-4 py-2 bg-primary text-white rounded-md font-medium hover:bg-green-800 transition-colors shadow-sm"
          >
            + Post Equipment
          </button>
          <button 
            onClick={() => setShowWorkerForm(true)}
            className="px-4 py-2 bg-primary text-white rounded-md font-medium hover:bg-green-800 transition-colors shadow-sm"
          >
            + Post Worker
          </button>
          <button 
            onClick={() => { auth.signOut(); navigate('/'); }}
            className="px-4 py-2 bg-red-50 text-red-600 rounded-md font-medium hover:bg-red-100 transition-colors"
          >
            {t('logout')}
          </button>
        </div>
      </div>
      
      {showEquipmentForm && (
        <EquipmentForm onClose={() => setShowEquipmentForm(false)} onAdded={() => alert('Check Equipment Marketplace!')} />
      )}
      {showWorkerForm && (
        <WorkerForm onClose={() => setShowWorkerForm(false)} onAdded={() => alert('Check Farm Workforce!')} />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div>
          <h2 className="text-xl font-bold text-text-primary mb-4 border-b border-border pb-2">
            My Booking Requests (Incoming)
          </h2>
          
          {ownerBookings.length === 0 ? (
            <div className="bg-card p-6 text-center rounded-xl border border-border text-text-secondary text-sm">
              No incoming requests.
            </div>
          ) : (
            <div className="space-y-4">
              {ownerBookings.map(b => (
                <div key={b.id} className="bg-card p-4 rounded-xl border border-border shadow-sm">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-bold text-primary">{b.targetName}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                      b.status === 'Pending' ? 'bg-yellow-100 text-yellow-800' :
                      b.status === 'Approved' ? 'bg-green-100 text-green-800' :
                      b.status === 'Rejected' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {b.status}
                    </span>
                  </div>
                  
                  <div className="text-xs text-text-secondary space-y-1 mb-3">
                    <p>Type: {b.type}</p>
                    <p>Date: {b.date}</p>
                    <p>Time Slot: {b.timeSlot}</p>
                    <p>Duration: {b.duration}</p>
                  </div>

                  {b.status === 'Pending' && (
                    <div className="flex space-x-2 border-t border-border pt-3">
                      <button onClick={() => handleStatusChange(b.id, 'Approved')} className="flex-1 bg-primary text-white py-1.5 rounded-md font-medium text-xs hover:bg-green-800">
                        Approve
                      </button>
                      <button onClick={() => handleStatusChange(b.id, 'Rejected')} className="flex-1 bg-red-50 text-red-600 py-1.5 rounded-md font-medium text-xs hover:bg-red-100">
                        Reject
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <h2 className="text-xl font-bold text-text-primary mb-4 border-b border-border pb-2">
            My Rentals (Outgoing)
          </h2>
          
          {farmerBookings.length === 0 ? (
            <div className="bg-card p-6 text-center rounded-xl border border-border text-text-secondary text-sm">
              No outgoing rentals.
            </div>
          ) : (
            <div className="space-y-4">
              {farmerBookings.map(b => (
                <div key={b.id} className="bg-card p-4 rounded-xl border border-border shadow-sm">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-bold text-primary">{b.targetName}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                      b.status === 'Pending' ? 'bg-yellow-100 text-yellow-800' :
                      b.status === 'Approved' ? 'bg-green-100 text-green-800' :
                      b.status === 'Rejected' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {b.status}
                    </span>
                  </div>
                  
                  <div className="text-xs text-text-secondary space-y-1">
                    <p>Type: {b.type}</p>
                    <p>Date: {b.date}</p>
                    <p>Time Slot: {b.timeSlot}</p>
                    <p>Duration: {b.duration}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
