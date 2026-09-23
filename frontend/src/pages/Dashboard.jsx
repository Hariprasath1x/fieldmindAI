import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useLanguage } from '../hooks/useLanguage';
import { useNavigate } from 'react-router-dom';
import { getFarmerBookings, getOwnerBookings, updateBookingStatus } from '../services/bookingApi';
import { getOwnerEquipment, deleteEquipment } from '../services/equipmentApi';
import { getManagerWorkers, deleteWorker } from '../services/workerApi';
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
  const [editingEquipment, setEditingEquipment] = useState(null);
  const [editingWorker, setEditingWorker] = useState(null);
  const [myEquipment, setMyEquipment] = useState([]);
  const [myWorkers, setMyWorkers] = useState([]);

  const [actionLoading, setActionLoading] = useState({});

  const setAction = (id, loading) => {
    setActionLoading(prev => ({ ...prev, [id]: loading }));
  };

  const fetchData = useCallback(async () => {
    try {
      const oRes = await getOwnerBookings(user.uid);
      setOwnerBookings(oRes);
      
      const fRes = await getFarmerBookings(user.uid);
      setFarmerBookings(fRes);
      
      const eRes = await getOwnerEquipment(user.uid);
      setMyEquipment(eRes);
      
      const wRes = await getManagerWorkers(user.uid);
      setMyWorkers(wRes);
    } catch (e) {
      console.error(e);
    }
  }, [user]);

  useEffect(() => {
    if (!loading && !user) {
      navigate('/login');
    } else if (user && profile) {
      fetchData();
    }
  }, [user, profile, loading, navigate, fetchData]);

  const handleStatusChange = async (id, status) => {
    if (actionLoading[id]) return;
    setAction(id, true);
    try {
      await updateBookingStatus(id, status);
      await fetchData(); // refresh
    } catch (e) {
      console.error(e);
      // Suppress alert for graceful 400 backend rejections (already handled)
      if (e.response?.status !== 400 && e.response?.status !== 409) {
        alert(e.response?.data?.detail || "Failed to update status");
      }
    } finally {
      setAction(id, false);
    }
  };

  const handleDeleteEquipment = async (id) => {
    if (actionLoading[id]) return;
    if (!window.confirm('Are you sure you want to delete this equipment?')) return;
    setAction(id, true);
    try {
      await deleteEquipment(id);
      await fetchData();
    } catch (e) {
      alert(e.response?.data?.detail || "Failed to delete equipment.");
    } finally {
      setAction(id, false);
    }
  };

  const handleDeleteWorker = async (id) => {
    if (actionLoading[id]) return;
    if (!window.confirm('Are you sure you want to delete this worker?')) return;
    setAction(id, true);
    try {
      await deleteWorker(id);
      await fetchData();
    } catch (e) {
      alert(e.response?.data?.detail || "Failed to delete worker.");
    } finally {
      setAction(id, false);
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
        <EquipmentForm 
          initialData={editingEquipment}
          onClose={() => { setShowEquipmentForm(false); setEditingEquipment(null); }} 
          onAdded={() => { fetchData(); alert(editingEquipment ? 'Equipment updated!' : 'Check Equipment Marketplace!'); }} 
        />
      )}
      {showWorkerForm && (
        <WorkerForm 
          initialData={editingWorker}
          onClose={() => { setShowWorkerForm(false); setEditingWorker(null); }} 
          onAdded={() => { fetchData(); alert(editingWorker ? 'Worker updated!' : 'Check Farm Workforce!'); }} 
        />
      )}

      {/* MY LISTINGS SECTION */}
      <div className="mb-12">
        <h2 className="text-xl font-bold text-text-primary mb-4 border-b border-border pb-2">
          My Listings
        </h2>
        {myEquipment.length === 0 && myWorkers.length === 0 ? (
          <div className="bg-card p-6 text-center rounded-xl border border-border text-text-secondary text-sm">
            You haven't posted any equipment or workers yet.
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Equipment Listings */}
            {myEquipment.length > 0 && (
              <div>
                <h3 className="font-bold text-primary mb-3">Equipment</h3>
                <div className="space-y-4">
                  {myEquipment.map(item => (
                    <div key={item.id} className="bg-card p-4 rounded-xl border border-border shadow-sm">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-bold text-text-primary">{item.name}</h4>
                        <span className="px-2 py-1 rounded-full text-xs font-bold bg-gray-100 text-gray-800">₹{item.dailyPrice}/day</span>
                      </div>
                      <div className="flex space-x-2 border-t border-border pt-3 mt-2">
                        <button onClick={() => { setEditingEquipment(item); setShowEquipmentForm(true); }} className="flex-1 bg-gray-50 text-gray-700 py-1.5 rounded-md font-medium text-xs hover:bg-gray-200 border border-border">Edit</button>
                        <button onClick={() => handleDeleteEquipment(item.id)} disabled={actionLoading[item.id]} className="flex-1 bg-red-50 text-red-600 py-1.5 rounded-md font-medium text-xs hover:bg-red-100 border border-red-100 disabled:opacity-50">
                          {actionLoading[item.id] ? 'Deleting...' : 'Delete'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Worker Listings */}
            {myWorkers.length > 0 && (
              <div>
                <h3 className="font-bold text-primary mb-3">Workforce</h3>
                <div className="space-y-4">
                  {myWorkers.map(worker => (
                    <div key={worker.id} className="bg-card p-4 rounded-xl border border-border shadow-sm">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-bold text-text-primary">{worker.name}</h4>
                        <span className="px-2 py-1 rounded-full text-xs font-bold bg-gray-100 text-gray-800">₹{worker.dailyWage}/day</span>
                      </div>
                      <div className="flex space-x-2 border-t border-border pt-3 mt-2">
                        <button onClick={() => { setEditingWorker(worker); setShowWorkerForm(true); }} className="flex-1 bg-gray-50 text-gray-700 py-1.5 rounded-md font-medium text-xs hover:bg-gray-200 border border-border">Edit</button>
                        <button onClick={() => handleDeleteWorker(worker.id)} disabled={actionLoading[worker.id]} className="flex-1 bg-red-50 text-red-600 py-1.5 rounded-md font-medium text-xs hover:bg-red-100 border border-red-100 disabled:opacity-50">
                          {actionLoading[worker.id] ? 'Deleting...' : 'Delete'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

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
                      b.status === 'Cancelled' ? 'bg-gray-200 text-gray-700 line-through' :
                      b.status === 'Completed' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {b.status}
                    </span>
                  </div>
                  
                  <div className="text-xs text-text-secondary space-y-1 mb-3">
                    <p>Type: {b.type}</p>
                    <p>Date: {b.date}</p>
                    <p>Time Slot: {b.timeSlot}</p>
                    <p>Duration: {b.duration} {b.timeSlot === 'Full Day' ? 'Days' : 'Hours'}</p>
                    {b.totalPrice && <p className="font-bold text-primary mt-1">Total: ₹{b.totalPrice}</p>}
                  </div>

                  {b.status === 'Pending' && (
                    <div className="flex space-x-2 border-t border-border pt-3 mt-3">
                      <button onClick={() => handleStatusChange(b.id, 'Approved')} disabled={actionLoading[b.id]} className="flex-1 bg-primary text-white py-1.5 rounded-md font-medium text-xs hover:bg-green-800 disabled:opacity-50">
                        {actionLoading[b.id] ? '...' : 'Approve'}
                      </button>
                      <button onClick={() => handleStatusChange(b.id, 'Rejected')} disabled={actionLoading[b.id]} className="flex-1 bg-red-50 text-red-600 py-1.5 rounded-md font-medium text-xs hover:bg-red-100 disabled:opacity-50">
                        {actionLoading[b.id] ? '...' : 'Reject'}
                      </button>
                    </div>
                  )}
                  {b.status === 'Approved' && (
                    <div className="flex space-x-2 border-t border-border pt-3 mt-3">
                      <button onClick={() => handleStatusChange(b.id, 'Completed')} disabled={actionLoading[b.id]} className="flex-1 bg-blue-600 text-white py-1.5 rounded-md font-medium text-xs hover:bg-blue-700 disabled:opacity-50">
                        {actionLoading[b.id] ? 'Processing...' : 'Mark as Completed'}
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
                      b.status === 'Cancelled' ? 'bg-gray-200 text-gray-700 line-through' :
                      b.status === 'Completed' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {b.status}
                    </span>
                  </div>
                  
                  <div className="text-xs text-text-secondary space-y-1">
                    <p>Type: {b.type}</p>
                    <p>Date: {b.date}</p>
                    <p>Time Slot: {b.timeSlot}</p>
                    <p>Duration: {b.duration} {b.timeSlot === 'Full Day' ? 'Days' : 'Hours'}</p>
                    {b.totalPrice && <p className="font-bold text-primary mt-1">Total: ₹{b.totalPrice}</p>}
                  </div>

                  {(b.status === 'Pending' || b.status === 'Approved') && (
                    <div className="flex space-x-2 border-t border-border pt-3 mt-3">
                      <button 
                        disabled={actionLoading[b.id]}
                        onClick={() => {
                          if(window.confirm('Are you sure you want to cancel this booking?')) {
                            handleStatusChange(b.id, 'Cancelled');
                          }
                        }} 
                        className="flex-1 bg-red-50 text-red-600 py-1.5 rounded-md font-medium text-xs hover:bg-red-100 disabled:opacity-50"
                      >
                        {actionLoading[b.id] ? 'Cancelling...' : 'Cancel Booking'}
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
