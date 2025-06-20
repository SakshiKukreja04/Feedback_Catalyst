import React from 'react';
import { useNavigate } from 'react-router-dom';
import { auth } from '../../firebase';
import './Header.css';

// You can replace this with your own image path or a public URL
const PROFILE_IMG = 'https://cdn-icons-png.flaticon.com/512/149/149071.png';

const Header = ({ isAuthenticated, hideNavButtons, transparentBg }) => {
  const navigate = useNavigate();

  const handleLogout = () => {
    auth.signOut();
    navigate('/');
  };

  return (
    <header className={`header${transparentBg ? ' transparent-bg' : ''}`}>
      <div className="header-inner">
        <div className="logo" onClick={() => navigate('/')}>
          <h1>Feedback Catalyst</h1>
        </div>
      </div>
      {!hideNavButtons && (
        <nav className="nav-buttons">
          {isAuthenticated ? (
            <div className="profile-logout-stack">
              <img src={PROFILE_IMG} alt="Profile" className="profile-img" />
              <button className="logout-btn" onClick={handleLogout}>Logout</button>
            </div>
          ) : (
            <>
              <button 
                className="btn-secondary"
                onClick={() => navigate('/login')}
              >
                Login
              </button>
              <button 
                className="btn-primary"
                onClick={() => navigate('/signup')}
              >
                Sign Up
              </button>
            </>
          )}
        </nav>
      )}
    </header>
  );
};

export default Header; 