import React, { useState, useEffect } from 'react';
import { Navbar, Nav, Container, Button } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import { signOut } from '../../services/auth';
import { useAuth } from '../../context/AuthContext';
import CompanySelector from '../CompanySelector/CompanySelector';

const Header = () => {
  const [selectedCompany, setSelectedCompany] = useState(null);
  const navigate = useNavigate();
  const { user, isAuthenticated, updateAuthState } = useAuth();
  
  useEffect(() => {
    // Check if there's a previously selected company in localStorage
    const savedCompany = localStorage.getItem('selectedCompany');
    if (savedCompany) {
      try {
        setSelectedCompany(JSON.parse(savedCompany));
      } catch (e) {
        console.error('Error parsing saved company:', e);
      }
    }
  }, []);
  
  const handleSignOut = () => {
    signOut();
    updateAuthState(false);
    navigate('/login');
  };
  
  // Handle company change from selector
  const handleCompanyChange = (company) => {
    setSelectedCompany(company);
    // You could trigger a refresh of data here if needed
    // For example, refetch devices for the selected company
  };
  
  return (
    <Navbar bg="dark" variant="dark" expand="lg">
      <Container>
        <Navbar.Brand as={Link} to="/">
          Campo Vision
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">
            {user && (
              <>
                <Nav.Link as={Link} to="/dashboard">Dashboard</Nav.Link>
              </>
            )}
          </Nav>
          <Nav className="d-flex align-items-center">
            {isAuthenticated && (
              <CompanySelector onCompanyChange={handleCompanyChange} />
            )}
            {isAuthenticated ? (
              <Button variant="outline-light" onClick={handleSignOut}>Sign Out</Button>
            ) : (
              <Nav.Link as={Link} to="/login">Sign In</Nav.Link>
            )}
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default Header;
