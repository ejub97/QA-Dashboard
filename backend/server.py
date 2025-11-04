from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import io
from docx import Document
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
import pandas as pd
import json
from auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_token,
    oauth2_scheme
)
from email_service import (
    generate_reset_token,
    get_token_expiry,
    send_password_reset_email
)
from database import get_db_pool, init_database, close_db_pool

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

app = FastAPI()
api_router = APIRouter(prefix="/api")

# ============ MODELS ============

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: EmailStr
    hashed_password: str
    role: str = "editor"  # editor or viewer
    created_at: datetime = Field(default_factory=lambda: CURRENT_TIMESTAMP)
    reset_token: Optional[str] = None
    reset_token_expires: Optional[datetime] = None

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = ""
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: CURRENT_TIMESTAMP)
    updated_at: datetime = Field(default_factory=lambda: CURRENT_TIMESTAMP)
    tabs: List[str] = ["General"]

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""

class TestCase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    tab_section: str = "General"
    title: str
    description: str
    priority: str
    type: str
    steps: str
    expected_result: str
    actual_result: Optional[str] = ""
    status: str = "draft"
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: CURRENT_TIMESTAMP)
    updated_at: datetime = Field(default_factory=lambda: CURRENT_TIMESTAMP)

class TestCaseCreate(BaseModel):
    project_id: str
    tab_section: Optional[str] = "General"
    title: str
    description: str
    priority: str
    type: str
    steps: str
    expected_result: str
    actual_result: Optional[str] = ""

class TestCaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    type: Optional[str] = None
    steps: Optional[str] = None
    expected_result: Optional[str] = None
    actual_result: Optional[str] = None
    status: Optional[str] = None
    tab_section: Optional[str] = None

class UpdateTabRequest(BaseModel):
    old_name: str
    new_name: str

class DeleteTabRequest(BaseModel):
    tab_name: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class UpdateUserRoleRequest(BaseModel):
    user_id: str
    new_role: str

class Statistics(BaseModel):
    total_projects: int
    total_test_cases: int
    draft_count: int
    success_count: int
    fail_count: int

# ============ STARTUP & SHUTDOWN ============

@app.on_event("startup")
async def startup_event():
    await init_database()
    print("✅ Application started with PostgreSQL")

@app.on_event("shutdown")
async def shutdown_event():
    await close_db_pool()
    print("👋 Application shutdown")

# ============ HELPER FUNCTIONS ============

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            user_data = await conn.fetchrow(
                'SELECT * FROM users WHERE id = $1',
                user_id
            )
            
            if not user_data:
                raise HTTPException(status_code=401, detail="User not found")
            
            return dict(user_data)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============ AUTHENTICATION ENDPOINTS ============

@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Check if user exists
        existing = await conn.fetchrow(
            'SELECT id FROM users WHERE email = $1 OR username = $2',
            user_data.email, user_data.username
        )
        
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Create new user
        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash(user_data.password)
        
        await conn.execute(
            '''INSERT INTO users (id, username, email, hashed_password, role)
               VALUES ($1, $2, $3, $4, $5)''',
            user_id, user_data.username, user_data.email, hashed_password, "editor"
        )
        
        # Create access token
        access_token = create_access_token(data={"sub": user_id})
        
        user_response = UserResponse(
            id=user_id,
            username=user_data.username,
            email=user_data.email,
            role="editor"
        )
        
        return Token(access_token=access_token, token_type="bearer", user=user_response)

@api_router.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        user_data = await conn.fetchrow(
            'SELECT * FROM users WHERE username = $1',
            form_data.username
        )
        
        if not user_data or not verify_password(form_data.password, user_data['hashed_password']):
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        
        access_token = create_access_token(data={"sub": user_data['id']})
        
        user_response = UserResponse(
            id=user_data['id'],
            username=user_data['username'],
            email=user_data['email'],
            role=user_data['role']
        )
        
        return Token(access_token=access_token, token_type="bearer", user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user['id'],
        username=current_user['username'],
        email=current_user['email'],
        role=current_user['role']
    )

