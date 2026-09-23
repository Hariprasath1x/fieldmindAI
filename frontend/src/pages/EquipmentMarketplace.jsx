import { useState, useEffect } from 'react';
import { useLanguage } from '../hooks/useLanguage';
import { getEquipment } from '../services/equipmentApi';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { Search, MapPin, Phone, User, Plus } from 'lucide-react';
import EquipmentForm from '../components/marketplace/EquipmentForm';

export default function EquipmentMarketplace() {
  const { t } = useLanguage();
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [showEquipmentForm, setShowEquipmentForm] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchEquipment();
  }, []);

  const fetchEquipment = async () => {
    try {
      const data = await getEquipment();
      setItems(data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };



  const filteredItems = items.filter(i => 
    i.name.toLowerCase().includes(search.toLowerCase()) || 
    i.category.toLowerCase().includes(search.toLowerCase()) ||
    i.village.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-w-6xl mx-auto py-8">
      <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
        <h1 className="text-3xl font-bold text-primary">{t('equipment_rental')}</h1>
        <div className="flex flex-col sm:flex-row items-center gap-4 w-full md:w-auto">
          <button 
            onClick={() => {
              if (!user) return alert('Please login first to post equipment.');
              setShowEquipmentForm(true);
            }}
            className="w-full sm:w-auto px-4 py-2 bg-primary text-white rounded-md font-medium hover:bg-green-800 transition-colors shadow-sm flex items-center justify-center shrink-0"
          >
            <Plus className="w-5 h-5 mr-1" /> Post Equipment
          </button>
          <div className="relative w-full md:w-72">
            <Search className="absolute left-3 top-2.5 w-5 h-5 text-text-secondary" />
            <input 
              type="text" 
              placeholder={t('search_equipment')}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-10">Loading...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredItems.map(item => (
            <div key={item.id} className="bg-card border-2 border-border rounded-xl shadow-sm overflow-hidden flex flex-col">
              <div className="h-48 bg-gray-200 w-full relative">
                {item.image ? (
                  <img src={item.image} alt={item.name} className="w-full h-full object-cover" />
                ) : (
                  <div className="flex items-center justify-center w-full h-full text-gray-400">No Image</div>
                )}
                <div className="absolute top-2 right-2 bg-white px-2 py-1 rounded-md text-xs font-bold shadow-sm">
                  {item.category}
                </div>
              </div>
              <div className="p-5 flex-1 flex flex-col">
                <h3 className="text-xl font-bold text-text-primary mb-2">{item.name}</h3>
                
                <div className="space-y-2 mb-4 text-sm text-text-secondary">
                  <div className="flex items-center"><MapPin className="w-4 h-4 mr-2 text-primary" /> {item.village}, {item.location}</div>
                  <div className="flex items-center"><User className="w-4 h-4 mr-2 text-primary" /> {item.ownerName}</div>
                  <div className="flex items-center"><Phone className="w-4 h-4 mr-2 text-primary" /> {item.ownerPhone}</div>
                </div>
                
                <div className="mt-auto pt-4 border-t border-border flex justify-between items-center">
                  <div>
                    <div className="text-lg font-bold text-primary">₹{item.hourlyPrice} <span className="text-xs text-text-secondary">{t('hourly')}</span></div>
                    <div className="text-xs text-text-secondary">₹{item.dailyPrice} {t('daily')}</div>
                  </div>
                  <button 
                    onClick={() => navigate(`/equipment/${item.id}`)}
                    className="bg-primary text-white px-4 py-2 rounded-md font-semibold hover:bg-green-800 transition-colors"
                  >
                    View Details
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}


      {/* Equipment Form Modal */}
      {showEquipmentForm && (
        <EquipmentForm 
          onClose={() => setShowEquipmentForm(false)} 
          onAdded={() => {
            setShowEquipmentForm(false);
            fetchEquipment();
            alert('Equipment posted successfully!');
          }} 
        />
      )}
    </div>
  );
}
