import React, { useState, useEffect } from 'react';
import { Form, Dropdown } from 'react-bootstrap';
import { getUserCompanies } from '../../services/api';

const CompanySelector = ({ onCompanyChange }) => {
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Load companies on component mount
  useEffect(() => {
    fetchCompanies();
  }, []);

  // Function to fetch companies for the current user
  const fetchCompanies = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await getUserCompanies();
      const userCompanies = response.companies || [];
      setCompanies(userCompanies);
      
      // If companies are available, select the first one by default
      if (userCompanies.length > 0) {
        handleCompanySelect(userCompanies[0]);
      }
    } catch (err) {
      setError('Error fetching companies');
      console.error('Error fetching companies:', err);
    } finally {
      setLoading(false);
    }
  };

  // Handle company selection
  const handleCompanySelect = (company) => {
    setSelectedCompany(company);
    
    // Store selected company in localStorage for persistence
    localStorage.setItem('selectedCompany', JSON.stringify(company));
    
    // Dispatch a custom event for same-tab communication
    window.dispatchEvent(new CustomEvent('companyChanged', { detail: company }));
    
    // Notify parent component
    if (onCompanyChange) {
      onCompanyChange(company);
    }
  };

  // If loading or error, show appropriate UI
  if (loading) {
    return <div className="text-white">Loading companies...</div>;
  }

  if (error) {
    return <div className="text-danger">{error}</div>;
  }

  // If no companies available
  if (companies.length === 0) {
    return <div className="text-white">No companies available</div>;
  }

  return (
    <Dropdown className="mx-3">
      <Dropdown.Toggle variant="outline-light" id="company-selector">
        {selectedCompany ? selectedCompany.name : 'Select Company'}
      </Dropdown.Toggle>

      <Dropdown.Menu>
        {companies.map((company) => (
          <Dropdown.Item 
            key={company.companyId} 
            onClick={() => handleCompanySelect(company)}
            active={selectedCompany && selectedCompany.companyId === company.companyId}
          >
            {company.name}
          </Dropdown.Item>
        ))}
      </Dropdown.Menu>
    </Dropdown>
  );
};

export default CompanySelector;
