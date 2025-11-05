import requests
import sys
import json
import re
from datetime import datetime
import uuid
import io
import tempfile
import os

class QADashboardImportTester:
    def __init__(self, base_url="https://testcenter.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.project_id = None
        self.other_project_id = None
        self.test_case_id = None
        self.access_token = None
        self.other_access_token = None
        # Use unique identifiers for this test session
        unique_id = str(uuid.uuid4())[:8]
        self.test_user_email = f"importtest{unique_id}@example.com"
        self.test_user_password = "ImportTest123"
        self.test_username = f"importtest{unique_id}"
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        default_headers = {'Content-Type': 'application/json'}
        
        if headers:
            default_headers.update(headers)
        
        # Add auth token if available
        if self.access_token:
            default_headers['Authorization'] = f'Bearer {self.access_token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=default_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=default_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=default_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                self.failed_tests.append(f"{name}: Expected {expected_status}, got {response.status_code}")
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            self.failed_tests.append(f"{name}: Exception - {str(e)}")
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    # Removed database connection test - focusing on rename/delete functionality

    def test_register_user(self):
        """Test user registration with full_name field"""
        user_data = {
            "username": self.test_username,
            "email": self.test_user_email,
            "password": self.test_user_password,
            "full_name": "Rename Test User"
        }
        success, response = self.run_test(
            "Register New User with full_name",
            "POST",
            "auth/register",
            200,
            data=user_data
        )
        if success and 'access_token' in response:
            self.access_token = response['access_token']
            print(f"   ✅ User registered with ID: {response.get('user', {}).get('id', 'N/A')}")
            print(f"   ✅ Full name: {response.get('user', {}).get('full_name', 'N/A')}")
            return True
        return False

    def create_csv_file(self, content, filename="test.csv"):
        """Create a temporary CSV file with given content"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.write(content)
        temp_file.close()
        return temp_file.name

    def create_txt_file(self, content, filename="test.txt"):
        """Create a temporary TXT file for testing invalid format"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_file.write(content)
        temp_file.close()
        return temp_file.name

    def cleanup_file(self, filepath):
        """Clean up temporary file"""
        try:
            os.unlink(filepath)
        except:
            pass

    def test_login_user(self):
        """Test user login with PostgreSQL"""
        login_data = {
            "username": self.test_username,
            "password": self.test_user_password
        }
        
        url = f"{self.api_url}/auth/login"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing User Login (PostgreSQL)...")
        print(f"   URL: {url}")
        
        try:
            response = requests.post(url, data=login_data, headers=headers)
            success = response.status_code == 200
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                response_data = response.json()
                if 'access_token' in response_data:
                    self.access_token = response_data['access_token']
                    print(f"   ✅ JWT token obtained from PostgreSQL")
                    print(f"   ✅ User role: {response_data.get('user', {}).get('role', 'N/A')}")
                return True
            else:
                self.failed_tests.append(f"Login: Expected 200, got {response.status_code}")
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False
        except Exception as e:
            self.failed_tests.append(f"Login: Exception - {str(e)}")
            print(f"❌ Failed - Error: {str(e)}")
            return False

    def test_get_current_user(self):
        """Test getting current user info from PostgreSQL"""
        success, response = self.run_test(
            "Get Current User (PostgreSQL)",
            "GET",
            "auth/me",
            200
        )
        if success and response.get('username') == self.test_username:
            print(f"   ✅ User data retrieved from PostgreSQL")
            print(f"   ✅ Username: {response.get('username')}")
            print(f"   ✅ Email: {response.get('email')}")
            print(f"   ✅ Role: {response.get('role')}")
            return True
        return False

    # Removed old password reset test methods - focusing on PostgreSQL migration testing

    def test_create_project(self):
        """Test project creation"""
        project_data = {
            "name": "Test Project",
            "description": "Test Description"
        }
        success, response = self.run_test(
            "Create Project",
            "POST",
            "projects",
            200,
            data=project_data
        )
        if success and 'id' in response:
            self.project_id = response['id']
            print(f"   ✅ Project created with ID: {self.project_id}")
            print(f"   ✅ Project name: {response.get('name')}")
            print(f"   ✅ Project description: {response.get('description')}")
            return True
        return False

    def test_create_other_project(self):
        """Test creating project with other user for permission testing"""
        # Switch to other user's token
        original_token = self.access_token
        self.access_token = self.other_access_token
        
        project_data = {
            "name": "Other User Project",
            "description": "Project owned by other user"
        }
        success, response = self.run_test(
            "Create Project with Other User",
            "POST",
            "projects",
            200,
            data=project_data
        )
        
        # Switch back to original token
        self.access_token = original_token
        
        if success and 'id' in response:
            self.other_project_id = response['id']
            print(f"   ✅ Other project created with ID: {self.other_project_id}")
            return True
        return False

    def test_project_rename_success(self):
        """Test project rename functionality (NEW FEATURE)"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
        
        # Test the new PUT /api/projects/{project_id} endpoint
        url = f"{self.api_url}/projects/{self.project_id}?name=Renamed%20Project&description=New%20Description"
        print(f"\n🔍 Testing Project Rename (NEW FEATURE)...")
        print(f"   URL: {url}")
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'} if self.access_token else {}
            response = requests.put(url, headers=headers)
            success = response.status_code == 200
            self.tests_run += 1
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   ✅ Response: {response_data}")
                    return True
                except:
                    print(f"   ✅ Project renamed successfully")
                    return True
            else:
                self.failed_tests.append(f"Project Rename: Expected 200, got {response.status_code}")
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False
        except Exception as e:
            self.failed_tests.append(f"Project Rename: Exception - {str(e)}")
            print(f"❌ Failed - Error: {str(e)}")
            self.tests_run += 1
            return False

    def test_verify_project_renamed(self):
        """Verify project name and description were updated"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
        
        success, response = self.run_test(
            "Verify Project Rename",
            "GET",
            f"projects/{self.project_id}",
            200
        )
        if success:
            expected_name = "Renamed Project"
            expected_desc = "New Description"
            actual_name = response.get('name', '')
            actual_desc = response.get('description', '')
            
            if actual_name == expected_name and actual_desc == expected_desc:
                print(f"   ✅ Project name updated to: {actual_name}")
                print(f"   ✅ Project description updated to: {actual_desc}")
                return True
            else:
                print(f"   ❌ Name mismatch - Expected: '{expected_name}', Got: '{actual_name}'")
                print(f"   ❌ Description mismatch - Expected: '{expected_desc}', Got: '{actual_desc}'")
                return False
        return False

    def test_permission_rename_other_project(self):
        """Test trying to rename a project you don't own (should fail with 403)"""
        if not self.other_project_id:
            print("❌ Skipping - No other project ID available")
            return False
        
        # Try to rename other user's project with current user's token
        url = f"{self.api_url}/projects/{self.other_project_id}?name=Hacked%20Project&description=Should%20not%20work"
        print(f"\n🔍 Testing Permission Denied for Rename...")
        print(f"   URL: {url}")
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'} if self.access_token else {}
            response = requests.put(url, headers=headers)
            success = response.status_code == 403  # Expecting 403 Forbidden
            self.tests_run += 1
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code} (Correctly forbidden)")
                try:
                    response_data = response.json()
                    print(f"   ✅ Error message: {response_data.get('detail', 'N/A')}")
                except:
                    pass
                return True
            else:
                self.failed_tests.append(f"Permission Test Rename: Expected 403, got {response.status_code}")
                print(f"❌ Failed - Expected 403, got {response.status_code}")
                print(f"   ❌ Security issue: User can rename projects they don't own!")
                return False
        except Exception as e:
            self.failed_tests.append(f"Permission Test Rename: Exception - {str(e)}")
            print(f"❌ Failed - Error: {str(e)}")
            self.tests_run += 1
            return False

    def test_permission_delete_other_project(self):
        """Test trying to delete a project you don't own (should fail with 403)"""
        if not self.other_project_id:
            print("❌ Skipping - No other project ID available")
            return False
        
        # Try to delete other user's project with current user's token
        success, response = self.run_test(
            "Permission Test - Delete Other Project",
            "DELETE",
            f"projects/{self.other_project_id}",
            403  # Expecting 403 Forbidden
        )
        if success:
            print(f"   ✅ Correctly forbidden - cannot delete other user's project")
            return True
        return False

    def test_project_delete(self):
        """Test project deletion"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
        
        success, response = self.run_test(
            "Delete Project",
            "DELETE",
            f"projects/{self.project_id}",
            200
        )
        if success:
            print(f"   ✅ Project deleted successfully")
            return True
        return False

    def test_verify_project_deleted(self):
        """Verify project is actually deleted"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
        
        success, response = self.run_test(
            "Verify Project Deleted",
            "GET",
            f"projects/{self.project_id}",
            404  # Expecting 404 Not Found
        )
        if success:
            print(f"   ✅ Project correctly not found after deletion")
            return True
        return False

    def test_get_projects(self):
        """Test getting all projects (verify no breaking changes)"""
        success, response = self.run_test(
            "List Projects (No Breaking Changes)",
            "GET",
            "projects",
            200
        )
        if success and isinstance(response, list):
            print(f"   ✅ Retrieved {len(response)} projects")
            print(f"   ✅ GET /api/projects endpoint still working")
            return True
        return False

    # Removed old methods - focusing on rename/delete functionality

    def test_create_test_case(self):
        """Test test case creation (verify no breaking changes)"""
        # Create a new project first since we deleted the previous one
        project_data = {
            "name": "Test Case Project",
            "description": "For testing test case creation"
        }
        success, response = self.run_test(
            "Create Project for Test Case",
            "POST",
            "projects",
            200,
            data=project_data
        )
        if success and 'id' in response:
            self.project_id = response['id']
            print(f"   ✅ New project created with ID: {self.project_id}")
        else:
            return False
        
        test_case_data = {
            "project_id": self.project_id,
            "tab": "General",
            "title": "Test Case Creation Test",
            "description": "Testing test case creation after rename functionality",
            "priority": "high",
            "type": "functional",
            "steps": "1. Create test case\n2. Verify data persistence\n3. Check functionality",
            "expected_result": "Test case should be created successfully",
            "actual_result": ""
        }
        success, response = self.run_test(
            "Create Test Case (No Breaking Changes)",
            "POST",
            "test-cases",
            200,
            data=test_case_data
        )
        if success and 'id' in response:
            self.test_case_id = response['id']
            print(f"   ✅ Test case created with ID: {self.test_case_id}")
            print(f"   ✅ Status: {response.get('status', 'N/A')}")
            print(f"   ✅ Tab: {response.get('tab', 'N/A')}")
            return True
        return False

    # Removed old test case methods - using PostgreSQL-specific tests

    def test_import_valid_csv(self):
        """Test importing valid CSV file"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
        
        # Create valid CSV content
        csv_content = """Title,Description,Priority,Type,Steps,Expected Result,Actual Result,Tab
