export default function Footer() {
  return (
    <footer className="bg-card border-t border-border mt-auto">
      <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
        <p className="text-center text-sm text-text-secondary">
          &copy; {new Date().getFullYear()} FieldMind. AI-Powered Crop Intelligence.
        </p>
      </div>
    </footer>
  );
}
