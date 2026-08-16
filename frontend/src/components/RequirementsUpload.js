import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Button,
  Alert,
  Table,
  Badge,
  Spinner,
  Nav,
} from 'react-bootstrap';
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

function RequirementsUpload({ tender, onSuccess, onBack }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [requirements, setRequirements] = useState([]);
  const [loadingRequirements, setLoadingRequirements] = useState(false);

  // NEW: category tab state
  const [selectedCategory, setSelectedCategory] = useState('All');

  const CATEGORY_TABS = [
    'All',
    'Technical Proposal',
    'Financial Proposal',
    'Guidelines',
    'Contract / Legal',
    'General',
  ];

  useEffect(() => {
    if (tender.requirements_document) {
      fetchRequirements();
    }
  }, [tender]);

  const fetchRequirements = async () => {
    setLoadingRequirements(true);
    try {
      const response = await axios.get(
        `${API_BASE_URL}/tenders/${tender.tender_id}/requirements`
      );
      setRequirements(response.data.requirements || []);
    } catch (err) {
      console.error('Error fetching requirements:', err);
    } finally {
      setLoadingRequirements(false);
    }
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError('');
  };

  const handleUpload = async (e) => {
    e.preventDefault();

    if (!file) {
      setError('Please select a file');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await axios.post(
        `${API_BASE_URL}/tenders/${tender.tender_id}/requirements`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );

      setSuccess(
        `Successfully extracted ${response.data.total_requirements} requirements!`
      );
      setRequirements(response.data.requirements || []);
      setFile(null);
      setSelectedCategory('All'); // reset filter after new upload
      document.getElementById('requirementsFile').value = '';
    } catch (err) {
      setError(err.response?.data?.detail || 'Error uploading requirements');
    } finally {
      setLoading(false);
    }
  };

  // UPDATED: category badges to match your new categories
  const getCategoryBadge = (category) => {
    const colors = {
      'Technical Proposal': 'primary',
      'Financial Proposal': 'success',
      Guidelines: 'info',
      'Contract / Legal': 'warning',
      General: 'secondary',
    };
    return colors[category] || 'secondary';
  };

  // NEW: filtered requirements based on selected tab
  const filteredRequirements =
    selectedCategory === 'All'
      ? requirements
      : requirements.filter((req) => req.category === selectedCategory);

  return (
    <>
      <Card className="mb-3">
        <Card.Header className="d-flex justify-content-between align-items-center">
          <h4>📄 Requirements Upload - {tender.tender_name}</h4>
          <Button variant="secondary" size="sm" onClick={onBack}>
            ← Back to List
          </Button>
        </Card.Header>
        <Card.Body>
          <Alert variant="info">
            <strong>Upload Government Requirements Document</strong>
            <p className="mb-0">
              Upload the official tender requirements document (PDF, DOCX, TXT).
              The system will automatically extract all requirements.
            </p>
          </Alert>

          {error && (
            <Alert
              variant="danger"
              dismissible
              onClose={() => setError('')}
            >
              {error}
            </Alert>
          )}
          {success && (
            <Alert
              variant="success"
              dismissible
              onClose={() => setSuccess('')}
            >
              {success}
            </Alert>
          )}

          <Form onSubmit={handleUpload}>
            <Form.Group className="mb-3">
              <Form.Label>Requirements Document</Form.Label>
              <Form.Control
                id="requirementsFile"
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileChange}
              />
              <Form.Text className="text-muted">
                Accepted formats: PDF, DOCX, TXT
              </Form.Text>
            </Form.Group>

            <Button variant="primary" type="submit" disabled={loading || !file}>
              {loading ? (
                <>
                  <Spinner animation="border" size="sm" /> Uploading &amp;
                  Extracting...
                </>
              ) : (
                'Upload & Extract Requirements'
              )}
            </Button>
          </Form>
        </Card.Body>
      </Card>

      {/* Display Extracted Requirements */}
      {requirements.length > 0 && (
        <Card>
          <Card.Header>
            <div className="d-flex justify-content-between align-items-center">
              <h5>
                📋 Extracted Requirements ({requirements.length})
              </h5>
              <small>
                Showing:{' '}
                <strong>
                  {selectedCategory === 'All'
                    ? 'All Categories'
                    : selectedCategory}
                </strong>
              </small>
            </div>
          </Card.Header>
          <Card.Body>
            {loadingRequirements ? (
              <div className="text-center py-5">
                <Spinner animation="border" />
                <p>Loading requirements...</p>
              </div>
            ) : (
              <>
                {/* NEW: Category tabs */}
                <Nav
                  variant="pills"
                  activeKey={selectedCategory}
                  onSelect={(key) =>
                    setSelectedCategory(key || 'All')
                  }
                  className="mb-3"
                >
                  {CATEGORY_TABS.map((cat) => (
                    <Nav.Item key={cat}>
                      <Nav.Link eventKey={cat}>{cat}</Nav.Link>
                    </Nav.Item>
                  ))}
                </Nav>

                <Table striped bordered hover responsive>
                  <thead>
                    <tr>
                      <th style={{ width: '100px' }}>Req ID</th>
                      <th>Requirement Text</th>
                      <th style={{ width: '150px' }}>Category</th>
                      <th style={{ width: '100px' }}>Mandatory</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRequirements.map((req) => (
                      <tr key={req.req_id}>
                        <td>
                          <code>{req.req_id}</code>
                        </td>
                        <td>{req.requirement_text}</td>
                        <td>
                          <Badge bg={getCategoryBadge(req.category)}>
                            {req.category}
                          </Badge>
                        </td>
                        <td>
                          {req.mandatory ? (
                            <Badge bg="danger">Yes</Badge>
                          ) : (
                            <Badge bg="secondary">No</Badge>
                          )}
                        </td>
                      </tr>
                    ))}

                    {filteredRequirements.length === 0 && (
                      <tr>
                        <td colSpan={4} className="text-center py-3">
                          No requirements in this category.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </Table>
              </>
            )}
          </Card.Body>
        </Card>
      )}
    </>
  );
}

export default RequirementsUpload;
