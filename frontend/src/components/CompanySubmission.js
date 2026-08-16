import React, { useState, useEffect } from 'react';
import { Card, Form, Button, Alert, Table, Badge, Spinner, Row, Col } from 'react-bootstrap';
import { FaFileUpload, FaCheckCircle } from 'react-icons/fa';
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

function CompanySubmission({ tender, onSuccess, onBack, onViewReport }) {
  const [companyName, setCompanyName] = useState('');
  const [documentType, setDocumentType] = useState('proposal');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [companies, setCompanies] = useState({});

  useEffect(() => {
    fetchCompanies();
  }, [tender]);

  const fetchCompanies = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/tenders/${tender.tender_id}/companies`);
      setCompanies(response.data.companies || {});
    } catch (err) {
      console.error('Error fetching companies:', err);
    }
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError('');
  };

  const handleUpload = async (e) => {
    e.preventDefault();

    if (!companyName.trim()) {
      setError('Company name is required');
      return;
    }

    if (!file) {
      setError('Please select a file');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await axios.post(
        `${API_BASE_URL}/tenders/${tender.tender_id}/companies/${companyName}/upload`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );

      setSuccess(`${getDocumentTypeLabel(documentType)} uploaded successfully!`);
      setFile(null);
      document.getElementById('companyFile').value = '';
      fetchCompanies();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error uploading document');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async (companyName) => {
    setAnalyzing(true);
    setError('');
    setSuccess('');

    try {
      await axios.post(
        `${API_BASE_URL}/tenders/${tender.tender_id}/companies/${companyName}/analyze`
      );

      setSuccess(`Analysis completed for ${companyName}!`);
      fetchCompanies();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error analyzing compliance');
    } finally {
      setAnalyzing(false);
    }
  };

  const getDocumentTypeLabel = (type) => {
    const labels = {
      'proposal': 'Proposal',
      'technical': 'Technical Response',
      'financial': 'Financial Bid',
      'compliance': 'Compliance Document',
      'experience': 'Experience & Credentials',
      'other': 'Other Document'
    };
    return labels[type] || type.toUpperCase();
  };

  return (
    <>
      <Card className="mb-3">
        <Card.Header className="d-flex justify-content-between align-items-center">
          <h4>🏢 Company Submission - {tender.tender_name}</h4>
          <Button variant="secondary" size="sm" onClick={onBack}>
            ← Back to List
          </Button>
        </Card.Header>
        <Card.Body>
          <Alert variant="info">
            <strong>Upload Company Response Documents</strong>
            <p className="mb-0">
              Companies submit their proposal and supporting documents in response to tender requirements.
              After uploading all documents, click "Analyze Compliance" to check against requirements.
            </p>
          </Alert>

          {error && <Alert variant="danger" dismissible onClose={() => setError('')}>{error}</Alert>}
          {success && <Alert variant="success" dismissible onClose={() => setSuccess('')}>{success}</Alert>}

          <Form onSubmit={handleUpload}>
            <Row>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>Company Name *</Form.Label>
                  <Form.Control
                    type="text"
                    placeholder="e.g., Tech Solutions Ltd"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    list="company-suggestions"
                  />
                  <datalist id="company-suggestions">
                    {Object.keys(companies).map(name => (
                      <option key={name} value={name} />
                    ))}
                  </datalist>
                  <Form.Text className="text-muted">
                    Enter company name responding to this tender
                  </Form.Text>
                </Form.Group>
              </Col>

              <Col md={3}>
                <Form.Group className="mb-3">
                  <Form.Label>Document Type *</Form.Label>
                  <Form.Select value={documentType} onChange={(e) => setDocumentType(e.target.value)}>
                    <option value="proposal">Proposal Document</option>
                    <option value="technical">Technical Response</option>
                    <option value="financial">Financial Bid</option>
                    <option value="compliance">Compliance Document</option>
                    <option value="experience">Experience & Credentials</option>
                    <option value="other">Other Supporting Document</option>
                  </Form.Select>
                  <Form.Text className="text-muted">
                    Type of response document
                  </Form.Text>
                </Form.Group>
              </Col>

              <Col md={5}>
                <Form.Group className="mb-3">
                  <Form.Label>Document File *</Form.Label>
                  <Form.Control
                    id="companyFile"
                    type="file"
                    accept=".pdf,.docx,.txt"
                    onChange={handleFileChange}
                  />
                  <Form.Text className="text-muted">
                    Accepted: PDF, DOCX, TXT
                  </Form.Text>
                </Form.Group>
              </Col>
            </Row>

            <Button variant="primary" type="submit" disabled={loading || !file}>
              {loading ? (
                <>
                  <Spinner animation="border" size="sm" /> Uploading...
                </>
              ) : (
                <>
                  <FaFileUpload /> Upload Document
                </>
              )}
            </Button>
          </Form>
        </Card.Body>
      </Card>

      {/* Submitted Companies */}
      {Object.keys(companies).length > 0 && (
        <Card>
          <Card.Header>
            <h5>📊 Submitted Companies ({Object.keys(companies).length})</h5>
          </Card.Header>
          <Card.Body>
            <Table striped bordered hover responsive>
              <thead>
                <tr>
                  <th>Company Name</th>
                  <th>Submission Date</th>
                  <th>Documents Submitted</th>
                  <th>Analysis Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(companies).map(([name, data]) => (
                  <tr key={name}>
                    <td><strong>{name}</strong></td>
                    <td>{data.submission_date}</td>
                    <td>
                      {Object.keys(data.documents || {}).map(docType => (
                        <Badge key={docType} bg="info" className="me-1">
                          {getDocumentTypeLabel(docType)}
                        </Badge>
                      ))}
                      <br />
                      <small className="text-muted">
                        {Object.keys(data.documents || {}).length} document(s)
                      </small>
                    </td>
                    <td>
                      {data.analysis_status === 'completed' ? (
                        <Badge bg="success">
                          <FaCheckCircle /> Analyzed
                        </Badge>
                      ) : data.analysis_status === 'analyzing' ? (
                        <Badge bg="warning">
                          <Spinner animation="border" size="sm" /> Analyzing...
                        </Badge>
                      ) : data.analysis_status === 'failed' ? (
                        <Badge bg="danger">❌ Failed</Badge>
                      ) : (
                        <Badge bg="secondary">Pending Analysis</Badge>
                      )}
                    </td>
                    <td>
                      {data.analysis_status === 'completed' ? (
                        <Button
                          size="sm"
                          variant="info"
                          onClick={() => {
                            if (onViewReport) {
                              onViewReport(name);
                            }
                          }}
                        >
                          View Report
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          variant="primary"
                          onClick={() => handleAnalyze(name)}
                          disabled={analyzing || Object.keys(data.documents || {}).length === 0}
                        >
                          {analyzing ? (
                            <>
                              <Spinner animation="border" size="sm" /> Analyzing...
                            </>
                          ) : (
                            'Analyze Compliance'
                          )}
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Card.Body>
        </Card>
      )}
    </>
  );
}

export default CompanySubmission;
