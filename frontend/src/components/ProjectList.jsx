import { Button } from '@/components/ui/button';
import { Link as LinkIcon, FolderOpen, Trash2 } from 'lucide-react';
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
import { useState } from 'react';

const ProjectList = ({ projects, selectedProject, onSelectProject, onCopyInvite, onDeleteProject }) => {
  const [deleteProject, setDeleteProject] = useState(null);
  return (
    <div className="glass-effect rounded-2xl p-4">
      <h2 className="text-lg font-semibold text-gray-900 mb-4" data-testid="projects-heading">Projects</h2>
      <div className="space-y-2">
        {projects.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-4">No projects yet</p>
        ) : (
          projects.map((project) => (
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
                    <FolderOpen size={16} className="text-blue-600 flex-shrink-0" />
                    <h3 className="font-medium text-sm text-gray-900 truncate" data-testid={`project-name-${project.id}`}>
                      {project.name}
                    </h3>
                  </div>
                  {project.description && (
                    <p className="text-xs text-gray-500 truncate">{project.description}</p>
                  )}
                </div>
              </div>
              <div className="flex gap-1 mt-2">
                <Button
                  size="sm"
                  variant="ghost"
                  className="flex-1 text-xs"
                  onClick={(e) => {
                    e.stopPropagation();
                    onCopyInvite(project);
                  }}
                  data-testid={`copy-invite-btn-${project.id}`}
                >
                  <LinkIcon size={12} className="mr-1" />
                  Copy Invite
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-xs text-red-600 hover:text-red-700 hover:bg-red-50"
                  onClick={(e) => {
                    e.stopPropagation();
                    setDeleteProject(project);
                  }}
                  data-testid={`delete-project-btn-${project.id}`}
                >
                  <Trash2 size={12} />
                </Button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deleteProject} onOpenChange={() => setDeleteProject(null)}>
        <AlertDialogContent data-testid="delete-project-dialog">
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Project</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{deleteProject?.name}"? This will also delete all associated test cases. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="cancel-delete-project-btn">Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={() => {
                onDeleteProject(deleteProject);
                setDeleteProject(null);
              }} 
              className="bg-red-600 hover:bg-red-700" 
              data-testid="confirm-delete-project-btn"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default ProjectList;