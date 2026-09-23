import { MapPin, Thermometer, Droplets, CloudRain, Beaker, Sprout } from 'lucide-react';
import { motion } from 'framer-motion';

export const FarmConditionsCard = ({ details, formValues }) => {
  if (!details && !formValues) return null;

  return (
    <motion.div 
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-card border-2 border-primary/20 rounded-xl p-4 sm:p-5 mb-8 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
    >
      <div className="flex-1">
        <h3 className="text-sm font-bold text-text-secondary uppercase tracking-wider mb-3 flex items-center">
          <Sprout className="w-4 h-4 mr-2" />
          Current Farm Conditions
        </h3>
        
        {details && (
          <div className="flex items-start text-sm text-text-primary mb-4 bg-primary/5 p-2 rounded-lg border border-primary/10">
            <MapPin className="w-4 h-4 text-primary shrink-0 mr-2 mt-0.5" />
            <span className="leading-tight">{details.formatted_address || `${details.district}, ${details.state}`}</span>
          </div>
        )}

        <div className="flex flex-wrap gap-x-6 gap-y-3">
          <div className="flex items-center space-x-2">
            <Thermometer className="w-4 h-4 text-orange-500" />
            <div className="flex flex-col">
              <span className="text-[10px] font-semibold text-text-secondary uppercase">Temp</span>
              <span className="text-sm font-bold text-text-primary">{formValues.temperature}°C</span>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Droplets className="w-4 h-4 text-blue-500" />
            <div className="flex flex-col">
              <span className="text-[10px] font-semibold text-text-secondary uppercase">Humidity</span>
              <span className="text-sm font-bold text-text-primary">{formValues.humidity}%</span>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <CloudRain className="w-4 h-4 text-indigo-500" />
            <div className="flex flex-col">
              <span className="text-[10px] font-semibold text-text-secondary uppercase">Rainfall</span>
              <span className="text-sm font-bold text-text-primary">{formValues.rainfall} mm</span>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <Beaker className="w-4 h-4 text-emerald-500" />
            <div className="flex flex-col">
              <span className="text-[10px] font-semibold text-text-secondary uppercase">Soil pH</span>
              <span className="text-sm font-bold text-text-primary">{formValues.ph}</span>
            </div>
          </div>
        </div>
      </div>
      
      <div className="bg-gray-50 border border-border p-3 rounded-lg flex space-x-4 w-full md:w-auto">
        <div className="text-center">
          <div className="text-[10px] font-bold text-text-secondary uppercase">N</div>
          <div className="font-mono font-bold text-primary">{formValues.nitrogen}</div>
        </div>
        <div className="text-center">
          <div className="text-[10px] font-bold text-text-secondary uppercase">P</div>
          <div className="font-mono font-bold text-primary">{formValues.phosphorous}</div>
        </div>
        <div className="text-center">
          <div className="text-[10px] font-bold text-text-secondary uppercase">K</div>
          <div className="font-mono font-bold text-primary">{formValues.potassium}</div>
        </div>
      </div>
    </motion.div>
  );
};
