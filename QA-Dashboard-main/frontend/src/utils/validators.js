/**
 * Frontend validation utilities
 */

export const Validators = {
  // Patterns
  EMAIL_PATTERN: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
  USERNAME_PATTERN: /^[a-zA-Z0-9_-]{3,30}$/,
  
  // Length limits
  MIN_PASSWORD_LENGTH: 6,
  MAX_PASSWORD_LENGTH: 100,
  MIN_USERNAME_LENGTH: 3,
  MAX_USERNAME_LENGTH: 30,
  MIN_PROJECT_NAME_LENGTH: 1,
  MAX_PROJECT_NAME_LENGTH: 100,
  MAX_DESCRIPTION_LENGTH: 500,
  MAX_TITLE_LENGTH: 200,
  MAX_STEPS_LENGTH: 5000,
  MAX_RESULT_LENGTH: 1000,
  MAX_COMMENT_LENGTH: 1000,
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  
  // Valid values
  VALID_PRIORITIES: ['low', 'medium', 'high'],
  VALID_TEST_TYPES: ['functional', 'negative', 'ui/ux', 'smoke', 'regression', 'api'],
  VALID_STATUSES: ['draft', 'success', 'fail'],
  VALID_ROLES: ['admin', 'editor', 'viewer'],
  
  /**
   * Validate email
   */
  validateEmail(email) {
    if (!email) return { valid: false, error: 'Email is required' };
    
    const trimmed = email.trim();
    
    if (!this.EMAIL_PATTERN.test(trimmed)) {
      return { valid: false, error: 'Invalid email format' };
    }
    
    if (trimmed.length > 255) {
      return { valid: false, error: 'Email is too long (max 255 characters)' };
    }
    
    return { valid: true, value: trimmed.toLowerCase() };
  },
  
  /**
   * Validate username
   */
  validateUsername(username) {
    if (!username) return { valid: false, error: 'Username is required' };
    
    const trimmed = username.trim();
    
    if (trimmed.length < this.MIN_USERNAME_LENGTH) {
      return { valid: false, error: `Username must be at least ${this.MIN_USERNAME_LENGTH} characters` };
    }
    
    if (trimmed.length > this.MAX_USERNAME_LENGTH) {
      return { valid: false, error: `Username must be less than ${this.MAX_USERNAME_LENGTH} characters` };
    }
    
    if (!this.USERNAME_PATTERN.test(trimmed)) {
      return { valid: false, error: 'Username can only contain letters, numbers, hyphens, and underscores' };
    }
    
    return { valid: true, value: trimmed };
  },
  
  /**
   * Validate password
   */
  validatePassword(password) {
    if (!password) return { valid: false, error: 'Password is required' };
    
    if (password.length < this.MIN_PASSWORD_LENGTH) {
      return { valid: false, error: `Password must be at least ${this.MIN_PASSWORD_LENGTH} characters` };
    }
    
    if (password.length > this.MAX_PASSWORD_LENGTH) {
      return { valid: false, error: `Password is too long (max ${this.MAX_PASSWORD_LENGTH} characters)` };
    }
    
    if (!/[a-zA-Z]/.test(password)) {
      return { valid: false, error: 'Password must contain at least one letter' };
    }
    
    if (!/[0-9]/.test(password)) {
      return { valid: false, error: 'Password must contain at least one number' };
    }
    
    return { valid: true, value: password };
  },
  
  /**
   * Validate full name
   */
  validateFullName(fullName) {
    if (!fullName) return { valid: false, error: 'Full name is required' };
    
    const trimmed = fullName.trim();
    
    if (trimmed.length < 2) {
      return { valid: false, error: 'Full name must be at least 2 characters' };
    }
    
    if (trimmed.length > 100) {
      return { valid: false, error: 'Full name is too long (max 100 characters)' };
    }
    
    return { valid: true, value: trimmed };
  },
  
  /**
   * Validate project name
   */
  validateProjectName(name) {
    if (!name) return { valid: false, error: 'Project name is required' };
    
    const trimmed = name.trim();
    
    if (trimmed.length < this.MIN_PROJECT_NAME_LENGTH) {
      return { valid: false, error: 'Project name cannot be empty' };
    }
    
    if (trimmed.length > this.MAX_PROJECT_NAME_LENGTH) {
      return { valid: false, error: `Project name is too long (max ${this.MAX_PROJECT_NAME_LENGTH} characters)` };
    }
    
    return { valid: true, value: trimmed };
  },
  
  /**
   * Validate description
   */
  validateDescription(description) {
    const trimmed = (description || '').trim();
    
    if (trimmed.length > this.MAX_DESCRIPTION_LENGTH) {
      return { valid: false, error: `Description is too long (max ${this.MAX_DESCRIPTION_LENGTH} characters)` };
    }
    
    return { valid: true, value: trimmed };
  },
  
  /**
   * Validate title
   */
  validateTitle(title) {
    if (!title) return { valid: false, error: 'Title is required' };
    
    const trimmed = title.trim();
    
    if (trimmed.length < 3) {
      return { valid: false, error: 'Title must be at least 3 characters' };
    }
    
    if (trimmed.length > this.MAX_TITLE_LENGTH) {
      return { valid: false, error: `Title is too long (max ${this.MAX_TITLE_LENGTH} characters)` };
    }
    
    return { valid: true, value: trimmed };
  },
  
  /**
   * Validate priority
   */
  validatePriority(priority) {
    if (!priority) return { valid: false, error: 'Priority is required' };
    
    const lower = priority.toLowerCase();
    
    if (!this.VALID_PRIORITIES.includes(lower)) {
      return { valid: false, error: `Invalid priority. Must be one of: ${this.VALID_PRIORITIES.join(', ')}` };
    }
    
    return { valid: true, value: lower };
  },
  
  /**
   * Validate test type
   */
  validateTestType(type) {
    if (!type) return { valid: false, error: 'Test type is required' };
    
    const lower = type.toLowerCase();
    
    if (!this.VALID_TEST_TYPES.includes(lower)) {
      return { valid: false, error: `Invalid type. Must be one of: ${this.VALID_TEST_TYPES.join(', ')}` };
    }
    
    return { valid: true, value: lower };
  },
  
  /**
   * Validate steps
   */
  validateSteps(steps) {
    if (!steps) return { valid: false, error: 'Test steps are required' };
    
    const trimmed = steps.trim();
    
    if (trimmed.length > this.MAX_STEPS_LENGTH) {
      return { valid: false, error: `Steps are too long (max ${this.MAX_STEPS_LENGTH} characters)` };
    }
    
    return { valid: true, value: trimmed };
  },
  
  /**
   * Validate expected result
   */
  validateExpectedResult(result) {
    if (!result) return { valid: false, error: 'Expected result is required' };
    
    const trimmed = result.trim();
    
    if (trimmed.length > this.MAX_RESULT_LENGTH) {
      return { valid: false, error: `Expected result is too long (max ${this.MAX_RESULT_LENGTH} characters)` };
    }
    
    return { valid: true, value: trimmed };
  },
  
  /**
   * Validate file size
   */
  validateFileSize(file) {
    if (!file) return { valid: false, error: 'No file selected' };
    
    if (file.size > this.MAX_FILE_SIZE) {
      const maxMB = this.MAX_FILE_SIZE / (1024 * 1024);
      return { valid: false, error: `File is too large. Maximum size is ${maxMB}MB` };
    }
    
    return { valid: true };
  },
  
  /**
   * Validate file type
   */
  validateFileType(file, allowedExtensions) {
    if (!file) return { valid: false, error: 'No file selected' };
    
    const extension = file.name.split('.').pop().toLowerCase();
    
    if (!allowedExtensions.includes(`.${extension}`)) {
      return { valid: false, error: `Invalid file type. Allowed: ${allowedExtensions.join(', ')}` };
    }
    
    return { valid: true };
  }
};

export default Validators;
