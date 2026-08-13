import { Droplets, Calendar, Activity } from 'lucide-react';

export const SeasonBadge = ({ season }) => (
  <div className="flex items-center space-x-1.5 bg-green-50 text-green-700 px-2.5 py-1 rounded-full text-xs font-semibold border border-green-200">
    <Calendar className="w-3.5 h-3.5" />
    <span>{season}</span>
  </div>
);

export const WaterRequirementBadge = ({ level, range }) => {
  const getColors = () => {
    switch (level.toLowerCase()) {
      case 'low': return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'medium': return 'bg-cyan-50 text-cyan-700 border-cyan-200';
      case 'high': return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      default: return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  return (
    <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${getColors()}`} title={range}>
      <Droplets className="w-3.5 h-3.5" />
      <span>{level} Water</span>
    </div>
  );
};

export const DifficultyBadge = ({ difficulty }) => {
  const getColors = () => {
    switch (difficulty.toLowerCase()) {
      case 'easy': return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'moderate': return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'advanced': return 'bg-red-50 text-red-700 border-red-200';
      default: return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  return (
    <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${getColors()}`}>
      <Activity className="w-3.5 h-3.5" />
      <span>{difficulty}</span>
    </div>
  );
};

export const SuitabilityBadge = ({ score, isTop }) => (
  <div className={`flex flex-col items-center justify-center ${isTop ? 'bg-white/20 text-white' : 'bg-primary/10 text-primary'} px-3 py-1.5 rounded-lg`}>
    <span className="text-[10px] font-bold uppercase tracking-wider opacity-90 leading-tight">Score</span>
    <div className="flex items-baseline space-x-0.5">
      <span className="text-xl font-black leading-none">{Math.round(score)}</span>
      <span className="text-xs font-medium opacity-75">/100</span>
    </div>
  </div>
);
