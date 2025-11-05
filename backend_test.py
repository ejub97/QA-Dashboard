import requests
import sys
import json
import re
from datetime import datetime
import uuid

class QADashboardProjectRenameTester:
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
        self.test_user_email = f"renametest{unique_id}@example.com"
        self.test_user_password = "RenameTest123"
        self.test_username = f"renametest{unique_id}"
        self.other_user_email = f"otheruser{unique_id}@example.com"
        self.other_user_password = "OtherUser123"
        self.other_username = f"otheruser{unique_id}"
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

    def test_database_connection(self):
        """Test PostgreSQL database connection"""
        success, response = self.run_test(
            "Database Health Check",
            "GET",
            "../health",
            200
        )
        if success and response.get('database') == 'connected':
            print(f"   ✅ PostgreSQL connection verified")
            return True
        return False

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

    def test_register_other_user(self):
        """Test registering another user for permission testing"""
        user_data = {
            "username": self.other_username,
            "email": self.other_user_email,
            "password": self.other_user_password,
            "full_name": "Other Test User"
        }
        success, response = self.run_test(
            "Register Other User for Permission Test",
            "POST",
            "auth/register",
            200,
            data=user_data
        )
        if success and 'access_token' in response:
            self.other_access_token = response['access_token']
            print(f"   ✅ Other user registered with ID: {response.get('user', {}).get('id', 'N/A')}")
            return True
        return False

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

    def test_add_tab_to_project(self):
        """Test adding tab to project in PostgreSQL"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
        
        success, response = self.run_test(
            "Add Tab to Project (PostgreSQL)",
            "POST",
            f"projects/{self.project_id}/tabs?tab_name=TestTab",
            200
        )
        if success and response.get('message') == 'Tab added successfully':
            print(f"   ✅ Tab added successfully")
            print(f"   ✅ Updated tabs: {response.get('tabs', [])}")
            return True
        return False

    # Removed old project test methods - using PostgreSQL-specific tests

    def test_create_test_case(self):
        """Test test case creation in PostgreSQL"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
        
        test_case_data = {
            "project_id": self.project_id,
            "tab_section": "General",
            "title": "PostgreSQL Migration Test Case",
            "description": "Testing test case creation after PostgreSQL migration",
            "priority": "high",
            "type": "functional",
            "steps": "1. Create test case in PostgreSQL\n2. Verify data persistence\n3. Check UUID generation",
            "expected_result": "Test case should be created and stored in PostgreSQL with UUID",
            "actual_result": ""
        }
        success, response = self.run_test(
            "Create Test Case (PostgreSQL)",
            "POST",
            "testcases",
            200,
            data=test_case_data
        )
        if success and 'id' in response:
            self.test_case_id = response['id']
            print(f"   ✅ Test case created with ID: {self.test_case_id}")
            print(f"   ✅ Status: {response.get('status', 'N/A')}")
            print(f"   ✅ Tab section: {response.get('tab_section', 'N/A')}")
            return True
        return False

    # Removed old test case methods - using PostgreSQL-specific tests

    def test_get_test_cases_by_project(self):
        """Test getting test cases by project from PostgreSQL"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
        
        success, response = self.run_test(
            "Get Test Cases by Project (PostgreSQL)",
            "GET",
            f"testcases/{self.project_id}",
            200
        )
        if success and isinstance(response, list):
            print(f"   ✅ Retrieved {len(response)} test cases from PostgreSQL")
            # Check if our created test case is in the list
            if response:
                test_case = response[0]
                print(f"   ✅ Test case title: {test_case.get('title', 'N/A')}")
                print(f"   ✅ Test case status: {test_case.get('status', 'N/A')}")
            return True
        return False

    # Removed duplicate test case methods - using PostgreSQL-specific versions

    def test_update_test_case(self):
        """Test updating test case in PostgreSQL"""
        if not self.test_case_id:
            print("❌ Skipping - No test case ID available")
            return False
        
        update_data = {"status": "success"}
        success, response = self.run_test(
            "Update Test Case Status (PostgreSQL)",
            "PUT",
            f"testcases/{self.test_case_id}",
            200,
            data=update_data
        )
        if success and response.get('status') == 'success':
            print(f"   ✅ Test case status updated to: {response.get('status')}")
            return True
        return False

    # Removed old CSV export test - using Word/Excel exports for PostgreSQL

    def test_export_word(self):
        """Test Word export from PostgreSQL"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
        
        url = f"{self.api_url}/export/word/{self.project_id}"
        print(f"\n🔍 Testing Export Word (PostgreSQL)...")
        print(f"   URL: {url}")
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'} if self.access_token else {}
            response = requests.get(url, headers=headers)
            success = response.status_code == 200 and 'officedocument' in response.headers.get('content-type', '')
            self.tests_run += 1
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                print(f"   ✅ Content-Type: {response.headers.get('content-type')}")
                print(f"   ✅ File size: {len(response.content)} bytes")
                return True
            else:
                self.failed_tests.append(f"Word Export: Expected 200, got {response.status_code}")
                print(f"❌ Failed - Status: {response.status_code}")
                return False
        except Exception as e:
            self.failed_tests.append(f"Word Export: Exception - {str(e)}")
            print(f"❌ Failed - Error: {str(e)}")
            self.tests_run += 1
            return False

    def test_export_excel(self):
        """Test Excel export from PostgreSQL"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
        
        url = f"{self.api_url}/export/excel/{self.project_id}"
        print(f"\n🔍 Testing Export Excel (PostgreSQL)...")
        print(f"   URL: {url}")
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'} if self.access_token else {}
            response = requests.get(url, headers=headers)
            success = response.status_code == 200 and 'spreadsheet' in response.headers.get('content-type', '')
            self.tests_run += 1
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                print(f"   ✅ Content-Type: {response.headers.get('content-type')}")
                print(f"   ✅ File size: {len(response.content)} bytes")
                return True
            else:
                self.failed_tests.append(f"Excel Export: Expected 200, got {response.status_code}")
                print(f"❌ Failed - Status: {response.status_code}")
                return False
        except Exception as e:
            self.failed_tests.append(f"Excel Export: Exception - {str(e)}")
            print(f"❌ Failed - Error: {str(e)}")
            self.tests_run += 1
            return False

    def test_statistics(self):
        """Test statistics from PostgreSQL"""
        success, response = self.run_test(
            "Get Statistics (PostgreSQL)",
            "GET",
            "statistics",
            200
        )
        if success:
            print(f"   ✅ Total projects: {response.get('total_projects', 0)}")
            print(f"   ✅ Total test cases: {response.get('total_test_cases', 0)}")
            print(f"   ✅ Draft count: {response.get('draft_count', 0)}")
            print(f"   ✅ Success count: {response.get('success_count', 0)}")
            print(f"   ✅ Fail count: {response.get('fail_count', 0)}")
            return True
        return False

    def test_delete_test_case(self):
        """Test deleting test case from PostgreSQL"""
        if not self.test_case_id:
            print("❌ Skipping - No test case ID available")
            return False
        
        success, response = self.run_test(
            "Delete Test Case (PostgreSQL)",
            "DELETE",
            f"testcases/{self.test_case_id}",
            200
        )
        if success:
            print(f"   ✅ Test case deleted from PostgreSQL")
            return True
        return False

    # Removed old error handling tests - focusing on PostgreSQL migration verification

def main():
    print("🚀 Starting QA Dashboard PostgreSQL Migration Tests")
    print("=" * 70)
    
    tester = QADashboardPostgreSQLTester()
    
    # Run comprehensive PostgreSQL migration tests
    test_results = []
    
    print("\n🗄️ === POSTGRESQL MIGRATION VERIFICATION ===")
    
    # Database connection test
    print("\n📊 Step 1: Database Connection Test")
    test_results.append(tester.test_database_connection())
    
    # Authentication flow tests
    print("\n🔐 Step 2: Authentication Flow (PostgreSQL)")
    test_results.append(tester.test_register_user())
    test_results.append(tester.test_login_user())
    test_results.append(tester.test_get_current_user())
    
    # Project management tests
    print("\n📁 Step 3: Project Management (PostgreSQL)")
    test_results.append(tester.test_create_project())
    test_results.append(tester.test_get_projects())
    test_results.append(tester.test_add_tab_to_project())
    
    # Test case management tests
    print("\n📝 Step 4: Test Case Management (PostgreSQL)")
    test_results.append(tester.test_create_test_case())
    test_results.append(tester.test_get_test_cases_by_project())
    test_results.append(tester.test_update_test_case())
    
    # Export functionality tests
    print("\n📤 Step 5: Export Functionality (PostgreSQL)")
    test_results.append(tester.test_export_word())
    test_results.append(tester.test_export_excel())
    
    # Statistics test
    print("\n📈 Step 6: Statistics (PostgreSQL)")
    test_results.append(tester.test_statistics())
    
    # Cleanup test
    print("\n🗑️ Step 7: Cleanup (PostgreSQL)")
    test_results.append(tester.test_delete_test_case())
    
    # Print final results
    print("\n" + "=" * 70)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    # Show failed tests if any
    if tester.failed_tests:
        print(f"\n❌ Failed Tests ({len(tester.failed_tests)}):")
        for failed_test in tester.failed_tests:
            print(f"   - {failed_test}")
    
    # Migration status
    if tester.tests_passed == tester.tests_run:
        print("\n🎉 PostgreSQL Migration Successful!")
        print("✅ All QA Dashboard functionality working with PostgreSQL!")
        print("✅ Database schema created correctly")
        print("✅ All CRUD operations functional")
        print("✅ Authentication system working")
        print("✅ Export features operational")
        return 0
    else:
        print(f"\n❌ PostgreSQL Migration Issues Detected!")
        print(f"❌ {tester.tests_run - tester.tests_passed} tests failed!")
        print("🔍 Check the detailed output above for specific failures.")
        print("🔧 Migration may need additional fixes.")
        return 1

if __name__ == "__main__":
    sys.exit(main())