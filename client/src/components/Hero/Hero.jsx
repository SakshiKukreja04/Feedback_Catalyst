import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './Hero.css';

const Hero = () => {
  const navigate = useNavigate();
  const imageRef = useRef(null);

  useEffect(() => {
    // Wait for GSAP to be available
    const initAnimation = () => {
      if (typeof gsap !== 'undefined') {
        const image = imageRef.current;
        
        if (image) {
          // Kill any existing animations
          gsap.killTweensOf(image);
          
          // Initial state - hide the image
          gsap.set(image, {
            opacity: 0,
            scale: 0.8,
            y: 50
          });

          // Page load animation
          const tl = gsap.timeline();
          tl.to(image, {
            opacity: 1,
            scale: 1,
            y: 0,
            duration: 1.2,
            ease: "power2.out"
          });

          // After load animation - floating effect
          tl.to(image, {
            y: -10,
            duration: 2,
            ease: "power1.inOut",
            yoyo: true,
            repeat: -1
          }, "-=0.5");

          // Glow animation
          gsap.to(image, {
            boxShadow: "0 0 30px rgba(59, 130, 246, 0.3)",
            duration: 2,
            ease: "power1.inOut",
            yoyo: true,
            repeat: -1
          });
        }
      } else {
        // Retry after a short delay if GSAP isn't loaded yet
        setTimeout(initAnimation, 100);
      }
    };

    initAnimation();

    // Cleanup function
    return () => {
      if (typeof gsap !== 'undefined' && imageRef.current) {
        gsap.killTweensOf(imageRef.current);
      }
    };
  }, []);

  return (
    <section className="hero">
      <div className="container hero-container">
        <div className="hero-illustration">
          <img 
            ref={imageRef}
            id="hero-image"
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