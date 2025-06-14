import React from 'react';
import './HowItWorks.css';

const steps = [
  {
    number: '01',
    title: 'Upload File',
    description: 'Upload your CSV or Excel file containing feedback data.'
  },
  {
    number: '02',
    title: 'Analyze Feedback',
    description: 'Our AI processes your data and generates comprehensive insights.'
  },
  {
    number: '03',
    title: 'Download Report',
    description: 'Get your detailed analysis report in your preferred format.'
  }
];

const HowItWorks = () => {
  return (
    <section className="how-it-works">
      <div className="container">
        <h2 className="section-title">How It Works</h2>
        <div className="steps-container">
          {steps.map((step, index) => (
            <div key={index} className="step">
              <div className="step-number">{step.number}</div>
              <div className="step-content">
                <h3>{step.title}</h3>
                <p>{step.description}</p>
              </div>
              {index < steps.length - 1 && <div className="step-connector" />}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default HowItWorks; 