import { AlertCircle } from 'lucide-react';
import { SeasonBadge, WaterRequirementBadge, DifficultyBadge, SuitabilityBadge } from './Badges';

export const AlternativeCropCard = ({ crop, index }) => {
  return (
    <div className="bg-card border-2 border-border p-5 rounded-xl shadow-sm hover:border-primary/30 transition-colors">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h4 className="text-[10px] font-bold text-text-secondary uppercase tracking-widest mb-1">
            Alternative Option #{index}
          </h4>
          <h2 className="text-2xl font-bold text-primary capitalize">{crop.crop}</h2>
        </div>
        <SuitabilityBadge score={crop.confidence} isTop={false} />
      </div>

      <div className="flex flex-wrap gap-2 mb-5">
        <SeasonBadge season={crop.season} />
        <WaterRequirementBadge level={crop.water_requirement} range={crop.water_range} />
        <DifficultyBadge difficulty={crop.difficulty} />
      </div>

      {crop.reasons && crop.reasons.length > 0 && (
        <div className="bg-orange-50/50 p-4 rounded-lg border border-orange-100/50">
          <h4 className="text-xs font-bold uppercase tracking-wider text-orange-800 mb-2 flex items-center">
            <AlertCircle className="w-3.5 h-3.5 mr-1.5 text-orange-600" />
            Lower suitability because
          </h4>
          <ul className="space-y-1.5">
            {crop.reasons.map((reason, i) => (
              <li key={i} className="text-sm text-orange-900/80 flex items-start">
                <span className="mr-2 text-orange-400 mt-0.5">•</span>
                <span className="leading-snug">{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
