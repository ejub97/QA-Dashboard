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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
            '''INSERT INTO users (id, username, email, hashed_password, role, created_at)
               VALUES ($1, $2, $3, $4, $5, $6)''',
            user_id, user_data.username, user_data.email, hashed_password,
            "editor", datetime.now(timezone.utc)
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
        if user['reset_token_expires'] < datetime.now(timezone.utc):
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
        now = datetime.now(timezone.utc)
        
        await conn.execute(
            '''INSERT INTO projects (id, name, description, created_by, created_at, updated_at, tabs)
               VALUES ($1, $2, $3, $4, $5, $6, $7)''',
            project_id, project_data.name, project_data.description or "",
            current_user['id'], now, now, json.dumps(["General"])
        )
        
        return Project(
            id=project_id,
            name=project_data.name,
            description=project_data.description or "",
            created_by=current_user['id'],
            created_at=now,
            updated_at=now,
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
            json.dumps(tabs), datetime.now(timezone.utc), project_id
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
            json.dumps(tabs), datetime.now(timezone.utc), project_id
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
            json.dumps(tabs), datetime.now(timezone.utc), project_id
        )
        
        # Delete test cases in this tab
        await conn.execute(
            'DELETE FROM test_cases WHERE project_id = $1 AND tab_section = $2',
            project_id, request.tab_name
        )
        
        return {"message": "Tab deleted successfully", "tabs": tabs}

# ============ TEST CASE ENDPOINTS ============