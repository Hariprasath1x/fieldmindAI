import { useState } from 'react';
import { createUserWithEmailAndPassword, updateProfile } from 'firebase/auth';
import { auth } from '../services/firebase';
import { useNavigate, Link } from 'react-router-dom';
import apiClient from '../services/api';

export default function Register() {
  const [formData, setFormData] = useState({
    name: '', email: '', password: '', phone: '', language: 'en'
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    
    if (formData.password.length < 6) {
      return setError("Password must be at least 6 characters long.");
    }
    
    setLoading(true);
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, formData.email, formData.password);
      await updateProfile(userCredential.user, { displayName: formData.name });
      
      // Sync with backend immediately
      await apiClient.post('/api/marketplace/users/sync', {
        uid: userCredential.user.uid,
        email: formData.email,
        displayName: formData.name,
        phone: formData.phone,
        role: 'User',
        language: formData.language
      });
      
      navigate('/dashboard');
    } catch (err) {
      // Provide more helpful error messages for Firebase 400s
      if (err.code === 'auth/email-already-in-use') {
        setError("This email is already in use.");
      } else if (err.code === 'auth/invalid-email') {
        setError("Invalid email address format.");
      } else if (err.code === 'auth/operation-not-allowed') {
        setError("Email/Password accounts are not enabled in your Firebase Console. Please enable them.");
      } else {
        setError(err.message);
      }
    }
    setLoading(false);
  };

  return (
    <div className="flex items-center justify-center min-h-[80vh] py-8">
      <div className="bg-card p-8 rounded-xl shadow-md border-2 border-border w-full max-w-md">
        <h2 className="text-3xl font-bold text-primary mb-6 text-center">Register</h2>
        
        {error && <div className="bg-red-50 text-red-600 p-3 rounded-md mb-4 text-sm font-medium">{error}</div>}
        
        <form onSubmit={handleRegister} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Full Name</label>
            <input name="name" type="text" onChange={handleChange} className="w-full px-4 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Email</label>
            <input name="email" type="email" onChange={handleChange} className="w-full px-4 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Password</label>
            <input name="password" type="password" onChange={handleChange} className="w-full px-4 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary" required minLength="6" />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Phone Number</label>
            <input name="phone" type="text" onChange={handleChange} className="w-full px-4 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Preferred Language</label>
            <select name="language" onChange={handleChange} className="w-full px-4 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary">
              <option value="en">English</option>
              <option value="ta">Tamil</option>
            </select>
          </div>
          <button type="submit" disabled={loading} className="w-full bg-primary text-white py-2 rounded-md font-semibold hover:bg-green-800 transition-colors mt-6">
            {loading ? 'Creating Account...' : 'Register'}
          </button>
        </form>
        
        <p className="mt-4 text-center text-sm text-text-secondary">
          Already have an account? <Link to="/login" className="text-primary hover:underline">Login</Link>
        </p>
      </div>
    </div>
  );
}
