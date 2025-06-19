import React, { useState, useRef } from 'react';
import './Report.css';

const emptyComparison = { yField: '', xFields: [] };

const Report = () => {
  const fileInputRef = useRef(null);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [fileHeaders, setFileHeaders] = useState([]);
  const [uploadedFilename, setUploadedFilename] = useState('');
  const [reportType, setReportType] = useState('generalized');
  const [comparisons, setComparisons] = useState([{ ...emptyComparison }]);

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

      // Store the filename for later use
      setUploadedFilename(data.filename);

      // Extract headers from the uploaded file
      const headersResponse = await fetch(`http://localhost:5000/headers/${data.filename}`);
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
    if (type === 'fieldwise') {
      setComparisons([{ ...emptyComparison }]);
    } else {
      setComparisons([{ ...emptyComparison }]);
    }
  };

  const handleComparisonChange = (idx, field, value) => {
    setComparisons(prev => prev.map((comp, i) => {
      if (i !== idx) return comp;
      if (field === 'yField') return { ...comp, yField: value };
      if (field === 'xFields') return { ...comp, xFields: value };
      return comp;
    }));
  };

  const addComparison = () => {
    setComparisons(prev => [...prev, { ...emptyComparison }]);
  };

  const removeComparison = (idx) => {
    setComparisons(prev => prev.filter((_, i) => i !== idx));
  };

  const isValid = comparisons.every(comp => comp.yField && comp.xFields.length > 0);

  const handleGenerate = (e) => {
    e.preventDefault();
    if (!isValid) return;
    alert('📄 Generating PDF Report…');
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

      {/* Step 3: Comparison Blocks */}
      {fileHeaders.length > 0 && (
        <div className="step-section">
          <h2>Step 3: Configure Comparisons</h2>
          {comparisons.map((comp, idx) => (
            <div className="comparison-block" key={idx}>
              <div className="field-group">
                <label><b>Select comparison field (Y-axis)</b></label>
                <select
                  value={comp.yField}
                  onChange={e => handleComparisonChange(idx, 'yField', e.target.value)}
                  className="single-select"
                >
                  <option value="">Select Y field</option>
                  {fileHeaders.map((header, i) => (
                    <option key={i} value={header}>{header}</option>
                  ))}
                </select>
              </div>
              <div className="field-group">
                <label><b>Select rating fields (X-axis)</b></label>
                <select
                  multiple
                  value={comp.xFields}
                  onChange={e => {
                    const options = Array.from(e.target.selectedOptions, option => option.value);
                    handleComparisonChange(idx, 'xFields', options);
                  }}
                  className="multi-select"
                  size={Math.min(6, fileHeaders.length)}
                >
                  {fileHeaders.map((header, i) => (
                    <option key={i} value={header}>{header}</option>
                  ))}
                </select>
              </div>
              {reportType === 'generalized' && comparisons.length > 1 && (
                <button className="btn-remove" onClick={() => removeComparison(idx)}>
                  Remove
                </button>
              )}
            </div>
          ))}
          {reportType === 'generalized' && (
            <button className="btn-add" onClick={addComparison}>
              ➕ Add Another Comparison
            </button>
          )}
        </div>
      )}

      {/* Step 4: Generate Button */}
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