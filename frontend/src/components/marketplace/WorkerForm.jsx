import { useState } from 'react';
import { createWorker } from '../../services/workerApi';
import { useAuth } from '../../hooks/useAuth';

export default function WorkerForm({ onClose, onAdded }) {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '', phone: '', village: '', experience: '', skills: '',
    dailyWage: '', hourlyWage: '', availableDays: 'Mon,Tue,Wed,Thu,Fri',
    availableTime: '8am - 5pm', languages: 'Tamil, English'
  });

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createWorker({
        ...formData,
        dailyWage: parseFloat(formData.dailyWage),
        hourlyWage: parseFloat(formData.hourlyWage),
        skills: formData.skills.split(',').map(s => s.trim()),
        availableDays: formData.availableDays.split(',').map(d => d.trim()),
        languages: formData.languages.split(',').map(l => l.trim()),
        managerId: user.uid
      });
      alert('Worker added successfully!');
      onAdded();
      onClose();
    } catch (err) {
      console.error(err);
      alert('Error adding worker');
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white rounded-xl p-6 w-full max-w-lg mt-20 md:mt-0">
        <h2 className="text-xl font-bold mb-4 text-primary">Add New Worker</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Full Name</label>
            <input name="name" type="text" onChange={handleChange} required className="w-full border p-2 rounded-md" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Phone</label>
              <input name="phone" type="text" onChange={handleChange} required className="w-full border p-2 rounded-md" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Village</label>
              <input name="village" type="text" onChange={handleChange} required className="w-full border p-2 rounded-md" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Experience (e.g. 5 Years)</label>
            <input name="experience" type="text" onChange={handleChange} required className="w-full border p-2 rounded-md" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Skills (Comma separated)</label>
            <input name="skills" type="text" placeholder="e.g. Harvesting, Sowing, Driving" onChange={handleChange} required className="w-full border p-2 rounded-md" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Daily Wage (₹)</label>
              <input name="dailyWage" type="number" onChange={handleChange} required className="w-full border p-2 rounded-md" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Hourly Wage (₹)</label>
              <input name="hourlyWage" type="number" onChange={handleChange} required className="w-full border p-2 rounded-md" />
            </div>
          </div>
          <div className="flex justify-end space-x-3 mt-6">
            <button type="button" onClick={onClose} className="px-4 py-2 border rounded-md font-medium text-text-secondary">Cancel</button>
            <button type="submit" disabled={loading} className="px-4 py-2 bg-primary text-white rounded-md font-medium">
              {loading ? 'Saving...' : 'Add Worker'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
