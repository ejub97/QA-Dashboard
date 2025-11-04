import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import TestCaseForm from './TestCaseFormEnhanced';
import StatisticsWidget from './StatisticsWidget';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Textarea } from '@/components/ui/textarea';
import { Plus, Edit, Trash2, FileSpreadsheet, FileText, X, Edit2, Search, Copy, Upload, ChevronDown, ChevronUp, MessageSquare, User, Calendar } from 'lucide-react';
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

const TestCaseList = ({ project, userRole }) => {
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
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCases, setSelectedCases] = useState([]);
  const [showBulkActions, setShowBulkActions] = useState(false);
  const [expandedCases, setExpandedCases] = useState({});
  const [showImport, setShowImport] = useState(false);
  const [importFile, setImportFile] = useState(null);
  const [showComments, setShowComments] = useState(null);
  const [commentText, setCommentText] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);

  // Role-based permissions
  const canEdit = userRole === 'owner' || userRole === 'editor' || userRole === 'admin';
  const canView = true; // Everyone can view

  useEffect(() => {
    if (project) {
      loadTestCases();
      loadTabs();
    }
  }, [project, refreshKey]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.ctrlKey && e.key === 'n') {
        e.preventDefault();
        setShowForm(true);
      }
      if (e.key === 'Escape') {
        setShowForm(false);
        setShowImport(false);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

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
      const params = { project_id: project.id, is_template: false };
      if (searchQuery) {
        params.search = searchQuery;
      }
      const response = await axios.get(`${API}/test-cases`, { params });
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
      setRefreshKey(prev => prev + 1);
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
      setRefreshKey(prev => prev + 1);
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
      setRefreshKey(prev => prev + 1);
      toast.success('Status updated successfully!');
    } catch (error) {
      toast.error('Failed to update status');
      console.error(error);
    }
  };

  const handleBulkStatusChange = async (status) => {
    try {
      await axios.post(`${API}/test-cases/bulk-status`, {
        test_case_ids: selectedCases,
        status
      });
      await loadTestCases();
      setSelectedCases([]);
      setShowBulkActions(false);
      setRefreshKey(prev => prev + 1);
      toast.success(`Updated ${selectedCases.length} test cases`);
    } catch (error) {
      toast.error('Failed to update test cases');
      console.error(error);
    }
  };

  const handleBulkDelete = async () => {
    try {
      await axios.delete(`${API}/test-cases/bulk`, { data: selectedCases });
      await loadTestCases();
      setSelectedCases([]);
      setShowBulkActions(false);
      await loadTabs();
      toast.success(`Deleted ${selectedCases.length} test cases`);
    } catch (error) {
      toast.error('Failed to delete test cases');
      console.error(error);
    }
  };

  const handleDuplicate = async (testCaseId) => {
    try {
      const response = await axios.post(`${API}/test-cases/${testCaseId}/duplicate`);
      setTestCases([...testCases, response.data]);
      toast.success('Test case duplicated successfully!');
    } catch (error) {
      toast.error('Failed to duplicate test case');
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
      const tabTestCases = testCases.filter(tc => tc.tab === editingTab);
      
      for (const tc of tabTestCases) {
        await axios.put(`${API}/test-cases/${tc.id}`, { tab: newTabName });
      }
      
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
      const tabTestCases = testCases.filter(tc => tc.tab === deleteTab);
      
      for (const tc of tabTestCases) {
        await axios.delete(`${API}/test-cases/${tc.id}`);
      }
      
      await loadTestCases();
      await loadTabs();
      setDeleteTab(null);
      toast.success('Tab and all test cases deleted successfully!');
    } catch (error) {
      toast.error('Failed to delete tab');
      console.error(error);
    }
  };

  const handleImport = async () => {
    if (!importFile) {
      toast.error('Please select a file');
      return;
    }

    const formData = new FormData();
    formData.append('file', importFile);

    try {
      const response = await axios.post(`${API}/test-cases/import/${project.id}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success(`Imported ${response.data.imported_count} test cases`);
      await loadTestCases();
      await loadTabs();
      setShowImport(false);
      setImportFile(null);
    } catch (error) {
      toast.error('Failed to import test cases');
      console.error(error);
    }
  };

  const handleAddComment = async (testCaseId) => {
    if (!commentText.trim()) return;

    try {
      await axios.post(`${API}/test-cases/${testCaseId}/comments`, {
        test_case_id: testCaseId,
        text: commentText,
        created_by: 'User' // In production, use actual user name
      });
      await loadTestCases();
      setCommentText('');
      toast.success('Comment added!');
    } catch (error) {
      toast.error('Failed to add comment');
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
      const extension = format === 'excel' ? 'xlsx' : 'docx';
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

  const toggleExpanded = (id) => {
    setExpandedCases(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const toggleSelectCase = (id) => {
    setSelectedCases(prev =>
      prev.includes(id) ? prev.filter(caseId => caseId !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = (tabCases) => {
    const tabCaseIds = tabCases.map(tc => tc.id);
    const allSelected = tabCaseIds.every(id => selectedCases.includes(id));
    
    if (allSelected) {
      setSelectedCases(prev => prev.filter(id => !tabCaseIds.includes(id)));
    } else {
      setSelectedCases(prev => [...new Set([...prev, ...tabCaseIds])]);
    }
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

  useEffect(() => {
    const debounce = setTimeout(() => {
      if (project) {
        loadTestCases();
      }
    }, 500);

    return () => clearTimeout(debounce);
  }, [searchQuery]);

  if (loading) {
    return <div className="glass-effect rounded-2xl p-8 text-center">Loading test cases...</div>;
  }

  return (
    <div>
      {/* Statistics Widget */}
      <StatisticsWidget project={project} key={refreshKey} />

      <div className="glass-effect rounded-2xl p-6" style={{ minHeight: '750px' }}>
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900" data-testid="testcases-title">{project.name}</h2>
            <p className="text-sm text-gray-600 mt-1">{testCases.length} test case(s)</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              onClick={() => setShowImport(true)}
              variant="outline"
              size="sm"
              className="btn-secondary"
              data-testid="import-btn"
            >
              <Upload size={16} className="mr-2" />
              Import
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
              onClick={() => handleExport('excel')}
              variant="outline"
              size="sm"
              className="btn-secondary"
              data-testid="export-excel-btn"
            >
              <FileSpreadsheet size={16} className="mr-2" />
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

        {/* Search Bar */}
        <div className="mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
            <Input
              placeholder="Search test cases by title, description, or steps... (Ctrl+F)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
              data-testid="search-input"
            />
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

        {/* Bulk Actions Bar */}
        {selectedCases.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 flex items-center justify-between">
            <span className="text-sm font-medium text-blue-900">
              {selectedCases.length} test case(s) selected
            </span>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={() => handleBulkStatusChange('success')} data-testid="bulk-success-btn">
                Mark Success
              </Button>
              <Button size="sm" variant="outline" onClick={() => handleBulkStatusChange('fail')} data-testid="bulk-fail-btn">
                Mark Fail
              </Button>
              <Button size="sm" variant="outline" onClick={() => handleBulkStatusChange('draft')} data-testid="bulk-draft-btn">
                Mark Draft
              </Button>
              <Button size="sm" variant="destructive" onClick={handleBulkDelete} data-testid="bulk-delete-btn">
                Delete Selected
              </Button>
            </div>
          </div>
        )}

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <div className="flex items-start gap-2 mb-4">
            <TabsList className="justify-start">
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

          {tabs.map((tab) => {
            const tabCases = getFilteredTestCases(tab);
            return (
              <TabsContent key={tab} value={tab} className="mt-0">
                {/* Select All for Tab */}
                {tabCases.length > 0 && (
                  <div className="flex items-center gap-2 mb-3">
                    <Checkbox
                      checked={tabCases.every(tc => selectedCases.includes(tc.id))}
                      onCheckedChange={() => toggleSelectAll(tabCases)}
                      data-testid="select-all-checkbox"
                    />
                    <span className="text-sm text-gray-600">Select All</span>
                  </div>
                )}

                <div className="space-y-4 custom-scrollbar" style={{ maxHeight: '500px', overflowY: 'auto' }}>
                  {tabCases.length === 0 ? (
                    <div className="text-center py-12">
                      <p className="text-gray-500 mb-4">No test cases found in this tab</p>
                      <Button onClick={() => setShowForm(true)} className="btn-dark">
                        <Plus size={16} className="mr-2" />
                        Create Test Case
                      </Button>
                    </div>
                  ) : (
                    tabCases.map((tc) => (
                      <div
                        key={tc.id}
                        data-testid={`testcase-card-${tc.id}`}
                        className="bg-white rounded-lg p-4 border border-gray-200 card-hover"
                      >
                        <div className="flex items-start gap-3">
                          <Checkbox
                            checked={selectedCases.includes(tc.id)}
                            onCheckedChange={() => toggleSelectCase(tc.id)}
                            data-testid={`select-checkbox-${tc.id}`}
                          />
                          
                          <div className="flex-1">
                            <div className="flex items-start justify-between mb-3">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                  <h3 className="font-semibold text-gray-900" data-testid={`testcase-title-${tc.id}`}>{tc.title}</h3>
                                  {getStatusBadge(tc.status)}
                                </div>
                                
                                {!expandedCases[tc.id] && (
                                  <p className="text-sm text-gray-600 mb-2 line-clamp-2" data-testid={`testcase-description-${tc.id}`}>
                                    {tc.description}
                                  </p>
                                )}
                                
                                <div className="flex flex-wrap gap-2 text-xs mb-2">
                                  <span className={`font-medium ${getPriorityColor(tc.priority)}`} data-testid={`testcase-priority-${tc.id}`}>
                                    Priority: {tc.priority}
                                  </span>
                                  <span className="text-gray-500">•</span>
                                  <span className="text-gray-600" data-testid={`testcase-type-${tc.id}`}>Type: {tc.type}</span>
                                  {tc.assigned_to && (
                                    <>
                                      <span className="text-gray-500">•</span>
                                      <span className="flex items-center gap-1 text-gray-600">
                                        <User size={12} /> {tc.assigned_to}
                                      </span>
                                    </>
                                  )}
                                  {tc.executed_at && (
                                    <>
                                      <span className="text-gray-500">•</span>
                                      <span className="flex items-center gap-1 text-gray-600">
                                        <Calendar size={12} /> {new Date(tc.executed_at).toLocaleDateString()}
                                      </span>
                                    </>
                                  )}
                                </div>
                              </div>
                              
                              <div className="flex gap-1">
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => toggleExpanded(tc.id)}
                                  data-testid={`expand-btn-${tc.id}`}
                                >
                                  {expandedCases[tc.id] ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                                </Button>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => handleDuplicate(tc.id)}
                                  data-testid={`duplicate-btn-${tc.id}`}
                                >
                                  <Copy size={16} />
                                </Button>
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

                            {expandedCases[tc.id] && (
                              <>
                                <div className="space-y-3 text-sm mb-3">
                                  <div>
                                    <span className="font-medium text-gray-700">Description:</span>
                                    <p className="text-gray-600 mt-1">{tc.description}</p>
                                  </div>
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

                                {/* Comments Section */}
                                <div className="border-t pt-3 mb-3">
                                  <div className="flex items-center gap-2 mb-2">
                                    <MessageSquare size={16} className="text-gray-600" />
                                    <span className="text-sm font-medium text-gray-700">Comments ({tc.comments?.length || 0})</span>
                                  </div>
                                  {tc.comments && tc.comments.length > 0 && (
                                    <div className="space-y-2 mb-3">
                                      {tc.comments.map((comment, idx) => (
                                        <div key={idx} className="bg-gray-50 rounded p-2 text-xs">
                                          <div className="flex justify-between mb-1">
                                            <span className="font-medium">{comment.created_by}</span>
                                            <span className="text-gray-500">
                                              {new Date(comment.created_at).toLocaleString()}
                                            </span>
                                          </div>
                                          <p className="text-gray-700">{comment.text}</p>
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                  <div className="flex gap-2">
                                    <Input
                                      placeholder="Add a comment..."
                                      value={showComments === tc.id ? commentText : ''}
                                      onChange={(e) => {
                                        setShowComments(tc.id);
                                        setCommentText(e.target.value);
                                      }}
                                      className="text-sm"
                                      data-testid={`comment-input-${tc.id}`}
                                    />
                                    <Button
                                      size="sm"
                                      onClick={() => handleAddComment(tc.id)}
                                      data-testid={`add-comment-btn-${tc.id}`}
                                    >
                                      Add
                                    </Button>
                                  </div>
                                </div>
                              </>
                            )}

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
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </TabsContent>
            );
          })}
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

        {/* Import Dialog */}
        <Dialog open={showImport} onOpenChange={setShowImport}>
          <DialogContent data-testid="import-dialog">
            <DialogHeader>
              <DialogTitle>Import Test Cases</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Select Excel or Word file</Label>
                <Input
                  type="file"
                  accept=".xlsx,.xls,.docx"
                  onChange={(e) => setImportFile(e.target.files[0])}
                  data-testid="import-file-input"
                />
                <p className="text-xs text-gray-500 mt-2">
                  File should include columns: Title, Description, Priority, Type, Steps, Expected Result, Tab (optional)
                </p>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setShowImport(false)}>Cancel</Button>
                <Button onClick={handleImport} className="btn-dark" data-testid="confirm-import-btn">Import</Button>
              </div>
            </div>
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
    </div>
  );
};

export default TestCaseList;
