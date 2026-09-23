import { useState, useEffect } from 'react';
import {
  signInWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  sendPasswordResetEmail,
} from 'firebase/auth';
import { auth } from '../services/firebase';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useLanguage } from '../hooks/useLanguage';
import { useAuth } from '../hooks/useAuth';

const TABS = ['google', 'email'];
const TAB_LABELS = { google: 'Google', email: 'Email' };

// ── helpers ──────────────────────────────────────────────────────────────────

function mapAuthError(err) {
  const code = err?.code || '';
  if (code === 'auth/popup-closed-by-user' || code === 'auth/cancelled-popup-request') return null; // user dismissed — not an error
  if (code === 'auth/popup-blocked') return 'Popup was blocked. Please allow popups for this site.';
  if (code === 'auth/unauthorized-domain') return 'This domain is not authorized. Check Firebase Console → Authentication → Settings → Authorized domains.';
  if (code === 'auth/account-exists-with-different-credential') return 'An account already exists with the same email using a different sign-in method.';
  if (code === 'auth/network-request-failed') return 'Network error. Check your internet connection.';
  if (code === 'auth/invalid-credential' || code === 'auth/wrong-password') return 'Invalid email or password.';
  if (code === 'auth/user-not-found') return 'No account found with this email.';
  if (code === 'auth/too-many-requests') return 'Too many attempts. Please try again later.';
  return err.message || 'Authentication failed.';
}

// ── GoogleTab ─────────────────────────────────────────────────────────────────

function GoogleTab({ onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGoogle = async () => {
    if (loading) return; // prevent double-click
    setError('');
    setLoading(true);
    console.log('[AUTH] Google sign-in started');
    try {
      const provider = new GoogleAuthProvider();
      provider.setCustomParameters({ prompt: 'select_account' });
      console.log('[AUTH] Opening Google popup');
      const result = await signInWithPopup(auth, provider);
      console.log('[AUTH] Google credential received. UID:', result.user.uid);
      console.log('[AUTH] User email:', result.user.email);
      onSuccess(result.user);
    } catch (err) {
      const msg = mapAuthError(err);
      console.warn('[AUTH ERROR] code:', err?.code, '| message:', err?.message);
      if (msg) setError(msg);
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg text-sm font-medium">
          {error}
        </div>
      )}
      <button
        id="btn-google-signin"
        onClick={handleGoogle}
        disabled={loading}
        className="w-full flex items-center justify-center gap-3 py-3 px-4 border-2 border-border rounded-xl font-semibold text-text-primary bg-card hover:bg-gray-50 active:scale-[0.98] transition-all shadow-sm disabled:opacity-60 disabled:cursor-not-allowed"
      >
        {loading ? (
          <span className="animate-spin h-5 w-5 border-2 border-primary border-t-transparent rounded-full" />
        ) : (
          <svg width="20" height="20" viewBox="0 0 48 48">
            <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
            <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
            <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
            <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.18 1.48-4.97 2.36-8.16 2.36-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
            <path fill="none" d="M0 0h48v48H0z"/>
          </svg>
        )}
        {loading ? 'Signing in…' : 'Continue with Google'}
      </button>
    </div>
  );
}

// ── EmailTab ──────────────────────────────────────────────────────────────────

