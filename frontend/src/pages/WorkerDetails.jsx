import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getWorkerById } from '../services/workerApi';
import { createBooking } from '../services/bookingApi';
import { useAuth } from '../hooks/useAuth';
import { MapPin, Phone, Briefcase, Calendar, Clock, ArrowLeft, User, CheckCircle2 } from 'lucide-react';

export default function WorkerDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [worker, setWorker] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [date, setDate] = useState('');
  const [timeSlot, setTimeSlot] = useState('Full Day');
  const [duration, setDuration] = useState(1);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingError, setBookingError] = useState('');
  const [bookingSuccess, setBookingSuccess] = useState('');

  useEffect(() => {
    fetchWorker();
  }, [id]);

  const fetchWorker = async () => {
    try {
      const data = await getWorkerById(id);
      setWorker(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load worker details');
    } finally {
      setLoading(false);
    }
  };

  const calculatePreviewPrice = () => {
    if (!worker) return 0;
    const rate = timeSlot === 'Full Day' ? worker.dailyWage : worker.hourlyWage;
    const finalRate = rate || worker.dailyWage; // Fallback if hourly is missing
    return finalRate * duration;
  };

  const handleBooking = async (e) => {
    e.preventDefault();
    setBookingError('');
    setBookingSuccess('');
    
    if (!user) {
      navigate('/login', { state: { from: { pathname: `/workforce/${id}` } } });
      return;
    }

    setBookingLoading(true);
    try {
      await createBooking({
        type: 'Worker',
        targetId: worker.id,
        targetName: worker.name,
        requesterId: user.uid,
        ownerId: worker.managerId,
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

  if (loading) return <div className="text-center py-20 text-text-secondary">Loading worker details...</div>;
  if (error) return <div className="text-center py-20 text-red-500 font-bold">{error}</div>;
  if (!worker) return null;

  return (
    <div className="max-w-5xl mx-auto py-8">
      <button 
        onClick={() => navigate('/workforce')}
        className="flex items-center text-text-secondary hover:text-primary mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-1" /> Back to Workforce
      </button>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Left Column: Details */}
        <div className="space-y-6">
          <div className="bg-card border-2 border-border rounded-2xl p-6 shadow-sm relative">
            <div className="absolute top-6 right-6 bg-green-100 text-green-800 px-3 py-1.5 rounded-full text-xs font-bold flex items-center">
              <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" /> {worker.status}
            </div>
            
            <div className="flex items-center mb-6">
              <div className="w-24 h-24 bg-gray-200 rounded-full flex items-center justify-center mr-6 overflow-hidden border-4 border-white shadow-sm">
                {worker.photo ? <img src={worker.photo} alt={worker.name} className="w-full h-full object-cover"/> : <User className="w-12 h-12 text-gray-400" />}
              </div>
              <div>
                <h1 className="text-3xl font-bold text-text-primary">{worker.name}</h1>
                <div className="text-primary font-medium mt-1">{worker.experience} Experience</div>
              </div>
            </div>
              
            <div className="flex flex-wrap gap-6 mb-6 pt-4 border-t border-border">
              <div>
                <div className="text-2xl font-bold text-primary">₹{worker.hourlyWage || '-'}</div>
                <div className="text-sm text-text-secondary">per hour</div>
              </div>
              <div className="border-l border-border pl-6">
                <div className="text-2xl font-bold text-primary">₹{worker.dailyWage}</div>
                <div className="text-sm text-text-secondary">per day</div>
              </div>
            </div>
            
            <div className="space-y-4 pt-4 border-t border-border">
              <div className="flex items-start">
                <Briefcase className="w-5 h-5 mr-3 text-primary shrink-0 mt-0.5" /> 
                <div>
                  <h3 className="font-bold text-text-primary text-sm mb-1">Skills</h3>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {worker.skills.map((skill, idx) => (
                      <span key={idx} className="bg-gray-100 text-gray-700 px-2.5 py-1 rounded-md text-xs font-medium border border-gray-200">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
              
              {worker.languages && worker.languages.length > 0 && (
                <div className="flex items-start">
                  <User className="w-5 h-5 mr-3 text-primary shrink-0 mt-0.5" /> 
                  <div>
                    <h3 className="font-bold text-text-primary text-sm mb-1">Languages</h3>
                    <p className="text-text-secondary text-sm">{worker.languages.join(', ')}</p>
                  </div>
                </div>
              )}

              <div className="flex items-start pt-2">
                <MapPin className="w-5 h-5 mr-3 text-primary shrink-0 mt-0.5" /> 
                <div>
                  <h3 className="font-bold text-text-primary text-sm mb-1">Location</h3>
                  <p className="text-text-secondary text-sm">{worker.village}</p>
                </div>
              </div>

              <div className="flex items-start pt-2">
                <Phone className="w-5 h-5 mr-3 text-primary shrink-0 mt-0.5" /> 
                <div>
                  <h3 className="font-bold text-text-primary text-sm mb-1">Contact</h3>
                  <p className="text-text-secondary text-sm">{worker.phone}</p>
                </div>
              </div>
            </div>

            {worker.description && (
              <div className="mt-6 pt-6 border-t border-border">
                <h3 className="font-bold text-text-primary mb-2">About</h3>
                <p className="text-text-secondary text-sm leading-relaxed">{worker.description}</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Booking Form */}
        <div>
          <div className="bg-card border-2 border-border rounded-2xl p-6 shadow-sm sticky top-6">
            <h2 className="text-xl font-bold text-text-primary mb-6 flex items-center border-b border-border pb-4">
              <Calendar className="w-5 h-5 mr-2 text-primary" /> Hire {worker.name}
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

            {user && user.uid === worker.managerId ? (
              <div className="bg-blue-50 border border-blue-200 text-blue-800 p-6 rounded-xl text-center shadow-inner">
                <div className="text-3xl mb-3">🛠️</div>
                <h3 className="text-lg font-bold mb-2">This is your workforce listing</h3>
                <p className="text-sm">You cannot hire your own workforce listing.</p>
              </div>
            ) : (
              <form onSubmit={handleBooking} className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Start Date</label>
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
                    <span>₹{timeSlot === 'Full Day' ? worker.dailyWage : (worker.hourlyWage || worker.dailyWage)} / {timeSlot === 'Full Day' ? 'day' : 'hr'}</span>
                  </div>
                  <div className="flex justify-between items-center text-sm mb-3 text-text-secondary">
                    <span>Duration</span>
                    <span>x {duration} {timeSlot === 'Full Day' ? 'days' : 'hrs'}</span>
                  </div>
                  <div className="flex justify-between items-center pt-3 border-t border-gray-200">
                    <span className="font-bold text-text-primary">Estimated Total</span>
                    <span className="font-bold text-xl text-primary">₹{calculatePreviewPrice()}</span>
                  </div>
                  <p className="text-xs text-text-secondary mt-2 text-center">Final price will be confirmed.</p>
                </div>

                <button 
                  type="submit" 
                  disabled={bookingLoading}
                  className="w-full py-3.5 bg-primary text-white rounded-xl font-bold hover:bg-green-800 transition-colors shadow-sm disabled:opacity-60"
                >
                  {bookingLoading ? 'Sending Request...' : 'Send Hiring Request'}
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
