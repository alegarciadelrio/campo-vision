import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { Container, Card, Form, Button, Row, Col } from 'react-bootstrap';
import { getTelemetryData } from '../../services/api';
import L from 'leaflet';
// Import Leaflet CSS in index.js instead

// Fix Leaflet icon issues
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

// Component to fit map bounds to markers
const FitBounds = ({ positions }) => {
  const map = useMap();
  
  if (positions.length > 0) {
    const bounds = L.latLngBounds(positions);
    map.fitBounds(bounds, { padding: [50, 50] });
  }
  
  return null;
};

const DeviceMap = () => {
  const [devices, setDevices] = useState([]);
  const [deviceId, setDeviceId] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mapCenter, setMapCenter] = useState([-33.4, -70.9]); // Default to central Chile (lat, lng)
  const [mapZoom, setMapZoom] = useState(9);

  // Function to fetch device data
  const fetchDeviceData = async () => {
    if (!deviceId) {
      setError('Please enter a Device ID');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      // Format dates for API
      const formattedStartDate = startDate ? new Date(startDate).toISOString() : undefined;
      const formattedEndDate = endDate ? new Date(endDate).toISOString() : undefined;
      
      // Fetch telemetry data
      const response = await getTelemetryData(deviceId, formattedStartDate, formattedEndDate);
      
      if (response.telemetry.length === 0) {
        setError('No data found for this device in the selected time range');
        setDevices([]);
        return;
      }
      
      setDevices(response.telemetry);
      
      // Set map center to the most recent device position
      if (response.telemetry.length > 0) {
        const latestDevice = response.telemetry[0];
        setMapCenter([latestDevice.latitude, latestDevice.longitude]);
        setMapZoom(13);
      }
    } catch (err) {
      setError('Error fetching device data: ' + (err.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container fluid className="mt-4">
      <Row>
        <Col md={3}>
          <Card className="mb-4">
            <Card.Header className="bg-primary text-white">
              <h5 className="mb-0">Device Filter</h5>
            </Card.Header>
            <Card.Body>
              <Form>
                <Form.Group className="mb-3">
                  <Form.Label>Device ID</Form.Label>
                  <Form.Control
                    type="text"
                    value={deviceId}
                    onChange={(e) => setDeviceId(e.target.value)}
                    placeholder="Enter device ID"
                  />
                </Form.Group>
                
                <Form.Group className="mb-3">
                  <Form.Label>Start Date</Form.Label>
                  <Form.Control
                    type="datetime-local"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                  />
                </Form.Group>
                
                <Form.Group className="mb-3">
                  <Form.Label>End Date</Form.Label>
                  <Form.Control
                    type="datetime-local"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                  />
                </Form.Group>
                
                <Button 
                  variant="primary" 
                  onClick={fetchDeviceData}
                  disabled={loading}
                  className="w-100"
                >
                  {loading ? 'Loading...' : 'Search'}
                </Button>
              </Form>
              
              {error && <div className="text-danger mt-3">{error}</div>}
            </Card.Body>
          </Card>
          
          {devices.length > 0 && (
            <Card>
              <Card.Header className="bg-success text-white">
                <h5 className="mb-0">Device Data</h5>
              </Card.Header>
              <Card.Body style={{ maxHeight: '300px', overflowY: 'auto' }}>
                <div className="small">
                  {devices.map((device, index) => (
                    <div key={index} className="mb-3 p-2 border-bottom">
                      <div><strong>Time:</strong> {new Date(device.timestamp).toLocaleString()}</div>
                      <div><strong>Lat/Long:</strong> {device.latitude}, {device.longitude}</div>
                      <div><strong>Temp:</strong> {device.temperature}°C</div>
                    </div>
                  ))}
                </div>
              </Card.Body>
            </Card>
          )}
        </Col>
        
        <Col md={9}>
          <Card className="map-container" style={{ height: '80vh' }}>
            <Card.Body className="p-0">
              <MapContainer 
                center={mapCenter} 
                zoom={mapZoom} 
                style={{ width: '100%', height: '100%' }}
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                
                {devices.map((device, index) => (
                  <Marker 
                    key={index} 
                    position={[device.latitude, device.longitude]}
                    icon={index === 0 ? 
                      L.icon({
                        iconUrl: icon,
                        shadowUrl: iconShadow,
                        iconSize: [25, 41],
                        iconAnchor: [12, 41],
                        className: 'first-marker'
                      }) : DefaultIcon
                    }
                  >
                    <Popup>
                      <div>
                        <h5>Device: {device.deviceId}</h5>
                        <p>Temperature: {device.temperature}°C</p>
                        <p>Time: {new Date(device.timestamp).toLocaleString()}</p>
                      </div>
                    </Popup>
                  </Marker>
                ))}
                
                {devices.length > 0 && (
                  <FitBounds 
                    positions={devices.map(device => [device.latitude, device.longitude])}
                  />
                )}
              </MapContainer>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default DeviceMap;
