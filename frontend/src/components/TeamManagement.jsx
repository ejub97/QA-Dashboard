import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Users, UserPlus, Trash2, Shield } from 'lucide-react';
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

const TeamManagement = ({ project, isOwner, canManageTeam, onUpdate }) => {
  const [showAddMember, setShowAddMember] = useState(false);
  const [username, setUsername] = useState('');
  const [role, setRole] = useState('viewer');
  const [loading, setLoading] = useState(false);
  const [removeMember, setRemoveMember] = useState(null);

  const handleAddMember = async () => {
    if (!username.trim()) {
      // 'Please enter a username');
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/projects/${project.id}/members`, {
        username,
        role
      });
      // `Added ${username} as ${role}`);
      setUsername('');
      setRole('viewer');
      setShowAddMember(false);
      if (onUpdate) onUpdate();
    } catch (error) {
      // error.response?.data?.detail || 'Failed to add member');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveMember = async () => {
    try {
      await axios.delete(`${API}/projects/${project.id}/members/${removeMember.user_id}`);
      // `Removed ${removeMember.username}`);
      setRemoveMember(null);
      if (onUpdate) onUpdate();
    } catch (error) {
      // 'Failed to remove member');
    }
  };

  const handleChangeRole = async (userId, newRole) => {
    try {
      await axios.put(`${API}/projects/${project.id}/members/${userId}/role`, null, {
        params: { role: newRole }
      });
      // 'Role updated successfully');
      if (onUpdate) onUpdate();
    } catch (error) {
      // 'Failed to update role');
    }
  };

  const getRoleBadgeColor = (role) => {
    const colors = {
      admin: 'bg-purple-100 text-purple-700 border-purple-300',
      editor: 'bg-blue-100 text-blue-700 border-blue-300',
      viewer: 'bg-gray-100 text-gray-700 border-gray-300'
    };
    return colors[role] || colors.viewer;
  };

  if (!canManageTeam && !isOwner) {
    return null;
  }

  return (
    <div className="glass-effect rounded-2xl p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Users size={24} className="text-blue-600" />
          <h2 className="text-xl font-bold text-gray-900">Team Members</h2>
        </div>
        <Button
          onClick={() => setShowAddMember(true)}
          className="btn-dark"
          size="sm"
          data-testid="add-member-btn"
        >
          <UserPlus size={16} className="mr-2" />
          Add Member
        </Button>
      </div>

      <div className="space-y-3">
        {/* Owner */}
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield className="text-yellow-500" size={20} />
              <div>
                <p className="font-medium text-gray-900">Project Owner</p>
                <p className="text-sm text-gray-500">Full access & control</p>
              </div>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700 border border-yellow-300">
              Owner
            </span>
          </div>
        </div>

        {/* Members */}
        {project.members && project.members.length > 0 ? (
          project.members.map((member) => (
            <div
              key={member.user_id}
              className="bg-white rounded-lg p-4 border border-gray-200"
              data-testid={`member-${member.username}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1">
                  <Users className="text-gray-400" size={20} />
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{member.username}</p>
                    <p className="text-xs text-gray-500">
                      Added {new Date(member.added_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {canManageTeam || isOwner ? (
                    <Select
                      value={member.role}
                      onValueChange={(newRole) => handleChangeRole(member.user_id, newRole)}
                    >
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="admin">Admin</SelectItem>
                        <SelectItem value="editor">Editor</SelectItem>
                        <SelectItem value="viewer">Viewer</SelectItem>
                      </SelectContent>
                    </Select>
                  ) : (
                    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getRoleBadgeColor(member.role)}`}>
                      {member.role}
                    </span>
                  )}
                  {(canManageTeam || isOwner) && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setRemoveMember(member)}
                      data-testid={`remove-member-${member.username}`}
                    >
                      <Trash2 size={16} className="text-red-500" />
                    </Button>
                  )}
                </div>
              </div>
            </div>
          ))
        ) : (
          <p className="text-center text-gray-500 py-4">No team members yet</p>
        )}
      </div>

      {/* Role Permissions Info */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <h3 className="font-medium text-blue-900 mb-2">Role Permissions:</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li><strong>Admin:</strong> Full access + manage team members</li>
          <li><strong>Editor:</strong> Create, edit, delete test cases</li>
          <li><strong>Viewer:</strong> View & download exports only</li>
        </ul>
      </div>

      {/* Add Member Dialog */}
      <Dialog open={showAddMember} onOpenChange={setShowAddMember}>
        <DialogContent data-testid="add-member-dialog">
          <DialogHeader>
            <DialogTitle>Add Team Member</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                placeholder="Enter username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                data-testid="add-member-username"
              />
            </div>
            <div>
              <Label htmlFor="role">Role</Label>
              <Select value={role} onValueChange={setRole}>
                <SelectTrigger data-testid="add-member-role">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="editor">Editor</SelectItem>
                  <SelectItem value="viewer">Viewer</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowAddMember(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleAddMember}
                className="btn-dark"
                disabled={loading}
                data-testid="confirm-add-member"
              >
                {loading ? 'Adding...' : 'Add Member'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Remove Member Confirmation */}
      <AlertDialog open={!!removeMember} onOpenChange={() => setRemoveMember(null)}>
        <AlertDialogContent data-testid="remove-member-dialog">
          <AlertDialogHeader>
            <AlertDialogTitle>Remove Team Member</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to remove {removeMember?.username} from this project?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleRemoveMember} className="bg-red-600 hover:bg-red-700">
              Remove
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default TeamManagement;