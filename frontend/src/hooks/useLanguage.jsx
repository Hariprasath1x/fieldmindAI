import { createContext, useContext, useState, useEffect } from 'react';
import en from '../i18n/en.json';
import ta from '../i18n/ta.json';
import { useAuth } from './useAuth';

const LanguageContext = createContext();

const translations = { en, ta };

export const LanguageProvider = ({ children }) => {
  const { profile } = useAuth();
  const [lang, setLang] = useState('en');

  // Sync language with profile if available
  useEffect(() => {
    if (profile?.language) {
      setLang(profile.language);
    }
  }, [profile]);

  const t = (key) => {
    return translations[lang][key] || key;
  };

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => useContext(LanguageContext);
