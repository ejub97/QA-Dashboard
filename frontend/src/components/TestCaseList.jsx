import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import TestCaseForm from './TestCaseForm';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Plus, Edit, Trash2, FileSpreadsheet, FileText, X, Edit2 } from 'lucide-react';
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
  const [tabs, setTabs] = useState(['General']);
  const [activeTab, setActiveTab] = useState('General');
  const [editingTab, setEditingTab] = useState(null);
  const [newTabName, setNewTabName] = useState('');
  const [deleteTab, setDeleteTab] = useState(null);

  useEffect(() => {
    if (project) {
      loadTestCases();
      loadTabs();
    }
  }, [project]);

  const loadTabs = async () => {
    try {
      const response = await axios.get(`${API}/projects/${project.id}/tabs`);
      if (response.data.tabs && response.data.tabs.length > 0) {
        setTabs(response.data.tabs);
        setActiveTab(response.data.tabs[0]);
      }
    } catch (error) {
      console.error('Failed to load tabs', error);
    }
  };

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
      await loadTabs();
      setActiveTab(data.tab);
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
      await loadTabs();
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
      await loadTabs();
      toast.success('Test case deleted successfully!');
    } catch (error) {
      toast.error('Failed to delete test case');
      console.error(error);
    }
  };

  const handleRenameTab = async () => {
    if (!newTabName.trim() || newTabName === editingTab) {
      setEditingTab(null);
      return;
    }

    try {
      // Update all test cases with the old tab name to the new tab name
      const tabTestCases = testCases.filter(tc => tc.tab === editingTab);
      
      for (const tc of tabTestCases) {
        await axios.put(`${API}/test-cases/${tc.id}`, { tab: newTabName });
      }
      
      // Reload test cases and tabs
      await loadTestCases();
      await loadTabs();
      setActiveTab(newTabName);
      setEditingTab(null);
      setNewTabName('');
      toast.success('Tab renamed successfully!');
    } catch (error) {
      toast.error('Failed to rename tab');
      console.error(error);
    }
  };

  const handleDeleteTab = async () => {
    try {
      // Delete all test cases in this tab
      const tabTestCases = testCases.filter(tc => tc.tab === deleteTab);
      
      for (const tc of tabTestCases) {
        await axios.delete(`${API}/test-cases/${tc.id}`);
      }
      
      // Reload
      await loadTestCases();
      await loadTabs();
      setDeleteTab(null);
      toast.success('Tab and all test cases deleted successfully!');
    } catch (error) {
      toast.error('Failed to delete tab');
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
      const extension = format === 'csv' ? 'csv' : format === 'excel' ? 'xlsx' : 'docx';
      link.setAttribute('download', `${project.name}_test_cases.${extension}`);
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

  const getFilteredTestCases = (tab) => {
    return testCases.filter((tc) => {
      if (tc.tab !== tab) return false;
      if (filterStatus !== 'all' && tc.status !== filterStatus) return false;
      if (filterPriority !== 'all' && tc.priority !== filterPriority) return false;
      if (filterType !== 'all' && tc.type !== filterType) return false;
      return true;
    });
  };

  if (loading) {
    return <div className="glass-effect rounded-2xl p-8 text-center">Loading test cases...</div>;
  }

  return (
    <div className="glass-effect rounded-2xl p-6" style={{ minHeight: '750px' }}>
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900" data-testid="testcases-title">{project.name}</h2>
          <p className="text-sm text-gray-600 mt-1">{testCases.length} test case(s)</p>
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
            onClick={() => handleExport('excel')}
            variant="outline"
            size="sm"
            className="btn-secondary"
            data-testid="export-excel-btn"
          >
            <FileText size={16} className="mr-2" />
            Export Excel
          </Button>
          <Button
            onClick={() => {
              setEditingTestCase(null);
              setShowForm(true);
            }}
            className="btn-dark"
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

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <div className="flex items-center gap-2 mb-4">
          <TabsList className="flex-1">
            {tabs.map((tab) => (
              <TabsTrigger key={tab} value={tab} data-testid={`tab-${tab}`} className="relative group">
                {tab} ({testCases.filter(tc => tc.tab === tab).length})
                <div className="absolute -top-1 -right-1 hidden group-hover:flex gap-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setEditingTab(tab);
                      setNewTabName(tab);
                    }}
                    className="bg-blue-500 hover:bg-blue-600 text-white rounded-full p-1"
                    data-testid={`rename-tab-btn-${tab}`}
                  >
                    <Edit2 size={10} />
                  </button>
                  {tabs.length > 1 && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setDeleteTab(tab);
                      }}
                      className="bg-red-500 hover:bg-red-600 text-white rounded-full p-1"
                      data-testid={`delete-tab-btn-${tab}`}
                    >
                      <X size={10} />
                    </button>
                  )}
                </div>
              </TabsTrigger>
            ))}
          </TabsList>
        </div>

        {tabs.map((tab) => (
          <TabsContent key={tab} value={tab} className="mt-0">
            <div className="space-y-4 custom-scrollbar" style={{ maxHeight: '500px', overflowY: 'auto' }}>
              {getFilteredTestCases(tab).length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-500 mb-4">No test cases found in this tab</p>
                  <Button onClick={() => setShowForm(true)} className="btn-dark">
                    <Plus size={16} className="mr-2" />
                    Create Test Case
                  </Button>
                </div>
              ) : (
                getFilteredTestCases(tab).map((tc) => (
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

                    <div className="space-y-3 text-sm">
                      <div>
                        <span className="font-medium text-gray-700">Steps:</span>
                        <p className="text-gray-600 mt-1 whitespace-pre-line" data-testid={`testcase-steps-${tc.id}`}>{tc.steps}</p>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Expected Result:</span>
                        <p className="text-gray-600 mt-1" data-testid={`testcase-expected-${tc.id}`}>{tc.expected_result}</p>
                      </div>
                      {tc.actual_result && (
                        <div>
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
          </TabsContent>
        ))}
      </Tabs>

      {/* Test Case Form Dialog */}
      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" data-testid="testcase-form-dialog">
          <DialogHeader>
            <DialogTitle>{editingTestCase ? 'Edit Test Case' : 'Create Test Case'}</DialogTitle>
          </DialogHeader>
          <TestCaseForm
            testCase={editingTestCase}
            currentTab={activeTab}
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

      {/* Rename Tab Dialog */}
      <Dialog open={!!editingTab} onOpenChange={() => setEditingTab(null)}>
        <DialogContent data-testid="rename-tab-dialog">
          <DialogHeader>
            <DialogTitle>Rename Tab</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="new-tab-name">New Tab Name</Label>
              <Input
                id="new-tab-name"
                data-testid="new-tab-name-input"
                value={newTabName}
                onChange={(e) => setNewTabName(e.target.value)}
                placeholder="Enter new tab name"
                className="input-focus"
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setEditingTab(null)} data-testid="cancel-rename-tab-btn">
                Cancel
              </Button>
              <Button onClick={handleRenameTab} className="btn-dark" data-testid="confirm-rename-tab-btn">
                Rename
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Tab Confirmation Dialog */}
      <AlertDialog open={!!deleteTab} onOpenChange={() => setDeleteTab(null)}>
        <AlertDialogContent data-testid="delete-tab-dialog">
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Tab</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete the "{deleteTab}" tab? This will delete all test cases ({testCases.filter(tc => tc.tab === deleteTab).length}) in this tab. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="cancel-delete-tab-btn">Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteTab} className="bg-red-600 hover:bg-red-700" data-testid="confirm-delete-tab-btn">
              Delete Tab
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default TestCaseList;
