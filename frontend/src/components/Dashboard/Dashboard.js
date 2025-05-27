import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Alert, Spinner } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import DeviceList from '../DeviceList/DeviceList';
import DeviceMap from '../Map/DeviceMap';
import { getUserCompanies } from '../../services/api';

const Dashboard = () => {
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [hasCompanies, setHasCompanies] = useState(null); // null means loading, true/false after check
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  
  // Check if user has any companies on component mount
  useEffect(() => {
    const checkUserCompanies = async () => {
      setLoading(true);
      setError('');
      
      try {
        const response = await getUserCompanies();
        const userCompanies = response.companies || [];
        
        // If user has no companies, set hasCompanies to false
        setHasCompanies(userCompanies.length > 0);
        
        // If no companies, redirect to company registration
        if (userCompanies.length === 0) {
          setTimeout(() => {
            navigate('/register-company');
          }, 2000); // Short delay to show the message
        }
      } catch (err) {
        setError('Error checking user companies: ' + (err.message || 'Unknown error'));
        setHasCompanies(false);
      } finally {
        setLoading(false);
      }
    };
    
    checkUserCompanies();
  }, [navigate]);
  
  // Handle device selection from the list
  const handleDeviceSelect = (device) => {
    setSelectedDevice(device);
  };
  
  // Show loading state
  if (loading) {
    return (
      <Container className="mt-5 text-center">
        <Spinner animation="border" />
        <p className="mt-3">Loading dashboard...</p>
      </Container>
    );
  }
  
  // Show error if any
  if (error) {
    return (
      <Container className="mt-5">
        <Alert variant="danger">{error}</Alert>
      </Container>
    );
  }
  
  // Show message if no companies
  if (hasCompanies === false) {
    return (
      <Container className="mt-5">
        <Alert variant="info">
          <Alert.Heading>No Company Found</Alert.Heading>
          <p>
            You don't have any companies registered. You need to register a company before you can view devices.
          </p>
          <p className="mb-0">
            Redirecting to company registration...
          </p>
        </Alert>
      </Container>
    );
  }
  
  // Regular dashboard view if user has companies
  return (
    <Container fluid className="mt-4">
      <Row className="h-100" style={{ minHeight: '80vh' }}>
        <Col md={3} className="h-100">
          <DeviceList 
            onDeviceSelect={handleDeviceSelect} 
            selectedDeviceId={selectedDevice?.deviceId}
          />
        </Col>
        <Col md={9} className="h-100">
          <DeviceMap 
            selectedDevice={selectedDevice}
            initialDeviceId={selectedDevice?.deviceId}
            initialPosition={
              selectedDevice?.lastTelemetry ? 
              [selectedDevice.lastTelemetry.latitude, selectedDevice.lastTelemetry.longitude] : 
              undefined
            }
          />
        </Col>
      </Row>
    </Container>
  );
};

export default Dashboard;
