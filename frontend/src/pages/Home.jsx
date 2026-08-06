import { Link } from 'react-router-dom';
import { ShieldCheck, Stethoscope, Droplets, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Home() {
  const features = [
    {
      title: 'Leaf Verification',
      description: 'Ensures the uploaded image is a valid plant leaf before analysis.',
      icon: ShieldCheck,
      color: 'text-primary'
    },
    {
      title: 'Disease Detection',
      description: 'Accurately identifies crop diseases using state-of-the-art AI.',
      icon: Stethoscope,
      color: 'text-warning'
    },
    {
      title: 'Crop Recommendation',
      description: 'Suggests the best crops for your specific soil and climate conditions.',
      icon: Droplets,
      color: 'text-secondary'
    }
  ];

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="text-center py-12 md:py-20">
        <motion.h1 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-4xl md:text-5xl font-bold text-text-primary mb-4"
        >
          FieldMind
        </motion.h1>
        <motion.p 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="text-xl md:text-2xl text-text-secondary mb-8 max-w-2xl mx-auto"
        >
          AI Powered Crop Disease Detection & Crop Recommendation Platform
        </motion.p>
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex flex-col sm:flex-row justify-center items-center space-y-4 sm:space-y-0 sm:space-x-6"
        >
          <Link
            to="/disease-detection"
            className="w-full sm:w-auto px-8 py-3 bg-primary text-white font-medium rounded-md shadow-sm hover:bg-green-800 transition-colors flex items-center justify-center"
          >
            Detect Disease
            <ArrowRight className="ml-2 h-5 w-5" />
          </Link>
          <Link
            to="/crop-recommendation"
            className="w-full sm:w-auto px-8 py-3 bg-white text-primary border border-primary font-medium rounded-md shadow-sm hover:bg-gray-50 transition-colors flex items-center justify-center"
          >
            Recommend Crop
          </Link>
        </motion.div>
      </section>

      {/* Features Section */}
      <section>
        <h2 className="text-2xl font-bold text-text-primary mb-8 text-center">Platform Capabilities</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 + 0.3 }}
              className="bg-card p-6 rounded-xl shadow-sm border border-border hover:shadow-md transition-shadow"
            >
              <div className={`p-3 rounded-full bg-gray-50 inline-block mb-4 ${feature.color}`}>
                <feature.icon className="h-8 w-8" />
              </div>
              <h3 className="text-xl font-semibold text-text-primary mb-2">{feature.title}</h3>
              <p className="text-text-secondary">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </section>
    </div>
  );
}
