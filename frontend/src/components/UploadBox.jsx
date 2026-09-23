import { useState } from 'react';
import { UploadCloud, X } from 'lucide-react';

export default function UploadBox({ onUpload, isLoading }) {
  const [dragActive, setDragActive] = useState(false);
  const [preview, setPreview] = useState(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file) => {
    if (!file.type.match('image.*')) {
      alert('Please upload an image file.');
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target.result);
      onUpload(file, e.target.result);
    };
    reader.readAsDataURL(file);
  };

  const clearImage = (e) => {
    e.stopPropagation();
    setPreview(null);
    onUpload(null, null);
  };

  return (
    <div
      className={`relative w-full p-8 border-2 border-dashed rounded-xl transition-colors ${
        dragActive ? 'border-primary bg-primary/5' : 'border-border bg-card'
      } ${isLoading ? 'opacity-50 pointer-events-none' : 'cursor-pointer hover:bg-gray-50'}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={() => document.getElementById('file-upload').click()}
    >
      <input
        id="file-upload"
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleChange}
      />
      
      {preview ? (
        <div className="relative max-w-sm mx-auto">
          <img src={preview} alt="Preview" className="rounded-lg shadow-sm w-full h-auto object-cover max-h-64" />
          <button
            onClick={clearImage}
            className="absolute -top-3 -right-3 bg-white text-error rounded-full p-1 shadow-md hover:bg-red-50"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center text-center">
          <div className="bg-primary/10 p-4 rounded-full mb-4">
            <UploadCloud className="h-10 w-10 text-primary" />
          </div>
          <h3 className="text-lg font-semibold text-text-primary mb-2">
            Click or drag image to upload
          </h3>
          <p className="text-sm text-text-secondary">
            Supported formats: JPEG, PNG, WEBP
          </p>
        </div>
      )}
    </div>
  );
}
