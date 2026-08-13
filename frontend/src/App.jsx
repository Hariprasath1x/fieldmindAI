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
import FarmWorkforce from './pages/FarmWorkforce'
import Dashboard from './pages/Dashboard'
import DiagnosisHistory from './pages/DiagnosisHistory'
import MLDashboard from './pages/MLDashboard'

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
              <Route path="/equipment" element={<EquipmentMarketplace />} />
              <Route path="/workforce" element={<FarmWorkforce />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/diagnosis-history" element={<DiagnosisHistory />} />
              <Route path="/ml-dashboard" element={<MLDashboard />} />
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
