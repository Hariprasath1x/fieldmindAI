import { useState, useEffect } from 'react';
import { useLanguage } from '../hooks/useLanguage';
import { getWorkers } from '../services/workerApi';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { Search, MapPin, Phone, Briefcase, CheckCircle2, Plus, User } from 'lucide-react';
import WorkerForm from '../components/marketplace/WorkerForm';

export default function FarmWorkforce() {
  const { t } = useLanguage();
  const { user } = useAuth();
  const [workers, setWorkers] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [showWorkerForm, setShowWorkerForm] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchWorkers();
  }, []);

  const fetchWorkers = async () => {
    try {
      const data = await getWorkers();
      setWorkers(data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };



  const filteredWorkers = workers.filter(w => 
    w.name.toLowerCase().includes(search.toLowerCase()) || 
    w.village.toLowerCase().includes(search.toLowerCase()) ||
    w.skills.some(s => s.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="max-w-6xl mx-auto py-8">
      <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
        <h1 className="text-3xl font-bold text-primary">{t('farm_workforce')}</h1>
        <div className="flex flex-col sm:flex-row items-center gap-4 w-full md:w-auto">
          <button 
            onClick={() => {
              if (!user) return alert('Please login first to post a worker profile.');
              setShowWorkerForm(true);
            }}
            className="w-full sm:w-auto px-4 py-2 bg-primary text-white rounded-md font-medium hover:bg-green-800 transition-colors shadow-sm flex items-center justify-center shrink-0"
          >
            <Plus className="w-5 h-5 mr-1" /> Post Worker
          </button>
          <div className="relative w-full md:w-72">
            <Search className="absolute left-3 top-2.5 w-5 h-5 text-text-secondary" />
            <input 
              type="text" 
              placeholder={t('search_workers')}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-10">Loading...</div>
      ) : filteredWorkers.length === 0 ? (
        <div className="text-center py-20 bg-card border border-border rounded-xl shadow-sm mt-8">
          <div className="text-5xl mb-4">🧑‍🌾</div>
          <h3 className="text-xl font-bold text-text-primary mb-2">No workers found</h3>
          <p className="text-text-secondary max-w-md mx-auto mb-6">
            {search 
              ? `We couldn't find any workforce profiles matching "${search}". Try adjusting your search.`
              : 'There are no workforce profiles available yet. Be the first to post a profile!'}
          </p>
          {search && (
            <button 
              onClick={() => setSearch('')}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md font-medium hover:bg-gray-200 transition-colors"
            >
              Clear Search
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredWorkers.map(worker => (
            <div key={worker.id} className="bg-card border-2 border-border rounded-xl shadow-sm p-6 flex flex-col relative">
              <div className="absolute top-4 right-4 flex flex-col gap-2 items-end">
                <div className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-bold flex items-center">
                  <CheckCircle2 className="w-3 h-3 mr-1" /> {worker.status}
                </div>
                {user && user.uid === worker.managerId && (
                  <div className="bg-blue-100 text-blue-800 px-2 py-1 rounded-md text-xs font-bold shadow-sm border border-blue-200">
                    Your Listing
                  </div>
                )}
              </div>
              
              <div className="flex items-center mb-4">
                <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mr-4 overflow-hidden">
                  {worker.photo ? <img src={worker.photo} alt={worker.name} className="w-full h-full object-cover"/> : <User className="w-8 h-8 text-gray-400" />}
                </div>
                <div>
                  <h3 className="text-xl font-bold text-text-primary">{worker.name}</h3>
                  <div className="text-sm text-text-secondary">{worker.experience} Experience</div>
                </div>
              </div>
              
              <div className="space-y-2 mb-4 text-sm text-text-secondary flex-1">
                <div className="flex items-center"><MapPin className="w-4 h-4 mr-2 text-primary" /> {worker.village}</div>
                <div className="flex items-center"><Phone className="w-4 h-4 mr-2 text-primary" /> {worker.phone}</div>
                <div className="flex items-start">
                  <Briefcase className="w-4 h-4 mr-2 text-primary mt-0.5 shrink-0" /> 
                  <span className="leading-tight">{worker.skills.join(', ')}</span>
                </div>
              </div>
              
              <div className="mt-auto pt-4 border-t border-border flex justify-between items-center">
                <div>
                  <div className="text-lg font-bold text-primary">₹{worker.dailyWage} <span className="text-xs text-text-secondary">{t('daily')}</span></div>
                </div>
                <button 
                  onClick={() => navigate(`/workforce/${worker.id}`)}
                  className="bg-primary text-white px-4 py-2 rounded-md font-semibold hover:bg-green-800 transition-colors"
                >
                  View Profile
                </button>
              </div>
            </div>
          ))}
        </div>
      )}


      {/* Worker Form Modal */}
      {showWorkerForm && (
        <WorkerForm 
          onClose={() => setShowWorkerForm(false)} 
          onAdded={() => {
            setShowWorkerForm(false);
            fetchWorkers();
            alert('Worker profile posted successfully!');
          }} 
        />
      )}
    </div>
  );
}
