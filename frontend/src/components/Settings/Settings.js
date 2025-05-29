import React, { useState } from 'react';
import { Container, Row, Col, Nav, Tab } from 'react-bootstrap';
import CompanySettings from './CompanySettings';
import DeviceSettings from './DeviceSettings';

const Settings = () => {
  const [activeTab, setActiveTab] = useState('companies');

  return (
    <Container className="mt-4 mb-5">
      <h2 className="mb-4">Settings</h2>
      
      <Tab.Container id="settings-tabs" activeKey={activeTab} onSelect={(k) => setActiveTab(k)}>
        <Row>
          <Col md={3}>
            <Nav variant="pills" className="flex-column">
              <Nav.Item>
                <Nav.Link eventKey="companies">Companies</Nav.Link>
              </Nav.Item>
              <Nav.Item>
                <Nav.Link eventKey="devices">Devices</Nav.Link>
              </Nav.Item>
            </Nav>
          </Col>
          <Col md={9}>
            <Tab.Content>
              <Tab.Pane eventKey="companies">
                <CompanySettings />
              </Tab.Pane>
              <Tab.Pane eventKey="devices">
                <DeviceSettings />
              </Tab.Pane>
            </Tab.Content>
          </Col>
        </Row>
      </Tab.Container>
    </Container>
  );
};

export default Settings;