function EmailTab({ onSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [resetSent, setResetSent] = useState(false);
  const [showReset, setShowReset] = useState(false);
  const [resetEmail, setResetEmail] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const result = await signInWithEmailAndPassword(auth, email, password);
      onSuccess(result.user);
    } catch (err) {
      setError(mapAuthError(err) || 'Login failed.');
    }
    setLoading(false);
  };

  const handlePasswordReset = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await sendPasswordResetEmail(auth, resetEmail || email);
      setResetSent(true);
    } catch (err) {
      setError(err.message);
    }
  };

  if (showReset) {
    return (
      <div className="space-y-4">
        <button onClick={() => { setShowReset(false); setResetSent(false); }} className="flex items-center gap-1 text-sm text-text-secondary hover:text-primary transition-colors">
          ← Back to login
        </button>
        <h3 className="font-semibold text-text-primary">Reset your password</h3>
        {resetSent ? (
          <div className="bg-green-50 text-green-700 p-3 rounded-lg text-sm font-medium">
            ✅ Password reset email sent! Check your inbox.
          </div>
        ) : (
          <form onSubmit={handlePasswordReset} className="space-y-3">
            {error && <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">{error}</div>}
            <div>
              <label htmlFor="reset-email" className="block text-sm font-medium text-text-secondary mb-1">Email</label>
              <input
                id="reset-email"
                name="email"
                type="email"
                autoComplete="email"
                value={resetEmail || email}
                onChange={(e) => setResetEmail(e.target.value)}
                className="w-full px-4 py-2.5 border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary bg-card"
                required
              />
            </div>
            <button type="submit" className="w-full bg-primary text-white py-2.5 rounded-xl font-semibold hover:bg-green-800 transition-colors">
              Send Reset Email
            </button>
          </form>
        )}
      </div>
    );
  }

  return (
    <form onSubmit={handleLogin} className="space-y-4">
      {error && <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm font-medium">{error}</div>}
      <div>
        <label htmlFor="email-input" className="block text-sm font-medium text-text-secondary mb-1">Email</label>
        <input
          id="email-input"
          name="email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full px-4 py-2.5 border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary bg-card"
          required
        />
      </div>
      <div>
        <label htmlFor="password-input" className="block text-sm font-medium text-text-secondary mb-1">Password</label>
        <input
          id="password-input"
          name="password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full px-4 py-2.5 border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary bg-card"
          required
        />
      </div>
      <div className="flex justify-end">
        <button type="button" onClick={() => setShowReset(true)} className="text-sm text-primary hover:underline font-medium">
          Forgot password?
        </button>
      </div>
      <button
        id="btn-email-login"
        type="submit"
        disabled={loading}
        className="w-full bg-primary text-white py-2.5 rounded-xl font-semibold hover:bg-green-800 active:scale-[0.98] transition-all disabled:opacity-60"
      >
        {loading ? 'Logging in…' : 'Login'}
      </button>
    </form>
  );
}

// ── Main Login page ───────────────────────────────────────────────────────────

export default function Login() {
  const [tab, setTab] = useState('google');
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useLanguage();
  const { user, loading: authLoading } = useAuth();

  const from = location.state?.from?.pathname || '/';

  // Auto-redirect: if Firebase already has an authenticated user (e.g. after
  // Google popup completes and onAuthStateChanged fires), go to destination.
  // Depends on `user` only — not `profile` — so it fires immediately.
  useEffect(() => {
    if (!authLoading && user) {
      console.log(`[AUTH] User detected on Login page. Redirecting to ${from}`);
      navigate(from, { replace: true });
    }
  }, [user, authLoading, navigate, from]);

  const handleSuccess = () => {
    navigate(from, { replace: true });
  };

  return (
    <>
      <div className="flex items-center justify-center min-h-[75vh] py-8">
        <div className="bg-card p-8 rounded-2xl shadow-lg border border-border w-full max-w-md">
          {/* Header */}
          <div className="text-center mb-7">
            <div className="text-4xl mb-2">🌿</div>
            <h1 className="text-2xl font-bold text-primary">Welcome back</h1>
            <p className="text-text-secondary text-sm mt-1">Sign in to your FieldMind account</p>
          </div>

          {/* Tab selector */}
          <div className="flex gap-1 mb-6 bg-gray-100 rounded-xl p-1">
            {TABS.map((tabKey) => (
              <button
                key={tabKey}
                id={`tab-${tabKey}`}
                onClick={() => setTab(tabKey)}
                className={`flex-1 py-2 rounded-lg font-medium text-sm transition-all ${
                  tab === tabKey
                    ? 'bg-white shadow text-primary'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {TAB_LABELS[tabKey]}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div>
            {tab === 'google' && <GoogleTab onSuccess={handleSuccess} />}
            {tab === 'email' && <EmailTab onSuccess={handleSuccess} />}
          </div>

          {/* Footer */}
          <div className="mt-6 pt-4 border-t border-border text-center text-sm text-text-secondary">
            Don't have an account?{' '}
            <Link to="/register" className="text-primary hover:underline font-medium">
              Register
            </Link>
          </div>
        </div>
      </div>
    </>
  );
}
