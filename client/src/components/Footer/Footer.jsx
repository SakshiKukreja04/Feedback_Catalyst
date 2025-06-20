import React from 'react';
import './Footer.css';

const Footer = () => {
  return (
    <>
      <hr style={{ margin: '2rem 0', border: 'none', borderTop: '1.5px solid rgb(21, 1, 1)' }} />
      <footer className="footer">
        <div className="container footer-container">
          <div className="copyright">
            © 2025 Feedback Catalyst
          </div>
          <div className="footer-links">
            <a href="/privacy">Privacy Policy</a>
            <a href="/terms">Terms of Use</a>
            <a href="/contact">Contact Us</a>
          </div>
        </div>
      </footer>
    </>
  );
};

export default Footer; 