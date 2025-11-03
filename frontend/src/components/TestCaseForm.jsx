import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

const TestCaseForm = ({ testCase, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    type: 'functional',
    steps: '',
    expected_result: '',
    actual_result: '',
  });

  useEffect(() => {
    if (testCase) {
      setFormData({
        title: testCase.title || '',
        description: testCase.description || '',
        priority: testCase.priority || 'medium',
        type: testCase.type || 'functional',
        steps: testCase.steps || '',
        expected_result: testCase.expected_result || '',
        actual_result: testCase.actual_result || '',
      });
    }
  }, [testCase]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handleChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="title">Title *</Label>
        <Input
          id="title"
          data-testid="testcase-title-input"
          placeholder="Enter test case title"
          value={formData.title}
          onChange={(e) => handleChange('title', e.target.value)}
          className="input-focus"
          required
        />
      </div>

      <div>
        <Label htmlFor="description">Description *</Label>
        <Textarea
          id="description"
          data-testid="testcase-description-input"
          placeholder="Enter test case description"
          value={formData.description}
          onChange={(e) => handleChange('description', e.target.value)}
          rows={2}
          className="input-focus"
          required
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="priority">Priority *</Label>
          <Select value={formData.priority} onValueChange={(value) => handleChange('priority', value)}>
            <SelectTrigger data-testid="testcase-priority-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="low">Low</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="high">High</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor="type">Type *</Label>
          <Select value={formData.type} onValueChange={(value) => handleChange('type', value)}>
            <SelectTrigger data-testid="testcase-type-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
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

      <div>
        <Label htmlFor="steps">Steps *</Label>
        <Textarea
          id="steps"
          data-testid="testcase-steps-input"
          placeholder="Enter test steps (one per line)"
          value={formData.steps}
          onChange={(e) => handleChange('steps', e.target.value)}
          rows={4}
          className="input-focus"
          required
        />
      </div>

      <div>
        <Label htmlFor="expected_result">Expected Result *</Label>
        <Textarea
          id="expected_result"
          data-testid="testcase-expected-input"
          placeholder="Enter expected result"
          value={formData.expected_result}
          onChange={(e) => handleChange('expected_result', e.target.value)}
          rows={3}
          className="input-focus"
          required
        />
      </div>

      <div>
        <Label htmlFor="actual_result">Actual Result</Label>
        <Textarea
          id="actual_result"
          data-testid="testcase-actual-input"
          placeholder="Enter actual result (optional)"
          value={formData.actual_result}
          onChange={(e) => handleChange('actual_result', e.target.value)}
          rows={3}
          className="input-focus"
        />
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="button" variant="outline" onClick={onCancel} data-testid="cancel-testcase-btn">
          Cancel
        </Button>
        <Button type="submit" className="btn-dark" data-testid="submit-testcase-btn">
          {testCase ? 'Update' : 'Create'} Test Case
        </Button>
      </div>
    </form>
  );
};

export default TestCaseForm;