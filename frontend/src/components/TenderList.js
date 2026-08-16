import React, { useState } from 'react';
import { Card, Table, Button, Badge, ButtonGroup, Modal } from 'react-bootstrap';
import { FaFileUpload, FaBuilding, FaChartLine, FaTrash, FaEye } from 'react-icons/fa';
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

function TenderList({ tenders, onRefresh, onViewChange }) {
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [tenderToDelete, setTenderToDelete] = useState(null);

  const handleDelete = async () => {
    try {
      await axios.delete(`${API_BASE_URL}/tenders/${tenderToDelete.tender_id}`);
      setShowDeleteModal(false);
      setTenderToDelete(null);
      onRefresh();
    } catch (error) {
      console.error('Error deleting tender:', error);
      alert('Error deleting tender');
    }
  };

  const confirmDelete = (tender) => {
    setTenderToDelete(tender);
    setShowDeleteModal(true);
  };

  return (
    <>
      <Card>
        <Card.Header className="d-flex justify-content-between align-items-center">
          <h4>📋 All Tenders</h4>
          <Button variant="primary" onClick={() => onViewChange('create')}>
            ➕ Create New Tender
          </Button>
        </Card.Header>
        <Card.Body>
          {tenders.length === 0 ? (
            <div className="text-center py-5">
              <h5>No tenders found</h5>
              <p>Create your first tender to get started</p>
            </div>
          ) : (
            <Table striped bordered hover responsive>
              <thead>
                <tr>
                  <th>Tender ID</th>
                  <th>Tender Name</th>
                  <th>Created Date</th>
                  <th>Status</th>
                  <th>Requirements</th>
                  <th>Companies</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {tenders.map((tender) => (
                  <tr key={tender.tender_id}>
                    <td><code>{tender.tender_id}</code></td>
                    <td><strong>{tender.tender_name}</strong></td>
                    <td>{tender.created_date}</td>
                    <td>
                      <Badge bg={tender.status === 'active' ? 'success' : 'secondary'}>
                        {tender.status}
                      </Badge>
                    </td>
                    <td>
                      {tender.total_requirements > 0 ? (
                        <Badge bg="info">{tender.total_requirements} requirements</Badge>
                      ) : (
                        <Badge bg="warning">Not uploaded</Badge>
                      )}
                    </td>
                    <td>
                      <Badge bg="primary">
                        {Object.keys(tender.companies || {}).length} companies
                      </Badge>
                    </td>
                    <td>
                      <ButtonGroup size="sm">
                        {!tender.requirements_document ? (
                          <Button
                            variant="warning"
                            onClick={() => onViewChange('requirements', tender)}
                            title="Upload Requirements"
                          >
                            <FaFileUpload /> Upload Req
                          </Button>
                        ) : (
                          <Button
                            variant="info"
                            onClick={() => onViewChange('requirements', tender)}
                            title="View Requirements"
                          >
                            <FaEye /> View Req
                          </Button>
                        )}
                        
                        <Button
                          variant="success"
                          onClick={() => onViewChange('submit', tender)}
                          title="Company Submission"
                        >
                          <FaBuilding /> Submit
                        </Button>
                        
                        {Object.keys(tender.companies || {}).length > 0 && (
                          <Button
                            variant="primary"
                            onClick={() => onViewChange('compare', tender)}
                            title="Compare Companies"
                          >
                            <FaChartLine /> Compare
                          </Button>
                        )}
                        
                        <Button
                          variant="danger"
                          onClick={() => confirmDelete(tender)}
                          title="Delete Tender"
                        >
                          <FaTrash />
                        </Button>
                      </ButtonGroup>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card.Body>
      </Card>

      {/* Delete Confirmation Modal */}
      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Delete</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Are you sure you want to delete tender <strong>{tenderToDelete?.tender_name}</strong>?
          <br />
          This action cannot be undone.
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleDelete}>
            Delete
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
}

export default TenderList;
