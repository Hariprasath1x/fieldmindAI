export default function About() {
  return (
    <div className="max-w-3xl mx-auto space-y-8 py-6">
      <h1 className="text-3xl font-bold text-text-primary">About FieldMind</h1>
      
      <div className="bg-card rounded-xl shadow-sm border border-border p-6 sm:p-8 space-y-6">
        <section>
          <h2 className="text-xl font-semibold text-text-primary mb-3">What is FieldMind?</h2>
          <p className="text-text-secondary leading-relaxed">
            FieldMind is an intelligent agricultural platform designed to empower farmers, students, and researchers with AI-driven insights. It provides two primary services: early crop disease detection through leaf image analysis and intelligent crop recommendations based on soil and environmental parameters.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-text-primary mb-3">Technology Stack</h2>
          <ul className="list-disc pl-5 text-text-secondary space-y-2">
            <li><strong className="text-text-primary">Frontend:</strong> React 19, Vite, Tailwind CSS</li>
            <li><strong className="text-text-primary">Backend:</strong> FastAPI (Python)</li>
            <li><strong className="text-text-primary">Machine Learning:</strong> ONNX Runtime, YOLO for object detection</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-text-primary mb-3">Project Architecture</h2>
          <p className="text-text-secondary leading-relaxed">
            The platform utilizes a multi-stage AI pipeline for disease detection: first verifying if the uploaded image is a valid plant leaf, then classifying the disease, and finally assessing its severity using YOLO bounding box detection. The crop recommendation engine uses standard machine learning models to analyze N-P-K levels, pH, temperature, humidity, and rainfall to suggest optimal crops.
          </p>
        </section>

        <section className="pt-4 border-t border-border">
          <p className="text-sm text-text-secondary text-center">
            Developed with <span className="text-red-500">♥</span> for the agricultural community.
          </p>
        </section>
      </div>
    </div>
  );
}
