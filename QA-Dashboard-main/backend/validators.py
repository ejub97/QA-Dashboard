"""
Validation utilities for the QA Dashboard application
"""
import re
from typing import Optional
from fastapi import HTTPException


class ValidationError(Exception):
    """Custom validation error"""
    pass


class Validators:
    """Collection of validation methods"""
    
    # Regex patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,30}$')
    
    # Length limits
    MIN_PASSWORD_LENGTH = 6
    MAX_PASSWORD_LENGTH = 100
    MIN_USERNAME_LENGTH = 3
    MAX_USERNAME_LENGTH = 30
    MIN_PROJECT_NAME_LENGTH = 1
    MAX_PROJECT_NAME_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 500
    MAX_TITLE_LENGTH = 200
    MAX_STEPS_LENGTH = 5000
    MAX_RESULT_LENGTH = 1000
    MAX_COMMENT_LENGTH = 1000
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Valid enums
    VALID_PRIORITIES = ['low', 'medium', 'high']
    VALID_TEST_TYPES = ['functional', 'negative', 'ui/ux', 'smoke', 'regression', 'api']
    VALID_STATUSES = ['draft', 'success', 'fail']
    VALID_ROLES = ['admin', 'editor', 'viewer']
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format"""
        if not email:
            raise ValidationError("Email is required")
        
        email = email.strip().lower()
        
        if not Validators.EMAIL_PATTERN.match(email):
            raise ValidationError("Invalid email format")
        
        if len(email) > 255:
            raise ValidationError("Email is too long (max 255 characters)")
        
        return email
    
    @staticmethod
    def validate_username(username: str) -> str:
        """Validate username format"""
        if not username:
            raise ValidationError("Username is required")
        
        username = username.strip()
        
        if len(username) < Validators.MIN_USERNAME_LENGTH:
            raise ValidationError(f"Username must be at least {Validators.MIN_USERNAME_LENGTH} characters")
        
        if len(username) > Validators.MAX_USERNAME_LENGTH:
            raise ValidationError(f"Username must be less than {Validators.MAX_USERNAME_LENGTH} characters")
        
        if not Validators.USERNAME_PATTERN.match(username):
            raise ValidationError("Username can only contain letters, numbers, hyphens, and underscores")
        
        return username
    
    @staticmethod
    def validate_password(password: str) -> None:
        """Validate password strength"""
        if not password:
            raise ValidationError("Password is required")
        
        if len(password) < Validators.MIN_PASSWORD_LENGTH:
            raise ValidationError(f"Password must be at least {Validators.MIN_PASSWORD_LENGTH} characters")
        
        if len(password) > Validators.MAX_PASSWORD_LENGTH:
            raise ValidationError(f"Password is too long (max {Validators.MAX_PASSWORD_LENGTH} characters)")
        
        # Check for at least one letter and one number
        if not re.search(r'[a-zA-Z]', password):
            raise ValidationError("Password must contain at least one letter")
        
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must contain at least one number")
    
    @staticmethod
    def validate_full_name(full_name: str) -> str:
        """Validate full name"""
        if not full_name:
            raise ValidationError("Full name is required")
        
        full_name = full_name.strip()
        
        if len(full_name) < 2:
            raise ValidationError("Full name must be at least 2 characters")
        
        if len(full_name) > 100:
            raise ValidationError("Full name is too long (max 100 characters)")
        
        return full_name
    
    @staticmethod
    def validate_project_name(name: str) -> str:
        """Validate project name"""
        if not name:
            raise ValidationError("Project name is required")
        
        name = name.strip()
        
        if len(name) < Validators.MIN_PROJECT_NAME_LENGTH:
            raise ValidationError("Project name cannot be empty")
        
        if len(name) > Validators.MAX_PROJECT_NAME_LENGTH:
            raise ValidationError(f"Project name is too long (max {Validators.MAX_PROJECT_NAME_LENGTH} characters)")
        
        return name
    
    @staticmethod
    def validate_description(description: Optional[str]) -> str:
        """Validate description"""
        if not description:
            return ""
        
        description = description.strip()
        
        if len(description) > Validators.MAX_DESCRIPTION_LENGTH:
            raise ValidationError(f"Description is too long (max {Validators.MAX_DESCRIPTION_LENGTH} characters)")
        
        return description
    
    @staticmethod
    def validate_title(title: str) -> str:
        """Validate test case title"""
        if not title:
            raise ValidationError("Title is required")
        
        title = title.strip()
        
        if len(title) < 3:
            raise ValidationError("Title must be at least 3 characters")
        
        if len(title) > Validators.MAX_TITLE_LENGTH:
            raise ValidationError(f"Title is too long (max {Validators.MAX_TITLE_LENGTH} characters)")
        
        return title
    
    @staticmethod
    def validate_priority(priority: str) -> str:
        """Validate priority value"""
        if not priority:
            raise ValidationError("Priority is required")
        
        priority = priority.strip().lower()
        
        if priority not in Validators.VALID_PRIORITIES:
            raise ValidationError(f"Invalid priority. Must be one of: {', '.join(Validators.VALID_PRIORITIES)}")
        
        return priority
    
    @staticmethod
    def validate_test_type(test_type: str) -> str:
        """Validate test type value"""
        if not test_type:
            raise ValidationError("Test type is required")
        
        test_type = test_type.strip().lower()
        
        if test_type not in Validators.VALID_TEST_TYPES:
            raise ValidationError(f"Invalid test type. Must be one of: {', '.join(Validators.VALID_TEST_TYPES)}")
        
        return test_type
    
    @staticmethod
    def validate_status(status: str) -> str:
        """Validate status value"""
        if not status:
            return "draft"
        
        status = status.strip().lower()
        
        if status not in Validators.VALID_STATUSES:
            raise ValidationError(f"Invalid status. Must be one of: {', '.join(Validators.VALID_STATUSES)}")
        
        return status
    
    @staticmethod
    def validate_role(role: str) -> str:
        """Validate role value"""
        if not role:
            raise ValidationError("Role is required")
        
        role = role.strip().lower()
        
        if role not in Validators.VALID_ROLES:
            raise ValidationError(f"Invalid role. Must be one of: {', '.join(Validators.VALID_ROLES)}")
        
        return role
    
    @staticmethod
    def validate_steps(steps: str) -> str:
        """Validate test steps"""
        if not steps:
            raise ValidationError("Test steps are required")
        
        steps = steps.strip()
        
        if len(steps) > Validators.MAX_STEPS_LENGTH:
            raise ValidationError(f"Steps are too long (max {Validators.MAX_STEPS_LENGTH} characters)")
        
        return steps
    
    @staticmethod
    def validate_expected_result(result: str) -> str:
        """Validate expected result"""
        if not result:
            raise ValidationError("Expected result is required")
        
        result = result.strip()
        
        if len(result) > Validators.MAX_RESULT_LENGTH:
            raise ValidationError(f"Expected result is too long (max {Validators.MAX_RESULT_LENGTH} characters)")
        
        return result
    
    @staticmethod
    def validate_actual_result(result: Optional[str]) -> str:
        """Validate actual result"""
        if not result:
            return ""
        
        result = result.strip()
        
        if len(result) > Validators.MAX_RESULT_LENGTH:
            raise ValidationError(f"Actual result is too long (max {Validators.MAX_RESULT_LENGTH} characters)")
        
        return result
    
    @staticmethod
    def validate_comment(comment: str) -> str:
        """Validate comment text"""
        if not comment:
            raise ValidationError("Comment cannot be empty")
        
        comment = comment.strip()
        
        if len(comment) > Validators.MAX_COMMENT_LENGTH:
            raise ValidationError(f"Comment is too long (max {Validators.MAX_COMMENT_LENGTH} characters)")
        
        return comment
    
    @staticmethod
    def validate_tab_name(tab_name: str) -> str:
        """Validate tab/section name"""
        if not tab_name:
            raise ValidationError("Tab name is required")
        
        tab_name = tab_name.strip()
        
        if len(tab_name) < 1:
            raise ValidationError("Tab name cannot be empty")
        
        if len(tab_name) > 50:
            raise ValidationError("Tab name is too long (max 50 characters)")
        
        # Prevent special characters that might cause issues
        if re.search(r'[<>:"/\\|?*]', tab_name):
            raise ValidationError("Tab name contains invalid characters")
        
        return tab_name
    
    @staticmethod
    def validate_file_size(file_size: int) -> None:
        """Validate file size"""
        if file_size > Validators.MAX_FILE_SIZE:
            max_mb = Validators.MAX_FILE_SIZE / (1024 * 1024)
            raise ValidationError(f"File is too large. Maximum size is {max_mb}MB")
    
    @staticmethod
    def sanitize_search_query(query: str) -> str:
        """Sanitize search query to prevent injection"""
        if not query:
            return ""
        
        # Remove potential injection characters
        query = query.strip()
        
        # Limit length
        if len(query) > 200:
            query = query[:200]
        
        # Remove special regex characters that could cause issues
        query = re.sub(r'[<>{}[\]\\]', '', query)
        
        return query


def validate_http_exception(func):
    """Decorator to convert ValidationError to HTTPException"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return wrapper
