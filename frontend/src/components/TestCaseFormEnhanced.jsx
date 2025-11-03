import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { CalendarIcon } from 'lucide-react';
import { format } from 'date-fns';

const TestCaseForm = ({ testCase, onSubmit, onCancel, currentTab }) => {
  const [formData, setFormData] = useState({
    tab: currentTab || 'General',
    title: '',
    description: '',
    priority: 'medium',
    type: 'functional',
    steps: '',
    expected_result: '',
    actual_result: '',
    assigned_to: '',
    is_template: false,
  });
  const [executionDate, setExecutionDate] = useState(null);

  useEffect(() => {
    if (testCase) {
      setFormData({
        tab: testCase.tab || 'General',
        title: testCase.title || '',
        description: testCase.description || '',
        priority: testCase.priority || 'medium',
        type: testCase.type || 'functional',
        steps: testCase.steps || '',
        expected_result: testCase.expected_result || '',
        actual_result: testCase.actual_result || '',
        assigned_to: testCase.assigned_to || '',
        is_template: testCase.is_template || false,
      });
      if (testCase.executed_at) {
        setExecutionDate(new Date(testCase.executed_at));
      }
    } else if (currentTab) {
      setFormData(prev => ({ ...prev, tab: currentTab }));
    }
  }, [testCase, currentTab]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const submitData = { ...formData };
    if (executionDate) {
      submitData.executed_at = executionDate.toISOString();
    }
    onSubmit(submitData);
  };

  const handleChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <Label htmlFor="tab">Tab/Section *</Label>
          <Input
            id="tab"
            data-testid="testcase-tab-input"
            placeholder="Enter tab name (e.g., Registration, Login)"
            value={formData.tab}
            onChange={(e) => handleChange('tab', e.target.value)}
            className="input-focus"
            required
          />
        </div>
        <div className="flex items-center space-x-2 pt-6">
          <Checkbox
            id="is_template"
            checked={formData.is_template}
            onCheckedChange={(checked) => handleChange('is_template', checked)}
            data-testid="testcase-template-checkbox"
          />
          <Label htmlFor="is_template" className="text-sm cursor-pointer">
            Save as Template
          </Label>
        </div>
      </div>

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

      <div className="grid grid-cols-3 gap-4">
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

        <div>
          <Label htmlFor="assigned_to">Assigned To</Label>
          <Input
            id="assigned_to"
            data-testid="testcase-assigned-input"
            placeholder="Team member name"
            value={formData.assigned_to}
            onChange={(e) => handleChange('assigned_to', e.target.value)}
            className="input-focus"
          />
        </div>
      </div>

      <div>
        <Label htmlFor="steps">Steps *</Label>
        <Textarea
          id="steps"
          data-testid="testcase-steps-input"
          placeholder="Enter test steps (one per line)&#10;1. First step&#10;2. Second step&#10;3. Third step"
          value={formData.steps}
          onChange={(e) => handleChange('steps', e.target.value)}
          rows={5}
          className="input-focus"
          required
        />
        <p className="text-xs text-gray-500 mt-1">Add each step on a new line with numbering (1., 2., 3...)</p>
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

      <div>
        <Label>Execution Date</Label>
        <Popover>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              className="w-full justify-start text-left font-normal"
              data-testid="execution-date-picker"
            >
              <CalendarIcon className="mr-2 h-4 w-4" />
              {executionDate ? format(executionDate, 'PPP') : <span>Pick execution date</span>}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0">
            <Calendar
              mode="single"
              selected={executionDate}
              onSelect={setExecutionDate}
              initialFocus
            />
          </PopoverContent>
        </Popover>
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