@api_router.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            'SELECT * FROM users WHERE email = $1',
            request.email
        )
        
        # Always return success for security (don't reveal if email exists)
        if not user:
            return {"message": "If the email exists, a password reset link has been sent"}
        
        # Generate reset token
        reset_token = generate_reset_token()
        token_expiry = get_token_expiry()
        
        # Save token to database
        await conn.execute(
            'UPDATE users SET reset_token = $1, reset_token_expires = $2 WHERE id = $3',
            reset_token, token_expiry, user['id']
        )
        
        # Send email
        await send_password_reset_email(user['email'], reset_token, user['username'])
        
        return {"message": "If the email exists, a password reset link has been sent"}

@api_router.post("/auth/reset-password")
async def reset_password(request: ResetPasswordRequest):
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            'SELECT * FROM users WHERE reset_token = $1',
            request.token
        )
        
        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
        # Check if token is expired
        if user['reset_token_expires'] < CURRENT_TIMESTAMP:
            raise HTTPException(status_code=400, detail="Reset token has expired")
        
        # Update password and clear reset token
        new_hashed_password = get_password_hash(request.new_password)
        await conn.execute(
            'UPDATE users SET hashed_password = $1, reset_token = NULL, reset_token_expires = NULL WHERE id = $2',
            new_hashed_password, user['id']
        )
        
        return {"message": "Password reset successful"}

# ============ USER MANAGEMENT ENDPOINTS ============

@api_router.get("/users", response_model=List[UserResponse])
async def get_users(current_user: dict = Depends(get_current_user)):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        users = await conn.fetch('SELECT * FROM users ORDER BY created_at DESC')
        
        return [
            UserResponse(
                id=u['id'],
                username=u['username'],
                email=u['email'],
                role=u['role']
            )
            for u in users
        ]

@api_router.put("/users/role")
async def update_user_role(
    request: UpdateUserRoleRequest,
    current_user: dict = Depends(get_current_user)
):
    if request.new_role not in ["editor", "viewer"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            'UPDATE users SET role = $1 WHERE id = $2',
            request.new_role, request.user_id
        )
        
        return {"message": "User role updated successfully"}

@api_router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    if user_id == current_user['id']:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        result = await conn.execute('DELETE FROM users WHERE id = $1', user_id)
        
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "User deleted successfully"}

# ============ PROJECT ENDPOINTS ============

@api_router.get("/projects", response_model=List[Project])
async def get_projects(current_user: dict = Depends(get_current_user)):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        projects = await conn.fetch(
            'SELECT * FROM projects ORDER BY created_at DESC'
        )
        
        return [
            Project(
                id=p['id'],
                name=p['name'],
                description=p['description'] or "",
                created_by=p['created_by'],
                created_at=p['created_at'],
                updated_at=p['updated_at'],
                tabs=json.loads(p['tabs']) if isinstance(p['tabs'], str) else p['tabs']
            )
            for p in projects
        ]

@api_router.post("/projects", response_model=Project)
async def create_project(
    project_data: ProjectCreate,
    current_user: dict = Depends(get_current_user)
):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        project_id = str(uuid.uuid4())
        
        await conn.execute(
            '''INSERT INTO projects (id, name, description, created_by, tabs)
               VALUES ($1, $2, $3, $4, $5)''',
            project_id, project_data.name, project_data.description or "",
            current_user['id'], json.dumps(["General"])
        )
        
        # Fetch the created project to get the actual timestamps
        created_project = await conn.fetchrow('SELECT * FROM projects WHERE id = $1', project_id)
        
        return Project(
            id=project_id,
            name=project_data.name,
            description=project_data.description or "",
            created_by=current_user['id'],
            created_at=created_project['created_at'],
            updated_at=created_project['updated_at'],
            tabs=["General"]
        )

@api_router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        result = await conn.execute('DELETE FROM projects WHERE id = $1', project_id)
        
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {"message": "Project deleted successfully"}

