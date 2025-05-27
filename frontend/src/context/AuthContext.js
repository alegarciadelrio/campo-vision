import React, { createContext, useState, useEffect, useContext } from 'react';
import { getCurrentUser, getSession } from '../services/auth';

// Create the context
const AuthContext = createContext();

// Create a provider component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Function to check authentication status
  const checkAuthStatus = async () => {
    setLoading(true);
    try {
      const currentUser = getCurrentUser();
      if (currentUser) {
        try {
          // Verify the session is valid
          await getSession();
          setUser(currentUser);
          setIsAuthenticated(true);
        } catch (error) {
          console.error('Session invalid:', error);
          setUser(null);
          setIsAuthenticated(false);
        }
      } else {
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  // Check auth status on mount
  useEffect(() => {
    checkAuthStatus();
    
    // Set up an interval to periodically check auth status
    const interval = setInterval(checkAuthStatus, 300000); // 5 minutes
    
    // Clean up on unmount
    return () => clearInterval(interval);
  }, []);

  // Create a custom event for auth state changes
  const updateAuthState = (newState) => {
    setUser(newState ? getCurrentUser() : null);
    setIsAuthenticated(!!newState);
    
    // Dispatch a custom event that other components can listen to
    window.dispatchEvent(new CustomEvent('authStateChanged', { 
      detail: { isAuthenticated: !!newState } 
    }));
  };

  // The context value that will be provided
  const contextValue = {
    user,
    isAuthenticated,
    loading,
    checkAuthStatus,
    updateAuthState
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use the auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
