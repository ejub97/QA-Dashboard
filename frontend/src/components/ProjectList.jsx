import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { FolderOpen, Shield, Trash2, Edit2, X, Check } from 'lucide-react';
import { useState } from 'react';

const ProjectList = ({ projects, selectedProject, onSelectProject, onDeleteProject, onRenameProject, user }) => {
  const [editingProject, setEditingProject] = useState(null);
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const getProjectRole = (project) => {
    if (!user) return null;
    if (project.owner_id === user.id) return 'owner';
    const member = project.members?.find(m => m.user_id === user.id);
    return member?.role || null;
  };

  return (
    <div className="glass-effect rounded-2xl p-4">
      <h2 className="text-lg font-semibold text-gray-900 mb-4" data-testid="projects-heading">Projects</h2>
      <div className="space-y-2">
        {projects.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-4">No projects yet</p>
        ) : (
          projects.map((project) => {
            const role = getProjectRole(project);
            const isOwner = project.owner_id === user?.id;
            
            return (
              <div
                key={project.id}
                data-testid={`project-item-${project.id}`}
                className={`p-3 rounded-lg cursor-pointer transition-all ${
                  selectedProject?.id === project.id
                    ? 'bg-blue-50 border-2 border-blue-500'
                    : 'bg-white border border-gray-200 hover:border-blue-300'
                }`}
                onClick={() => onSelectProject(project)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {isOwner && <Shield size={14} className="text-yellow-500 flex-shrink-0" />}
                      <FolderOpen size={16} className="text-blue-600 flex-shrink-0" />
                      <h3 className="font-medium text-sm text-gray-900 truncate" data-testid={`project-name-${project.id}`}>
                        {project.name}
                      </h3>
                    </div>
                    {project.description && (
                      <p className="text-xs text-gray-500 truncate">{project.description}</p>
                    )}
                    <p className="text-xs text-gray-500 mt-1">
                      {isOwner ? (
                        <span className="text-yellow-600 font-medium">Owner</span>
                      ) : (
                        <span className="capitalize">{role}</span>
                      )}
                      {' • '}
                      {project.members?.length || 0} member(s)
                    </p>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default ProjectList;