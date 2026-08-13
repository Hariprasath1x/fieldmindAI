/**
 * Diagnosis API service.
 * Handles disease inference submission, polling, history, and feedback.
 */
import apiClient from './api';

const BASE = '/api';

// ── Inference ─────────────────────────────────────────────────────────────────

/**
 * Submit an image for async disease analysis.
 * Returns { job_id, status, request_id }.
 */
export const submitInference = async (
  imageFile,
  { plantId = null, fieldId = null, userId = null } = {}
) => {
  const formData = new FormData();
  formData.append('file', imageFile);
  if (plantId) formData.append('plant_id', plantId);
  if (fieldId) formData.append('field_id', fieldId);

  const headers = { 'Content-Type': 'multipart/form-data' };
  if (userId) headers['X-User-ID'] = userId;

  const response = await apiClient.post(`${BASE}/inference/submit`, formData, { headers });
  return response.data;
};

/**
 * Poll inference job status.
 * Returns { job_id, status, result, error, created_at, updated_at }.
 */
export const getInferenceStatus = async (jobId, userId = null) => {
  const headers = {};
  if (userId) headers['X-User-ID'] = userId;
  const response = await apiClient.get(`${BASE}/inference/${jobId}`, { headers });
  return response.data;
};

/**
 * Poll until job reaches a terminal state (completed / failed).
 * Calls onProgress with each status update.
 *
 * @param {string} jobId
 * @param {Function} onProgress  (statusData) => void
 * @param {Object} options
 * @param {number} options.intervalMs   Polling interval in ms (default 1500)
 * @param {number} options.maxAttempts  Maximum polling attempts (default 40)
 * @param {string|null} options.userId
 */
export const pollInferenceResult = async (
  jobId,
  onProgress,
  { intervalMs = 1500, maxAttempts = 40, userId = null } = {}
) => {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    await new Promise((r) => setTimeout(r, intervalMs));
    const statusData = await getInferenceStatus(jobId, userId);
    if (onProgress) onProgress(statusData);

    if (statusData.status === 'completed' || statusData.status === 'failed') {
      return statusData;
    }
  }
  throw new Error('Inference job timed out. Please try again.');
};

// ── Diagnosis History ─────────────────────────────────────────────────────────

export const getDiagnosisHistory = async (userId, { limit = 20, plantId = null } = {}) => {
  const params = new URLSearchParams({ limit });
  if (plantId) params.append('plant_id', plantId);
  const response = await apiClient.get(`${BASE}/diagnosis/history?${params}`, {
    headers: { 'X-User-ID': userId },
  });
  return response.data;
};

export const getDiagnosis = async (diagnosisId, userId) => {
  const response = await apiClient.get(`${BASE}/diagnosis/${diagnosisId}`, {
    headers: { 'X-User-ID': userId },
  });
  return response.data;
};

export const getDiagnosisProgression = async (diagnosisId, userId) => {
  const response = await apiClient.get(`${BASE}/diagnosis/${diagnosisId}/progression`, {
    headers: { 'X-User-ID': userId },
  });
  return response.data;
};

// ── Feedback ──────────────────────────────────────────────────────────────────

export const submitFeedback = async ({ predictionId, userId, predictedLabel, actualLabel, feedbackType }) => {
  const response = await apiClient.post(
    `${BASE}/feedback`,
    {
      prediction_id: predictionId,
      user_id: userId,
      predicted_label: predictedLabel,
      actual_label: actualLabel || null,
      feedback_type: feedbackType,
    },
    { headers: { 'X-User-ID': userId } }
  );
  return response.data;
};

export const getFeedbackDashboard = async (userId) => {
  const response = await apiClient.get(`${BASE}/feedback/dashboard`, {
    headers: { 'X-User-ID': userId },
  });
  return response.data;
};

// ── ML Dashboard ──────────────────────────────────────────────────────────────

export const getMLDashboard = async () => {
  const response = await apiClient.get(`${BASE}/ml/dashboard`);
  return response.data;
};

export const getLatestEvaluation = async (modelName) => {
  const response = await apiClient.get(`${BASE}/ml/evaluation/latest?model=${modelName}`);
  return response.data;
};
