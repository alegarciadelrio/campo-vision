import React, { useState } from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import DeviceList from '../DeviceList/DeviceList';
import DeviceMap from '../Map/DeviceMap';

const Dashboard = () => {
  const [selectedDevice, setSelectedDevice] = useState(null);
  
  // Handle device selection from the list
  const handleDeviceSelect = (device) => {
    setSelectedDevice(device);
  };
  
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
