import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Hero.css';

const Hero = () => {
  const navigate = useNavigate();

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
              className="btn-secondary get-analysis-btn"
              onClick={() => navigate('/report')}
            >
              Go to Report Generator
            </button>
            <p className="file-types">Supports .csv and .xlsx formats</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero; 