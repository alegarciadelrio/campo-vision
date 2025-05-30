import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, Polyline } from 'react-leaflet';
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
  
  useEffect(() => {
    if (positions && positions.length > 0) {
      const bounds = L.latLngBounds(positions);
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [map, positions]);
  
  return null;
};

const DeviceMap = ({ selectedDevice, allDevices, initialDeviceId, initialPosition }) => {
  const { theme } = useTheme();
  const [deviceTelemetry, setDeviceTelemetry] = useState([]);
  const [deviceId, setDeviceId] = useState(initialDeviceId || '');
  const [mapCenter, setMapCenter] = useState(initialPosition || [-33.4, -70.9]); // Default to central Chile (lat, lng)
  const [mapZoom, setMapZoom] = useState(9);
  const [displayedDevices, setDisplayedDevices] = useState([]);
  const [showTrack, setShowTrack] = useState(false); // State to control track visibility
  
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
      // Calculate a time range for the last hour
      const endTime = new Date().toISOString();
      const startTime = new Date(Date.now() - 60 * 60 * 1000).toISOString();
      
      // Fetch telemetry data with time range to get historical data for the track
      const response = await getTelemetryData(id, startTime, endTime);
      
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
      setShowTrack(false); // Reset track visibility when selecting a new device
      
      // Always fetch telemetry data when a device is selected to get the track
      // but we won't show it until the user clicks "See track"
      fetchDeviceData(selectedDevice.deviceId);
      
      if (selectedDevice.lastTelemetry && 
          selectedDevice.lastTelemetry.latitude && 
          selectedDevice.lastTelemetry.longitude) {
        // Set map center to the device's last position
        setMapCenter([selectedDevice.lastTelemetry.latitude, selectedDevice.lastTelemetry.longitude]);
        setMapZoom(13);
      }
    }
  }, [selectedDevice]);
  
  // Toggle track visibility
  const handleToggleTrack = () => {
    setShowTrack(!showTrack);
  };

  // Extract positions from telemetry data for the track line
  const getTrackPositions = () => {
    if (!deviceTelemetry || deviceTelemetry.length === 0) {
      return [];
    }
    
    // Sort telemetry data by timestamp (oldest to newest)
    const sortedTelemetry = [...deviceTelemetry].sort((a, b) => 
      new Date(a.timestamp) - new Date(b.timestamp)
    );
    
    // Extract positions for the polyline
    return sortedTelemetry.map(telemetry => {
      // Ensure we have valid coordinates
      if (typeof telemetry.latitude === 'number' && typeof telemetry.longitude === 'number') {
        return [telemetry.latitude, telemetry.longitude];
      }
      return null;
    }).filter(position => position !== null); // Filter out any null positions
  };

  return (
    <Container fluid className="h-100">
      <Row className="h-100">
        <Col md={12}>
          <Card className="map-container" style={{ height: '80vh' }}>
            <Card.Header className="d-flex justify-content-between align-items-center">
              <h4 className="mb-0">Device Map</h4>
              {selectedDevice && (
                <div className="d-flex align-items-center">
                  <div className="text-muted me-3">
                    {selectedDevice.name || selectedDevice.deviceId}
                  </div>
                  <button 
                    className={`btn btn-sm ${showTrack ? 'btn-secondary' : 'btn-primary'}`}
                    onClick={handleToggleTrack}
                  >
                    {showTrack ? 'Hide Track' : 'See Track'}
                  </button>
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
                
                {/* Display additional telemetry data for selected device if showTrack is true */}
                {showTrack && deviceTelemetry.length > 0 && deviceTelemetry.map((telemetry, index) => {
                  // Skip the first point (most recent) as it's already shown in the devices list
                  // and only show historical points when showTrack is true
                  if (index === 0 || !telemetry.latitude || !telemetry.longitude) return null;
                  
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
                
                {/* Add a polyline to show the device's track only when showTrack is true */}
                {showTrack && deviceTelemetry.length > 1 && (
                  <Polyline 
                    positions={getTrackPositions()} 
                    pathOptions={{ 
                      color: theme === 'dark' ? '#00ffff' : '#0000ff',
                      weight: 3,
                      opacity: 0.7,
                      dashArray: theme === 'dark' ? '' : '',
                    }}
                  />
                )}
                
                {/* Fit bounds to show all devices or just the selected one */}
                {displayedDevices.length > 0 && (
                  <FitBounds 
                    positions={
                      selectedDevice && showTrack && deviceTelemetry.length > 0
                      ? getTrackPositions()
                      : selectedDevice && selectedDevice.lastTelemetry
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
