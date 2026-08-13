import { useState, useEffect } from 'react';
import { signInWithEmailAndPassword, RecaptchaVerifier, signInWithPhoneNumber } from 'firebase/auth';
import { auth } from '../services/firebase';
import { useNavigate, Link } from 'react-router-dom';
import { useLanguage } from '../hooks/useLanguage';
import apiClient from '../services/api';

export default function Login() {
  const [method, setMethod] = useState('email'); // 'email' or 'phone'
  
  // Email state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  // Phone state
  const [phone, setPhone] = useState('+91');
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { t } = useLanguage();

  useEffect(() => {
    if (!window.recaptchaVerifier) {
      window.recaptchaVerifier = new RecaptchaVerifier(auth, 'recaptcha-container', {
        'size': 'invisible'
      });
    }
  }, []);

  const handleEmailLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await signInWithEmailAndPassword(auth, email, password);
      navigate('/dashboard');
    } catch (err) {
      if (err.code === 'auth/invalid-credential') setError("Invalid email or password.");
      else setError(err.message);
    }
    setLoading(false);
  };

  const handleSendOtp = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const appVerifier = window.recaptchaVerifier;
      const confirmationResult = await signInWithPhoneNumber(auth, phone, appVerifier);
      window.confirmationResult = confirmationResult;
      setOtpSent(true);
    } catch (err) {
      setError(err.message);
      // reset recaptcha on error
      if (window.recaptchaVerifier) window.recaptchaVerifier.render().then(widgetId => grecaptcha.reset(widgetId));
    }
    setLoading(false);
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const result = await window.confirmationResult.confirm(otp);
      
      // Ensure phone user exists in our backend DB
      try {
        await apiClient.post('/api/marketplace/users/sync', {
          uid: result.user.uid,
          email: result.user.email || '',
          displayName: result.user.displayName || 'Phone User',
          phone: result.user.phoneNumber,
          role: 'User',
          language: 'en'
        });
      } catch (syncErr) {
        console.warn("Backend sync failed on phone login", syncErr);
      }
      
      navigate('/dashboard');
    } catch (err) {
      console.error(err);
      setError("Invalid OTP.");
    }
    setLoading(false);
  };

  return (
    <div className="flex items-center justify-center min-h-[70vh] py-8">
      <div className="bg-card p-8 rounded-xl shadow-md border-2 border-border w-full max-w-md">
        <h2 className="text-3xl font-bold text-primary mb-6 text-center">{t('login')}</h2>
        
        <div className="flex mb-6 bg-gray-100 rounded-lg p-1">
          <button 
            onClick={() => setMethod('email')} 
            className={`flex-1 py-2 rounded-md font-medium text-sm transition-colors ${method === 'email' ? 'bg-white shadow-sm text-primary' : 'text-gray-500'}`}
          >
            Email
          </button>
          <button 
            onClick={() => setMethod('phone')} 
            className={`flex-1 py-2 rounded-md font-medium text-sm transition-colors ${method === 'phone' ? 'bg-white shadow-sm text-primary' : 'text-gray-500'}`}
          >
            Phone Number
          </button>
        </div>

        {error && <div className="bg-red-50 text-red-600 p-3 rounded-md mb-4 text-sm font-medium">{error}</div>}
        
        {method === 'email' ? (
          <form onSubmit={handleEmailLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">Email</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full px-4 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full px-4 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary" required />
            </div>
            <button type="submit" disabled={loading} className="w-full bg-primary text-white py-2 rounded-md font-semibold hover:bg-green-800 transition-colors">
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>
        ) : (
          <div className="space-y-4">
            <div id="recaptcha-container"></div>
            {!otpSent ? (
              <form onSubmit={handleSendOtp} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Phone Number (with country code)</label>
                  <input type="text" placeholder="+919876543210" value={phone} onChange={(e) => setPhone(e.target.value)} className="w-full px-4 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary" required />
                </div>
                <button type="submit" disabled={loading} className="w-full bg-primary text-white py-2 rounded-md font-semibold hover:bg-green-800 transition-colors">
                  {loading ? 'Sending OTP...' : 'Send OTP'}
                </button>
              </form>
            ) : (
              <form onSubmit={handleVerifyOtp} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Enter OTP</label>
                  <input type="text" value={otp} onChange={(e) => setOtp(e.target.value)} className="w-full px-4 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary" required />
                </div>
                <button type="submit" disabled={loading} className="w-full bg-primary text-white py-2 rounded-md font-semibold hover:bg-green-800 transition-colors">
                  {loading ? 'Verifying...' : 'Verify OTP'}
                </button>
              </form>
            )}
          </div>
        )}

        <div className="mt-6 text-center text-sm text-text-secondary">
          Don't have an account? <Link to="/register" className="text-primary hover:underline font-medium">Register</Link>
        </div>
      </div>
    </div>
  );
}
