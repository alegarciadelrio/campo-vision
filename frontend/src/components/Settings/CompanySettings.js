import React, { useState, useEffect } from 'react';
import { Card, Button, Table, Form, Modal, Alert, Spinner } from 'react-bootstrap';
import { getUserCompanies, registerCompany, updateCompany, deleteCompany } from '../../services/api';

const CompanySettings = () => {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [currentCompany, setCurrentCompany] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: ''
  });

  // Fetch companies on component mount
  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    setLoading(true);
    try {
      const response = await getUserCompanies();
      setCompanies(response.companies || []);
      setError('');
    } catch (err) {
      setError('Failed to load companies: ' + (err.message || 'Unknown error'));
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

  // Open add modal
  const handleAddClick = () => {
    setFormData({ name: '', description: '' });
    setShowAddModal(true);
  };

  // Open edit modal
  const handleEditClick = (company) => {
    setCurrentCompany(company);
    setFormData({
      name: company.name,
      description: company.description || ''
    });
    setShowEditModal(true);
  };

  // Open delete modal
  const handleDeleteClick = (company) => {
    setCurrentCompany(company);
    setShowDeleteModal(true);
  };

  // Add company
  const handleAddSubmit = async (e) => {
    e.preventDefault();
    try {
      await registerCompany(formData);
      await fetchCompanies();
      setShowAddModal(false);
      setError('');
    } catch (err) {
      setError('Failed to add company: ' + (err.message || 'Unknown error'));
    }
  };

  // Edit company
  const handleEditSubmit = async (e) => {
    e.preventDefault();
    // Prepare the data to update
    const updatedData = {
      ...formData,
      companyId: currentCompany.companyId
    };
    
    // Call the API with the new approach that doesn't throw errors
    const result = await updateCompany(currentCompany.companyId, updatedData);
    
    if (result.success) {
      // Normal success flow
      await fetchCompanies();
      setShowEditModal(false);
      setError('');
    } else if (result.partialSuccess) {
      // Partial success - update might have worked but had response issues
      setError(result.message || 'Company may have been updated. Please refresh to confirm.');
      setShowEditModal(false);
      // Try to fetch companies to refresh the list
      try {
        await fetchCompanies();
      } catch (fetchErr) {
        // Don't log the error to console
      }
    } else {
      // Definite failure
      setError(result.message || 'Failed to update company');
    }
  };

  // Delete company
  const handleDeleteSubmit = async () => {
    try {
      setShowDeleteModal(false); // Close modal immediately
      setError('Deleting company and associated devices...');
      
      await deleteCompany(currentCompany.companyId);
      await fetchCompanies();
      setError('');
    } catch (err) {
      setError('Failed to delete company: ' + (err.message || 'Unknown error'));
      // Try to refresh the companies list anyway
      try {
        await fetchCompanies();
      } catch (fetchErr) {
        // Ignore fetch errors
      }
    }
  };

  return (
    <Card>
      <Card.Header className="d-flex justify-content-between align-items-center">
        <h4 className="mb-0">Company Management</h4>
        <Button variant="primary" onClick={handleAddClick}>
          Add Company
        </Button>
      </Card.Header>
      <Card.Body>
        {error && <Alert variant="danger">{error}</Alert>}
        
        {loading ? (
          <div className="text-center p-4">
            <Spinner animation="border" role="status">
              <span className="visually-hidden">Loading...</span>
            </Spinner>
          </div>
        ) : companies.length === 0 ? (
          <Alert variant="info">
            You don't have any companies yet. Click "Add Company" to create one.
          </Alert>
        ) : (
          <Table responsive striped hover>
            <thead>
              <tr>
                <th>Name</th>
                <th>Description</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {companies.map(company => (
                <tr key={company.companyId}>
                  <td>{company.name}</td>
                  <td>{company.description || '-'}</td>
                  <td>
                    <Button 
                      variant="outline-primary" 
                      size="sm" 
                      className="me-2"
                      onClick={() => handleEditClick(company)}
                    >
                      Edit
                    </Button>
                    <Button 
                      variant="outline-danger" 
                      size="sm"
                      onClick={() => handleDeleteClick(company)}
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

      {/* Add Company Modal */}
      <Modal show={showAddModal} onHide={() => setShowAddModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Add Company</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleAddSubmit}>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Company Name*</Form.Label>
              <Form.Control
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                required
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
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowAddModal(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Add Company
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>

      {/* Edit Company Modal */}
      <Modal show={showEditModal} onHide={() => setShowEditModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Edit Company</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleEditSubmit}>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Company Name*</Form.Label>
              <Form.Control
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                required
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

      {/* Delete Company Modal */}
      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Delete Company</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>Are you sure you want to delete the company "{currentCompany?.name}"?</p>
          <Alert variant="warning">
            This action cannot be undone. All devices associated with this company will also be deleted.
          </Alert>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleDeleteSubmit}>
            Delete Company
          </Button>
        </Modal.Footer>
      </Modal>
    </Card>
  );
};

export default CompanySettings;
