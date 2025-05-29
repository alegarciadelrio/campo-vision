import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { Container, Card, Row, Col } from 'react-bootstrap';
import { getTelemetryData } from '../../services/api';
import { useTheme } from '../../context/ThemeContext';
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

const DeviceMap = ({ selectedDevice, allDevices, initialDeviceId, initialPosition }) => {
  const { theme } = useTheme();
  const [deviceTelemetry, setDeviceTelemetry] = useState([]);
  const [deviceId, setDeviceId] = useState(initialDeviceId || '');
  const [mapCenter, setMapCenter] = useState(initialPosition || [-33.4, -70.9]); // Default to central Chile (lat, lng)
  const [mapZoom, setMapZoom] = useState(9);
  const [displayedDevices, setDisplayedDevices] = useState([]);
  
  // Map style options for dark mode - adjust the darkMapStyle value to change the style
  // Options: 'esri_dark_gray', 'carto_dark', 'esri_world_imagery'
  const darkMapStyle = 'esri_world_imagery';
  
  // Map tile configurations
  const mapTiles = {
    light: {
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    },
    carto_dark: {
      url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | &copy; <a href="https://carto.com/attributions">CARTO</a>'
    },
    esri_dark_gray: {
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
      attribution: '&copy; <a href="https://www.esri.com/">Esri</a> | Sources: Esri, HERE, Garmin, FAO, NOAA, USGS, © OpenStreetMap contributors, and the GIS User Community'
    },
    esri_world_imagery: {
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    }
  };

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
        setDeviceTelemetry([]);
        return;
      }
      
      setDeviceTelemetry(response.telemetry);
      
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

  // Process all devices to display on the map
  useEffect(() => {
    if (allDevices && allDevices.length > 0) {
      // Filter devices that have telemetry data
      const devicesWithLocation = allDevices.filter(device => 
        device.lastTelemetry && 
        device.lastTelemetry.latitude && 
        device.lastTelemetry.longitude
      );
      
      // Update the displayed devices
      setDisplayedDevices(devicesWithLocation);
      
      // If no device is selected, fit the map to show all devices
      if (!selectedDevice && devicesWithLocation.length > 0) {
        // No need to set center as FitBounds component will handle it
        setMapZoom(9); // Default zoom to see multiple devices
      }
    } else {
      setDisplayedDevices([]);
    }
  }, [allDevices, selectedDevice]);
  
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
        
        // We'll still display all devices, but highlight the selected one
      } else {
        // If no telemetry data is available, fetch it
        fetchDeviceData(selectedDevice.deviceId);
        
        // Keep the current map view if we can't center on the selected device
        // This prevents errors when selecting a device without telemetry
      }
    }
  }, [selectedDevice]);

  return (
    <Container fluid className="h-100">
      <Row className="h-100">
        <Col md={12}>
          <Card className="map-container" style={{ height: '80vh' }}>
            <Card.Header className="d-flex justify-content-between align-items-center">
              <h4 className="mb-0">Device Map</h4>
              {selectedDevice && (
                <div className="text-muted">
                  {selectedDevice.name || selectedDevice.deviceId}
                </div>
              )}
            </Card.Header>
            <Card.Body className="p-0">
              <MapContainer 
                center={mapCenter} 
                zoom={mapZoom} 
                style={{ width: '100%', height: '100%' }}
              >
                {theme === 'dark' ? (
                  <TileLayer
                    attribution={mapTiles[darkMapStyle].attribution}
                    url={mapTiles[darkMapStyle].url}
                  />
                ) : (
                  <TileLayer
                    attribution={mapTiles.light.attribution}
                    url={mapTiles.light.url}
                  />
                )}
                
                {/* Display all devices on the map */}
                {displayedDevices.map((device, index) => {
                  // Only proceed if the device has valid telemetry data
                  if (!device.lastTelemetry || 
                      !device.lastTelemetry.latitude || 
                      !device.lastTelemetry.longitude) {
                    return null; // Skip devices without valid location data
                  }
                  
                  const isSelected = selectedDevice && device.deviceId === selectedDevice.deviceId;
                  const devicePosition = [
                    device.lastTelemetry.latitude,
                    device.lastTelemetry.longitude
                  ];
                  
                  return (
                    <Marker 
                      key={device.deviceId} 
                      position={devicePosition}
                      icon={isSelected ? 
                        L.icon({
                          iconUrl: icon,
                          shadowUrl: iconShadow,
                          iconSize: [25, 41],
                          iconAnchor: [12, 41],
                          className: 'selected-marker'
                        }) : DefaultIcon
                      }
                    >
                      <Popup>
                        <div>
                          <h5>{device.name || device.deviceId}</h5>
                          {device.description && <p>{device.description}</p>}
                          <p>Temperature: {device.lastTelemetry.temperature !== undefined ? `${device.lastTelemetry.temperature}°C` : 'N/A'}</p>
                          <p>Last seen: {new Date(device.lastTelemetry.timestamp).toLocaleString()}</p>
                        </div>
                      </Popup>
                    </Marker>
                  );
                })}
                
                {/* Display additional telemetry data for selected device if available */}
                {deviceTelemetry.length > 0 && deviceTelemetry.map((telemetry, index) => {
                  // Skip the first point as it's already shown in the devices list
                  if (index === 0) return null;
                  
                  return (
                    <Marker 
                      key={`telemetry-${index}`} 
                      position={[telemetry.latitude, telemetry.longitude]}
                      icon={DefaultIcon}
                      opacity={0.7} // Make historical points slightly transparent
                    >
                      <Popup>
                        <div>
                          <h5>Device: {telemetry.deviceId}</h5>
                          <p>Temperature: {telemetry.temperature}°C</p>
                          <p>Time: {new Date(telemetry.timestamp).toLocaleString()}</p>
                        </div>
                      </Popup>
                    </Marker>
                  );
                })}
                
                {/* Fit bounds to show all devices or just the selected one */}
                {displayedDevices.length > 0 && (
                  <FitBounds 
                    positions={
                      selectedDevice && selectedDevice.lastTelemetry 
                      ? [[selectedDevice.lastTelemetry.latitude, selectedDevice.lastTelemetry.longitude]] 
                      : displayedDevices.map(device => [device.lastTelemetry.latitude, device.lastTelemetry.longitude])}
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
