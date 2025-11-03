import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import TestCaseForm from './TestCaseForm';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Download, Edit, Trash2, FileSpreadsheet, FileText } from 'lucide-react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TestCaseList = ({ project }) => {
  const [testCases, setTestCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingTestCase, setEditingTestCase] = useState(null);
  const [deleteTestCase, setDeleteTestCase] = useState(null);
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterPriority, setFilterPriority] = useState('all');
  const [filterType, setFilterType] = useState('all');

  useEffect(() => {
    if (project) {
      loadTestCases();
    }
  }, [project]);

  const loadTestCases = async () => {
    try {
      const response = await axios.get(`${API}/test-cases?project_id=${project.id}`);
      setTestCases(response.data);
    } catch (error) {
      toast.error('Failed to load test cases');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTestCase = async (data) => {
    try {
      const response = await axios.post(`${API}/test-cases`, { ...data, project_id: project.id });
      setTestCases([...testCases, response.data]);
      setShowForm(false);
      toast.success('Test case created successfully!');
    } catch (error) {
      toast.error('Failed to create test case');
      console.error(error);
    }
  };

  const handleUpdateTestCase = async (data) => {
    try {
      const response = await axios.put(`${API}/test-cases/${editingTestCase.id}`, data);
      setTestCases(testCases.map((tc) => (tc.id === editingTestCase.id ? response.data : tc)));
      setEditingTestCase(null);
      setShowForm(false);
      toast.success('Test case updated successfully!');
    } catch (error) {
      toast.error('Failed to update test case');
      console.error(error);
    }
  };

  const handleStatusChange = async (testCaseId, newStatus) => {
    try {
      const response = await axios.patch(`${API}/test-cases/${testCaseId}/status`, { status: newStatus });
      setTestCases(testCases.map((tc) => (tc.id === testCaseId ? response.data : tc)));
      toast.success('Status updated successfully!');
    } catch (error) {
      toast.error('Failed to update status');
      console.error(error);
    }
  };

  const handleDeleteConfirm = async () => {
    try {
      await axios.delete(`${API}/test-cases/${deleteTestCase.id}`);
      setTestCases(testCases.filter((tc) => tc.id !== deleteTestCase.id));
      setDeleteTestCase(null);
      toast.success('Test case deleted successfully!');
    } catch (error) {
      toast.error('Failed to delete test case');
      console.error(error);
    }
  };

  const handleExport = async (format) => {
    try {
      const response = await axios.get(`${API}/test-cases/export/${format}/${project.id}`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${project.name}_test_cases.${format === 'csv' ? 'csv' : 'docx'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success(`Exported as ${format.toUpperCase()} successfully!`);
    } catch (error) {
      toast.error(`Failed to export as ${format.toUpperCase()}`);
      console.error(error);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      draft: 'badge-draft',
      success: 'badge-success',
      fail: 'badge-fail',
    };
    return <Badge className={`${styles[status]} text-xs px-2 py-1`} data-testid={`status-badge-${status}`}>{status}</Badge>;
  };

  const getPriorityColor = (priority) => {
    const colors = {
      low: 'text-green-600',
      medium: 'text-yellow-600',
      high: 'text-red-600',
    };
    return colors[priority] || 'text-gray-600';
  };

  const filteredTestCases = testCases.filter((tc) => {
    if (filterStatus !== 'all' && tc.status !== filterStatus) return false;
    if (filterPriority !== 'all' && tc.priority !== filterPriority) return false;
    if (filterType !== 'all' && tc.type !== filterType) return false;
    return true;
  });

  if (loading) {
    return <div className="glass-effect rounded-2xl p-8 text-center">Loading test cases...</div>;
  }

  return (
    <div className="glass-effect rounded-2xl p-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900" data-testid="testcases-title">{project.name}</h2>
          <p className="text-sm text-gray-600 mt-1">{filteredTestCases.length} test case(s)</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            onClick={() => handleExport('csv')}
            variant="outline"
            size="sm"
            className="btn-secondary"
            data-testid="export-csv-btn"
          >
            <FileSpreadsheet size={16} className="mr-2" />
            Export CSV
          </Button>
          <Button
            onClick={() => handleExport('docx')}
            variant="outline"
            size="sm"
            className="btn-secondary"
            data-testid="export-docx-btn"
          >
            <FileText size={16} className="mr-2" />
            Export Word
          </Button>
          <Button
            onClick={() => {
              setEditingTestCase(null);
              setShowForm(true);
            }}
            className="btn-primary"
            size="sm"
            data-testid="add-testcase-btn"
          >
            <Plus size={16} className="mr-2" />
            Add Test Case
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
        <div>
          <label className="text-xs font-medium text-gray-700 mb-1 block">Status</label>
          <Select value={filterStatus} onValueChange={setFilterStatus}>
            <SelectTrigger data-testid="filter-status">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="success">Success</SelectItem>
              <SelectItem value="fail">Fail</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <label className="text-xs font-medium text-gray-700 mb-1 block">Priority</label>
          <Select value={filterPriority} onValueChange={setFilterPriority}>
            <SelectTrigger data-testid="filter-priority">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Priorities</SelectItem>
              <SelectItem value="low">Low</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="high">High</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <label className="text-xs font-medium text-gray-700 mb-1 block">Type</label>
          <Select value={filterType} onValueChange={setFilterType}>
            <SelectTrigger data-testid="filter-type">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="functional">Functional</SelectItem>
              <SelectItem value="negative">Negative</SelectItem>
              <SelectItem value="ui/ux">UI/UX</SelectItem>
              <SelectItem value="smoke">Smoke</SelectItem>
              <SelectItem value="regression">Regression</SelectItem>
              <SelectItem value="api">API</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Test Cases List */}
      <div className="space-y-4 custom-scrollbar" style={{ maxHeight: '600px', overflowY: 'auto' }}>
        {filteredTestCases.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 mb-4">No test cases found</p>
            <Button onClick={() => setShowForm(true)} className="btn-primary">
              <Plus size={16} className="mr-2" />
              Create First Test Case
            </Button>
          </div>
        ) : (
          filteredTestCases.map((tc) => (
            <div
              key={tc.id}
              data-testid={`testcase-card-${tc.id}`}
              className="bg-white rounded-lg p-4 border border-gray-200 card-hover"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="font-semibold text-gray-900" data-testid={`testcase-title-${tc.id}`}>{tc.title}</h3>
                    {getStatusBadge(tc.status)}
                  </div>
                  <p className="text-sm text-gray-600 mb-2" data-testid={`testcase-description-${tc.id}`}>{tc.description}</p>
                  <div className="flex flex-wrap gap-2 text-xs">
                    <span className={`font-medium ${getPriorityColor(tc.priority)}`} data-testid={`testcase-priority-${tc.id}`}>
                      Priority: {tc.priority}
                    </span>
                    <span className="text-gray-500">•</span>
                    <span className="text-gray-600" data-testid={`testcase-type-${tc.id}`}>Type: {tc.type}</span>
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setEditingTestCase(tc);
                      setShowForm(true);
                    }}
                    data-testid={`edit-testcase-btn-${tc.id}`}
                  >
                    <Edit size={16} />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setDeleteTestCase(tc)}
                    data-testid={`delete-testcase-btn-${tc.id}`}
                  >
                    <Trash2 size={16} className="text-red-500" />
                  </Button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Steps:</span>
                  <p className="text-gray-600 mt-1 whitespace-pre-line" data-testid={`testcase-steps-${tc.id}`}>{tc.steps}</p>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Expected Result:</span>
                  <p className="text-gray-600 mt-1" data-testid={`testcase-expected-${tc.id}`}>{tc.expected_result}</p>
                </div>
                {tc.actual_result && (
                  <div className="md:col-span-2">
                    <span className="font-medium text-gray-700">Actual Result:</span>
                    <p className="text-gray-600 mt-1" data-testid={`testcase-actual-${tc.id}`}>{tc.actual_result}</p>
                  </div>
                )}
              </div>

              <div className="mt-3 pt-3 border-t border-gray-200">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-600">Change Status:</span>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      className={`text-xs ${tc.status === 'draft' ? 'badge-draft' : ''}`}
                      onClick={() => handleStatusChange(tc.id, 'draft')}
                      data-testid={`status-draft-btn-${tc.id}`}
                    >
                      Draft
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className={`text-xs ${tc.status === 'success' ? 'badge-success' : ''}`}
                      onClick={() => handleStatusChange(tc.id, 'success')}
                      data-testid={`status-success-btn-${tc.id}`}
                    >
                      Success
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className={`text-xs ${tc.status === 'fail' ? 'badge-fail' : ''}`}
                      onClick={() => handleStatusChange(tc.id, 'fail')}
                      data-testid={`status-fail-btn-${tc.id}`}
                    >
                      Fail
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Test Case Form Dialog */}
      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" data-testid="testcase-form-dialog">
          <DialogHeader>
            <DialogTitle>{editingTestCase ? 'Edit Test Case' : 'Create Test Case'}</DialogTitle>
          </DialogHeader>
          <TestCaseForm
            testCase={editingTestCase}
            onSubmit={editingTestCase ? handleUpdateTestCase : handleCreateTestCase}
            onCancel={() => {
              setShowForm(false);
              setEditingTestCase(null);
            }}
          />
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deleteTestCase} onOpenChange={() => setDeleteTestCase(null)}>
        <AlertDialogContent data-testid="delete-confirmation-dialog">
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Test Case</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{deleteTestCase?.title}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="cancel-delete-btn">Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteConfirm} className="bg-red-600 hover:bg-red-700" data-testid="confirm-delete-btn">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default TestCaseList;