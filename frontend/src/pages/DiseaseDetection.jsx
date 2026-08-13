import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import UploadBox from '../components/UploadBox';
import Timeline from '../components/Timeline';
import { useAuth } from '../hooks/useAuth';
import {
  ShieldCheck,
  AlertTriangle,
  Info,
  Play,
  CheckCircle,
  ThumbsUp,
  ThumbsDown,
  Loader2,
  MapPin,
} from 'lucide-react';
import { submitInference, pollInferenceResult, submitFeedback } from '../services/diagnosisApi';

// ── Pipeline steps ─────────────────────────────────────────────────────────────
const STEPS = [
  { title: 'Upload Image', description: 'Upload a clear image of a plant leaf.' },
  { title: 'Validating Image', description: 'Checking image quality and format.' },
  { title: 'Leaf Verification', description: 'Verifying the image contains a leaf.' },
  { title: 'Disease Classification', description: 'Identifying the specific disease.' },
  { title: 'Severity Analysis', description: 'Assessing affected area and severity.' },
  { title: 'Diagnosis Ready', description: 'Generating treatment recommendations.' },
];

// ── Stage to step index mapping ─────────────────────────────────────────────────
const STAGE_STEP = {
  queued: 1,
  processing: 1,
  validating_image: 1,
  verifying_leaf: 2,
  classifying_disease: 3,
  analysing_severity: 4,
  completed: 5,
  failed: 5,
};

const CONFIDENCE_COLORS = {
  high: 'bg-green-50 text-green-800 border-green-200',
  medium: 'bg-yellow-50 text-yellow-800 border-yellow-200',
  low: 'bg-red-50 text-red-800 border-red-200',
};

const CONFIDENCE_LABELS = {
  high: 'High Confidence',
  medium: 'Moderate Confidence',
  low: 'Low Confidence',
};

