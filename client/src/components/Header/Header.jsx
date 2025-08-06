import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Header.css';

const Header = ({ hideNavButtons, transparentBg }) => {
  const navigate = useNavigate();

  return (
    <header className={`header${transparentBg ? ' transparent-bg' : ''}`}>
      <div className="header-inner">
        <div className="logo" onClick={() => navigate('/')}>
          <h1>Feedback Catalyst</h1>
        </div>
      </div>
      {!hideNavButtons && (
        <nav className="nav-buttons">
          <button 
            className="btn-primary"
            onClick={() => navigate('/report')}
          >
            Get Started
          </button>
        </nav>
      )}
    </header>
  );
};

export default Header; 