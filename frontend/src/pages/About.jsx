import { Cpu, Database, Code2, Layers, AlertCircle } from 'lucide-react';

const PIPELINE_STEPS = [
  { step: '1', label: 'Image Upload', detail: 'User uploads a plant leaf photograph' },
  { step: '2', label: 'Image Validation', detail: 'Check format, size, and sharpness (Laplacian variance)' },
  { step: '3', label: 'Leaf Verification', detail: 'ONNX MobileNetV3 binary classifier — leaf vs. non-leaf' },
  { step: '4', label: 'Disease Classification', detail: 'ONNX EfficientNet classifier across 20+ disease classes' },
  { step: '5', label: 'Severity Detection', detail: 'YOLOv8 bounding-box localisation of diseased regions' },
  { step: '6', label: 'Recommendation', detail: 'Rule-based treatment guidance from classification output' },
  { step: '7', label: 'Persistence', detail: 'Results stored per-user in Firestore for history tracking' },
];

const TECH = [
  {
    icon: Code2,
    label: 'Frontend',
    items: ['React 19', 'Vite', 'Tailwind CSS', 'Framer Motion', 'Axios', 'React Hook Form'],
  },
  {
    icon: Layers,
    label: 'Backend',
    items: ['FastAPI (Python)', 'Pydantic', 'ONNX Runtime', 'OpenCV', 'Pillow', 'Scikit-learn'],
  },
  {
    icon: Cpu,
    label: 'ML / AI',
    items: ['PyTorch (training)', 'ONNX (inference)', 'MobileNetV3 (leaf verifier)', 'EfficientNet (disease classifier)', 'YOLOv8 (severity detection)', 'RandomForest (crop recommendation)'],
  },
  {
    icon: Database,
    label: 'Infrastructure',
    items: ['Firebase Authentication', 'Google Firestore', 'Firebase Admin SDK', 'Redis + RQ (async workers)'],
  },
];

export default function About() {
  return (
    <div className="max-w-4xl mx-auto space-y-8 py-6">
      <h1 className="text-3xl font-bold text-text-primary">About FieldMind</h1>

      {/* Overview */}
      <div className="bg-card rounded-xl shadow-sm border border-border p-6 sm:p-8">
        <h2 className="text-xl font-semibold text-text-primary mb-3">What is FieldMind?</h2>
        <p className="text-text-secondary leading-relaxed mb-4">
          FieldMind is a full-stack AI agricultural assistant built as a B.Tech final-year student project.
          It demonstrates end-to-end integration of Deep Learning, Computer Vision, and modern web technologies
          to help farmers and researchers identify crop diseases, get crop recommendations, and manage farm
          resources through an online marketplace.
        </p>
        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start gap-2 text-sm text-yellow-800">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5 text-yellow-600" />
          <span>
            <strong>Academic Project Disclaimer:</strong> AI predictions are for demonstration purposes.
            Disease identification may be incorrect. Always verify with a certified agronomist before taking
            any agricultural decisions.
          </span>
        </div>
      </div>

      {/* ML Pipeline */}
      <div className="bg-card rounded-xl shadow-sm border border-border p-6 sm:p-8">
        <h2 className="text-xl font-semibold text-text-primary mb-6">AI Inference Pipeline</h2>
        <div className="space-y-3">
          {PIPELINE_STEPS.map(({ step, label, detail }) => (
            <div key={step} className="flex items-start gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-sm">
                {step}
              </div>
              <div className="pt-0.5">
                <p className="font-medium text-text-primary">{label}</p>
                <p className="text-sm text-text-secondary">{detail}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Technology Stack */}
      <div className="bg-card rounded-xl shadow-sm border border-border p-6 sm:p-8">
        <h2 className="text-xl font-semibold text-text-primary mb-6">Technology Stack</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {TECH.map(({ icon: Icon, label, items }) => (
            <div key={label} className="p-4 bg-background-app rounded-lg border border-border">
              <div className="flex items-center gap-2 mb-3">
                <Icon className="h-5 w-5 text-primary" />
                <h3 className="font-semibold text-text-primary">{label}</h3>
              </div>
              <ul className="space-y-1">
                {items.map(item => (
                  <li key={item} className="text-sm text-text-secondary flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-primary/40 flex-shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Key Features */}
      <div className="bg-card rounded-xl shadow-sm border border-border p-6 sm:p-8">
        <h2 className="text-xl font-semibold text-text-primary mb-4">Key Features</h2>
        <ul className="space-y-2 text-text-secondary text-sm">
          <li>🌿 <strong className="text-text-primary">Crop Disease Detection</strong> — Upload a leaf photo → get disease classification, severity heatmap, and treatment recommendation</li>
          <li>🌾 <strong className="text-text-primary">Crop Recommendation</strong> — Input soil NPK/pH and weather parameters → ranked crop suggestions with seasonal suitability</li>
          <li>📊 <strong className="text-text-primary">Diagnosis History</strong> — Per-user history with progression tracking (improving / worsening / stable)</li>
          <li>🤝 <strong className="text-text-primary">Equipment Marketplace</strong> — Peer-to-peer booking of farm equipment (tractors, harvesters) with full booking lifecycle</li>
          <li>👷 <strong className="text-text-primary">Farm Workforce</strong> — Directory and booking for agricultural labour</li>
          <li>📈 <strong className="text-text-primary">ML Dashboard</strong> — Offline model evaluation metrics and real-time user feedback tracking</li>
        </ul>
      </div>

      <div className="bg-card rounded-xl shadow-sm border border-border p-6 text-center text-sm text-text-secondary">
        Developed with <span className="text-red-500">♥</span> for the agricultural community as a B.Tech Computer Science project.
      </div>
    </div>
  );
}
