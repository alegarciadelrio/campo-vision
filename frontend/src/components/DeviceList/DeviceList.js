import React, { useState, useEffect } from 'react';
import { Card, Form, Button, Spinner, Alert, Table } from 'react-bootstrap';
import DeviceRegister from '../Device/DeviceRegister';
import { getAllDevices } from '../../services/api';

const DeviceList = ({ onDeviceSelect, selectedDeviceId }) => {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCompany, setSelectedCompany] = useState(null);
  // Register modal state is kept but disabled by default
  const [showRegisterModal] = useState(false);

  // Check for selected company in localStorage on component mount
  useEffect(() => {
    const savedCompany = localStorage.getItem('selectedCompany');
    if (savedCompany) {
      try {
        setSelectedCompany(JSON.parse(savedCompany));
      } catch (e) {
        console.error('Error parsing saved company:', e);
      }
    }
  }, []);

  // Fetch devices when component mounts or when selected company changes
  useEffect(() => {
    // Only fetch devices if a company is selected
    if (selectedCompany) {
      fetchDevices();
    } else {
      // If no company is selected, clear the devices list and set loading to false
      setDevices([]);
      setLoading(false);
    }
  }, [selectedCompany]);

  // Function to fetch all devices
  const fetchDevices = async () => {
    setLoading(true);
    setError('');
    
    try {
      // Only fetch devices if a company is selected
      if (selectedCompany) {
        const companyId = selectedCompany.companyId;
        const response = await getAllDevices(companyId);
        setDevices(response.devices || []);
      } else {
        // If no company is selected, clear the devices list
        setDevices([]);
      }
    } catch (err) {
      setError('Error fetching devices: ' + (err.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  // Listen for company selection changes
  useEffect(() => {
    const handleStorageChange = () => {
      const savedCompany = localStorage.getItem('selectedCompany');
      if (savedCompany) {
        try {
          const parsedCompany = JSON.parse(savedCompany);
          setSelectedCompany(parsedCompany);
        } catch (e) {
          console.error('Error parsing saved company:', e);
        }
      }
    };

    // Add event listener for storage changes
    window.addEventListener('storage', handleStorageChange);
    
    // Custom event for same-tab communication
    window.addEventListener('companyChanged', handleStorageChange);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('companyChanged', handleStorageChange);
    };
  }, []);

  // Filter devices based on search term
  const filteredDevices = devices.filter(device => 
    device.deviceId.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (device.name && device.name.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <>
      <Card className="h-100 d-flex flex-column">
        <Card.Header className="d-flex justify-content-between align-items-center">
          <h4 className="mb-0">Devices</h4>
          <Button 
            variant="primary" 
            size="sm"
            onClick={fetchDevices}
            disabled={loading}
          >
            {loading ? <Spinner animation="border" size="sm" /> : 'Refresh'}
          </Button>
        </Card.Header>
        <Card.Body className="d-flex flex-column">
          <Form className="mb-3">
            <Form.Group>
              <Form.Control
                type="text"
                placeholder="Search devices..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </Form.Group>
          </Form>

          {error && <Alert variant="danger">{error}</Alert>}
          
          <div className="flex-grow-1 overflow-auto">
            {loading ? (
              <div className="text-center p-4">
                <Spinner animation="border" />
                <p className="mt-2">Loading devices...</p>
              </div>
            ) : !selectedCompany ? (
              <div className="text-center p-4">
                <p className="text-muted">Please select a company from the dropdown in the navigation bar to view devices</p>
              </div>
            ) : filteredDevices.length === 0 ? (
              <Alert variant="info">
                No devices found for the selected company. Please add devices from the Settings page.
              </Alert>
            ) : (
              <div className="table-responsive">
                <Table responsive striped hover>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Status</th>
                      <th>Last Seen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredDevices.map((device) => {
                      const isSelected = selectedDeviceId === device.deviceId;
                      const hasLocation = device.lastTelemetry && 
                                        device.lastTelemetry.latitude && 
                                        device.lastTelemetry.longitude;
                      
                      return (
                        <tr 
                          key={device.deviceId}
                          onClick={() => onDeviceSelect(device)}
                          className={isSelected ? 'table-primary' : ''}
                          style={{ cursor: 'pointer' }}
                        >
                          <td>
                            <strong>{device.name || device.deviceId}</strong>
                            {device.description && (
                              <div><small className="text-muted">{device.description}</small></div>
                            )}
                          </td>
                          <td>
                            {hasLocation ? 
                              <span className="text-success">● Online</span> : 
                              <span className="text-secondary">● No data</span>
                            }
                          </td>
                          <td>
                            {hasLocation ? 
                              new Date(device.lastTelemetry.timestamp).toLocaleString() : 
                              'Never'
                            }
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </Table>
              </div>
            )}
          </div>
        </Card.Body>
      </Card>
      
      {/* Device Registration Modal - Hidden but kept for future use */}
      <DeviceRegister 
        show={showRegisterModal} 
        onHide={() => {}} 
        onDeviceRegistered={fetchDevices}
        companyId={selectedCompany?.companyId}
      />
    </>
  );
};

export default DeviceList;
