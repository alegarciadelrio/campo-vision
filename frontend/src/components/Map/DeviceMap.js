import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { Container, Card, Row, Col } from 'react-bootstrap';
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

const DeviceMap = ({ selectedDevice, initialDeviceId, initialPosition }) => {
  const [devices, setDevices] = useState([]);
  const [deviceId, setDeviceId] = useState(initialDeviceId || '');
  const [mapCenter, setMapCenter] = useState(initialPosition || [-33.4, -70.9]); // Default to central Chile (lat, lng)
  const [mapZoom, setMapZoom] = useState(9);

  // Function to fetch device data
  const fetchDeviceData = async (id) => {
    if (!id) {
      console.log('No device ID provided');
      return;
    }
    
    try {
      // Fetch telemetry data (most recent only)
      const response = await getTelemetryData(id);
      
      if (response.telemetry.length === 0) {
        console.log('No data found for this device');
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
      console.error('Error fetching device data:', err);
    }
  };

  // Effect to update map when selected device changes
  useEffect(() => {
    if (selectedDevice && selectedDevice.deviceId) {
      setDeviceId(selectedDevice.deviceId);
      
      if (selectedDevice.lastTelemetry && 
          selectedDevice.lastTelemetry.latitude && 
          selectedDevice.lastTelemetry.longitude) {
        // Set map center to the device's last position
        setMapCenter([selectedDevice.lastTelemetry.latitude, selectedDevice.lastTelemetry.longitude]);
        setMapZoom(13);
        
        // Update devices array with the last telemetry data
        setDevices([selectedDevice.lastTelemetry]);
      } else {
        // If no telemetry data is available, fetch it
        fetchDeviceData(selectedDevice.deviceId);
      }
    }
  }, [selectedDevice]);

  return (
    <Container fluid className="h-100">
      <Row className="h-100">
        <Col md={12}>
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
