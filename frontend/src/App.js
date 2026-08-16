import React, { useState, useEffect } from 'react';
import axios from 'axios';
import 'bootstrap/dist/css/bootstrap.min.css';
import { Container, Row, Col, Nav } from 'react-bootstrap';
import './App.css';

// Import components
import TenderList from './components/TenderList';
import TenderCreate from './components/TenderCreate';
import RequirementsUpload from './components/RequirementsUpload';
import CompanySubmission from './components/CompanySubmission';
import ComplianceReport from './components/ComplianceReport';
import ComparisonDashboard from './components/ComparisonDashboard';
import Statistics from './components/Statistics';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

function App() {
  const [activeView, setActiveView] = useState('list'); // list, create, requirements, submit, report, compare, stats
  const [selectedTender, setSelectedTender] = useState(null);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [tenders, setTenders] = useState([]);

  useEffect(() => {
    fetchTenders();
  }, []);

  const fetchTenders = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/tenders`);
      setTenders(response.data.tenders || []);
    } catch (error) {
      console.error('Error fetching tenders:', error);
    }
  };

  const handleViewChange = (view, tender = null, company = null) => {
    setActiveView(view);
    setSelectedTender(tender);
    setSelectedCompany(company);
  };

  return (
    <div className="app">
      {/* Sidebar */}
      <div className="sidebar">
        <h3 className="sidebar-title">🎯 Tender Compliance System</h3>
        <Nav className="flex-column">
          <Nav.Link
            className={activeView === 'list' ? 'active' : ''}
            onClick={() => handleViewChange('list')}
          >
            📋 Tender List
          </Nav.Link>
          <Nav.Link
            className={activeView === 'create' ? 'active' : ''}
            onClick={() => handleViewChange('create')}
          >
            ➕ Create Tender
          </Nav.Link>
          <Nav.Link
            className={activeView === 'stats' ? 'active' : ''}
            onClick={() => handleViewChange('stats')}
          >
            📊 Statistics
          </Nav.Link>
        </Nav>
      </div>

      {/* Main Content */}
      <div className="main-content">
        <Container fluid>
          {activeView === 'list' && (
            <TenderList
              tenders={tenders}
              onRefresh={fetchTenders}
              onViewChange={handleViewChange}
            />
          )}

          {activeView === 'create' && (
            <TenderCreate
              onSuccess={() => {
                fetchTenders();
                handleViewChange('list');
              }}
              onCancel={() => handleViewChange('list')}
            />
          )}

          {activeView === 'requirements' && selectedTender && (
            <RequirementsUpload
              tender={selectedTender}
              onSuccess={() => {
                fetchTenders();
                handleViewChange('list');
              }}
              onBack={() => handleViewChange('list')}
            />
          )}

          {activeView === 'submit' && selectedTender && (
            <CompanySubmission
              tender={selectedTender}
              onSuccess={() => {
                fetchTenders();
                handleViewChange('list');
              }}
              onBack={() => handleViewChange('list')}
              // 🔹 NEW: when child asks to view a report, go to report view
              onViewReport={(companyName) =>
                handleViewChange('report', selectedTender, companyName)
              }
            />
          )}

          {activeView === 'report' && selectedTender && selectedCompany && (
            <ComplianceReport
              tender={selectedTender}
              companyName={selectedCompany}
              // 🔹 Go back to company submission screen for this tender
              onBack={() => handleViewChange('submit', selectedTender)}
            />
          )}

          {activeView === 'compare' && selectedTender && (
            <ComparisonDashboard
              tender={selectedTender}
              onBack={() => handleViewChange('list')}
            />
          )}

          {activeView === 'stats' && <Statistics />}
        </Container>
      </div>
    </div>
  );
}

export default App;
