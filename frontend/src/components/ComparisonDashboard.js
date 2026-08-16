import React, { useState, useEffect } from 'react';
import { Card, Table, Badge, Button, Alert, Spinner } from 'react-bootstrap';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import axios from 'axios';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const API_BASE_URL = 'http://127.0.0.1:8000/api';

function ComparisonDashboard({ tender, onBack }) {
  const [comparison, setComparison] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchComparison();
  }, [tender]);

  const fetchComparison = async () => {
    setLoading(true);
    try {
      const response = await axios.get(
        `${API_BASE_URL}/tenders/${tender.tender_id}/comparison`
      );
      setComparison(response.data.comparison || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error fetching comparison data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" variant="primary" />
        <p>Loading comparison data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="danger">
        <h5>Error</h5>
        <p>{error}</p>
        <Button variant="secondary" onClick={onBack}>← Back</Button>
      </Alert>
    );
  }

  if (comparison.length === 0) {
    return (
      <Card>
        <Card.Header className="d-flex justify-content-between align-items-center">
          <h4>📊 Company Comparison</h4>
          <Button variant="secondary" size="sm" onClick={onBack}>
            ← Back
          </Button>
        </Card.Header>
        <Card.Body className="text-center py-5">
          <h5>No analyzed companies found</h5>
          <p>Companies need to be analyzed before comparison data is available.</p>
        </Card.Body>
      </Card>
    );
  }

  // Chart data
  const chartData = {
    labels: comparison.map(c => c.company_name),
    datasets: [
      {
        label: 'Requirements Met',
        data: comparison.map(c => c.requirements_met),
        backgroundColor: 'rgba(40, 167, 69, 0.7)',
        borderColor: 'rgba(40, 167, 69, 1)',
        borderWidth: 2
      },
      {
        label: 'Requirements Partial',
        data: comparison.map(c => c.requirements_partial),
        backgroundColor: 'rgba(255, 193, 7, 0.7)',
        borderColor: 'rgba(255, 193, 7, 1)',
        borderWidth: 2
      },
      {
        label: 'Requirements Missing',
        data: comparison.map(c => c.requirements_missing),
        backgroundColor: 'rgba(220, 53, 69, 0.7)',
        borderColor: 'rgba(220, 53, 69, 1)',
        borderWidth: 2
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: { position: 'top' },
      title: {
        display: true,
        text: 'Requirements Compliance Comparison'
      }
    },
    scales: {
      x: { 
        stacked: true,
        type: 'category'
      },
      y: { 
        stacked: true, 
        beginAtZero: true,
        type: 'linear'
      }
    }
  };

  const getRankBadge = (rank) => {
    if (rank === 1) return <Badge bg="success">🥇 1st</Badge>;
    if (rank === 2) return <Badge bg="info">🥈 2nd</Badge>;
    if (rank === 3) return <Badge bg="warning">🥉 3rd</Badge>;
    return <Badge bg="secondary">{rank}th</Badge>;
  };

  return (
    <>
      <Card className="mb-3">
        <Card.Header className="d-flex justify-content-between align-items-center">
          <h4>📊 Company Comparison - {tender.tender_name}</h4>
          <Button variant="secondary" size="sm" onClick={onBack}>
            ← Back to List
          </Button>
        </Card.Header>
      </Card>

      {/* Comparison Table */}
      <Card className="mb-3">
        <Card.Header>
          <h5>Company Rankings</h5>
        </Card.Header>
        <Card.Body>
          <Table striped bordered hover responsive>
            <thead>
              <tr>
                <th>Rank</th>
                <th>Company Name</th>
                <th>Compliance %</th>
                <th>Met</th>
                <th>Partial</th>
                <th>Missing</th>
                <th>Analysis Date</th>
              </tr>
            </thead>
            <tbody>
              {comparison.map((company) => (
                <tr key={company.company_name}>
                  <td>{getRankBadge(company.rank)}</td>
                  <td><strong>{company.company_name}</strong></td>
                  <td>
                    <h5>
                      <Badge 
                        bg={company.compliance_percentage >= 80 ? 'success' : 
                            company.compliance_percentage >= 60 ? 'warning' : 'danger'}
                      >
                        {company.compliance_percentage}%
                      </Badge>
                    </h5>
                  </td>
                  <td><Badge bg="success">{company.requirements_met}</Badge></td>
                  <td><Badge bg="warning">{company.requirements_partial}</Badge></td>
                  <td><Badge bg="danger">{company.requirements_missing}</Badge></td>
                  <td><small>{company.analysis_date}</small></td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card.Body>
      </Card>

      {/* Chart */}
      <Card>
        <Card.Header>
          <h5>Visual Comparison</h5>
        </Card.Header>
        <Card.Body>
          <div style={{ height: '400px', position: 'relative' }}>
            <Bar data={chartData} options={chartOptions} />
          </div>
        </Card.Body>
      </Card>
    </>
  );
}

export default ComparisonDashboard;
