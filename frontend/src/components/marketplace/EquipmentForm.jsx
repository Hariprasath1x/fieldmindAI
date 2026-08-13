import { useState } from 'react';
import { createEquipment } from '../../services/equipmentApi';
import { useAuth } from '../../hooks/useAuth';

export default function EquipmentForm({ onClose, onAdded }) {
  const { user, profile } = useAuth();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '', category: 'Tractor', hourlyPrice: '', dailyPrice: '',
    location: '', village: '', quantity: 1, description: '', image: ''
  });

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createEquipment({
        ...formData,
        hourlyPrice: parseFloat(formData.hourlyPrice),
        dailyPrice: parseFloat(formData.dailyPrice),
        quantity: parseInt(formData.quantity),
        ownerId: user.uid,
        ownerName: profile?.displayName || user?.displayName || user?.email || 'Unknown Owner',
        ownerPhone: profile?.phone || user?.phoneNumber || 'Not provided'
      });
      alert('Equipment added successfully!');
      onAdded();
      onClose();
    } catch (err) {
      console.error(err);
      alert('Error adding equipment');
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white rounded-xl p-6 w-full max-w-lg mt-20 md:mt-0">
        <h2 className="text-xl font-bold mb-4 text-primary">Add New Equipment</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Equipment Name</label>
            <input name="name" type="text" onChange={handleChange} required className="w-full border p-2 rounded-md" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Category</label>
            <select name="category" onChange={handleChange} className="w-full border p-2 rounded-md">
              <option>Tractor</option>
              <option>Rotavator</option>
              <option>Harvester</option>
              <option>Seeder</option>
              <option>Sprayer</option>
              <option>Water Tanker</option>
              <option>Others</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Hourly Price (₹)</label>
              <input name="hourlyPrice" type="number" onChange={handleChange} required className="w-full border p-2 rounded-md" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Daily Price (₹)</label>
              <input name="dailyPrice" type="number" onChange={handleChange} required className="w-full border p-2 rounded-md" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Village</label>
              <input name="village" type="text" onChange={handleChange} required className="w-full border p-2 rounded-md" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Location / City</label>
              <input name="location" type="text" onChange={handleChange} required className="w-full border p-2 rounded-md" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Quantity Available</label>
            <input name="quantity" type="number" min="1" value={formData.quantity} onChange={handleChange} required className="w-full border p-2 rounded-md" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Image URL (Optional)</label>
            <input name="image" type="text" onChange={handleChange} className="w-full border p-2 rounded-md" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Description (Optional)</label>
            <textarea name="description" onChange={handleChange} className="w-full border p-2 rounded-md" rows="2"></textarea>
          </div>
          <div className="flex justify-end space-x-3 mt-6">
            <button type="button" onClick={onClose} className="px-4 py-2 border rounded-md font-medium text-text-secondary">Cancel</button>
            <button type="submit" disabled={loading} className="px-4 py-2 bg-primary text-white rounded-md font-medium">
              {loading ? 'Saving...' : 'Add Equipment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
