import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import UploadBox from '../components/UploadBox';
import Timeline from '../components/Timeline';
import { ShieldCheck, AlertTriangle, Info, Play, CheckCircle } from 'lucide-react';
// import { verifyLeaf, detectDisease } from '../services/api';

const steps = [
  { title: 'Upload Image', description: 'Upload a clear image of a plant leaf.' },
  { title: 'Leaf Verification', description: 'Checking if the image is a valid leaf.' },
  { title: 'Disease Classification', description: 'Identifying the specific disease.' },
  { title: 'Severity Analysis', description: 'Assessing how severely the plant is affected.' },
  { title: 'Recommendation', description: 'Generating treatment suggestions.' }
];

export default function DiseaseDetection() {
  const [currentStep, setCurrentStep] = useState(0);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleUpload = (uploadedFile, imagePreview) => {
    setFile(uploadedFile);
    setPreview(imagePreview);
    if (uploadedFile) {
      setCurrentStep(1);
      setError(null);
    } else {
      setCurrentStep(0);
      setResults(null);
    }
  };

  const startDetection = async () => {
    if (!file) return;
    setIsProcessing(true);
    setError(null);
    
    try {
      // Step 1: Verification
      setCurrentStep(1);
      await new Promise(resolve => setTimeout(resolve, 1500)); // Mock API delay
      // const verification = await verifyLeaf(file);
      
      // Step 2: Classification
      setCurrentStep(2);
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Step 3: Severity
      setCurrentStep(3);
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Step 4: Recommendation & Final Results
      setCurrentStep(4);
      
      // Mock results
      setResults({
        disease: 'Apple Scab',
        confidence: 96,
        severity: 'Moderate',
        affectedCrop: 'Apple',
        description: 'Apple scab is a disease of Malus trees, such as apple trees, caused by the ascomycete fungus Venturia inaequalis.',
        preventive: ['Prune trees to allow air circulation', 'Rake up and destroy fallen leaves'],
        treatment: ['Apply fungicide when leaves begin to emerge'],
      });
      setCurrentStep(5); // Completed
    } catch (err) {
      setError('An error occurred during processing. Please try again.');
      setCurrentStep(1); // Reset to start
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-6 space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-text-primary mb-2">Disease Detection</h1>
        <p className="text-text-secondary">Upload a clear image of a crop leaf to identify diseases and get treatment recommendations.</p>
      </div>

      <div className="bg-card p-6 md:p-8 rounded-xl shadow-sm border border-border">
        <UploadBox onUpload={handleUpload} isLoading={isProcessing} />
        
        {file && !isProcessing && currentStep === 1 && !results && (
          <div className="mt-6 flex justify-center">
            <button
              onClick={startDetection}
              className="flex items-center px-6 py-3 bg-primary text-white font-medium rounded-md shadow-sm hover:bg-green-800 transition-colors"
            >
              <Play className="mr-2 h-5 w-5" />
              Start Analysis
            </button>
          </div>
        )}

        {error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-md flex items-start text-error">
            <AlertTriangle className="h-5 w-5 mr-3 shrink-0 mt-0.5" />
            <p>{error}</p>
          </div>
        )}
      </div>

      {currentStep > 0 && (
        <div className="bg-card p-6 md:p-8 rounded-xl shadow-sm border border-border">
          <h2 className="text-xl font-bold text-text-primary mb-6">Processing Steps</h2>
          <Timeline currentStep={currentStep} steps={steps} />
        </div>
      )}

      <AnimatePresence>
        {results && currentStep === 5 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Disease Result Card */}
            <div className="bg-card p-6 md:p-8 rounded-xl shadow-sm border border-border">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-text-primary">{results.disease}</h2>
                <div className="flex items-center space-x-2 bg-green-50 text-primary px-3 py-1 rounded-full border border-green-200">
                  <ShieldCheck className="h-4 w-4" />
                  <span className="font-semibold">{results.confidence}% Match</span>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                  <h3 className="text-sm font-medium text-text-secondary mb-1">Affected Crop</h3>
                  <p className="text-text-primary font-medium">{results.affectedCrop}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-text-secondary mb-1">Severity Level</h3>
                  <div className="flex items-center">
                    <span className="text-warning font-medium mr-2">{results.severity}</span>
                    <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full bg-warning w-2/3"></div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className="text-sm font-medium text-text-secondary mb-2">Description</h3>
                <p className="text-text-primary leading-relaxed">{results.description}</p>
              </div>
            </div>

            {/* Recommendation Card */}
            <div className="bg-card p-6 md:p-8 rounded-xl shadow-sm border border-border">
               <h2 className="text-xl font-bold text-text-primary mb-6 flex items-center">
                 <Info className="h-5 w-5 mr-2 text-secondary" />
                 Treatment & Recommendations
               </h2>
               
               <div className="space-y-6">
                 <div>
                   <h3 className="text-lg font-semibold text-text-primary mb-3">Preventive Measures</h3>
                   <ul className="space-y-2">
                     {results.preventive.map((item, idx) => (
                       <li key={idx} className="flex items-start">
                         <CheckCircle className="h-5 w-5 text-success mr-3 shrink-0" />
                         <span className="text-text-secondary">{item}</span>
                       </li>
                     ))}
                   </ul>
                 </div>
                 
                 <div>
                   <h3 className="text-lg font-semibold text-text-primary mb-3">Suggested Treatment</h3>
                   <ul className="space-y-2">
                     {results.treatment.map((item, idx) => (
                       <li key={idx} className="flex items-start">
                         <CheckCircle className="h-5 w-5 text-success mr-3 shrink-0" />
                         <span className="text-text-secondary">{item}</span>
                       </li>
                     ))}
                   </ul>
                 </div>
               </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
