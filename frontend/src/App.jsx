import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Sidebar from './components/Sidebar'
import Footer from './components/Footer'

import Home from './pages/Home'
import DiseaseDetection from './pages/DiseaseDetection'
import CropRecommendation from './pages/CropRecommendation'
import About from './pages/About'
import Settings from './pages/Settings'
import NotFound from './pages/NotFound'

import Login from './pages/Login'
import Register from './pages/Register'
import EquipmentMarketplace from './pages/EquipmentMarketplace'
import EquipmentDetails from './pages/EquipmentDetails'
import FarmWorkforce from './pages/FarmWorkforce'
import WorkerDetails from './pages/WorkerDetails'
import Dashboard from './pages/Dashboard'
import DiagnosisHistory from './pages/DiagnosisHistory'
import MLDashboard from './pages/MLDashboard'
import MobileNumber from './pages/MobileNumber'
import { useAuth } from './hooks/useAuth'
import { Navigate, useLocation } from 'react-router-dom'

function RequireMobileNumber({ children }) {
  const { user, profile, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div className="flex justify-center p-8"><span className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" /></div>;
  }
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  if (profile && !profile.phone) {
    return <Navigate to="/mobile-number" state={{ from: location }} replace />;
  }
  return children;
}

function App() {
  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-4 md:p-8 bg-background-app">
          <div className="max-w-7xl mx-auto">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/disease-detection" element={<DiseaseDetection />} />
              <Route path="/crop-recommendation" element={<CropRecommendation />} />
              <Route path="/equipment" element={
                <RequireMobileNumber>
                  <EquipmentMarketplace />
                </RequireMobileNumber>
              } />
              <Route path="/equipment/:id" element={
                <RequireMobileNumber>
                  <EquipmentDetails />
                </RequireMobileNumber>
              } />
              <Route path="/workforce" element={
                <RequireMobileNumber>
                  <FarmWorkforce />
                </RequireMobileNumber>
              } />
              <Route path="/workforce/:id" element={
                <RequireMobileNumber>
                  <WorkerDetails />
                </RequireMobileNumber>
              } />
              <Route path="/dashboard" element={
                <RequireMobileNumber>
                  <Dashboard />
                </RequireMobileNumber>
              } />
              <Route path="/diagnosis-history" element={<DiagnosisHistory />} />
              <Route path="/ml-dashboard" element={<MLDashboard />} />
              <Route path="/mobile-number" element={<MobileNumber />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/about" element={<About />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </div>
        </main>
      </div>
      <Footer />
    </div>
  )
}

export default App
