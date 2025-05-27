import React, { useState, useEffect } from 'react';
import { Form, Button, Alert, Container, Row, Col, Card } from 'react-bootstrap';
import { confirmSignUp, resendConfirmationCode } from '../../services/auth';
import { useNavigate, useLocation, Link } from 'react-router-dom';

const VerifyEmail = () => {
  const [code, setCode] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Check if email was passed in location state
    if (location.state && location.state.email) {
      setEmail(location.state.email);
    }
  }, [location]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await confirmSignUp(email, code);
      setSuccess(true);
      // Wait a moment before redirecting to login
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err) {
      setError(err.message || 'Failed to verify email');
    } finally {
      setLoading(false);
    }
  };

  const handleResendCode = async () => {
    setResending(true);
    setError('');

    try {
      await resendConfirmationCode(email);
      setSuccess(true);
      // Reset success after a moment
      setTimeout(() => {
        setSuccess(false);
      }, 3000);
    } catch (err) {
      setError(err.message || 'Failed to resend verification code');
    } finally {
      setResending(false);
    }
  };

  return (
    <Container className="mt-5">
      <Row className="justify-content-center">
        <Col md={6}>
          <Card>
            <Card.Header className="bg-primary text-white">
              <h4 className="mb-0">Verify Your Email</h4>
            </Card.Header>
            <Card.Body>
              {error && <Alert variant="danger">{error}</Alert>}
              {success && !loading && (
                <Alert variant="success">
                  {loading 
                    ? 'Verification successful! Redirecting to login...' 
                    : 'Verification code has been sent to your email.'}
                </Alert>
              )}
              <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-3">
                  <Form.Label>Email</Form.Label>
                  <Form.Control
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    disabled={loading}
                  />
                </Form.Group>
                <Form.Group className="mb-3">
                  <Form.Label>Verification Code</Form.Label>
                  <Form.Control
                    type="text"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    required
                    disabled={loading}
                    placeholder="Enter the code sent to your email"
                  />
                </Form.Group>
                <div className="d-grid gap-2">
                  <Button 
                    variant="primary" 
                    type="submit" 
                    disabled={loading}
                  >
                    {loading ? 'Verifying...' : 'Verify Email'}
                  </Button>
                  <Button 
                    variant="outline-secondary" 
                    type="button" 
                    disabled={resending || !email}
                    onClick={handleResendCode}
                  >
                    {resending ? 'Sending...' : 'Resend Code'}
                  </Button>
                </div>
              </Form>
            </Card.Body>
            <Card.Footer className="text-center">
              <p className="mb-0">
                Already verified? <Link to="/login">Sign in</Link>
              </p>
            </Card.Footer>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default VerifyEmail;
