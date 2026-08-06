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
      setUser(currentUser);
      if (currentUser) {
        // Fetch or create profile in backend
        try {
          const res = await apiClient.post('/api/marketplace/users/sync', {
            uid: currentUser.uid,
            email: currentUser.email,
            phone: currentUser.phoneNumber,
            displayName: currentUser.displayName
          });
          
          // Get the full profile
          const profileRes = await apiClient.get(`/api/marketplace/users/${currentUser.uid}`);
          setProfile(profileRes.data);
        } catch (error) {
          console.error("Error syncing user:", error);
        }
      } else {
        setProfile(null);
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  return (
    <AuthContext.Provider value={{ user, profile, loading }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
