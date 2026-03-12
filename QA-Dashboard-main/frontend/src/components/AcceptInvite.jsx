import { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Loader2, CheckCircle, XCircle, Mail, Users } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AcceptInvite = () => {
  const { token } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [inviteDetails, setInviteDetails] = useState(null);
  const [error, setError] = useState('');
  const [accepting, setAccepting] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    loadInviteDetails();
  }, [token]);

  const loadInviteDetails = async () => {
    try {
      const response = await axios.get(`${API}/invites/${token}`);
      setInviteDetails(response.data);
    } catch (error) {
      setError(error.response?.data?.detail || 'Invalid or expired invitation');
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptInvite = async () => {
    if (!user) {
      // Redirect to login with return URL
      navigate(`/login?redirect=/accept-invite/${token}`);
      return;
    }

    setAccepting(true);
    try {
      const response = await axios.post(`${API}/invites/${token}/accept`);
      setSuccess(true);
      console.log('Invitation accepted successfully');
      
      // Redirect to dashboard after 2 seconds
      setTimeout(() => {
        navigate('/');
      }, 2000);
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to accept invitation');
    } finally {
      setAccepting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <Loader2 className="animate-spin h-12 w-12 text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading invitation...</p>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
        <Card className="max-w-md w-full p-8 text-center">
          <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Invitation Accepted!</h1>
          <p className="text-gray-600 mb-4">
            You've been added to <strong>{inviteDetails?.project_name}</strong>
          </p>
          <p className="text-sm text-gray-500">Redirecting to dashboard...</p>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
        <Card className="max-w-md w-full p-8 text-center">
          <XCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Invalid Invitation</h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <Link to="/login">
            <Button className="btn-dark">Go to Login</Button>
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <Card className="max-w-md w-full p-8">
        <div className="text-center mb-6">
          <Mail className="h-16 w-16 text-blue-600 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">You're Invited!</h1>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3 mb-3">
            <Users className="text-blue-600 mt-1" size={20} />
            <div>
              <p className="text-sm text-gray-700">
                <strong>{inviteDetails?.invited_by}</strong> has invited you to join:
              </p>
              <p className="text-lg font-bold text-gray-900 mt-1">
                {inviteDetails?.project_name}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 mt-3">
            <span className="text-sm text-gray-600">Your role:</span>
            <span className="px-3 py-1 bg-blue-600 text-white text-xs font-medium rounded-full">
              {inviteDetails?.role?.toUpperCase()}
            </span>
          </div>
        </div>

        {!user && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-yellow-800">
              ℹ️ You need to be logged in to accept this invitation. 
              If you don't have an account, please register first.
            </p>
          </div>
        )}

        <div className="space-y-3">
          <Button
            onClick={handleAcceptInvite}
            className="w-full btn-dark"
            disabled={accepting}
          >
            {accepting ? (
              <>
                <Loader2 className="animate-spin mr-2" size={16} />
                Accepting...
              </>
            ) : (
              user ? 'Accept Invitation' : 'Login to Accept'
            )}
          </Button>

          {!user && (
            <Link to="/register" className="block">
              <Button variant="outline" className="w-full">
                Don't have an account? Register
              </Button>
            </Link>
          )}

          <Link to="/login" className="block">
            <Button variant="ghost" className="w-full">
              Back to Login
            </Button>
          </Link>
        </div>
      </Card>
    </div>
  );
};

export default AcceptInvite;
