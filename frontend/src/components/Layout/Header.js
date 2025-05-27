import React, { useState, useEffect } from 'react';
import { Navbar, Nav, Container, Button } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import { getCurrentUser, signOut } from '../../services/auth';
import CompanySelector from '../CompanySelector/CompanySelector';

const Header = () => {
  const [user, setUser] = useState(null);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const navigate = useNavigate();
  
  useEffect(() => {
    const checkUser = () => {
      const currentUser = getCurrentUser();
      setUser(currentUser);
    };
    
    // Check if there's a previously selected company in localStorage
    const savedCompany = localStorage.getItem('selectedCompany');
    if (savedCompany) {
      try {
        setSelectedCompany(JSON.parse(savedCompany));
      } catch (e) {
        console.error('Error parsing saved company:', e);
      }
    }
    
    checkUser();
    // Check user status every 5 minutes
    const interval = setInterval(checkUser, 300000);
    
    return () => clearInterval(interval);
  }, []);
  
  const handleSignOut = () => {
    signOut();
    setUser(null);
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
            {user && (
              <CompanySelector onCompanyChange={handleCompanyChange} />
            )}
            {user ? (
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
