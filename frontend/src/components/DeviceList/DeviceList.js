import React, { useState, useEffect } from 'react';
import { Card, ListGroup, Form, Button, Spinner, Alert } from 'react-bootstrap';
import { getAllDevices } from '../../services/api';

const DeviceList = ({ onDeviceSelect, selectedDeviceId }) => {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch devices on component mount
  useEffect(() => {
    fetchDevices();
  }, []);

  // Function to fetch all devices
  const fetchDevices = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await getAllDevices();
      setDevices(response.devices || []);
    } catch (err) {
      setError('Error fetching devices: ' + (err.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  // Filter devices based on search term
  const filteredDevices = devices.filter(device => 
    device.deviceId.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (device.name && device.name.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <Card className="mb-4 h-100">
      <Card.Header className="bg-primary text-white">
        <h5 className="mb-0">Registered Devices</h5>
      </Card.Header>
      <Card.Body className="p-0 d-flex flex-column">
        <Form className="p-3">
          <Form.Group>
            <Form.Control
              type="text"
              placeholder="Search devices..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </Form.Group>
          <div className="d-flex justify-content-end mt-2">
            <Button 
              variant="outline-primary" 
              size="sm"
              onClick={fetchDevices}
              disabled={loading}
            >
              {loading ? <Spinner animation="border" size="sm" /> : 'Refresh'}
            </Button>
          </div>
        </Form>

        {error && <Alert variant="danger" className="mx-3">{error}</Alert>}
        
        <div className="flex-grow-1 overflow-auto">
          {loading && !devices.length ? (
            <div className="text-center p-4">
              <Spinner animation="border" />
              <p className="mt-2">Loading devices...</p>
            </div>
          ) : filteredDevices.length === 0 ? (
            <div className="text-center p-4">
              <p className="text-muted">No devices found</p>
            </div>
          ) : (
            <ListGroup variant="flush">
              {filteredDevices.map((device) => {
                const isSelected = selectedDeviceId === device.deviceId;
                const hasLocation = device.lastTelemetry && 
                                   device.lastTelemetry.latitude && 
                                   device.lastTelemetry.longitude;
                
                return (
                  <ListGroup.Item 
                    key={device.deviceId}
                    action
                    active={isSelected}
                    onClick={() => onDeviceSelect(device)}
                    className="d-flex flex-column"
                  >
                    <div className="d-flex justify-content-between align-items-center">
                      <strong>{device.name || device.deviceId}</strong>
                      {hasLocation && <small className="text-success">● Online</small>}
                      {!hasLocation && <small className="text-secondary">● No data</small>}
                    </div>
                    {device.description && (
                      <small className="text-muted">{device.description}</small>
                    )}
                    {hasLocation && (
                      <small className="mt-1">
                        Last seen: {new Date(device.lastTelemetry.timestamp).toLocaleString()}
                      </small>
                    )}
                  </ListGroup.Item>
                );
              })}
            </ListGroup>
          )}
        </div>
      </Card.Body>
    </Card>
  );
};

export default DeviceList;
