import React, { useState, useEffect, useContext } from 'react';
import ThemeContext from '../../context/ThemeContext';
import { Container, Row, Col, Alert, Spinner, Card, Form, Button } from 'react-bootstrap';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import DeviceList from '../DeviceList/DeviceList';
import { getTelemetryData } from '../../services/api';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const Metrics = () => {
  const { theme } = useContext(ThemeContext) || { theme: 'light' };
  const isDarkMode = theme === 'dark';
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [telemetryData, setTelemetryData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [timeRange, setTimeRange] = useState('24h'); // Default to last 24 hours
  const [enabledAttributes, setEnabledAttributes] = useState({});
  
  // Fetch telemetry data when a device is selected
  useEffect(() => {
    if (selectedDevice) {
      fetchTelemetryData();
    } else {
      setTelemetryData([]);
    }
  }, [selectedDevice, timeRange]);
  
  // Initialize enabled attributes when telemetry data changes
  useEffect(() => {
    if (telemetryData.length > 0) {
      const attributes = getGraphAttributes();
      const initialState = {};
      
      // Set all attributes to enabled by default
      attributes.forEach(attr => {
        initialState[attr] = true;
      });
      
      setEnabledAttributes(initialState);
    }
  }, [telemetryData.length]);
  
  // Function to fetch telemetry data for the selected device
  const fetchTelemetryData = async () => {
    if (!selectedDevice) return;
    
    setLoading(true);
    setError('');
    
    try {
      // Calculate start and end times based on selected time range
      let endTime = new Date().toISOString();
      let startTime;
      
      switch (timeRange) {
        case '1h':
          startTime = new Date(Date.now() - 60 * 60 * 1000).toISOString();
          break;
        case '6h':
          startTime = new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString();
          break;
        case '24h':
          startTime = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
          break;
        case '7d':
          startTime = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
          break;
        case '30d':
          startTime = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString();
          break;
        default:
          startTime = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
      }
      
      // No specific date handling needed anymore
      
      console.log('Fetching telemetry data with params:', { deviceId: selectedDevice.deviceId, startTime, endTime });
      const response = await getTelemetryData(selectedDevice.deviceId, startTime, endTime);
      console.log('API response:', response);
      
      // Handle different response formats
      let telemetryItems = [];
      
      // Based on the logs, the telemetry data is in response.telemetry
      if (response.telemetry && Array.isArray(response.telemetry)) {
        console.log('Found telemetry data in response.telemetry');
        telemetryItems = response.telemetry;
      } else if (response.items && Array.isArray(response.items)) {
        telemetryItems = response.items;
      } else if (response.data && Array.isArray(response.data)) {
        telemetryItems = response.data;
      } else if (Array.isArray(response)) {
        telemetryItems = response;
      }
      
      console.log('Processed telemetry items:', telemetryItems);
      setTelemetryData(telemetryItems);
    } catch (err) {
      setError('Error fetching telemetry data: ' + (err.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };
  
  // Handle device selection from the list
  const handleDeviceSelect = (device) => {
    setSelectedDevice(device);
  };
  
  // Get unique telemetry attributes from data
  const getTelemetryAttributes = () => {
    if (!telemetryData || telemetryData.length === 0) return [];
    
    // Get all keys from the first item, excluding timestamp and any metadata fields
    const excludedFields = ['timestamp', 'deviceId', 'id', 'createdAt', 'updatedAt'];
    const firstItem = telemetryData[0];
    
    console.log('First telemetry item:', firstItem);
    
    // Check if we have any telemetry data
    if (!firstItem) return [];
    
    const attributes = Object.keys(firstItem).filter(key => !excludedFields.includes(key));
    console.log('Detected attributes:', attributes);
    return attributes;
  };
  
  // Get attributes to display as graphs (excluding latitude and longitude)
  const getGraphAttributes = () => {
    const allAttributes = getTelemetryAttributes();
    const excludedFromGraphs = ['latitude', 'longitude'];
    return allAttributes.filter(attr => !excludedFromGraphs.includes(attr));
  };
  
  // Get enabled graph attributes (attributes that are toggled on)
  const getEnabledGraphAttributes = () => {
    return getGraphAttributes().filter(attr => enabledAttributes[attr] !== false);
  };
  
  // Toggle attribute enabled/disabled state
  const toggleAttribute = (attribute) => {
    setEnabledAttributes(prev => ({
      ...prev,
      [attribute]: prev[attribute] === false ? true : false
    }));
  };
  
  // Get color for a specific attribute
  const getAttributeColor = (attribute, index) => {
    // Predefined colors for common attributes with increased brightness for dark mode
    const colorMap = {
      'temperature': { border: 'rgb(255, 99, 132)', background: 'rgba(255, 99, 132, 0.7)' },
      'humidity': { border: 'rgb(54, 162, 235)', background: 'rgba(54, 162, 235, 0.7)' },
      'pressure': { border: 'rgb(75, 192, 192)', background: 'rgba(75, 192, 192, 0.7)' },
      'latitude': { border: 'rgb(153, 102, 255)', background: 'rgba(153, 102, 255, 0.7)' },
      'longitude': { border: 'rgb(255, 159, 64)', background: 'rgba(255, 159, 64, 0.7)' },
      'altitude': { border: 'rgb(255, 205, 86)', background: 'rgba(255, 205, 86, 0.7)' },
      'speed': { border: 'rgb(201, 203, 207)', background: 'rgba(201, 203, 207, 0.7)' },
      'battery': { border: 'rgb(75, 192, 75)', background: 'rgba(75, 192, 75, 0.7)' }
    };
    
    // Return predefined color if available, otherwise generate based on index
    if (colorMap[attribute]) {
      return colorMap[attribute];
    } else {
      // Generate colors based on index for attributes not in the map
      // Increased saturation and lightness for better visibility in dark mode
      const hue = (index * 137) % 360; // Golden angle approximation for good distribution
      return {
        border: `hsl(${hue}, 80%, 60%)`,
        background: `hsla(${hue}, 80%, 60%, 0.7)`
      };
    }
  };
  
  // Prepare chart data
  const prepareChartData = (dataType) => {
    if (!telemetryData || telemetryData.length === 0) {
      return {
        labels: [],
        datasets: [
          {
            label: dataType,
            data: [],
            borderColor: getAttributeColor(dataType, 0).border,
            backgroundColor: getAttributeColor(dataType, 0).background,
          },
        ],
      };
    }
    
    // Sort data by timestamp
    const sortedData = [...telemetryData].sort((a, b) => 
      new Date(a.timestamp) - new Date(b.timestamp)
    );
    
    return {
      labels: sortedData.map(item => {
        const date = new Date(item.timestamp);
        return date.toLocaleString();
      }),
      datasets: [
        {
          label: dataType,
          data: sortedData.map(item => item[dataType]),
          borderColor: getAttributeColor(dataType, 0).border,
          backgroundColor: getAttributeColor(dataType, 0).background,
        },
      ],
    };
  };
  
  // Chart options that work in both light and dark modes
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          font: {
            weight: 'bold'
          }
        }
      },
      title: {
        display: true,
        text: 'Telemetry Data',
        font: {
          size: 16,
          weight: 'bold'
        }
      },
    },
    scales: {
      x: {
        ticks: {
          maxRotation: 45,
          minRotation: 45,
          font: {
            size: 10
          }
        },
        grid: {
          display: true
        }
      },
      y: {
        beginAtZero: false,
        grace: '10%',  // Add some padding above and below data points
        ticks: {
          precision: 1,
          font: {
            size: 10
          }
        },
        grid: {
          display: true
        }
      }
    }
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
          <Card className="mb-4">
            <Card.Header className="d-flex justify-content-between align-items-center">
              <h4 className="mb-0">Telemetry Metrics</h4>
              <Form.Select 
                style={{ width: 'auto' }} 
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                disabled={!selectedDevice}
              >
                <option value="1h">Last Hour</option>
                <option value="6h">Last 6 Hours</option>
                <option value="24h">Last 24 Hours</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
              </Form.Select>
            </Card.Header>
            <Card.Body>
              {!selectedDevice ? (
                <Alert variant="info">
                  Please select a device from the list to view metrics.
                </Alert>
              ) : loading ? (
                <div className="text-center p-4">
                  <Spinner animation="border" />
                  <p className="mt-2">Loading telemetry data...</p>
                </div>
              ) : error ? (
                <Alert variant="danger">{error}</Alert>
              ) : telemetryData.length === 0 ? (
                <Alert variant="warning">
                  No telemetry data available for the selected time range.
                </Alert>
              ) : (
                <div>
                  {/* Display available attributes at the top with improved contrast */}
                  <Card className="mb-4">
                    <Card.Header className="d-flex justify-content-between align-items-center">
                      <h4 className="mb-0">Available Telemetry Attributes</h4>
                    </Card.Header>
                    <Card.Body>
                      <div className="d-flex flex-wrap gap-2">
                        {getGraphAttributes().map((attribute, index) => (
                          <div 
                            key={attribute} 
                            className={`badge ${enabledAttributes[attribute] !== false ? 'bg-primary text-white' : 'bg-secondary text-white'} p-2 d-flex align-items-center cursor-pointer`}
                            style={{ 
                              borderLeft: `4px solid ${getAttributeColor(attribute, index).border}`,
                              fontSize: '1rem',
                              cursor: 'pointer',
                              opacity: enabledAttributes[attribute] !== false ? 1 : 0.6,
                              boxShadow: enabledAttributes[attribute] !== false ? '0 2px 4px rgba(0,0,0,0.2)' : 'none'
                            }}
                            onClick={() => toggleAttribute(attribute)}
                            title={`Click to ${enabledAttributes[attribute] !== false ? 'disable' : 'enable'} ${attribute} graph`}
                          >
                            {attribute}
                            {enabledAttributes[attribute] !== false ? 
                              <span className="ms-2 text-success">✓</span> : 
                              <span className="ms-2 text-danger">✕</span>
                            }
                          </div>
                        ))}
                      </div>
                    </Card.Body>
                  </Card>
                  
                  {/* Dynamically generate charts for each enabled attribute with improved contrast */}
                  <Row className="mb-4">
                    {getEnabledGraphAttributes().map((attribute, index) => (
                      <Col md={6} key={attribute} className="mb-4">
                        <Card>
                          <Card.Header className="text-capitalize d-flex justify-content-between align-items-center">
                            <strong>{attribute}</strong>
                            <Button 
                              variant="danger" 
                              size="sm"
                              onClick={() => toggleAttribute(attribute)}
                              title={`Disable ${attribute} graph`}
                            >
                              Hide
                            </Button>
                          </Card.Header>
                          <Card.Body style={{ minHeight: '300px' }}>
                            <Line options={chartOptions} data={prepareChartData(attribute)} />
                          </Card.Body>
                        </Card>
                      </Col>
                    ))}
                  </Row>
                  
                  {/* Table showing all telemetry values with improved contrast */}
                  <Card className="mb-4">
                    <Card.Header className="d-flex justify-content-between align-items-center">
                      <h4 className="mb-0">Telemetry Data Table</h4>
                    </Card.Header>
                    <Card.Body className="p-0">
                      <div className="table-responsive">
                        <table className={`table table-striped table-hover table-sm`}>
                          <thead>
                            <tr>
                              <th>Timestamp</th>
                              {getGraphAttributes().map(attribute => (
                                <th key={attribute} className="text-capitalize">{attribute}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {telemetryData.length === 0 ? (
                              <tr>
                                <td colSpan={getGraphAttributes().length + 1} className="text-center">
                                  No data available
                                </td>
                              </tr>
                            ) : (
                              [...telemetryData]
                                .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
                                .map((item, index) => (
                                  <tr key={index}>
                                    <td>{new Date(item.timestamp).toLocaleString()}</td>
                                    {getGraphAttributes().map(attribute => (
                                      <td key={attribute}>
                                        {item[attribute] !== undefined ? 
                                          typeof item[attribute] === 'number' ? 
                                            item[attribute].toFixed(2) : 
                                            item[attribute]
                                          : '-'}
                                      </td>
                                    ))}
                                  </tr>
                                ))
                            )}
                          </tbody>
                        </table>
                      </div>
                    </Card.Body>
                  </Card>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Metrics;
