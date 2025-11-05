import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email configuration from environment
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "noreply@qadashboard.com")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://testcenter.preview.emergentagent.com")

def generate_reset_token():
    """Generate a secure random token for password reset"""
    return secrets.token_urlsafe(32)

def get_token_expiry():
    """Get token expiry time (1 hour from now)"""
    return datetime.now(timezone.utc) + timedelta(hours=1)

async def send_password_reset_email(email: str, reset_token: str, username: str):
    """Send password reset email"""
    reset_link = f"{FRONTEND_URL}/reset-password/{reset_token}"
    
    # For development/testing without SMTP, just log the link
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"""
        ═══════════════════════════════════════════════════════════
        📧 PASSWORD RESET EMAIL (Development Mode)
        ═══════════════════════════════════════════════════════════
        To: {email}
        Username: {username}
        
        Reset Link: {reset_link}
        
        ⚠️  This link expires in 1 hour
        ═══════════════════════════════════════════════════════════
        
        💡 To enable actual email sending, set these environment variables:
           - SMTP_HOST (default: smtp.gmail.com)
           - SMTP_PORT (default: 587)
           - SMTP_USER (your email)
           - SMTP_PASSWORD (your email password or app password)
           - FROM_EMAIL (sender email)
        ═══════════════════════════════════════════════════════════
        """)
        return True
    
    # Create email message
    message = MIMEMultipart("alternative")
    message["Subject"] = "Reset Your QA Dashboard Password"
    message["From"] = FROM_EMAIL
    message["To"] = email
    
    # HTML email body
    html_body = f"""
    <html>
      <head>
        <style>
          body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
          .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
          .header {{ background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
          .content {{ background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }}
          .button {{ display: inline-block; padding: 15px 30px; background: #222831; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }}
          .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>🔐 Password Reset Request</h1>
          </div>
          <div class="content">
            <p>Hi <strong>{username}</strong>,</p>
            <p>We received a request to reset your password for your QA Test Dashboard account.</p>
            <p>Click the button below to reset your password:</p>
            <p style="text-align: center;">
              <a href="{reset_link}" class="button">Reset Password</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; background: #fff; padding: 10px; border: 1px solid #e5e7eb; border-radius: 5px;">
              {reset_link}
            </p>
            <p><strong>⚠️ This link will expire in 1 hour.</strong></p>
            <p>If you didn't request this password reset, you can safely ignore this email. Your password will remain unchanged.</p>
          </div>
          <div class="footer">
            <p>QA Test Dashboard - Manage your test cases efficiently</p>
            <p>This is an automated email, please do not reply.</p>
          </div>
        </div>
      </body>
    </html>
    """
    
    # Plain text alternative
    text_body = f"""
    Password Reset Request
    
    Hi {username},
    
    We received a request to reset your password for your QA Test Dashboard account.
    
    Click the link below to reset your password:
    {reset_link}
    
    ⚠️  This link will expire in 1 hour.
    
    If you didn't request this password reset, you can safely ignore this email.
    
    ---
    QA Test Dashboard
    """
    
    part1 = MIMEText(text_body, "plain")
    part2 = MIMEText(html_body, "html")
    
    message.attach(part1)
    message.attach(part2)
    
    # Send email
    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            start_tls=True,
        )
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False



async def send_invite_email(email: str, invite_token: str, project_name: str, invited_by: str, role: str):
    """Send project invitation email"""
    invite_link = f"{FRONTEND_URL}/accept-invite/{invite_token}"
    
    # For development/testing without SMTP, just log the link
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"""
        ═══════════════════════════════════════════════════════════
        📧 PROJECT INVITE EMAIL (Development Mode)
        ═══════════════════════════════════════════════════════════
        To: {email}
        Project: {project_name}
        Role: {role}
        Invited by: {invited_by}
        
        Invite Link: {invite_link}
        
        ⚠️  This link expires in 1 hour
        ═══════════════════════════════════════════════════════════
        """)
        return True
    
    # Create email message
    message = MIMEMultipart("alternative")
    message["Subject"] = f"Invitation to join {project_name} on QA Dashboard"
    message["From"] = FROM_EMAIL
    message["To"] = email
    
    # HTML email body
    html_body = f"""
    <html>
      <head>
        <style>
          body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
          .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
          .header {{ background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
          .content {{ background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }}
          .button {{ display: inline-block; padding: 15px 30px; background: #222831; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }}
          .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
          .role-badge {{ display: inline-block; padding: 5px 15px; background: #3b82f6; color: white; border-radius: 20px; font-size: 14px; }}
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>🎉 You're Invited!</h1>
          </div>
          <div class="content">
            <p>Hi there,</p>
            <p><strong>{invited_by}</strong> has invited you to join the project <strong>{project_name}</strong> on QA Test Dashboard.</p>
            <p>Your role: <span class="role-badge">{role.upper()}</span></p>
            <p>Click the button below to accept the invitation:</p>
            <p style="text-align: center;">
              <a href="{invite_link}" class="button">Accept Invitation</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; background: #fff; padding: 10px; border: 1px solid #e5e7eb; border-radius: 5px;">
              {invite_link}
            </p>
            <p><strong>⚠️ This invitation will expire in 1 hour.</strong></p>
            <p>If you don't have an account yet, you'll need to register first before accepting the invitation.</p>
          </div>
          <div class="footer">
            <p>QA Test Dashboard - Collaborative Test Case Management</p>
            <p>This is an automated email, please do not reply.</p>
          </div>
        </div>
      </body>
    </html>
    """
    
    # Plain text alternative
    text_body = f"""
    You're Invited to Join {project_name}!
    
    Hi there,
    
    {invited_by} has invited you to join the project "{project_name}" on QA Test Dashboard.
    
    Your role: {role.upper()}
    
    Click the link below to accept the invitation:
    {invite_link}
    
    ⚠️  This invitation will expire in 1 hour.
    
    If you don't have an account yet, you'll need to register first.
    
    ---
    QA Test Dashboard
    """
    
    part1 = MIMEText(text_body, "plain")
    part2 = MIMEText(html_body, "html")
    
    message.attach(part1)
    message.attach(part2)
    
    # Send email
    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            start_tls=True,
        )
        return True
    except Exception as e:
        print(f"Failed to send invite email: {e}")
        return False
