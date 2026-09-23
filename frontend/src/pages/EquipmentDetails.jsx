import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getEquipmentById } from '../services/equipmentApi';
import { createBooking } from '../services/bookingApi';
import { useAuth } from '../hooks/useAuth';
import { MapPin, Phone, User, Calendar, Clock, ArrowLeft } from 'lucide-react';

export default function EquipmentDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [equipment, setEquipment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [date, setDate] = useState('');
  const [timeSlot, setTimeSlot] = useState('Full Day');
  const [duration, setDuration] = useState(1);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingError, setBookingError] = useState('');
  const [bookingSuccess, setBookingSuccess] = useState('');

  useEffect(() => {
    fetchEquipment();
  }, [id]);

  const fetchEquipment = async () => {
    try {
      const data = await getEquipmentById(id);
      setEquipment(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load equipment details');
    } finally {
      setLoading(false);
    }
  };

  const calculatePreviewPrice = () => {
    if (!equipment) return 0;
    const rate = timeSlot === 'Full Day' ? equipment.dailyPrice : equipment.hourlyPrice;
    return rate * duration;
  };

  const handleBooking = async (e) => {
    e.preventDefault();
    setBookingError('');
    setBookingSuccess('');
    
    if (!user) {
      navigate('/login', { state: { from: { pathname: `/equipment/${id}` } } });
      return;
    }

    setBookingLoading(true);
    try {
      await createBooking({
        type: 'Equipment',
        targetId: equipment.id,
        targetName: equipment.name,
        requesterId: user.uid,
        ownerId: equipment.ownerId,
        date,
        timeSlot,
        duration: parseInt(duration, 10)
      });
      setBookingSuccess('Booking request sent successfully!');
      setDate('');
      setDuration(1);
    } catch (err) {
      setBookingError(err.response?.data?.detail || 'Failed to send booking request.');
    } finally {
      setBookingLoading(false);
    }
  };

  if (loading) return <div className="text-center py-20 text-text-secondary">Loading equipment details...</div>;
  if (error) return <div className="text-center py-20 text-red-500 font-bold">{error}</div>;
  if (!equipment) return null;

  return (
    <div className="max-w-5xl mx-auto py-8">
      <button 
        onClick={() => navigate('/equipment')}
        className="flex items-center text-text-secondary hover:text-primary mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-1" /> Back to Equipment
      </button>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Left Column: Details */}
        <div className="space-y-6">
          <div className="bg-card border-2 border-border rounded-2xl overflow-hidden shadow-sm">
            <div className="h-72 bg-gray-200 w-full relative">
              {equipment.image ? (
                <img src={equipment.image} alt={equipment.name} className="w-full h-full object-cover" />
              ) : (
                <div className="flex items-center justify-center w-full h-full text-gray-400">No Image Available</div>
              )}
              <div className="absolute top-4 right-4 bg-white px-3 py-1 rounded-lg text-sm font-bold shadow-sm text-primary">
                {equipment.category}
              </div>
            </div>
            
            <div className="p-6">
              <h1 className="text-3xl font-bold text-text-primary mb-4">{equipment.name}</h1>
              
              <div className="flex flex-wrap gap-6 mb-6">
                <div>
                  <div className="text-2xl font-bold text-primary">₹{equipment.hourlyPrice}</div>
                  <div className="text-sm text-text-secondary">per hour</div>
                </div>
                <div className="border-l border-border pl-6">
                  <div className="text-2xl font-bold text-primary">₹{equipment.dailyPrice}</div>
                  <div className="text-sm text-text-secondary">per day</div>
                </div>
              </div>
              
              {equipment.description && (
                <div className="mb-6">
                  <h3 className="font-bold text-text-primary mb-2">Description</h3>
                  <p className="text-text-secondary text-sm leading-relaxed">{equipment.description}</p>
                </div>
              )}

              <div className="space-y-3 pt-4 border-t border-border">
                <div className="flex items-center text-text-secondary">
                  <MapPin className="w-5 h-5 mr-3 text-primary" /> 
                  <span>{equipment.village}, {equipment.location}</span>
                </div>
                <div className="flex items-center text-text-secondary">
                  <User className="w-5 h-5 mr-3 text-primary" /> 
                  <span>Owned by <span className="font-semibold text-text-primary">{equipment.ownerName}</span></span>
                </div>
                <div className="flex items-center text-text-secondary">
                  <Phone className="w-5 h-5 mr-3 text-primary" /> 
                  <span>{equipment.ownerPhone}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Booking Form */}
        <div>
          <div className="bg-card border-2 border-border rounded-2xl p-6 shadow-sm sticky top-6">
            <h2 className="text-xl font-bold text-text-primary mb-6 flex items-center border-b border-border pb-4">
              <Calendar className="w-5 h-5 mr-2 text-primary" /> Check Availability & Book
            </h2>
            
            {bookingSuccess && (
              <div className="mb-6 p-4 bg-green-50 text-green-800 border border-green-200 rounded-xl text-sm font-medium">
                ✅ {bookingSuccess} <br/>
                <button onClick={() => navigate('/dashboard')} className="mt-2 underline font-bold">Go to My Bookings</button>
              </div>
            )}
            
            {bookingError && (
              <div className="mb-6 p-4 bg-red-50 text-red-800 border border-red-200 rounded-xl text-sm font-medium">
                ⚠️ {bookingError}
              </div>
            )}

            {user && user.uid === equipment.ownerId ? (
              <div className="bg-blue-50 border border-blue-200 text-blue-800 p-6 rounded-xl text-center shadow-inner">
                <div className="text-3xl mb-3">🛠️</div>
                <h3 className="text-lg font-bold mb-2">This is your listing</h3>
                <p className="text-sm">You cannot book your own equipment.</p>
              </div>
            ) : (
              <form onSubmit={handleBooking} className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Rental Date</label>
                  <input 
                    type="date" 
                    value={date} 
                    onChange={(e) => setDate(e.target.value)} 
                    required 
                    min={new Date().toISOString().split('T')[0]}
                    className="w-full border border-border bg-background-app p-3 rounded-xl focus:ring-2 focus:ring-primary focus:outline-none" 
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Time Slot</label>
                  <div className="relative">
                    <Clock className="absolute left-3 top-3.5 w-4 h-4 text-text-secondary" />
                    <select 
                      value={timeSlot} 
                      onChange={(e) => setTimeSlot(e.target.value)} 
                      className="w-full border border-border bg-background-app p-3 pl-9 rounded-xl focus:ring-2 focus:ring-primary focus:outline-none appearance-none"
                    >
                      <option value="Morning">Morning (8am - 12pm)</option>
                      <option value="Afternoon">Afternoon (1pm - 5pm)</option>
                      <option value="Evening">Evening (5pm - 8pm)</option>
                      <option value="Full Day">Full Day</option>
                    </select>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">
                    Duration ({timeSlot === 'Full Day' ? 'Days' : 'Hours'})
                  </label>
                  <input 
                    type="number" 
                    min="1"
                    value={duration} 
                    onChange={(e) => setDuration(e.target.value)} 
                    required 
                    className="w-full border border-border bg-background-app p-3 rounded-xl focus:ring-2 focus:ring-primary focus:outline-none" 
                  />
                </div>
                
                <div className="bg-gray-50 p-4 rounded-xl border border-border mt-6">
                  <div className="flex justify-between items-center text-sm mb-1 text-text-secondary">
                    <span>Rate</span>
                    <span>₹{timeSlot === 'Full Day' ? equipment.dailyPrice : equipment.hourlyPrice} / {timeSlot === 'Full Day' ? 'day' : 'hr'}</span>
                  </div>
                  <div className="flex justify-between items-center text-sm mb-3 text-text-secondary">
                    <span>Duration</span>
                    <span>x {duration} {timeSlot === 'Full Day' ? 'days' : 'hrs'}</span>
                  </div>
                  <div className="flex justify-between items-center pt-3 border-t border-gray-200">
                    <span className="font-bold text-text-primary">Estimated Total</span>
                    <span className="font-bold text-xl text-primary">₹{calculatePreviewPrice()}</span>
                  </div>
                  <p className="text-xs text-text-secondary mt-2 text-center">Final price will be confirmed by the owner.</p>
                </div>

                <button 
                  type="submit" 
                  disabled={bookingLoading}
                  className="w-full py-3.5 bg-primary text-white rounded-xl font-bold hover:bg-green-800 transition-colors shadow-sm disabled:opacity-60"
                >
                  {bookingLoading ? 'Sending Request...' : 'Request Booking'}
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
