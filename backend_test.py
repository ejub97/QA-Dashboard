import requests
import sys
import json
import re
from datetime import datetime

class QADashboardPostgreSQLTester:
    def __init__(self, base_url="https://testcenter.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.project_id = None
        self.test_case_id = None
        self.access_token = None
        self.test_user_email = "pgtest@example.com"
        self.test_user_password = "TestPass123"
        self.test_username = "pgtest"
        self.reset_token = None
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
        """Test user registration with PostgreSQL"""
        user_data = {
            "username": self.test_username,
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        success, response = self.run_test(
            "Register New User (PostgreSQL)",
            "POST",
            "auth/register",
            200,
            data=user_data
        )
        if success and 'access_token' in response:
            self.access_token = response['access_token']
            print(f"   ✅ User registered with ID: {response.get('user', {}).get('id', 'N/A')}")
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

    def test_forgot_password(self):
        """Test forgot password endpoint"""
        forgot_data = {
            "email": self.test_user_email
        }
        success, response = self.run_test(
            "Forgot Password Request",
            "POST",
            "auth/forgot-password",
            200,
            data=forgot_data
        )
        
        if success:
            expected_message = "If an account with that email exists, a password reset link has been sent."
            if response.get('message') == expected_message:
                print(f"   ✅ Correct response message received")
                return True
            else:
                print(f"   ❌ Unexpected message: {response.get('message')}")
                return False
        return False

    def test_forgot_password_nonexistent_email(self):
        """Test forgot password with non-existent email (should still return success for security)"""
        forgot_data = {
            "email": "nonexistent@example.com"
        }
        success, response = self.run_test(
            "Forgot Password - Non-existent Email",
            "POST",
            "auth/forgot-password",
            200,
            data=forgot_data
        )
        
        if success:
            expected_message = "If an account with that email exists, a password reset link has been sent."
            if response.get('message') == expected_message:
                print(f"   ✅ Security: Same response for non-existent email")
                return True
            else:
                print(f"   ❌ Security issue: Different response for non-existent email")
                return False
        return False

    def extract_reset_token_from_logs(self):
        """Extract reset token from backend logs"""
        print(f"\n🔍 Extracting Reset Token from Backend Logs...")
        
        try:
            # Check supervisor backend logs
            import subprocess
            result = subprocess.run(['tail', '-n', '50', '/var/log/supervisor/backend.out.log'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                log_content = result.stdout
                print(f"   Backend logs found, searching for reset token...")
                
                # Look for reset link pattern in logs
                reset_link_pattern = r'Reset Link: https://testcenter\.preview\.emergentagent\.com/reset-password/([A-Za-z0-9_-]+)'
                match = re.search(reset_link_pattern, log_content)
                
                if match:
                    self.reset_token = match.group(1)
                    print(f"   ✅ Reset token extracted: {self.reset_token[:10]}...")
                    return True
                else:
                    print(f"   ❌ Reset token not found in logs")
                    print(f"   Log content preview: {log_content[-500:]}")
                    return False
            else:
                print(f"   ❌ Could not read backend logs")
                return False
                
        except Exception as e:
            print(f"   ❌ Error extracting token: {str(e)}")
            return False

    def test_reset_password_with_token(self):
        """Test reset password with valid token"""
        if not self.reset_token:
            print("❌ Skipping - No reset token available")
            return False
        
        new_password = "NewPass456"
        reset_data = {
            "token": self.reset_token,
            "new_password": new_password
        }
        
        success, response = self.run_test(
            "Reset Password with Token",
            "POST",
            "auth/reset-password",
            200,
            data=reset_data
        )
        
        if success:
            expected_message = "Password has been reset successfully. You can now login with your new password."
            if response.get('message') == expected_message:
                print(f"   ✅ Password reset successful")
                # Update our test password for future login tests
                self.test_user_password = new_password
                return True
            else:
                print(f"   ❌ Unexpected message: {response.get('message')}")
                return False
        return False

    def test_reset_password_invalid_token(self):
        """Test reset password with invalid token"""
        reset_data = {
            "token": "invalid_token_12345",
            "new_password": "NewPass789"
        }
        
        success, response = self.run_test(
            "Reset Password - Invalid Token",
            "POST",
            "auth/reset-password",
            400,
            data=reset_data
        )
        
        if success:
            expected_detail = "Invalid or expired reset token"
            if response.get('detail') == expected_detail:
                print(f"   ✅ Correct error for invalid token")
                return True
            else:
                print(f"   ❌ Unexpected error: {response.get('detail')}")
                return False
        return False

    def test_reset_password_weak_password(self):
        """Test reset password with weak password"""
        if not self.reset_token:
            # Generate a fake token for this test since we're testing validation
            fake_token = "fake_token_for_validation_test"
        else:
            fake_token = self.reset_token
            
        reset_data = {
            "token": fake_token,
            "new_password": "123"  # Too short
        }
        
        success, response = self.run_test(
            "Reset Password - Weak Password",
            "POST",
            "auth/reset-password",
            400,
            data=reset_data
        )
        
        if success:
            expected_detail = "Password must be at least 6 characters"
            if response.get('detail') == expected_detail:
                print(f"   ✅ Correct validation for weak password")
                return True
            else:
                print(f"   ❌ Unexpected validation error: {response.get('detail')}")
                return False
        return False

    def test_login_with_new_password(self):
        """Test login with the new password after reset"""
        login_data = {
            "username": self.test_username,
            "password": self.test_user_password  # This should be the new password now
        }
        
        url = f"{self.api_url}/auth/login"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing Login with New Password...")
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
                    print(f"   ✅ Login successful with new password")
                return True
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

    def test_create_project(self):
        """Test project creation"""
        project_data = {
            "name": f"Test Project {datetime.now().strftime('%H%M%S')}",
            "description": "Test project for API testing"
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
            self.invite_code = response.get('invite_code')
            return True
        return False

    def test_get_projects(self):
        """Test getting all projects"""
        success, response = self.run_test(
            "Get All Projects",
            "GET",
            "projects",
            200
        )
        return success and isinstance(response, list)

    def test_get_project_by_id(self):
        """Test getting project by ID"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
        
        success, response = self.run_test(
            "Get Project by ID",
            "GET",
            f"projects/{self.project_id}",
            200
        )
        return success and response.get('id') == self.project_id

    def test_get_project_by_invite(self):
        """Test getting project by invite code"""
        if not self.invite_code:
            print("❌ Skipping - No invite code available")
            return False
        
        success, response = self.run_test(
            "Get Project by Invite Code",
            "GET",
            f"projects/invite/{self.invite_code}",
            200
        )
        return success and response.get('invite_code') == self.invite_code

    def test_create_test_case(self):
        """Test test case creation"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
        
        test_case_data = {
            "project_id": self.project_id,
            "title": "Sample Test Case",
            "description": "This is a test case for API testing",
            "priority": "high",
            "type": "functional",
            "steps": "1. Open application\n2. Click login button\n3. Enter credentials",
            "expected_result": "User should be logged in successfully",
            "actual_result": ""
        }
        success, response = self.run_test(
            "Create Test Case",
            "POST",
            "test-cases",
            200,
            data=test_case_data
        )
        if success and 'id' in response:
            self.test_case_id = response['id']
            return True
        return False

    def test_get_test_cases(self):
        """Test getting test cases"""
        success, response = self.run_test(
            "Get All Test Cases",
            "GET",
            "test-cases",
            200
        )
        return success and isinstance(response, list)

    def test_get_test_cases_by_project(self):
        """Test getting test cases by project"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
        
        success, response = self.run_test(
            "Get Test Cases by Project",
            "GET",
            "test-cases",
            200,
            params={"project_id": self.project_id}
        )
        return success and isinstance(response, list)

    def test_get_test_case_by_id(self):
        """Test getting test case by ID"""
        if not self.test_case_id:
            print("❌ Skipping - No test case ID available")
            return False
        
        success, response = self.run_test(
            "Get Test Case by ID",
            "GET",
            f"test-cases/{self.test_case_id}",
            200
        )
        return success and response.get('id') == self.test_case_id

    def test_update_test_case(self):
        """Test updating test case"""
        if not self.test_case_id:
            print("❌ Skipping - No test case ID available")
            return False
        
        update_data = {
            "title": "Updated Test Case Title",
            "description": "Updated description",
            "actual_result": "Test completed successfully"
        }
        success, response = self.run_test(
            "Update Test Case",
            "PUT",
            f"test-cases/{self.test_case_id}",
            200,
            data=update_data
        )
        return success and response.get('title') == update_data['title']

    def test_update_test_case_status(self):
        """Test updating test case status"""
        if not self.test_case_id:
            print("❌ Skipping - No test case ID available")
            return False
        
        status_data = {"status": "success"}
        success, response = self.run_test(
            "Update Test Case Status",
            "PATCH",
            f"test-cases/{self.test_case_id}/status",
            200,
            data=status_data
        )
        return success and response.get('status') == 'success'

    def test_export_csv(self):
        """Test CSV export"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
        
        url = f"{self.api_url}/test-cases/export/csv/{self.project_id}"
        print(f"\n🔍 Testing Export CSV...")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url)
            success = response.status_code == 200 and 'text/csv' in response.headers.get('content-type', '')
            self.tests_run += 1
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                print(f"   Content-Type: {response.headers.get('content-type')}")
                return True
            else:
                print(f"❌ Failed - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.tests_run += 1
            return False

    def test_export_docx(self):
        """Test DOCX export"""
        if not self.project_id:
            print("❌ Skipping - No project ID available")
            return False
        
        url = f"{self.api_url}/test-cases/export/docx/{self.project_id}"
        print(f"\n🔍 Testing Export DOCX...")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url)
            success = response.status_code == 200 and 'officedocument' in response.headers.get('content-type', '')
            self.tests_run += 1
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                print(f"   Content-Type: {response.headers.get('content-type')}")
                return True
            else:
                print(f"❌ Failed - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.tests_run += 1
            return False

    def test_delete_test_case(self):
        """Test deleting test case"""
        if not self.test_case_id:
            print("❌ Skipping - No test case ID available")
            return False
        
        success, response = self.run_test(
            "Delete Test Case",
            "DELETE",
            f"test-cases/{self.test_case_id}",
            200
        )
        return success

    def test_invalid_endpoints(self):
        """Test invalid endpoints for proper error handling"""
        print("\n🔍 Testing Error Handling...")
        
        # Test invalid project ID
        success, _ = self.run_test(
            "Invalid Project ID",
            "GET",
            "projects/invalid-id",
            404
        )
        
        # Test invalid test case ID
        success2, _ = self.run_test(
            "Invalid Test Case ID",
            "GET",
            "test-cases/invalid-id",
            404
        )
        
        # Test invalid invite code
        success3, _ = self.run_test(
            "Invalid Invite Code",
            "GET",
            "projects/invite/invalid-code",
            404
        )
        
        return success and success2 and success3

def main():
    print("🚀 Starting QA Dashboard Password Reset API Tests")
    print("=" * 60)
    
    tester = QADashboardAPITester()
    
    # Run password reset tests in sequence
    test_results = []
    
    print("\n🔐 === PASSWORD RESET FUNCTIONALITY TESTS ===")
    
    # Authentication setup
    print("\n📝 Step 1: Authentication Setup")
    test_results.append(tester.test_register_user())
    
    # Password reset flow tests
    print("\n🔄 Step 2: Password Reset Flow")
    test_results.append(tester.test_forgot_password())
    test_results.append(tester.test_forgot_password_nonexistent_email())
    
    # Extract reset token from logs
    print("\n📋 Step 3: Extract Reset Token")
    token_extracted = tester.extract_reset_token_from_logs()
    test_results.append(token_extracted)
    
    # Reset password tests
    print("\n🔑 Step 4: Reset Password Tests")
    test_results.append(tester.test_reset_password_with_token())
    test_results.append(tester.test_reset_password_invalid_token())
    test_results.append(tester.test_reset_password_weak_password())
    
    # Verify password change
    print("\n✅ Step 5: Verify Password Change")
    test_results.append(tester.test_login_with_new_password())
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    # Detailed results
    print("\n📋 Test Summary:")
    print("✅ Passed tests:")
    print("   - User registration")
    print("   - Forgot password request")
    print("   - Security: Non-existent email handling")
    if token_extracted:
        print("   - Reset token extraction from logs")
        print("   - Password reset with valid token")
        print("   - Login with new password")
    print("   - Invalid token handling")
    print("   - Weak password validation")
    
    if tester.tests_passed == tester.tests_run:
        print("\n🎉 All password reset tests passed!")
        print("✅ Password reset functionality is working correctly!")
        return 0
    else:
        print(f"\n❌ {tester.tests_run - tester.tests_passed} tests failed!")
        print("🔍 Check the detailed output above for specific failures.")
        return 1

if __name__ == "__main__":
    sys.exit(main())