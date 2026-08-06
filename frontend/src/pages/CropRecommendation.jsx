import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Droplets, Thermometer, Wind, Beaker, CloudRain, Activity, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function CropRecommendation() {
  const { register, handleSubmit, formState: { errors } } = useForm();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  const onSubmit = async (data) => {
    setIsSubmitting(true);
    setResult(null);
    try {
      // Mock API Call
      await new Promise(resolve => setTimeout(resolve, 1500));
      setResult({
        crop: 'Rice',
        confidence: 94.5,
        message: 'Based on your high rainfall and humidity levels, Rice is highly recommended for this environment.'
      });
    } catch (error) {
      console.error(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const InputField = ({ label, name, icon: Icon, type = "number", step = "0.01", placeholder }) => (
    <div className="space-y-2">
      <label className="flex items-center text-sm font-medium text-text-primary">
        <Icon className="w-4 h-4 mr-2 text-text-secondary" />
        {label}
      </label>
      <input
        type={type}
        step={step}
        placeholder={placeholder}
        {...register(name, { required: true, valueAsNumber: true })}
        className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
      />
      {errors[name] && <span className="text-xs text-error">This field is required</span>}
    </div>
  );

  return (
    <div className="max-w-5xl mx-auto py-6 space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-text-primary mb-2">Crop Recommendation</h1>
        <p className="text-text-secondary">Enter your soil and environmental parameters to get the best crop suggestion.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-card p-6 md:p-8 rounded-xl shadow-sm border border-border">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <InputField label="Nitrogen (N)" name="nitrogen" icon={Activity} placeholder="e.g. 90" />
              <InputField label="Phosphorus (P)" name="phosphorous" icon={Activity} placeholder="e.g. 42" />
              <InputField label="Potassium (K)" name="potassium" icon={Activity} placeholder="e.g. 43" />
              <InputField label="pH Level" name="ph" icon={Beaker} placeholder="e.g. 6.5" />
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
                {isSubmitting ? 'Analyzing...' : 'Get Recommendation'}
              </button>
            </div>
          </form>
        </div>

        <div className="lg:col-span-1">
          <AnimatePresence>
            {result && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-primary text-white p-6 md:p-8 rounded-xl shadow-lg h-full flex flex-col justify-center"
              >
                <div className="text-center space-y-4">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-white/20 mb-2">
                    <CheckCircle2 className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-sm font-medium text-green-100 uppercase tracking-wider">Recommended Crop</h3>
                  <h2 className="text-4xl font-bold">{result.crop}</h2>
                  
                  <div className="inline-block bg-white/20 rounded-full px-4 py-1 text-sm font-semibold">
                    {result.confidence}% Confidence
                  </div>
                  
                  <p className="text-green-50 mt-4 text-sm leading-relaxed">
                    {result.message}
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
