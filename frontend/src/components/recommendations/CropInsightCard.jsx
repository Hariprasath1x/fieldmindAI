import { CheckCircle2, Info } from 'lucide-react';
import { SeasonBadge, WaterRequirementBadge, DifficultyBadge, SuitabilityBadge } from './Badges';

export const CropInsightCard = ({ crop }) => {
  return (
    <div className="bg-primary text-white p-6 md:p-8 rounded-xl shadow-lg border-4 border-white outline outline-1 outline-border relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute -right-10 -top-10 opacity-10">
        <CheckCircle2 className="w-64 h-64" />
      </div>

      <div className="relative z-10">
        <div className="flex justify-between items-start mb-6">
          <div className="flex items-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-white/20 mr-4">
              <CheckCircle2 className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-green-100 uppercase tracking-widest mb-1">Top Recommendation</h3>
              <h2 className="text-4xl font-black capitalize tracking-tight">{crop.crop}</h2>
            </div>
          </div>
          <SuitabilityBadge score={crop.confidence} isTop={true} />
        </div>

        <p className="text-green-50 text-base md:text-lg leading-relaxed font-medium mb-6 max-w-2xl">
          {crop.description}
        </p>

        <div className="flex flex-wrap gap-3 mb-6 bg-white/10 p-4 rounded-xl border border-white/20">
          <SeasonBadge season={crop.season} />
          <WaterRequirementBadge level={crop.water_requirement} range={crop.water_range} />
          <DifficultyBadge difficulty={crop.difficulty} />
        </div>

        {crop.reasons && crop.reasons.length > 0 && (
          <div className="bg-black/10 p-4 rounded-lg border border-black/5">
            <h4 className="text-xs font-bold uppercase tracking-wider text-green-100 mb-2 flex items-center">
              <Info className="w-3.5 h-3.5 mr-1.5" />
              Why this crop?
            </h4>
            <ul className="space-y-1.5">
              {crop.reasons.map((reason, i) => (
                <li key={i} className="text-sm text-green-50 flex items-start">
                  <span className="mr-2 text-green-200 mt-0.5">•</span>
                  <span className="leading-snug">{reason}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};
