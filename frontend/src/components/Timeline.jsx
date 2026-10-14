import { CheckCircle2, Circle, Loader2, AlertTriangle } from 'lucide-react';

export default function Timeline({ currentStep, steps, failedStep = null, warningStep = null }) {
  return (
    <div className="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-gray-200 before:to-transparent">
      {steps.map((step, index) => {
        const isCompleted = currentStep > index && failedStep !== index && warningStep !== index;
        const isCurrent = currentStep === index && failedStep === null && warningStep === null;
        const isFailed = failedStep === index;
        const isWarning = warningStep === index;
        const isSkipped = (failedStep !== null && index > failedStep) || (warningStep !== null && index > warningStep);

        return (
          <div key={index} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
            <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 bg-white shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow-sm relative z-10 
              ${isCompleted ? 'border-primary text-primary' : isCurrent ? 'border-secondary text-secondary' : isFailed ? 'border-error text-error bg-red-50' : isWarning ? 'border-yellow-500 text-yellow-600 bg-yellow-50' : 'border-gray-200 text-gray-400'}`}>
              {isCompleted ? (
                <CheckCircle2 className="h-6 w-6 text-success" />
              ) : isFailed ? (
                <div className="text-error font-bold text-lg">×</div>
              ) : isWarning ? (
                <AlertTriangle className="h-5 w-5 text-yellow-600" />
              ) : isCurrent ? (
                <Loader2 className="h-5 w-5 animate-spin text-secondary" />
              ) : (
                <Circle className="h-5 w-5 text-gray-300" />
              )}
            </div>
            <div className={`w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-lg border border-border shadow-sm ${isSkipped ? 'bg-gray-50 opacity-60' : isFailed ? 'bg-red-50/50' : isWarning ? 'bg-yellow-50/50' : 'bg-card'}`}>
              <h3 className={`font-semibold text-base ${isCompleted || isCurrent ? 'text-text-primary' : isFailed ? 'text-error' : isWarning ? 'text-yellow-700' : 'text-gray-400'}`}>
                {step.title} {isFailed && <span className="text-sm font-normal text-error ml-2">— Failed</span>}
                {isWarning && <span className="text-sm font-normal text-yellow-700 ml-2">— Uncertain</span>}
                {isSkipped && <span className="text-sm font-normal text-gray-400 ml-2">— Skipped</span>}
              </h3>
              {step.description && (
                <p className="text-sm text-text-secondary mt-1">{step.description}</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
