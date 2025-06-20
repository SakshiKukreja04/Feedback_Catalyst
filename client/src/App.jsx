import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { onAuthStateChanged } from 'firebase/auth';
import { auth } from './firebase';
import Header from './components/Header/Header';
import Hero from './components/Hero/Hero';
import Features from './components/Features/Features';
import HowItWorks from './components/HowItWorks/HowItWorks';
import Footer from './components/Footer/Footer';
import Login from './components/Auth/Login';
import Signup from './components/Auth/Signup';
import Report from './components/Report/Report';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setIsAuthenticated(!!user);
      setIsLoading(false);
    });

    return () => unsubscribe();
  }, []);

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <Router>
      <div className="app">
        <Routes>
          <Route path="/" element={
            <>
              <Header isAuthenticated={isAuthenticated} />
              <Hero />
              <Features />
              <HowItWorks />
              <Footer />
            </>
          } />
          <Route 
            path="/login" 
            element={
              isAuthenticated ? 
              <Navigate to="/" replace /> : 
              <Login onAuth={setIsAuthenticated} />
            } 
          />
          <Route 
            path="/signup" 
            element={
              isAuthenticated ? 
              <Navigate to="/" replace /> : 
              <Signup onAuth={setIsAuthenticated} />
            } 
          />
          <Route 
            path="/report" 
            element={
              <>
                <Header isAuthenticated={isAuthenticated} />
                <Report />
                <Footer />
              </>
            } 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
