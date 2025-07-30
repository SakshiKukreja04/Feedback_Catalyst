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
  const [uploadedFiles, setUploadedFiles] = useState([]); // Store multiple files for stakeholder
  const [uploadedFilenames, setUploadedFilenames] = useState([]); // Store backend filenames
  const [fileHeadersList, setFileHeadersList] = useState([]); // Store headers for each file

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
    const files = Array.from(event.target.files);
    if (!files.length) return;

    setChartUrls([]);
    setIsUploading(true);
    setUploadStatus({ type: 'loading', message: 'Uploading file(s)...' });

    try {
      const validTypes = ['.csv', '.xlsx'];
      const tooLarge = files.find(file => file.size > 5 * 1024 * 1024);
      if (tooLarge) throw new Error('Each file must be less than 5MB');
      const invalid = files.find(file => !validTypes.includes(file.name.substring(file.name.lastIndexOf('.')).toLowerCase()));
      if (invalid) throw new Error('All files must be .csv or .xlsx');

      let filenames = [];
      let headersList = [];
      for (const file of files) {
        // Always use base filename (no folder path)
        const baseFilename = file.name.split(/[/\\]/).pop();
        const formData = new FormData();
        formData.append('file', file);
        const uploadResponse = await fetch('http://localhost:5001/upload', {
          method: 'POST',
          body: formData,
        });
        if (!uploadResponse.ok) {
          const errorText = await uploadResponse.text();
          throw new Error(`Upload failed (Status: ${uploadResponse.status}): ${errorText}`);
        }
        const uploadData = await uploadResponse.json();
        filenames.push(baseFilename);
        // Get headers for each file using base filename
        const headersResponse = await fetch(`http://localhost:5001/headers/${encodeURIComponent(baseFilename)}`);
        if (!headersResponse.ok) {
          const errorText = await headersResponse.text();
          throw new Error(`Failed to get headers (Status: ${headersResponse.status}): ${errorText}`);
        }
        const headersData = await headersResponse.json();
        headersList.push(headersData.headers);
      }
      setUploadedFiles(files);
      setUploadedFilenames(filenames);
      setFileHeadersList(headersList);
      setFileHeaders(headersList[0] || []); // For UI compatibility, use first file's headers
      setUploadedFilename(filenames[0] || '');
      setUploadStatus({ type: 'success', message: 'Files uploaded successfully! You can now generate a report or view charts.' });
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
    if (!isValid || (feedbackType === 'stakeholder' && uploadedFiles.length === 0) || (feedbackType === 'subject' && !fileInputRef.current.files[0])) return;

    setIsGenerating(true);
    setChartUrls([]);
    setUploadStatus({ type: 'loading', message: 'Generating report...' });

    try {
      const formData = new FormData();
      if (feedbackType === 'stakeholder') {
        uploadedFiles.forEach(file => formData.append('files[]', file));
        formData.append('uploadedFilenames', JSON.stringify(uploadedFilenames));
      } else {
        formData.append('file', fileInputRef.current.files[0]);
        formData.append('uploadedFilename', uploadedFilename.replace(/\.[^/.]+$/, ""));
      }
      formData.append('choice', reportType === 'fieldwise' ? "2" : "1");
      formData.append('feedbackType', feedbackType);
      formData.append('reportType', reportType);

      const endpoint = (feedbackType === 'stakeholder') ? 'http://localhost:5001/api/generate-stakeholder-report' : 'http://localhost:5001/generate-report';
      const response = await fetch(endpoint, {
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
    if (!isValid || (feedbackType === 'stakeholder' && uploadedFiles.length === 0) || (feedbackType === 'subject' && !fileInputRef.current.files[0])) return;

    setIsGenerating(true);
    setChartUrls([]);
    setUploadStatus({ type: 'loading', message: 'Generating charts...' });

    try {
        const formData = new FormData();
        
        if (feedbackType === 'stakeholder') {
            // For stakeholder feedback, use uploadedFiles
            uploadedFiles.forEach(file => formData.append('file', file));
        } else {
            // For subject feedback, use fileInputRef.current.files
            const files = fileInputRef.current.files;
            for (let i = 0; i < files.length; i++) {
                formData.append('file', files[i]);
            }
        }

        formData.append('choice', reportType === 'fieldwise' ? "2" : "1");
        formData.append('feedbackType', feedbackType);
        formData.append('uploadedFilename', uploadedFilename.replace(/\.[^/.]+$/, ""));
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
        const urls = data.chart_urls;
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

  // Add this handler in your Report component
  const handleDownloadSuggestions = async () => {
    setUploadStatus({ type: 'loading', message: 'Generating suggestions PDF...' });

    try {
      const formData = new FormData();
      if (feedbackType === 'stakeholder') {
        uploadedFiles.forEach(file => formData.append('files[]', file));
        formData.append('uploadedFilenames', JSON.stringify(uploadedFilenames));
      } else {
        formData.append('file', fileInputRef.current.files[0]);
        formData.append('uploadedFilename', uploadedFilename.replace(/\.[^/.]+$/, ""));
      }
      formData.append('feedbackType', feedbackType);

      const response = await fetch('http://localhost:5001/get-suggestions', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to generate suggestions PDF (Status: ${response.status}): ${errorText}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'Suggestions_Summary.pdf';
      document.body.appendChild(a);
      a.click();
      a.remove();
      setUploadStatus({ type: 'success', message: '✅ Suggestions PDF generated and downloaded.' });
    } catch (error) {
      setUploadStatus({ type: 'error', message: error.message });
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
            multiple={feedbackType === 'stakeholder'}
            webkitdirectory={feedbackType === 'stakeholder' ? '' : undefined}
            directory={feedbackType === 'stakeholder' ? '' : undefined}
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
            <button
              className="btn-secondary"
              onClick={handleDownloadSuggestions}
              disabled={isGenerating}
            >
              Download Suggestions PDF
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