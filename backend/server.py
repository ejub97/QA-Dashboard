from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import io
import csv
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import secrets
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = ""
    invite_code: str = Field(default_factory=lambda: secrets.token_urlsafe(8))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""

class TestCase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    tab: str = "General"  # Tab/Section name
    title: str
    description: str
    priority: str  # low, medium, high
    type: str  # functional, negative, ui/ux, smoke, regression, api
    steps: str
    expected_result: str
    actual_result: Optional[str] = ""
    status: str = "draft"  # draft, success, fail
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TestCaseCreate(BaseModel):
    project_id: str
    tab: Optional[str] = "General"
    title: str
    description: str
    priority: str
    type: str
    steps: str
    expected_result: str
    actual_result: Optional[str] = ""

class TestCaseUpdate(BaseModel):
    tab: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    type: Optional[str] = None
    steps: Optional[str] = None
    expected_result: Optional[str] = None
    actual_result: Optional[str] = None
    status: Optional[str] = None

class StatusUpdate(BaseModel):
    status: str


# Project Routes
@api_router.post("/projects", response_model=Project)
async def create_project(input: ProjectCreate):
    project_dict = input.model_dump()
    project_obj = Project(**project_dict)
    
    doc = project_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.projects.insert_one(doc)
    return project_obj

@api_router.get("/projects", response_model=List[Project])
async def get_projects():
    projects = await db.projects.find({}, {"_id": 0}).to_list(1000)
    
    for project in projects:
        if isinstance(project['created_at'], str):
            project['created_at'] = datetime.fromisoformat(project['created_at'])
    
    return projects

@api_router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if isinstance(project['created_at'], str):
        project['created_at'] = datetime.fromisoformat(project['created_at'])
    
    return project

