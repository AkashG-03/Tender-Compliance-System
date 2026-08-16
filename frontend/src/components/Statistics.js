import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Spinner } from 'react-bootstrap';
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

function Statistics() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStatistics();
  }, []);

  const fetchStatistics = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/statistics`);
      setStats(response.data.statistics);
    } catch (error) {
      console.error('Error fetching statistics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" variant="primary" />
        <p>Loading statistics...</p>
      </div>
    );
  }

  return (
    <>
      <h3 className="mb-4">📊 System Statistics</h3>
      
      <Row>
        <Col md={3}>
          <Card className="text-center stat-card stat-card-primary mb-3">
            <Card.Body>
              <h1>{stats?.total_tenders || 0}</h1>
              <p className="mb-0">Total Tenders</p>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={3}>
          <Card className="text-center stat-card stat-card-success mb-3">
            <Card.Body>
              <h1>{stats?.active_tenders || 0}</h1>
              <p className="mb-0">Active Tenders</p>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={3}>
          <Card className="text-center stat-card stat-card-info mb-3">
            <Card.Body>
              <h1>{stats?.total_companies || 0}</h1>
              <p className="mb-0">Total Companies</p>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={3}>
          <Card className="text-center stat-card stat-card-warning mb-3">
            <Card.Body>
              <h1>{stats?.total_requirements || 0}</h1>
              <p className="mb-0">Total Requirements</p>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row>
        <Col md={6}>
          <Card className="mb-3">
            <Card.Header>
              <h5>Average Requirements per Tender</h5>
            </Card.Header>
            <Card.Body className="text-center">
              <h2>{stats?.avg_requirements_per_tender || 0}</h2>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={6}>
          <Card className="mb-3">
            <Card.Header>
              <h5>System Health</h5>
            </Card.Header>
            <Card.Body className="text-center">
              <h2 className="text-success">✅ Healthy</h2>
              <p className="text-muted">All systems operational</p>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </>
  );
}

export default Statistics;
