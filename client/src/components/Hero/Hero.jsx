import React, { useRef, useState } from 'react';
import './Hero.css';

const Hero = () => {
  const fileInputRef = useRef(null);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Check file type
    const validTypes = ['.csv', '.xlsx'];
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!validTypes.includes(fileExtension)) {
      setUploadStatus({ type: 'error', message: 'Please upload a CSV or Excel file' });
      return;
    }

    // Check file size (5MB limit)
    if (file.size > 5 * 1024 * 1024) {
      setUploadStatus({ type: 'error', message: 'File size should be less than 5MB' });
      return;
    }

    setIsUploading(true);
    setUploadStatus(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:5000/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Upload failed');
      }

      setUploadStatus({ type: 'success', message: 'File uploaded successfully!' });
    } catch (error) {
      setUploadStatus({ type: 'error', message: error.message });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <section className="hero">
      <div className="container hero-container">
        <div className="hero-illustration">
          <img 
            src="/Freepik.png" 
            alt="Feedback Analysis Illustration"
            className="hero-image"
          />
        </div>
        <div className="hero-content">
          <h1>Turn Raw Feedback into Meaningful Insights</h1>
          <p className="subtitle">
            Upload CSV or Excel files and instantly generate comprehensive feedback analysis reports.
          </p>
          <div className="upload-section">
            <button 
              className="btn-primary upload-btn"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
            >
              {isUploading ? 'Uploading...' : 'Upload Your File'}
            </button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".csv,.xlsx"
              style={{ display: 'none' }}
            />
            <button className="btn-secondary get-analysis-btn">Get Analysis</button>
            <p className="file-types">Supports .csv and .xlsx formats</p>
            {uploadStatus && (
              <p className={`upload-status ${uploadStatus.type}`}>
                {uploadStatus.message}
              </p>
            )}
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero; 