@api_router.get("/projects/invite/{invite_code}", response_model=Project)
async def get_project_by_invite(invite_code: str):
    project = await db.projects.find_one({"invite_code": invite_code}, {"_id": 0})
    
    if not project:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    
    if isinstance(project['created_at'], str):
        project['created_at'] = datetime.fromisoformat(project['created_at'])
    
    return project

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    # Delete all test cases for this project first
    await db.test_cases.delete_many({"project_id": project_id})
    
    # Delete the project
    result = await db.projects.delete_one({"id": project_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"message": "Project and associated test cases deleted successfully"}

@api_router.get("/projects/{project_id}/tabs")
async def get_project_tabs(project_id: str):
    """Get unique tabs for a project"""
    test_cases = await db.test_cases.find({"project_id": project_id}, {"_id": 0, "tab": 1}).to_list(1000)
    tabs = list(set([tc.get('tab', 'General') for tc in test_cases]))
    if not tabs:
        tabs = ["General"]
    return {"tabs": sorted(tabs)}


# Test Case Routes
@api_router.post("/test-cases", response_model=TestCase)
async def create_test_case(input: TestCaseCreate):
    # Verify project exists
    project = await db.projects.find_one({"id": input.project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    test_case_dict = input.model_dump()
    test_case_obj = TestCase(**test_case_dict)
    
    doc = test_case_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    await db.test_cases.insert_one(doc)
    return test_case_obj

@api_router.get("/test-cases", response_model=List[TestCase])
async def get_test_cases(project_id: Optional[str] = None, tab: Optional[str] = None):
    query = {}
    if project_id:
        query["project_id"] = project_id
    if tab:
        query["tab"] = tab
    
    test_cases = await db.test_cases.find(query, {"_id": 0}).to_list(1000)
    
    for tc in test_cases:
        if isinstance(tc['created_at'], str):
            tc['created_at'] = datetime.fromisoformat(tc['created_at'])
        if isinstance(tc['updated_at'], str):
            tc['updated_at'] = datetime.fromisoformat(tc['updated_at'])
    
    return test_cases

@api_router.get("/test-cases/{test_case_id}", response_model=TestCase)
async def get_test_case(test_case_id: str):
    test_case = await db.test_cases.find_one({"id": test_case_id}, {"_id": 0})
    
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    if isinstance(test_case['created_at'], str):
        test_case['created_at'] = datetime.fromisoformat(test_case['created_at'])
    if isinstance(test_case['updated_at'], str):
        test_case['updated_at'] = datetime.fromisoformat(test_case['updated_at'])
    
    return test_case

@api_router.put("/test-cases/{test_case_id}", response_model=TestCase)
async def update_test_case(test_case_id: str, input: TestCaseUpdate):
    test_case = await db.test_cases.find_one({"id": test_case_id}, {"_id": 0})
    
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.test_cases.update_one(
        {"id": test_case_id},
        {"$set": update_data}
    )
    
    updated_test_case = await db.test_cases.find_one({"id": test_case_id}, {"_id": 0})
    
    if isinstance(updated_test_case['created_at'], str):
        updated_test_case['created_at'] = datetime.fromisoformat(updated_test_case['created_at'])
    if isinstance(updated_test_case['updated_at'], str):
        updated_test_case['updated_at'] = datetime.fromisoformat(updated_test_case['updated_at'])
    
    return updated_test_case

@api_router.patch("/test-cases/{test_case_id}/status", response_model=TestCase)
async def update_test_case_status(test_case_id: str, input: StatusUpdate):
    test_case = await db.test_cases.find_one({"id": test_case_id}, {"_id": 0})
    
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    await db.test_cases.update_one(
        {"id": test_case_id},
        {"$set": {"status": input.status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    updated_test_case = await db.test_cases.find_one({"id": test_case_id}, {"_id": 0})
    
    if isinstance(updated_test_case['created_at'], str):
        updated_test_case['created_at'] = datetime.fromisoformat(updated_test_case['created_at'])
    if isinstance(updated_test_case['updated_at'], str):
        updated_test_case['updated_at'] = datetime.fromisoformat(updated_test_case['updated_at'])
    
    return updated_test_case

@api_router.delete("/test-cases/{test_case_id}")
async def delete_test_case(test_case_id: str):
    result = await db.test_cases.delete_one({"id": test_case_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    return {"message": "Test case deleted successfully"}


# Export Routes
@api_router.get("/test-cases/export/csv/{project_id}")
async def export_csv(project_id: str):
    # Get project
    project = await db.projects.find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get test cases sorted by tab and created_at
    test_cases = await db.test_cases.find({"project_id": project_id}, {"_id": 0}).to_list(1000)
    test_cases.sort(key=lambda x: (x.get('tab', 'General'), x.get('created_at', '')))
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['TC ID', 'Tab', 'Title', 'Description', 'Priority', 'Type', 'Steps', 'Expected Result', 'Actual Result', 'Status'])
    
    # Write data with TC ID
    for idx, tc in enumerate(test_cases, start=1):
        tc_id = f"TC{str(idx).zfill(3)}"
        writer.writerow([
            tc_id,
            tc.get('tab', 'General'),
            tc.get('title', ''),
            tc.get('description', ''),
            tc.get('priority', ''),
            tc.get('type', ''),
            tc.get('steps', ''),
            tc.get('expected_result', ''),
            tc.get('actual_result', ''),
            tc.get('status', '')
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={project['name']}_test_cases.csv"}
    )

@api_router.get("/test-cases/export/excel/{project_id}")
async def export_excel(project_id: str):
    # Get project
    project = await db.projects.find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get test cases
    test_cases = await db.test_cases.find({"project_id": project_id}, {"_id": 0}).to_list(1000)
    
    # Group test cases by tab
    tabs_dict = {}
    for tc in test_cases:
        tab = tc.get('tab', 'General')
        if tab not in tabs_dict:
            tabs_dict[tab] = []
        tabs_dict[tab].append(tc)
    
    # Sort test cases within each tab by created_at
    for tab in tabs_dict:
        tabs_dict[tab].sort(key=lambda x: x.get('created_at', ''))
    
    # Create Excel workbook
    wb = Workbook()
    wb.remove(wb.active)  # Remove default sheet
    
    # Define header style
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    # Define data cell alignment with wrap text
    data_alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
    
    # Create a sheet for each tab
    global_counter = 1
    for tab_name in sorted(tabs_dict.keys()):
        # Sanitize sheet name (Excel has limitations)
        safe_sheet_name = tab_name[:31].replace('/', '-').replace('\\', '-').replace('*', '').replace('?', '').replace('[', '').replace(']', '')
        ws = wb.create_sheet(title=safe_sheet_name)
        
        # Write headers
        headers = ['TC ID', 'Title', 'Description', 'Priority', 'Type', 'Steps', 'Expected Result', 'Actual Result', 'Status']
        ws.append(headers)
        
        # Style header row
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
        
        # Write data
        for tc in tabs_dict[tab_name]:
            tc_id = f"TC{str(global_counter).zfill(3)}"
            global_counter += 1
            
            # Format steps to ensure each step is on a new line
            steps = tc.get('steps', '')
            
            row_data = [
                tc_id,
                tc.get('title', ''),
                tc.get('description', ''),
                tc.get('priority', ''),
                tc.get('type', ''),
                steps,
                tc.get('expected_result', ''),
                tc.get('actual_result', ''),
                tc.get('status', '')
            ]
            ws.append(row_data)
            
            # Apply wrap text and alignment to data cells
            current_row = ws.max_row
            for cell in ws[current_row]:
                cell.alignment = data_alignment
        
        # Set row heights to auto
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
            ws.row_dimensions[row[0].row].height = None  # Auto height
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 10
        ws.column_dimensions['B'].width = 25
        ws.column_dimensions['C'].width = 30
        ws.column_dimensions['D'].width = 12
        ws.column_dimensions['E'].width = 15
        ws.column_dimensions['F'].width = 35
        ws.column_dimensions['G'].width = 35
        ws.column_dimensions['H'].width = 35
        ws.column_dimensions['I'].width = 12
    
    # If no test cases, create a default sheet
    if not tabs_dict:
        ws = wb.create_sheet(title="General")
        headers = ['TC ID', 'Title', 'Description', 'Priority', 'Type', 'Steps', 'Expected Result', 'Actual Result', 'Status']
        ws.append(headers)
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
    
    # Save to memory
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={project['name']}_test_cases.xlsx"}
    )

@api_router.get("/test-cases/export/docx/{project_id}")
async def export_docx(project_id: str):
    # Get project
    project = await db.projects.find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get test cases sorted by tab
    test_cases = await db.test_cases.find({"project_id": project_id}, {"_id": 0}).to_list(1000)
    test_cases.sort(key=lambda x: (x.get('tab', 'General'), x.get('created_at', '')))
    
    # Create Word document
    doc = Document()
    
    # Add title
    title = doc.add_heading(f"{project['name']} - Test Cases", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Add table
    table = doc.add_table(rows=1, cols=9)
    table.style = 'Light Grid Accent 1'
    
    # Header row
    hdr_cells = table.rows[0].cells
    headers = ['TC ID', 'Tab', 'Title', 'Description', 'Priority', 'Type', 'Steps', 'Expected Result', 'Actual Result']
    for i, header in enumerate(headers):
        hdr_cells[i].text = header
        for paragraph in hdr_cells[i].paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
    
    # Data rows
    for idx, tc in enumerate(test_cases, start=1):
        tc_id = f"TC{str(idx).zfill(3)}"
        row_cells = table.add_row().cells
        row_cells[0].text = tc_id
        row_cells[1].text = tc.get('tab', 'General')
        row_cells[2].text = tc.get('title', '')
        row_cells[3].text = tc.get('description', '')
        row_cells[4].text = tc.get('priority', '')
        row_cells[5].text = tc.get('type', '')
        
        # Format steps to ensure each step is on a new line
        steps = tc.get('steps', '')
        row_cells[6].text = steps
        
        row_cells[7].text = tc.get('expected_result', '')
        row_cells[8].text = tc.get('actual_result', '')
    
    # Save to memory
    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={project['name']}_test_cases.docx"}
    )


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()