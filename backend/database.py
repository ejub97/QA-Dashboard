"""
PostgreSQL database connection and schema setup
"""
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

DATABASE_URL = os.environ['DATABASE_URL']

# Global connection pool
pool = None

async def get_db_pool():
    """Get or create database connection pool"""
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(
            DATABASE_URL, 
            min_size=2, 
            max_size=10,
            command_timeout=60,
            server_settings={
                'application_name': 'qa_dashboard',
                'jit': 'off'
            }
        )
    return pool

async def close_db_pool():
    """Close database connection pool"""
    global pool
    if pool is not None:
        await pool.close()
        pool = None

async def init_database():
    """Initialize database schema"""
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        # Create users table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(255) PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'editor',
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                reset_token VARCHAR(255),
                reset_token_expires TIMESTAMPTZ
            )
        ''')
        
        # Create projects table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                created_by VARCHAR(255) REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                tabs JSONB DEFAULT '["General"]'::jsonb
            )
        ''')
        
        # Create test_cases table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS test_cases (
                id VARCHAR(255) PRIMARY KEY,
                project_id VARCHAR(255) REFERENCES projects(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                priority VARCHAR(50) DEFAULT 'medium',
                type VARCHAR(50) DEFAULT 'functional',
                steps TEXT,
                expected_result TEXT,
                actual_result TEXT,
                status VARCHAR(50) DEFAULT 'draft',
                tab_section VARCHAR(255) DEFAULT 'General',
                created_by VARCHAR(255) REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indices for better performance
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_test_cases_project_id 
            ON test_cases(project_id)
        ''')
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_test_cases_tab_section 
            ON test_cases(tab_section)
        ''')
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_users_email 
            ON users(email)
        ''')
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_users_reset_token 
            ON users(reset_token)
        ''')
        
        print("✅ Database schema initialized successfully")
