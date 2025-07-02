import React, { useState, useRef } from 'react';
import './Report.css';

const Report = () => {
  const fileInputRef = useRef(null);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [fileHeaders, setFileHeaders] = useState([]);
  const [uploadedFilename, setUploadedFilename] = useState('');
  const [reportType, setReportType] = useState('generalized');

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const validTypes = ['.csv', '.xlsx'];
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!validTypes.includes(fileExtension)) {
      setUploadStatus({ type: 'error', message: 'Please upload a CSV or Excel file' });
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setUploadStatus({ type: 'error', message: 'File size should be less than 5MB' });
      return;
    }

    setIsUploading(true);
    setUploadStatus(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:5001/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Upload failed');
      }

      setUploadedFilename(data.filename);

      const headersResponse = await fetch(`http://localhost:5001/headers/${data.filename}`);
      const headersData = await headersResponse.json();

      if (headersResponse.ok) {
        setFileHeaders(headersData.headers);
        setUploadStatus({ type: 'success', message: 'File uploaded successfully! Headers extracted.' });
      } else {
        throw new Error(headersData.error || 'Failed to extract headers');
      }
    } catch (error) {
      setUploadStatus({ type: 'error', message: error.message });
    } finally {
      setIsUploading(false);
    }
  };

  const handleReportTypeChange = (type) => {
    setReportType(type);
  };

  const isValid = fileHeaders.length > 0;

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!isValid || !fileInputRef.current.files[0]) return;

    const formData = new FormData();
    formData.append('file', fileInputRef.current.files[0]);

    let choice = "1";
    if (reportType === 'fieldwise') choice = "2";

    formData.append('choice', choice);

    try {
      setUploadStatus({ type: 'loading', message: 'Generating report...' });

      const response = await fetch('http://localhost:5001/generate-report', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        try {
          const jsonError = JSON.parse(errorText);
          throw new Error(jsonError.error || 'Failed to generate report');
        } catch {
          throw new Error('Failed to generate report. Server responded with HTML.');
        }
      }

      const contentType = response.headers.get('Content-Type');
      if (contentType && contentType.includes('application/zip')) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'Feedback_Reports.zip';
        document.body.appendChild(a);
        a.click();
        a.remove();

        setUploadStatus({ type: 'success', message: '✅ Report generated and downloaded.' });
      } else {
        const text = await response.text();
        throw new Error(`Unexpected response format. Details: ${text}`);
      }

    } catch (error) {
      setUploadStatus({ type: 'error', message: error.message });
    }
  };

  return (
    <div className="report-container">
      <div className="report-header">
        <h1>Generate PDF Report</h1>
        <p>Upload your dataset and create insightful reports</p>
      </div>

      {/* Step 1: File Upload */}
      <div className="step-section">
        <h2>Step 1: Upload Your File</h2>
        <div className="upload-section">
          <button 
            className="btn-primary upload-btn"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
          >
            {isUploading ? 'Uploading...' : 'Choose File'}
          </button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".csv,.xlsx"
            style={{ display: 'none' }}
          />
          <p className="file-types">Supports .csv and .xlsx formats (max 5MB)</p>
          {uploadStatus && (
            <p className={`upload-status ${uploadStatus.type}`}>
              {uploadStatus.message}
            </p>
          )}
         {uploadStatus?.type === 'loading' && (
          <div className="loader"></div>
        )}
        </div>
      </div>

      {/* Step 2: Report Type Toggle */}
      {fileHeaders.length > 0 && (
        <div className="step-section">
          <h2>Step 2: Choose Report Type</h2>
          <div className="report-type-selection">
            <label className="report-type-option">
              <input
                type="radio"
                name="reportType"
                value="generalized"
                checked={reportType === 'generalized'}
                onChange={() => handleReportTypeChange('generalized')}
              />
              Generalized Report
            </label>
            <label className="report-type-option">
              <input
                type="radio"
                name="reportType"
                value="fieldwise"
                checked={reportType === 'fieldwise'}
                onChange={() => handleReportTypeChange('fieldwise')}
              />
              Field-Wise Report
            </label>
          </div>
        </div>
      )}

      {/* Step 3 Removed */}

      {/* Step 4: Generate Report */}
      {fileHeaders.length > 0 && isValid && (
        <div className="step-section">
          <h2>Step 4: Generate Report</h2>
          <button 
            className="btn-generate"
            onClick={handleGenerate}
          >
            Get PDF Report
          </button>
        </div>
      )}
    </div>
  );
};

export default Report;
