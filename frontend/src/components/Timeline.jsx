import { CheckCircle2, Circle, Loader2 } from 'lucide-react';

export default function Timeline({ currentStep, steps }) {
  return (
    <div className="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-gray-200 before:to-transparent">
      {steps.map((step, index) => {
        const isCompleted = currentStep > index;
        const isCurrent = currentStep === index;

        return (
          <div key={index} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
            <div className="flex items-center justify-center w-10 h-10 rounded-full border-2 bg-white shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow-sm relative z-10 
              ${isCompleted ? 'border-primary text-primary' : isCurrent ? 'border-secondary text-secondary' : 'border-gray-200 text-gray-400'}">
              {isCompleted ? (
                <CheckCircle2 className="h-6 w-6 text-success" />
              ) : isCurrent ? (
                <Loader2 className="h-5 w-5 animate-spin text-secondary" />
              ) : (
                <Circle className="h-5 w-5 text-gray-300" />
              )}
            </div>
            <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-lg border border-border bg-card shadow-sm">
              <h3 className={`font-semibold text-base ${isCompleted || isCurrent ? 'text-text-primary' : 'text-gray-400'}`}>
                {step.title}
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
