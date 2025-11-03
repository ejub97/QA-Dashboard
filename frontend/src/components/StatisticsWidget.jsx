import { useEffect, useState } from 'react';
import axios from 'axios';
import { FileText, CheckCircle, XCircle, Clock } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const StatisticsWidget = ({ project }) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (project) {
      loadStatistics();
    }
  }, [project]);

  const loadStatistics = async () => {
    try {
      const response = await axios.get(`${API}/projects/${project.id}/statistics`);
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load statistics', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !stats) return null;

  const successRate = stats.total > 0 ? Math.round((stats.success / stats.total) * 100) : 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div className="glass-effect rounded-xl p-4" data-testid="stats-total">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">Total Cases</p>
            <p className="text-3xl font-bold text-gray-900">{stats.total}</p>
          </div>
          <FileText className="text-blue-500" size={32} />
        </div>
      </div>

      <div className="glass-effect rounded-xl p-4" data-testid="stats-draft">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">Draft</p>
            <p className="text-3xl font-bold text-yellow-600">{stats.draft}</p>
          </div>
          <Clock className="text-yellow-500" size={32} />
        </div>
      </div>

      <div className="glass-effect rounded-xl p-4" data-testid="stats-success">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">Passed</p>
            <p className="text-3xl font-bold text-green-600">{stats.success}</p>
          </div>
          <CheckCircle className="text-green-500" size={32} />
        </div>
      </div>

      <div className="glass-effect rounded-xl p-4" data-testid="stats-fail">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">Failed</p>
            <p className="text-3xl font-bold text-red-600">{stats.fail}</p>
          </div>
          <XCircle className="text-red-500" size={32} />
        </div>
      </div>

      {/* Success Rate Bar */}
      <div className="md:col-span-4 glass-effect rounded-xl p-4">
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm font-medium text-gray-700">Test Execution Progress</p>
          <p className="text-sm font-bold text-blue-600">{successRate}% Success Rate</p>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div 
            className="bg-gradient-to-r from-green-400 to-green-600 h-3 rounded-full transition-all duration-500"
            style={{ width: `${successRate}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>{stats.success} passed</span>
          <span>{stats.fail} failed</span>
          <span>{stats.draft} pending</span>
        </div>
      </div>
    </div>
  );
};

export default StatisticsWidget;