Test Login,Login functionality test,high,functional,"1. Open login page
2. Enter valid credentials
3. Click login button",User should be logged in successfully,,Authentication
Test Logout,Logout functionality test,medium,functional,"1. Click logout button
2. Verify redirect",User should be logged out,,Authentication
Invalid Login,Test invalid credentials,high,negative,"1. Enter invalid credentials
2. Click login",Should show error message,,Authentication"""
        
        csv_file = self.create_csv_file(csv_content)
        
        try:
            url = f"{self.api_url}/test-cases/import/{self.project_id}"
            headers = {'Authorization': f'Bearer {self.access_token}'} if self.access_token else {}
            
            self.tests_run += 1
            print(f"\n🔍 Testing Valid CSV Import...")
            print(f"   URL: {url}")
            
            with open(csv_file, 'rb') as f:
                files = {'file': ('test_cases.csv', f, 'text/csv')}
                response = requests.post(url, files=files, headers=headers)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                response_data = response.json()
                imported_count = response_data.get('imported_count', 0)
                print(f"   ✅ Imported {imported_count} test cases")
                if imported_count >= 3:
                    print(f"   ✅ All test cases imported successfully")
                    return True
                else:
                    print(f"   ❌ Expected at least 3 imports, got {imported_count}")
                    return False
            else:
                self.failed_tests.append(f"Valid CSV Import: Expected 200, got {response.status_code}")
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False
        except Exception as e:
            self.failed_tests.append(f"Valid CSV Import: Exception - {str(e)}")
            print(f"❌ Failed - Error: {str(e)}")
            return False
        finally:
            self.cleanup_file(csv_file)

    def test_import_invalid_file_format(self):
        """Test importing invalid file format (TXT)"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
        
        # Create TXT file (invalid format)
        txt_content = "This is a text file, not CSV or Excel"
        txt_file = self.create_txt_file(txt_content)
        
        try:
            url = f"{self.api_url}/test-cases/import/{self.project_id}"
            headers = {'Authorization': f'Bearer {self.access_token}'} if self.access_token else {}
            
            self.tests_run += 1
            print(f"\n🔍 Testing Invalid File Format (TXT)...")
            print(f"   URL: {url}")
            
            with open(txt_file, 'rb') as f:
                files = {'file': ('test_cases.txt', f, 'text/plain')}
                response = requests.post(url, files=files, headers=headers)
            
            success = response.status_code == 400
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                response_data = response.json()
                error_detail = response_data.get('detail', '')
                if 'Unsupported file format' in error_detail:
                    print(f"   ✅ Correct error message: {error_detail}")
                    return True
                else:
                    print(f"   ❌ Unexpected error message: {error_detail}")
                    return False
            else:
                self.failed_tests.append(f"Invalid File Format: Expected 400, got {response.status_code}")
                print(f"❌ Failed - Expected 400, got {response.status_code}")
                return False
        except Exception as e:
            self.failed_tests.append(f"Invalid File Format: Exception - {str(e)}")
            print(f"❌ Failed - Error: {str(e)}")
            return False
        finally:
            self.cleanup_file(txt_file)

    def test_import_missing_columns(self):
        """Test importing CSV with missing required columns"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
        
        # Create CSV with missing required column (no "Title" column)
        csv_content = """Description,Priority,Type,Steps,Expected Result
Login test,high,functional,Enter credentials,Should login"""
        
        csv_file = self.create_csv_file(csv_content)
        
        try:
            url = f"{self.api_url}/test-cases/import/{self.project_id}"
            headers = {'Authorization': f'Bearer {self.access_token}'} if self.access_token else {}
            
            self.tests_run += 1
            print(f"\n🔍 Testing Missing Required Columns...")
            print(f"   URL: {url}")
            
            with open(csv_file, 'rb') as f:
                files = {'file': ('missing_columns.csv', f, 'text/csv')}
                response = requests.post(url, files=files, headers=headers)
            
            success = response.status_code == 400
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                response_data = response.json()
                error_detail = response_data.get('detail', '')
                if 'Missing columns' in error_detail or 'Required CSV/Excel Format' in error_detail:
                    print(f"   ✅ Correct error with format guide provided")
                    return True
                else:
                    print(f"   ❌ Unexpected error message: {error_detail}")
                    return False
            else:
                self.failed_tests.append(f"Missing Columns: Expected 400, got {response.status_code}")
                print(f"❌ Failed - Expected 400, got {response.status_code}")
                return False
        except Exception as e:
            self.failed_tests.append(f"Missing Columns: Exception - {str(e)}")
            print(f"❌ Failed - Error: {str(e)}")
            return False
        finally:
            self.cleanup_file(csv_file)

    def test_import_invalid_data(self):
        """Test importing CSV with invalid data values"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
        
        # Create CSV with invalid priority and type values
        csv_content = """Title,Description,Priority,Type,Steps,Expected Result,Actual Result,Tab
