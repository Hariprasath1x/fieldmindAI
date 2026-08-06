import { useState } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { Droplets, Thermometer, Wind, Beaker, CloudRain, Activity, MapPin, Edit2, AlertCircle, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { recommendCrop, collectLocationData } from '../services/api';

import { FarmConditionsCard } from '../components/recommendations/FarmConditionsCard';
import { CropInsightCard } from '../components/recommendations/CropInsightCard';
import { AlternativeCropCard } from '../components/recommendations/AlternativeCropCard';

export default function CropRecommendation() {
  const { register, handleSubmit, setValue, control, formState: { errors } } = useForm();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [results, setResults] = useState(null);
  const [mode, setMode] = useState(null); // 'location' or 'manual'
  
  // Location flow states
  const [locationStatus, setLocationStatus] = useState('');
  const [isCollecting, setIsCollecting] = useState(false);
  const [estimatedFields, setEstimatedFields] = useState({
    nitrogen: false, phosphorus: false, potassium: false
  });
  const [locationDetails, setLocationDetails] = useState(null);

  // Watch form values for the FarmConditionsCard
  const formValues = useWatch({ control });

  const startLocationFlow = () => {
    setMode('location');
    setIsCollecting(true);
    setLocationStatus('📍 Requesting location permission...');
    
    if (!navigator.geolocation) {
      handleLocationError('Geolocation is not supported by your browser. Falling back to manual entry.');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        setLocationStatus('📍 Location detected. Fetching environmental data...');
        try {
          const { latitude, longitude } = position.coords;
          const data = await collectLocationData(latitude, longitude);
          
          setLocationStatus('✓ Environmental data retrieved successfully.');
          setLocationDetails(data.location);
          
          // Auto-fill form
          if (data.weather) {
            setValue('temperature', data.weather.temperature);
            setValue('humidity', data.weather.humidity);
            setValue('rainfall', data.weather.rainfall);
          }
          if (data.soil) {
            setValue('ph', data.soil.ph);
            if (data.soil.nitrogen) setValue('nitrogen', data.soil.nitrogen);
            if (data.soil.phosphorus) setValue('phosphorous', data.soil.phosphorus);
            if (data.soil.potassium) setValue('potassium', data.soil.potassium);
          }
          if (data.estimated && data.estimated.is_estimated) {
            setValue('nitrogen', data.estimated.nitrogen);
            setValue('phosphorous', data.estimated.phosphorus);
            setValue('potassium', data.estimated.potassium);
            setEstimatedFields({ nitrogen: true, phosphorus: true, potassium: true });
          }
          
          setIsCollecting(false);
        } catch (error) {
          console.error("API Error:", error);
          handleLocationError(`Failed to fetch environmental data: ${error.message}. Falling back to manual entry.`);
        }
      },
      (error) => {
        console.error("Geolocation Error:", error);
        handleLocationError(`Location error (${error.code}): ${error.message}. Falling back to manual entry.`);
      },
      { timeout: 10000, maximumAge: 0, enableHighAccuracy: false }
    );
  };

  const handleLocationError = (msg) => {
    setLocationStatus(`❌ ${msg}`);
    setTimeout(() => {
      setMode('manual');
      setIsCollecting(false);
      setLocationStatus('');
    }, 3000);
  };

  const onSubmit = async (data) => {
    setIsSubmitting(true);
    setResults(null);
    try {
      const payload = {
        N: data.nitrogen,
        P: data.phosphorous,
        K: data.potassium,
        temperature: data.temperature,
        humidity: data.humidity,
        pH: data.ph,
        rainfall: data.rainfall
      };
      
      const response = await recommendCrop(payload);
      if (response.recommendations) {
        setResults(response.recommendations);
      }
    } catch (error) {
      console.error(error);
      alert('Failed to get recommendation. Please check if the backend is running.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const InputField = ({ label, name, icon: Icon, placeholder, isEstimated }) => (
    <div className="space-y-2 relative">
      <label className="flex items-center text-sm font-medium text-text-primary">
        <Icon className="w-4 h-4 mr-2 text-text-secondary" />
        {label}
      </label>
      <input
        type="number"
        step="0.01"
        placeholder={placeholder}
        {...register(name, { required: true, valueAsNumber: true })}
        className="w-full px-4 py-2 bg-white border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all shadow-sm"
      />
      {isEstimated && (
        <span className="absolute right-3 top-9 text-[10px] font-semibold bg-warning text-white px-2 py-0.5 rounded-full">
          Estimated
        </span>
      )}
      {errors[name] && <span className="text-xs text-error">This field is required</span>}
    </div>
  );

  return (
    <div className="max-w-6xl mx-auto py-6 space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-text-primary mb-2">Crop Recommendation</h1>
        <p className="text-text-secondary">Enter your soil and environmental parameters to get the best crop suggestion.</p>
      </div>

      {!mode && (
        <div className="flex flex-col sm:flex-row justify-center items-center gap-6 mt-12">
          <button
            onClick={startLocationFlow}
            className="flex flex-col items-center justify-center p-8 bg-card border-2 border-primary rounded-xl shadow-sm hover:bg-primary/5 transition-all w-full max-w-sm group"
          >
            <div className="bg-primary text-white p-4 rounded-full mb-4 group-hover:scale-110 transition-transform">
              <MapPin className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold text-text-primary mb-2">Use My Location</h3>
            <p className="text-sm text-text-secondary text-center">Automatically fetch weather and soil data based on your current location.</p>
          </button>
          
          <button
            onClick={() => setMode('manual')}
            className="flex flex-col items-center justify-center p-8 bg-card border-2 border-border rounded-xl shadow-sm hover:border-secondary hover:bg-gray-50 transition-all w-full max-w-sm group"
          >
            <div className="bg-gray-100 text-text-secondary p-4 rounded-full mb-4 group-hover:scale-110 transition-transform group-hover:text-secondary">
              <Edit2 className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold text-text-primary mb-2">Manual Entry</h3>
            <p className="text-sm text-text-secondary text-center">I know my exact soil and weather parameters and want to enter them manually.</p>
          </button>
        </div>
      )}

      {mode && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            
            {isCollecting && (
              <div className="bg-card p-6 rounded-xl shadow-sm border border-border flex items-center justify-center space-x-4">
                <Loader2 className="w-6 h-6 animate-spin text-primary" />
                <span className="text-text-primary font-medium">{locationStatus}</span>
              </div>
            )}
            
            {!isCollecting && locationStatus.includes('❌') && (
              <div className="bg-red-50 p-4 rounded-xl border border-red-200 flex items-center text-error">
                <AlertCircle className="w-5 h-5 mr-3 shrink-0" />
                <span>{locationStatus}</span>
              </div>
            )}

            {!isCollecting && (
              <>
                {(locationDetails || formValues.temperature) && (
                  <FarmConditionsCard details={locationDetails} formValues={formValues} />
                )}

                <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-card p-6 md:p-8 rounded-xl shadow-sm border border-border"
                >
                  <div className="flex justify-between items-center mb-6 pb-4 border-b border-border">
                    <h2 className="text-xl font-bold text-text-primary">
                      {mode === 'location' ? 'Edit Parameters' : 'Enter Parameters'}
                    </h2>
                    <button 
                      onClick={() => { setMode(null); setLocationDetails(null); setResults(null); }}
                      className="text-sm text-primary hover:underline font-medium"
                    >
                      Change Mode
                    </button>
                  </div>

                  <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-gray-50/50 p-4 rounded-lg">
                      <div className="col-span-full mb-2">
                        <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider">Soil Nutrients</h3>
                      </div>
                      <InputField label="Nitrogen (N)" name="nitrogen" icon={Activity} placeholder="e.g. 90" isEstimated={estimatedFields.nitrogen} />
                      <InputField label="Phosphorus (P)" name="phosphorous" icon={Activity} placeholder="e.g. 42" isEstimated={estimatedFields.phosphorus} />
                      <InputField label="Potassium (K)" name="potassium" icon={Activity} placeholder="e.g. 43" isEstimated={estimatedFields.potassium} />
                      <InputField label="pH Level" name="ph" icon={Beaker} placeholder="e.g. 6.5" />
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-gray-50/50 p-4 rounded-lg">
                      <div className="col-span-full mb-2">
                        <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider">Environment</h3>
                      </div>
                      <InputField label="Temperature (°C)" name="temperature" icon={Thermometer} placeholder="e.g. 28.5" />
                      <InputField label="Humidity (%)" name="humidity" icon={Droplets} placeholder="e.g. 80.2" />
                      <InputField label="Rainfall (mm)" name="rainfall" icon={CloudRain} placeholder="e.g. 200.5" />
                    </div>

                    <div className="pt-4 flex justify-end">
                      <button
                        type="submit"
                        disabled={isSubmitting}
                        className={`px-8 py-3 bg-primary text-white font-medium rounded-md shadow-sm hover:bg-green-800 transition-colors flex items-center ${isSubmitting ? 'opacity-75 cursor-not-allowed' : ''}`}
                      >
                        {isSubmitting ? <><Loader2 className="w-5 h-5 mr-2 animate-spin"/> Analyzing...</> : 'Get Recommendation'}
                      </button>
                    </div>
                  </form>
                </motion.div>
              </>
            )}
          </div>

          <div className="lg:col-span-1">
            <AnimatePresence>
              {results && results.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="space-y-6"
                >
                  <CropInsightCard crop={results[0]} />
                  
                  {results.slice(1).map((crop, idx) => (
                    <AlternativeCropCard key={idx} crop={crop} index={idx + 1} />
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      )}
    </div>
  );
}
