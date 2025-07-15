import React, { useState, useRef } from 'react';
import './Report.css';

const Report = () => {
  const fileInputRef = useRef(null);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [fileHeaders, setFileHeaders] = useState([]);
  const [uploadedFilename, setUploadedFilename] = useState('');
  const [feedbackType, setFeedbackType] = useState('stakeholder'); // New state for feedback type
  const [reportType, setReportType] = useState('generalized');
  const [chartUrls, setChartUrls] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleFeedbackTypeChange = (type) => {
    setFeedbackType(type);
    // Reset other states when feedback type changes
    setFileHeaders([]);
    setUploadedFilename('');
    setUploadStatus(null);
    setChartUrls([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setChartUrls([]);
    setIsUploading(true);
    setUploadStatus({ type: 'loading', message: 'Uploading file...' });

    try {
      const validTypes = ['.csv', '.xlsx'];
      const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
      if (!validTypes.includes(fileExtension)) {
        throw new Error('Please upload a CSV or Excel file');
      }

      if (file.size > 5 * 1024 * 1024) {
        throw new Error('File size should be less than 5MB');
      }

      const formData = new FormData();
      formData.append('file', file);

      // --- Upload Request ---
      const uploadResponse = await fetch('http://localhost:5001/upload', {
        method: 'POST',
        body: formData,
      });

      if (!uploadResponse.ok) {
        const errorText = await uploadResponse.text();
        throw new Error(`Upload failed (Status: ${uploadResponse.status}): ${errorText}`);
      }
      
      const uploadData = await uploadResponse.json();
      setUploadedFilename(uploadData.filename);

      // --- Headers Request ---
      const headersResponse = await fetch(`http://localhost:5001/headers/${uploadData.filename}`);
      if (!headersResponse.ok) {
        const errorText = await headersResponse.text();
        throw new Error(`Failed to get headers (Status: ${headersResponse.status}): ${errorText}`);
      }

      const headersData = await headersResponse.json();
      setFileHeaders(headersData.headers);
      setUploadStatus({ type: 'success', message: 'File uploaded successfully! You can now generate a report or view charts.' });

    } catch (error) {
      let message = error.message;
      if (error instanceof SyntaxError) {
          message = 'Received an invalid response from the server (likely an HTML error page instead of JSON). Please ensure the backend server is running the correct code and check its console for errors.';
      }
      setUploadStatus({ type: 'error', message: message });
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

    setIsGenerating(true);
    setChartUrls([]);
    setUploadStatus({ type: 'loading', message: 'Generating report...' });

    try {
      const formData = new FormData();
      formData.append('file', fileInputRef.current.files[0]);
      formData.append('choice', reportType === 'fieldwise' ? "2" : "1");
      formData.append('feedbackType', feedbackType); // Send feedback type to backend
      formData.append('uploadedFilename', uploadedFilename.replace(/\.[^/.]+$/, "")); // file name without extension
      formData.append('reportType', reportType);

      const response = await fetch('http://localhost:5001/generate-report', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to generate report (Status: ${response.status}): ${errorText}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'Feedback_Reports.zip';
      document.body.appendChild(a);
      a.click();
      a.remove();
      setUploadStatus({ type: 'success', message: '✅ Report generated and downloaded.' });

    } catch (error) {
        setUploadStatus({ type: 'error', message: error.message });
    } finally {
        setIsGenerating(false);
    }
  };

  const handleViewCharts = async (e) => {
    e.preventDefault();
    if (!isValid || !fileInputRef.current.files[0]) return;

    setIsGenerating(true);
    setChartUrls([]);
    setUploadStatus({ type: 'loading', message: 'Generating charts...' });

    try {
        const formData = new FormData();
        formData.append('file', fileInputRef.current.files[0]);
        formData.append('choice', reportType === 'fieldwise' ? "2" : "1");
        formData.append('feedbackType', feedbackType); // Send feedback type to backend
        formData.append('uploadedFilename', uploadedFilename.replace(/\.[^/.]+$/, "")); // file name without extension
        formData.append('reportType', reportType);

        const response = await fetch('http://localhost:5001/generate-charts', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Failed to generate charts (Status: ${response.status}): ${errorText}`);
        }

        const data = await response.json();
        const urls = data.chart_urls; // ✅ this is the correct field name now
        setChartUrls(urls);
        setUploadStatus({ type: 'success', message: 'Charts generated successfully!' });


    } catch (error) {
        let message = error.message;
        if (error instanceof SyntaxError) {
            message = 'Received an invalid response from the server (likely an HTML error page instead of JSON). Please ensure the backend server is running the correct code and check its console for errors.';
        }
        setUploadStatus({ type: 'error', message: message });
    } finally {
        setIsGenerating(false);
    }
  };

  return (
    <div className="report-container">
      <div className="report-header">
        <h1>Generate PDF Report or View Charts</h1>
        <p>Upload your dataset and create insightful reports and visualizations</p>
      </div>

      {/* Step 1: Feedback Type Selection */}
      <div className="step-section">
        <h2>Step 1: Select Feedback Type</h2>
        <div className="feedback-type-selection">
          <label className="feedback-type-option">
            <input
              type="radio"
              name="feedbackType"
              value="stakeholder"
              checked={feedbackType === 'stakeholder'}
              onChange={() => handleFeedbackTypeChange('stakeholder')}
            />
            Stakeholder Feedback
          </label>
          <label className="feedback-type-option">
            <input
              type="radio"
              name="feedbackType"
              value="subject"
              checked={feedbackType === 'subject'}
              onChange={() => handleFeedbackTypeChange('subject')}
            />
            Subject Feedback
          </label>
        </div>
      </div>

      {/* Step 2: File Upload */}
      <div className="step-section">
        <h2>Step 2: Upload Your File</h2>
        <div className="upload-section">
          <button
            className="btn-primary upload-btn"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading || isGenerating}
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
         {(isUploading || isGenerating) && (
           <div className="loader"></div>
         )}
        </div>
      </div>

      {/* Step 3: Report Type Toggle (Only for Stakeholder Feedback) */}
      {fileHeaders.length > 0 && feedbackType === 'stakeholder' && (
        <div className="step-section">
          <h2>Step 3: Choose Report Type</h2>
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

      {/* Step 4: Generate (Step number adjusts based on feedback type) */}
      {fileHeaders.length > 0 && isValid && (
        <div className="step-section">
          <h2>Step {feedbackType === 'stakeholder' ? '4' : '3'}: Generate Output</h2>
          <div className="generate-buttons">
            <button
              className="btn-generate"
              onClick={handleGenerate}
              disabled={isGenerating}
            >
              Get PDF Report
            </button>
            <button
              className="btn-secondary"
              onClick={handleViewCharts}
              disabled={isGenerating}
            >
              View Charts
            </button>
          </div>
        </div>
      )}

      {/* Step 5: Display Charts (Step number adjusts based on feedback type) */}
      {chartUrls.length > 0 && (
        <div className="step-section">
          <h2>Generated Charts</h2>
          <div className="charts-container">
            {chartUrls.map((url, index) => (
              <div key={index} className="chart-item">
                <img src={url} alt={`Generated chart ${index + 1}`} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Report;