Valid Test,Valid test case,high,functional,Test steps,Expected result,,General
Invalid Priority,Test with invalid priority,super-high,functional,Test steps,Expected result,,General
Invalid Type,Test with invalid type,medium,invalid-type,Test steps,Expected result,,General"""
        
        csv_file = self.create_csv_file(csv_content)
        
        try:
            url = f"{self.api_url}/test-cases/import/{self.project_id}"
            headers = {'Authorization': f'Bearer {self.access_token}'} if self.access_token else {}
            
            self.tests_run += 1
            print(f"\n🔍 Testing Invalid Data Values...")
            print(f"   URL: {url}")
            
            with open(csv_file, 'rb') as f:
                files = {'file': ('invalid_data.csv', f, 'text/csv')}
                response = requests.post(url, files=files, headers=headers)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                response_data = response.json()
                imported_count = response_data.get('imported_count', 0)
                errors = response_data.get('errors', [])
                
                if imported_count >= 1 and len(errors) >= 2:
                    print(f"   ✅ Imported {imported_count} valid test case(s)")
                    print(f"   ✅ Reported {len(errors)} validation errors")
                    for error in errors[:2]:  # Show first 2 errors
                        print(f"   ✅ Error: {error}")
                    return True
                else:
                    print(f"   ❌ Expected 1+ imports and 2+ errors, got {imported_count} imports and {len(errors)} errors")
                    return False
            else:
                self.failed_tests.append(f"Invalid Data: Expected 200, got {response.status_code}")
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                return False
        except Exception as e:
            self.failed_tests.append(f"Invalid Data: Exception - {str(e)}")
            print(f"❌ Failed - Error: {str(e)}")
            return False
        finally:
            self.cleanup_file(csv_file)

    def test_import_empty_file(self):
        """Test importing empty CSV file"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
        
        # Create empty CSV file
        csv_content = ""
        csv_file = self.create_csv_file(csv_content)
        
        try:
            url = f"{self.api_url}/test-cases/import/{self.project_id}"
            headers = {'Authorization': f'Bearer {self.access_token}'} if self.access_token else {}
            
            self.tests_run += 1
            print(f"\n🔍 Testing Empty File...")
            print(f"   URL: {url}")
            
            with open(csv_file, 'rb') as f:
                files = {'file': ('empty.csv', f, 'text/csv')}
                response = requests.post(url, files=files, headers=headers)
            
            success = response.status_code == 400
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                response_data = response.json()
                error_detail = response_data.get('detail', '')
                if 'empty' in error_detail.lower():
                    print(f"   ✅ Correct error message: {error_detail}")
                    return True
                else:
                    print(f"   ❌ Unexpected error message: {error_detail}")
                    return False
            else:
                self.failed_tests.append(f"Empty File: Expected 400, got {response.status_code}")
                print(f"❌ Failed - Expected 400, got {response.status_code}")
                return False
        except Exception as e:
            self.failed_tests.append(f"Empty File: Exception - {str(e)}")
            print(f"❌ Failed - Error: {str(e)}")
            return False
        finally:
            self.cleanup_file(csv_file)

    def test_verify_imported_data(self):
        """Verify imported test cases exist in the database"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
        
        success, response = self.run_test(
            "Verify Imported Test Cases",
            "GET",
            f"test-cases?project_id={self.project_id}",
            200
        )
        if success and isinstance(response, list):
            imported_cases = [tc for tc in response if 'Login' in tc.get('title', '')]
            print(f"   ✅ Retrieved {len(response)} total test cases")
            print(f"   ✅ Found {len(imported_cases)} imported test cases")
            
            if imported_cases:
                # Check specific imported test case
                login_test = next((tc for tc in imported_cases if 'Test Login' in tc.get('title', '')), None)
                if login_test:
                    print(f"   ✅ Login test case found:")
                    print(f"      - Title: {login_test.get('title')}")
                    print(f"      - Priority: {login_test.get('priority')}")
                    print(f"      - Type: {login_test.get('type')}")
                    print(f"      - Tab: {login_test.get('tab')}")
                    return True
            
            print(f"   ❌ No imported test cases found")
            return False
        return False

    # Removed old methods - focusing on rename/delete functionality testing

def main():
    print("🚀 Starting QA Dashboard Project Rename/Delete Functionality Tests")
    print("=" * 80)
    
    tester = QADashboardProjectRenameTester()
    
    # Run comprehensive project rename/delete tests
    test_results = []
    
    print("\n🔄 === PROJECT RENAME/DELETE FUNCTIONALITY TESTING ===")
    
    # User setup tests
    print("\n👤 Step 1: User Setup")
    test_results.append(tester.test_register_user())
    test_results.append(tester.test_login_user())
    test_results.append(tester.test_get_current_user())
    test_results.append(tester.test_register_other_user())
    
    # Project creation tests
    print("\n📁 Step 2: Project Creation")
    test_results.append(tester.test_create_project())
    test_results.append(tester.test_create_other_project())
    
    # NEW FEATURE: Project rename tests
    print("\n🔄 Step 3: Project Rename (NEW FEATURE)")
    test_results.append(tester.test_project_rename_success())
    test_results.append(tester.test_verify_project_renamed())
    
    # Permission tests
    print("\n🔒 Step 4: Permission Tests")
    test_results.append(tester.test_permission_rename_other_project())
    test_results.append(tester.test_permission_delete_other_project())
    
    # Project delete tests
    print("\n🗑️ Step 5: Project Delete")
    test_results.append(tester.test_project_delete())
    test_results.append(tester.test_verify_project_deleted())
    
    # Verify no breaking changes
    print("\n✅ Step 6: Verify No Breaking Changes")
    test_results.append(tester.test_get_projects())
    test_results.append(tester.test_create_test_case())
    test_results.append(tester.test_get_test_cases_by_project())
    
    # Print final results
    print("\n" + "=" * 80)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    # Show failed tests if any
    if tester.failed_tests:
        print(f"\n❌ Failed Tests ({len(tester.failed_tests)}):")
        for failed_test in tester.failed_tests:
            print(f"   - {failed_test}")
    
    # Test results summary
    if tester.tests_passed == tester.tests_run:
        print("\n🎉 Project Rename/Delete Functionality Tests Successful!")
        print("✅ NEW FEATURE: Project rename working correctly!")
        print("✅ Project delete functionality working!")
        print("✅ Permission system working (403 for unauthorized actions)!")
        print("✅ No breaking changes detected in existing endpoints!")
        print("✅ User registration with full_name field working!")
        return 0
    else:
        print(f"\n❌ Project Rename/Delete Functionality Issues Detected!")
        print(f"❌ {tester.tests_run - tester.tests_passed} tests failed!")
        print("🔍 Check the detailed output above for specific failures.")
        print("🔧 New functionality may need fixes.")
        return 1

if __name__ == "__main__":
    sys.exit(main())