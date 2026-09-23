import { Link } from 'react-router-dom';
import { AlertCircle, Home } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <AlertCircle className="h-16 w-16 text-warning mb-4" />
      <h1 className="text-4xl font-bold text-text-primary mb-2">404 - Page Not Found</h1>
      <p className="text-xl text-text-secondary mb-8">
        The page you are looking for does not exist or has been moved.
      </p>
      <Link
        to="/"
        className="inline-flex items-center px-6 py-3 bg-primary text-white font-medium rounded-md shadow-sm hover:bg-green-800 transition-colors"
      >
        <Home className="mr-2 h-5 w-5" />
        Back to Home
      </Link>
    </div>
  );
}
