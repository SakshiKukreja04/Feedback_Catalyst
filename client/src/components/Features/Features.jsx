import React from 'react';
import './Features.css';

const features = [
  {
    title: 'Auto-generated Reports',
    description: 'Get comprehensive reports automatically generated from your feedback data.',
    icon: '📊'
  },
  {
    title: 'Smart Sentiment Analysis',
    description: 'Advanced AI-powered sentiment analysis to understand customer emotions.',
    icon: '🤖'
  },
  {
    title: 'Visual Rating Insights',
    description: 'Beautiful visualizations to help you understand rating patterns.',
    icon: '📈'
  }
];

const Features = () => {
  return (
    <section className="features">
      <div className="container">
        <div className="features-grid">
          {features.map((feature, index) => (
            <div key={index} className="feature-card">
              <div className="feature-icon">{feature.icon}</div>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features; 