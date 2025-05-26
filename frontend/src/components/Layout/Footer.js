import React from 'react';
import { Container } from 'react-bootstrap';

const Footer = () => {
  return (
    <footer className="bg-dark text-white py-3 mt-auto">
      <Container className="text-center">
        <p className="mb-0">
          &copy; {new Date().getFullYear()} Campo Vision - Agricultural Telemetry System
        </p>
      </Container>
    </footer>
  );
};

export default Footer;
