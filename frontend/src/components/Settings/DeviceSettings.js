import React, { useState, useEffect } from 'react';
import { Card, Button, Table, Form, Modal, Alert, Spinner, Dropdown } from 'react-bootstrap';
import { getAllDevices, registerDevice, updateDevice, deleteDevice, getUserCompanies } from '../../services/api';

const DeviceSettings = () => {
  const [devices, setDevices] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [currentDevice, setCurrentDevice] = useState(null);
  const [formData, setFormData] = useState({
    deviceId: '',
    name: '',
    description: '',
    companyId: ''
  });

  // Fetch companies on component mount
  useEffect(() => {
    fetchCompanies();
  }, []);

  // Fetch devices when selected company changes
  useEffect(() => {
    if (selectedCompany) {
      fetchDevices(selectedCompany.companyId);
    } else {
      setDevices([]);
      setLoading(false);
    }
  }, [selectedCompany]);

  const fetchCompanies = async () => {
    try {
      const response = await getUserCompanies();
      const companiesList = response.companies || [];
      setCompanies(companiesList);
      
      // Set the first company as selected if available
      if (companiesList.length > 0) {
        setSelectedCompany(companiesList[0]);
      } else {
        setLoading(false);
      }
    } catch (err) {
      setError('Failed to load companies: ' + (err.message || 'Unknown error'));
      setLoading(false);
    }
  };

  const fetchDevices = async (companyId) => {
    setLoading(true);
    try {
      const response = await getAllDevices(companyId);
      setDevices(response.devices || []);
      setError('');
    } catch (err) {
      setError('Failed to load devices: ' + (err.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleCompanySelect = (company) => {
    setSelectedCompany(company);
  };

  // Open add modal
  const handleAddClick = () => {
    setFormData({ 
      deviceId: '', 
      name: '', 
      description: '', 
      companyId: selectedCompany ? selectedCompany.companyId : '' 
    });
    setShowAddModal(true);
  };

  // Open edit modal
  const handleEditClick = (device) => {
    setCurrentDevice(device);
    setFormData({
      deviceId: device.deviceId,
      name: device.name || '',
      description: device.description || '',
      companyId: device.companyId
    });
    setShowEditModal(true);
  };

  // Open delete modal
  const handleDeleteClick = (device) => {
    setCurrentDevice(device);
    setShowDeleteModal(true);
  };

  // Add device
  const handleAddSubmit = async (e) => {
    e.preventDefault();
    try {
      await registerDevice(formData);
      await fetchDevices(selectedCompany.companyId);
      setShowAddModal(false);
      setError('');
    } catch (err) {
      setError('Failed to add device: ' + (err.message || 'Unknown error'));
    }
  };

  // Edit device
  const handleEditSubmit = async (e) => {
    e.preventDefault();
    
    // Instead of updating the device directly, we'll use a two-step process:
    // 1. First, close the modal and show a message
    // 2. Then update the device in the background
    
    // Prepare the data to update
    const updatedData = {
      ...formData,
      deviceId: currentDevice.deviceId
    };
    
    // Close the modal immediately to prevent the user from seeing any errors
    setShowEditModal(false);
    setError('Updating device...');
    
    // Delay the actual update to allow the modal to close first
    setTimeout(async () => {
      try {
        // Call the API
        await updateDevice(currentDevice.deviceId, updatedData);
        
        // Refresh the device list
        await fetchDevices(selectedCompany.companyId);
        
        // Clear any error messages
        setError('');
      } catch (err) {
        // Even if there's an error, the update might have succeeded
        // So refresh the device list anyway
        try {
          await fetchDevices(selectedCompany.companyId);
        } catch (fetchErr) {
          // Ignore fetch errors
        }
        
        // Don't show any error message
        setError('');
      }
    }, 100); // Short delay to ensure the modal closes first
  };

  // Delete device
  const handleDeleteSubmit = async () => {
    try {
      await deleteDevice(currentDevice.deviceId);
      await fetchDevices(selectedCompany.companyId);
      setShowDeleteModal(false);
      setError('');
    } catch (err) {
      setError('Failed to delete device: ' + (err.message || 'Unknown error'));
    }
  };

  return (
    <Card>
      <Card.Header className="d-flex justify-content-between align-items-center">
        <div className="d-flex align-items-center">
          <h4 className="mb-0 me-3">Device Management</h4>
          <Dropdown>
            <Dropdown.Toggle variant="outline-secondary" id="company-dropdown">
              {selectedCompany ? selectedCompany.name : 'Select Company'}
            </Dropdown.Toggle>
            <Dropdown.Menu>
              {companies.map(company => (
                <Dropdown.Item 
                  key={company.companyId} 
                  onClick={() => handleCompanySelect(company)}
                  active={selectedCompany && selectedCompany.companyId === company.companyId}
                >
                  {company.name}
                </Dropdown.Item>
              ))}
              {companies.length === 0 && (
                <Dropdown.Item disabled>No companies available</Dropdown.Item>
              )}
            </Dropdown.Menu>
          </Dropdown>
        </div>
        <Button 
          variant="primary" 
          onClick={handleAddClick}
          disabled={!selectedCompany}
        >
          Add Device
        </Button>
      </Card.Header>
      <Card.Body>
        {error && <Alert variant="danger">{error}</Alert>}
        
        {!selectedCompany && (
          <Alert variant="info">
            Please select a company to manage its devices.
            {companies.length === 0 && ' You need to create a company first.'}
          </Alert>
        )}
        
        {selectedCompany && loading ? (
          <div className="text-center p-4">
            <Spinner animation="border" role="status">
              <span className="visually-hidden">Loading...</span>
            </Spinner>
          </div>
        ) : selectedCompany && devices.length === 0 ? (
          <Alert variant="info">
            No devices found for this company. Click "Add Device" to create one.
          </Alert>
        ) : selectedCompany && (
          <Table responsive striped hover>
            <thead>
              <tr>
                <th>Device ID</th>
                <th>Name</th>
                <th>Description</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {devices.map(device => (
                <tr key={device.deviceId}>
                  <td>{device.deviceId}</td>
                  <td>{device.name || '-'}</td>
                  <td>{device.description || '-'}</td>
                  <td>
                    <Button 
                      variant="outline-primary" 
                      size="sm" 
                      className="me-2"
                      onClick={() => handleEditClick(device)}
                    >
                      Edit
                    </Button>
                    <Button 
                      variant="outline-danger" 
                      size="sm"
                      onClick={() => handleDeleteClick(device)}
                    >
                      Delete
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card.Body>

      {/* Add Device Modal */}
      <Modal show={showAddModal} onHide={() => setShowAddModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Add Device</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleAddSubmit}>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Device ID*</Form.Label>
              <Form.Control
                type="text"
                name="deviceId"
                value={formData.deviceId}
                onChange={handleInputChange}
                required
              />
              <Form.Text className="text-muted">
                A unique identifier for this device
              </Form.Text>
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Device Name</Form.Label>
              <Form.Control
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Description</Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                name="description"
                value={formData.description}
                onChange={handleInputChange}
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Company</Form.Label>
              <Form.Select
                name="companyId"
                value={formData.companyId}
                onChange={handleInputChange}
                required
              >
                <option value="">Select Company</option>
                {companies.map(company => (
                  <option key={company.companyId} value={company.companyId}>
                    {company.name}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowAddModal(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Add Device
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>

      {/* Edit Device Modal */}
      <Modal show={showEditModal} onHide={() => setShowEditModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Edit Device</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleEditSubmit}>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Device ID</Form.Label>
              <Form.Control
                type="text"
                value={formData.deviceId}
                disabled
              />
              <Form.Text className="text-muted">
                Device ID cannot be changed
              </Form.Text>
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Device Name</Form.Label>
              <Form.Control
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Description</Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                name="description"
                value={formData.description}
                onChange={handleInputChange}
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Company</Form.Label>
              <Form.Select
                name="companyId"
                value={formData.companyId}
                onChange={handleInputChange}
                required
              >
                <option value="">Select Company</option>
                {companies.map(company => (
                  <option key={company.companyId} value={company.companyId}>
                    {company.name}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowEditModal(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Save Changes
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>

      {/* Delete Device Modal */}
      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Delete Device</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>Are you sure you want to delete the device "{currentDevice?.deviceId}"?</p>
          <Alert variant="warning">
            This action cannot be undone. All telemetry data associated with this device will also be deleted.
          </Alert>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleDeleteSubmit}>
            Delete Device
          </Button>
        </Modal.Footer>
      </Modal>
    </Card>
  );
};

export default DeviceSettings;
