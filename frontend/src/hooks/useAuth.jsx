import { useState, useEffect, createContext, useContext } from 'react';
import { onAuthStateChanged } from 'firebase/auth';
import { auth } from '../services/firebase';
import apiClient from '../services/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      console.log('[AUTH] onAuthStateChanged fired. user:', currentUser?.uid ?? 'null');
      setUser(currentUser);

      if (currentUser) {
        // Set a minimal profile immediately from Firebase user so the app
        // is never blocked waiting for the backend.
        setProfile({
          uid: currentUser.uid,
          displayName: currentUser.displayName || 'User',
          email: currentUser.email || '',
          phone: currentUser.phoneNumber || '',
          role: 'User',
          language: 'en',
        });
        // loading=false here so pages can render / redirect immediately
        setLoading(false);

        // Sync to backend in the background (non-blocking)
        try {
          const syncPayload = {
            uid: currentUser.uid,
            email: currentUser.email || '',
            displayName: currentUser.displayName || 'User',
            role: 'User',
            language: 'en',
          };
          if (currentUser.phoneNumber) {
            syncPayload.phone = currentUser.phoneNumber;
          }
          await apiClient.post('/api/marketplace/users/sync', syncPayload);
          
          const profileRes = await apiClient.get(`/api/marketplace/users/${currentUser.uid}`);
          setProfile(profileRes.data); // upgrade to full backend profile
        } catch (error) {
          console.warn('[AUTH] Backend sync failed (using Firebase profile fallback):', error.message);
          // profile already set above — no action needed
        }
      } else {
        setProfile(null);
        setLoading(false);
      }
    });

    return () => unsubscribe();
  }, []);

  return (
    <AuthContext.Provider value={{ user, profile, loading, setProfile }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