@api_router.post("/projects/{project_id}/tabs")
async def add_tab_to_project(
    project_id: str,
    tab_name: str,
    current_user: dict = Depends(get_current_user)
):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        project = await conn.fetchrow('SELECT tabs FROM projects WHERE id = $1', project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        tabs = json.loads(project['tabs']) if isinstance(project['tabs'], str) else project['tabs']
        
        if tab_name in tabs:
            raise HTTPException(status_code=400, detail="Tab already exists")
        
        tabs.append(tab_name)
        
        await conn.execute(
            'UPDATE projects SET tabs = $1, updated_at = $2 WHERE id = $3',
            json.dumps(tabs), CURRENT_TIMESTAMP, project_id
        )
        
        return {"message": "Tab added successfully", "tabs": tabs}

@api_router.put("/projects/{project_id}/tabs")
async def rename_tab(
    project_id: str,
    request: UpdateTabRequest,
    current_user: dict = Depends(get_current_user)
):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        project = await conn.fetchrow('SELECT tabs FROM projects WHERE id = $1', project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        tabs = json.loads(project['tabs']) if isinstance(project['tabs'], str) else project['tabs']
        
        if request.old_name not in tabs:
            raise HTTPException(status_code=404, detail="Tab not found")
        
        if request.new_name in tabs:
            raise HTTPException(status_code=400, detail="New tab name already exists")
        
        # Update tab name in tabs list
        tabs = [request.new_name if t == request.old_name else t for t in tabs]
        
        # Update project tabs
        await conn.execute(
            'UPDATE projects SET tabs = $1, updated_at = $2 WHERE id = $3',
            json.dumps(tabs), CURRENT_TIMESTAMP, project_id
        )
        
        # Update test cases with this tab
        await conn.execute(
            'UPDATE test_cases SET tab_section = $1 WHERE project_id = $2 AND tab_section = $3',
            request.new_name, project_id, request.old_name
        )
        
        return {"message": "Tab renamed successfully", "tabs": tabs}

@api_router.delete("/projects/{project_id}/tabs")
async def delete_tab(
    project_id: str,
    request: DeleteTabRequest,
    current_user: dict = Depends(get_current_user)
):
    if request.tab_name == "General":
        raise HTTPException(status_code=400, detail="Cannot delete General tab")
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        project = await conn.fetchrow('SELECT tabs FROM projects WHERE id = $1', project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        tabs = json.loads(project['tabs']) if isinstance(project['tabs'], str) else project['tabs']
        
        if request.tab_name not in tabs:
            raise HTTPException(status_code=404, detail="Tab not found")
        
        # Remove tab from list
        tabs.remove(request.tab_name)
        
        # Update project
        await conn.execute(
            'UPDATE projects SET tabs = $1, updated_at = $2 WHERE id = $3',
            json.dumps(tabs), CURRENT_TIMESTAMP, project_id
        )
        
        # Delete test cases in this tab
        await conn.execute(
            'DELETE FROM test_cases WHERE project_id = $1 AND tab_section = $2',
            project_id, request.tab_name
        )
        
        return {"message": "Tab deleted successfully", "tabs": tabs}

# ============ TEST CASE ENDPOINTS ============

@api_router.get("/testcases/{project_id}", response_model=List[TestCase])
async def get_test_cases(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        test_cases = await conn.fetch(
            'SELECT * FROM test_cases WHERE project_id = $1 ORDER BY created_at DESC',
            project_id
        )
        
        return [
            TestCase(
                id=tc['id'],
                project_id=tc['project_id'],
                tab_section=tc['tab_section'],
                title=tc['title'],
                description=tc['description'],
                priority=tc['priority'],
                type=tc['type'],
                steps=tc['steps'],
                expected_result=tc['expected_result'],
                actual_result=tc['actual_result'] or "",
                status=tc['status'],
                created_by=tc['created_by'],
                created_at=tc['created_at'],
                updated_at=tc['updated_at']
            )
            for tc in test_cases
        ]

@api_router.post("/testcases", response_model=TestCase)
async def create_test_case(
    test_case_data: TestCaseCreate,
    current_user: dict = Depends(get_current_user)
):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        tc_id = str(uuid.uuid4())
        now = CURRENT_TIMESTAMP
        
        await conn.execute(
            '''INSERT INTO test_cases (
                id, project_id, tab_section, title, description, priority, type,
                steps, expected_result, actual_result, status, created_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)''',
            tc_id, test_case_data.project_id, test_case_data.tab_section or "General",
            test_case_data.title, test_case_data.description, test_case_data.priority,
            test_case_data.type, test_case_data.steps, test_case_data.expected_result,
            test_case_data.actual_result or "", "draft", current_user['id']
        )
        
        # Fetch the created test case to get the actual timestamps
        created_tc = await conn.fetchrow('SELECT * FROM test_cases WHERE id = $1', tc_id)
        
        return TestCase(
            id=tc_id,
            project_id=test_case_data.project_id,
            tab_section=test_case_data.tab_section or "General",
            title=test_case_data.title,
            description=test_case_data.description,
            priority=test_case_data.priority,
            type=test_case_data.type,
            steps=test_case_data.steps,
            expected_result=test_case_data.expected_result,
            actual_result=test_case_data.actual_result or "",
            status="draft",
            created_by=current_user['id'],
            created_at=created_tc['created_at'],
            updated_at=created_tc['updated_at']
        )

@api_router.put("/testcases/{test_case_id}", response_model=TestCase)
async def update_test_case(
    test_case_id: str,
    test_case_data: TestCaseUpdate,
    current_user: dict = Depends(get_current_user)
):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get existing test case
        existing = await conn.fetchrow(
            'SELECT * FROM test_cases WHERE id = $1',
            test_case_id
        )
        
        if not existing:
            raise HTTPException(status_code=404, detail="Test case not found")
        
        # Build update query dynamically
        update_fields = []
        values = []
        param_count = 1
        
        for field, value in test_case_data.dict(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = ${param_count}")
                values.append(value)
                param_count += 1
        
        if update_fields:
            update_fields.append(f"updated_at = ${param_count}")
            values.append(CURRENT_TIMESTAMP)
            values.append(test_case_id)
            
            query = f"UPDATE test_cases SET {', '.join(update_fields)} WHERE id = ${param_count + 1}"
            await conn.execute(query, *values)
        
        # Fetch updated test case
        updated = await conn.fetchrow('SELECT * FROM test_cases WHERE id = $1', test_case_id)
        
        return TestCase(
            id=updated['id'],
            project_id=updated['project_id'],
            tab_section=updated['tab_section'],
            title=updated['title'],
            description=updated['description'],
            priority=updated['priority'],
            type=updated['type'],
            steps=updated['steps'],
            expected_result=updated['expected_result'],
            actual_result=updated['actual_result'] or "",
            status=updated['status'],
            created_by=updated['created_by'],
            created_at=updated['created_at'],
            updated_at=updated['updated_at']
        )

@api_router.delete("/testcases/{test_case_id}")
async def delete_test_case(
    test_case_id: str,
    current_user: dict = Depends(get_current_user)
):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        result = await conn.execute('DELETE FROM test_cases WHERE id = $1', test_case_id)
        
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Test case not found")
        
        return {"message": "Test case deleted successfully"}

# ============ EXPORT ENDPOINTS ============

def format_steps(steps_text):
    """Format steps with numbers for export"""
    if not steps_text:
        return []
    
    lines = steps_text.split('\n')
    formatted_steps = []
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if line:
            if not line[0].isdigit():
                formatted_steps.append(f"{i}. {line}")
            else:
                formatted_steps.append(line)
    return formatted_steps

@api_router.get("/export/word/{project_id}")
async def export_to_word(project_id: str, current_user: dict = Depends(get_current_user)):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get project
        project = await conn.fetchrow('SELECT * FROM projects WHERE id = $1', project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get test cases
        test_cases = await conn.fetch(
            'SELECT * FROM test_cases WHERE project_id = $1 ORDER BY created_at',
            project_id
        )
        
        if not test_cases:
            raise HTTPException(status_code=404, detail="No test cases found")
        
        # Create Word document
        doc = Document()
        doc.add_heading(f"Test Cases - {project['name']}", 0)
        
        for idx, tc in enumerate(test_cases, 1):
            doc.add_heading(f"TC{idx:03d}: {tc['title']}", level=1)
            
            table = doc.add_table(rows=8, cols=2)
            table.style = 'Table Grid'
            
            table.rows[0].cells[0].text = "TC ID"
            table.rows[0].cells[1].text = f"TC{idx:03d}"
            
            table.rows[1].cells[0].text = "Title"
            table.rows[1].cells[1].text = tc['title']
            
            table.rows[2].cells[0].text = "Description"
            table.rows[2].cells[1].text = tc['description']
            
            table.rows[3].cells[0].text = "Priority"
            table.rows[3].cells[1].text = tc['priority']
            
            table.rows[4].cells[0].text = "Type"
            table.rows[4].cells[1].text = tc['type']
            
            table.rows[5].cells[0].text = "Steps"
            formatted_steps = format_steps(tc['steps'])
            table.rows[5].cells[1].text = '\n'.join(formatted_steps)
            
            table.rows[6].cells[0].text = "Expected Result"
            table.rows[6].cells[1].text = tc['expected_result']
            
            table.rows[7].cells[0].text = "Actual Result"
            table.rows[7].cells[1].text = tc['actual_result'] or ""
            
            doc.add_paragraph()
        
        # Save to bytes
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename=test_cases_{project['name']}.docx"}
        )

@api_router.get("/export/excel/{project_id}")
async def export_to_excel(project_id: str, current_user: dict = Depends(get_current_user)):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get project
        project = await conn.fetchrow('SELECT * FROM projects WHERE id = $1', project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        tabs = json.loads(project['tabs']) if isinstance(project['tabs'], str) else project['tabs']
        
        # Get test cases
        test_cases = await conn.fetch(
            'SELECT * FROM test_cases WHERE project_id = $1 ORDER BY created_at',
            project_id
        )
        
        if not test_cases:
            raise HTTPException(status_code=404, detail="No test cases found")
        
        # Create Excel workbook
        wb = Workbook()
        wb.remove(wb.active)
        
        # Group test cases by tab
        test_cases_by_tab = {}
        for tc in test_cases:
            tab = tc['tab_section'] or 'General'
            if tab not in test_cases_by_tab:
                test_cases_by_tab[tab] = []
            test_cases_by_tab[tab].append(tc)
        
        # Create a sheet for each tab
        tc_counter = 1
        for tab_name in tabs:
            if tab_name not in test_cases_by_tab:
                continue
            
            ws = wb.create_sheet(title=tab_name[:31])
            
            # Header row
            headers = ["TC ID", "Title", "Description", "Priority", "Type", "Steps", 
                      "Expected Result", "Actual Result", "Status"]
            ws.append(headers)
            
            # Style header
            for cell in ws[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")
            
            # Data rows
            for tc in test_cases_by_tab[tab_name]:
                formatted_steps = '\n'.join(format_steps(tc['steps']))
                
                ws.append([
                    f"TC{tc_counter:03d}",
                    tc['title'],
                    tc['description'],
                    tc['priority'],
                    tc['type'],
                    formatted_steps,
                    tc['expected_result'],
                    tc['actual_result'] or "",
                    tc['status']
                ])
                tc_counter += 1
            
            # Auto-adjust column widths
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width
        
        # Save to bytes
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=test_cases_{project['name']}.xlsx"}
        )

# ============ STATISTICS ENDPOINT ============

@api_router.get("/statistics", response_model=Statistics)
async def get_statistics(current_user: dict = Depends(get_current_user)):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Get counts
        total_projects = await conn.fetchval('SELECT COUNT(*) FROM projects')
        total_test_cases = await conn.fetchval('SELECT COUNT(*) FROM test_cases')
        draft_count = await conn.fetchval("SELECT COUNT(*) FROM test_cases WHERE status = 'draft'")
        success_count = await conn.fetchval("SELECT COUNT(*) FROM test_cases WHERE status = 'success'")
        fail_count = await conn.fetchval("SELECT COUNT(*) FROM test_cases WHERE status = 'fail'")
        
        return Statistics(
            total_projects=total_projects or 0,
            total_test_cases=total_test_cases or 0,
            draft_count=draft_count or 0,
            success_count=success_count or 0,
            fail_count=fail_count or 0
        )

# ============ CORS & APP SETUP ============

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "QA Dashboard API with PostgreSQL - Running"}

@app.get("/health")
async def health_check():
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.fetchval('SELECT 1')
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
