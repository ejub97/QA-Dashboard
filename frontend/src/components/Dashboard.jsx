import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import ProjectList from './ProjectList';
import TestCaseList from './TestCaseListEnhanced';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { FileText, Plus, Link as LinkIcon, Moon, Sun } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const { inviteCode } = useParams();
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showProjectDialog, setShowProjectDialog] = useState(false);
  const [projectForm, setProjectForm] = useState({ name: '', description: '' });

  useEffect(() => {
    if (inviteCode) {
      loadProjectByInvite(inviteCode);
    } else {
      loadProjects();
    }
  }, [inviteCode]);

  const loadProjects = async () => {
    try {
      const response = await axios.get(`${API}/projects`);
      setProjects(response.data);
      if (response.data.length > 0 && !selectedProject) {
        setSelectedProject(response.data[0]);
      }
    } catch (error) {
      toast.error('Failed to load projects');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const loadProjectByInvite = async (code) => {
    try {
      const response = await axios.get(`${API}/projects/invite/${code}`);
      setSelectedProject(response.data);
      setProjects([response.data]);
      navigate('/', { replace: true });
      toast.success('Project loaded successfully!');
    } catch (error) {
      toast.error('Invalid invite code');
      console.error(error);
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const createProject = async (e) => {
    e.preventDefault();
    if (!projectForm.name.trim()) {
      toast.error('Project name is required');
      return;
    }

    try {
      const response = await axios.post(`${API}/projects`, projectForm);
      setProjects([...projects, response.data]);
      setSelectedProject(response.data);
      setProjectForm({ name: '', description: '' });
      setShowProjectDialog(false);
      toast.success('Project created successfully!');
    } catch (error) {
      toast.error('Failed to create project');
      console.error(error);
    }
  };

  const copyInviteLink = (project) => {
    const inviteLink = `${window.location.origin}/invite/${project.invite_code}`;
    navigator.clipboard.writeText(inviteLink);
    toast.success('Invite link copied to clipboard!');
  };

  const deleteProject = async (project) => {
    try {
      await axios.delete(`${API}/projects/${project.id}`);
      const updatedProjects = projects.filter(p => p.id !== project.id);
      setProjects(updatedProjects);
      
      // If deleted project was selected, select another or clear
      if (selectedProject?.id === project.id) {
        setSelectedProject(updatedProjects.length > 0 ? updatedProjects[0] : null);
      }
      
      toast.success('Project deleted successfully!');
    } catch (error) {
      toast.error('Failed to delete project');
      console.error(error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-gray-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="glass-effect rounded-2xl p-6 mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2" data-testid="dashboard-title">
                <FileText className="inline-block mr-3 mb-1" size={36} />
                QA Test Dashboard
              </h1>
              <p className="text-gray-600">Manage your test cases efficiently</p>
            </div>
            <Dialog open={showProjectDialog} onOpenChange={setShowProjectDialog}>
              <DialogTrigger asChild>
                <Button className="btn-dark" data-testid="create-project-btn">
                  <Plus className="mr-2" size={18} />
                  New Project
                </Button>
              </DialogTrigger>
              <DialogContent data-testid="project-dialog">
                <DialogHeader>
                  <DialogTitle>Create New Project</DialogTitle>
                </DialogHeader>
                <form onSubmit={createProject} className="space-y-4">
                  <div>
                    <Label htmlFor="project-name">Project Name *</Label>
                    <Input
                      id="project-name"
                      data-testid="project-name-input"
                      placeholder="Enter project name"
                      value={projectForm.name}
                      onChange={(e) => setProjectForm({ ...projectForm, name: e.target.value })}
                      className="input-focus"
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="project-description">Description</Label>
                    <Textarea
                      id="project-description"
                      data-testid="project-description-input"
                      placeholder="Enter project description"
                      value={projectForm.description}
                      onChange={(e) => setProjectForm({ ...projectForm, description: e.target.value })}
                      rows={3}
                      className="input-focus"
                    />
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button type="button" variant="outline" onClick={() => setShowProjectDialog(false)} data-testid="cancel-project-btn">
                      Cancel
                    </Button>
                    <Button type="submit" className="btn-dark" data-testid="submit-project-btn">
                      Create Project
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Projects Sidebar */}
          <div className="lg:col-span-1">
            <ProjectList
              projects={projects}
              selectedProject={selectedProject}
              onSelectProject={setSelectedProject}
              onCopyInvite={copyInviteLink}
              onDeleteProject={deleteProject}
            />
          </div>

          {/* Test Cases Main Area */}
          <div className="lg:col-span-3">
            {selectedProject ? (
              <TestCaseList project={selectedProject} />
            ) : (
              <div className="glass-effect rounded-2xl p-12 text-center">
                <FileText className="mx-auto mb-4 text-gray-400" size={64} />
                <h3 className="text-xl font-semibold text-gray-700 mb-2">No Project Selected</h3>
                <p className="text-gray-500 mb-6">Create a new project or select an existing one to get started</p>
                <Button onClick={() => setShowProjectDialog(true)} className="btn-dark">
                  <Plus className="mr-2" size={18} />
                  Create Your First Project
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;