// ── Feedback widget ────────────────────────────────────────────────────────────
function FeedbackWidget({ diagnosisId, predictedLabel, userId }) {
  const [submitted, setSubmitted] = useState(false);
  const [selectedType, setSelectedType] = useState(null);
  const [actualLabel, setActualLabel] = useState('');
  const [loading, setLoading] = useState(false);

  if (!diagnosisId || !userId) return null;

  const handleSubmit = async (type) => {
    setSelectedType(type);
    setLoading(true);
    try {
      await submitFeedback({
        predictionId: diagnosisId,
        userId,
        predictedLabel,
        actualLabel: type === 'incorrect' ? actualLabel || null : null,
        feedbackType: type,
      });
      setSubmitted(true);
    } catch {
      // Feedback failure is non-critical — don't block the user
      setSubmitted(true);
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700 flex items-center gap-2">
        <CheckCircle className="h-4 w-4 shrink-0" />
        Thank you for your feedback — it helps improve FieldMind.
      </div>
    );
  }

  return (
    <div className="mt-6 border-t border-border pt-5">
      <p className="text-sm font-medium text-text-secondary mb-3">Was this diagnosis helpful?</p>
      <div className="flex gap-3 flex-wrap">
        <button
          onClick={() => handleSubmit('correct')}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-md bg-green-50 text-green-700 border border-green-200 text-sm font-medium hover:bg-green-100 transition-colors disabled:opacity-50"
        >
          <ThumbsUp className="h-4 w-4" />
          Correct
        </button>
        <button
          onClick={() => setSelectedType('incorrect_form')}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-md bg-red-50 text-red-600 border border-red-200 text-sm font-medium hover:bg-red-100 transition-colors disabled:opacity-50"
        >
          <ThumbsDown className="h-4 w-4" />
          Incorrect
        </button>
      </div>

      {selectedType === 'incorrect_form' && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mt-3 flex gap-2"
        >
          <input
            type="text"
            placeholder="What is the actual disease? (optional)"
            value={actualLabel}
            onChange={(e) => setActualLabel(e.target.value)}
            className="flex-1 px-3 py-2 text-sm rounded-md border border-border bg-background-app text-text-primary placeholder:text-text-secondary focus:outline-none focus:ring-1 focus:ring-primary"
          />
          <button
            onClick={() => handleSubmit('incorrect')}
            disabled={loading}
            className="px-4 py-2 bg-primary text-white text-sm rounded-md hover:bg-green-800 disabled:opacity-50 transition-colors"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Submit'}
          </button>
        </motion.div>
      )}
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function DiseaseDetection() {
  const { user } = useAuth();
  const [currentStep, setCurrentStep] = useState(0);
  const [file, setFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [plantId, setPlantId] = useState('');

  const handleUpload = (uploadedFile) => {
    setFile(uploadedFile);
    setResults(null);
    setError(null);
    if (uploadedFile) setCurrentStep(1);
    else setCurrentStep(0);
  };

  const startDetection = async () => {
    if (!file) return;
    setIsProcessing(true);
    setError(null);
    setCurrentStep(1);

    try {
      // Submit job
      const job = await submitInference(file, {
        plantId: plantId || null,
        userId: user?.uid || null,
      });

      if (job.status === 'completed' || job.status === 'failed') {
        // Synchronous fallback — already done
        if (job.status === 'failed') {
          setError('Disease analysis failed. Please try again.');
        } else {
          // Fetch result via status endpoint
          // The job is done; fetch the result
          const { getInferenceStatus } = await import('../services/diagnosisApi');
          const statusData = await getInferenceStatus(job.job_id, user?.uid || null);
          handleResult(statusData);
        }
        return;
      }

      // Polling mode
      const finalData = await pollInferenceResult(
        job.job_id,
        (statusData) => {
          const stage = statusData.result?.stage || statusData.status;
          const step = STAGE_STEP[stage] ?? 1;
          setCurrentStep(step);
        },
        { userId: user?.uid || null }
      );

      handleResult(finalData);
    } catch (err) {
      const msg = err?.response?.data?.error?.message || err?.response?.data?.detail || err.message;
      setError(msg || 'An error occurred. Please try again.');
      setCurrentStep(1);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleResult = (statusData) => {
    const result = statusData.result;
    if (!result || !result.success) {
      // Validation / leaf rejection
      const userMsg =
        result?.user_message ||
        result?.message ||
        statusData.error ||
        'Analysis failed. Please upload a clearer leaf image.';
      setError(userMsg);
      setCurrentStep(1);
      return;
    }

    setResults(result);
    setCurrentStep(5);
  };

  const confidenceLevel = results?.confidence_level || 'low';
  const confidencePct = results ? Math.round(results.confidence * 100) : 0;

  return (
    <div className="max-w-4xl mx-auto py-6 space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-text-primary mb-2">Disease Detection</h1>
        <p className="text-text-secondary">
          Upload a clear image of a crop leaf to identify diseases and get treatment recommendations.
        </p>
      </div>

      {/* Upload Card */}
      <div className="bg-card p-6 md:p-8 rounded-xl shadow-sm border border-border">
        <UploadBox onUpload={handleUpload} isLoading={isProcessing} />

        {/* Plant ID (optional) */}
        {file && !isProcessing && !results && (
          <div className="mt-4">
            <label className="block text-sm font-medium text-text-secondary mb-1">
              Plant / Field ID <span className="text-text-secondary font-normal">(optional — used for progression tracking)</span>
            </label>
            <input
              type="text"
              value={plantId}
              onChange={(e) => setPlantId(e.target.value)}
              placeholder="e.g. field-A-tomato-row-3"
              className="w-full px-3 py-2 text-sm rounded-md border border-border bg-background-app text-text-primary placeholder:text-text-secondary focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        )}

        {file && !isProcessing && currentStep >= 1 && !results && (
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

      {/* Processing Timeline */}
      {currentStep > 0 && (
        <div className="bg-card p-6 md:p-8 rounded-xl shadow-sm border border-border">
          <h2 className="text-xl font-bold text-text-primary mb-6">
            {isProcessing ? 'Analysing...' : 'Processing Steps'}
          </h2>
          <Timeline currentStep={currentStep} steps={STEPS} />
        </div>
      )}

      {/* Results */}
      <AnimatePresence>
        {results && currentStep === 5 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Confidence banner */}
            {confidenceLevel !== 'high' && (
              <div className={`p-4 rounded-lg border flex items-start gap-3 ${CONFIDENCE_COLORS[confidenceLevel]}`}>
                <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />
                <p className="text-sm">
                  {results.user_message ||
                    (confidenceLevel === 'medium'
                      ? 'Moderate confidence result. Upload a clearer image for a definitive diagnosis.'
                      : 'Low confidence — FieldMind could not reliably identify this disease. Please upload a clearer image.')}
                </p>
              </div>
            )}

            {/* Disease Result Card */}
            <div className="bg-card p-6 md:p-8 rounded-xl shadow-sm border border-border">
              <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
                <h2 className="text-2xl font-bold text-text-primary">
                  {results.disease?.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                </h2>
                <span
                  className={`flex items-center gap-1 px-3 py-1 rounded-full border text-sm font-semibold ${CONFIDENCE_COLORS[confidenceLevel]}`}
                >
                  <ShieldCheck className="h-4 w-4" />
                  {CONFIDENCE_LABELS[confidenceLevel]} · {confidencePct}%
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                {results.crop && (
                  <div>
                    <h3 className="text-xs font-medium text-text-secondary uppercase tracking-wide mb-1">
                      Crop
                    </h3>
                    <p className="text-text-primary font-medium">{results.crop}</p>
                  </div>
                )}
                {results.severity?.affected_area_pct != null && (
                  <div>
                    <h3 className="text-xs font-medium text-text-secondary uppercase tracking-wide mb-1">
                      Estimated Affected Area
                    </h3>
                    <p className="text-text-primary font-medium">
                      {results.severity.affected_area_pct}%
                      <span className="text-xs text-text-secondary ml-1">(bbox approx.)</span>
                    </p>
                  </div>
                )}
                {results.image_quality?.blur_score != null && (
                  <div>
                    <h3 className="text-xs font-medium text-text-secondary uppercase tracking-wide mb-1">
                      Image Sharpness
                    </h3>
                    <p className="text-text-primary font-medium">
                      {results.image_quality.blur_score.toFixed(1)}
                    </p>
                  </div>
                )}
              </div>

              {/* Top predictions */}
              {results.top_predictions && results.top_predictions.length > 1 && (
                <div className="mb-6">
                  <h3 className="text-sm font-medium text-text-secondary mb-2">Top Predictions</h3>
                  <div className="space-y-2">
                    {results.top_predictions.map((pred, idx) => (
                      <div key={idx} className="flex items-center gap-3">
                        <span className="text-sm text-text-primary w-48 truncate">
                          {pred.label.replace(/_/g, ' ')}
                        </span>
                        <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary rounded-full transition-all"
                            style={{ width: `${Math.round(pred.confidence * 100)}%` }}
                          />
                        </div>
                        <span className="text-xs text-text-secondary w-10 text-right">
                          {Math.round(pred.confidence * 100)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendation */}
              <div className="p-4 bg-background-app rounded-lg border border-border">
                <div className="flex items-start gap-2">
                  <Info className="h-4 w-4 text-secondary shrink-0 mt-0.5" />
                  <p className="text-sm text-text-primary leading-relaxed">{results.recommendation}</p>
                </div>
              </div>

              {/* Feedback */}
              <FeedbackWidget
                diagnosisId={results.diagnosis_id}
                predictedLabel={results.disease}
                userId={user?.uid}
              />
            </div>

            {/* Severity Card */}
            {results.severity?.detections?.length > 0 && (
              <div className="bg-card p-6 rounded-xl shadow-sm border border-border">
                <h2 className="text-xl font-bold text-text-primary mb-4 flex items-center gap-2">
                  <MapPin className="h-5 w-5 text-secondary" />
                  Severity Detections
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {results.severity.detections.map((det, idx) => (
                    <div key={idx} className="p-3 border border-border rounded-lg bg-background-app">
                      <p className="font-medium text-text-primary capitalize">{det.label}</p>
                      <p className="text-sm text-text-secondary">
                        Confidence: {Math.round(det.confidence * 100)}%
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
