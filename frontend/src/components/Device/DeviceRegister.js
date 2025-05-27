import React, { useState } from 'react';
import { Modal, Form, Button, Alert } from 'react-bootstrap';
import { registerDevice } from '../../services/api';

const DeviceRegister = ({ show, onHide, onDeviceRegistered, companyId }) => {
  const [deviceData, setDeviceData] = useState({
    deviceId: '',
    name: '',
    description: '',
    companyId: companyId || ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setDeviceData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess(false);

    try {
      // Ensure companyId is set
      if (!deviceData.companyId && companyId) {
        deviceData.companyId = companyId;
      }

      // Validate required fields
      if (!deviceData.deviceId) {
        throw new Error('Device ID is required');
      }
      if (!deviceData.companyId) {
        throw new Error('Company ID is required');
      }

      await registerDevice(deviceData);
      setSuccess(true);
      setDeviceData({
        deviceId: '',
        name: '',
        description: '',
        companyId: companyId || ''
      });
      
      // Notify parent component
      if (onDeviceRegistered) {
        onDeviceRegistered();
      }
      
      // Close modal after a short delay
      setTimeout(() => {
        onHide();
      }, 1500);
    } catch (err) {
      setError('Error registering device: ' + (err.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title>Register New Device</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {error && <Alert variant="danger">{error}</Alert>}
        {success && <Alert variant="success">Device registered successfully!</Alert>}
        
        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-3">
            <Form.Label>Device ID*</Form.Label>
            <Form.Control
              type="text"
              name="deviceId"
              value={deviceData.deviceId}
              onChange={handleChange}
              placeholder="Enter unique device identifier"
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
              value={deviceData.name}
              onChange={handleChange}
              placeholder="Enter device name"
            />
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Description</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              name="description"
              value={deviceData.description}
              onChange={handleChange}
              placeholder="Enter device description"
            />
          </Form.Group>

          <div className="d-flex justify-content-end">
            <Button variant="secondary" onClick={onHide} className="me-2">
              Cancel
            </Button>
            <Button variant="primary" type="submit" disabled={loading}>
              {loading ? 'Registering...' : 'Register Device'}
            </Button>
          </div>
        </Form>
      </Modal.Body>
    </Modal>
  );
};

export default DeviceRegister;
