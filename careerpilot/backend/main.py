# FastAPI Backend

import base64
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import traceback

load_dotenv()

app = FastAPI(title="CareerPilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JobInput(BaseModel):
    job_title: str
    company: str
    job_description: str
    resume_text: str
    notes: str = ""


class EmailRequest(BaseModel):
    email: str
    subject: str
    body: str
    attachments: list = []


# Gmail OAuth2 setup
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
REDIRECT_URI = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8000/auth/callback")
CLIENT_SECRETS_FILE = os.getenv("GMAIL_CLIENT_SECRETS", "client_secret.json")
CREDENTIALS_FILE = Path(__file__).parent.parent / "gmail_credentials.json"


def get_google_auth_url():
    """Generate the Google OAuth2 authorization URL"""
    from google_auth_oauthlib.flow import InstalledAppFlow

    secrets_path = get_secrets_path()
    print(f"[Gmail Debug] Loading secrets from: {secrets_path}")
    flow = InstalledAppFlow.from_client_secrets_file(
        str(secrets_path),
        scopes=SCOPES
    )
    flow.redirect_uri = REDIRECT_URI
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    return auth_url


def save_credentials(code):
    """Exchange authorization code for credentials and save to disk"""
    from google_auth_oauthlib.flow import InstalledAppFlow

    secrets_path = get_secrets_path()
    flow = InstalledAppFlow.from_client_secrets_file(
        str(secrets_path),
        scopes=SCOPES
    )
    flow.redirect_uri = REDIRECT_URI
    flow.fetch_token(code=code)
    credentials = flow.credentials
    save_credentials_to_file(credentials)
    return credentials


def save_credentials_to_file(credentials):
    """Persist credentials to a JSON file"""
    import google.oauth2.credentials
    creds_data = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes,
        'expiry': credentials.expiry.isoformat() if credentials.expiry else None
    }
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump(creds_data, f)
    print(f"[Gmail Debug] Credentials saved to {CREDENTIALS_FILE}")


def load_credentials_from_file():
    """Load credentials from disk if they exist"""
    import google.oauth2.credentials
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    if not CREDENTIALS_FILE.exists():
        return None

    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            creds_data = json.load(f)

        credentials = Credentials(
            token=creds_data.get('token'),
            refresh_token=creds_data.get('refresh_token'),
            token_uri=creds_data.get('token_uri'),
            client_id=creds_data.get('client_id'),
            client_secret=creds_data.get('client_secret'),
            scopes=creds_data.get('scopes')
        )

        # Check if expired and refresh if needed
        if credentials.expired and credentials.refresh_token:
            print("[Gmail Debug] Token expired, refreshing...")
            credentials.refresh(Request())
            save_credentials_to_file(credentials)

        return credentials
    except Exception as e:
        print(f"[Gmail Debug] Error loading credentials: {e}")
        return None


def get_secrets_path():
    """Get the full path to client_secret.json"""
    return Path(__file__).parent.parent / CLIENT_SECRETS_FILE


def is_gmail_configured():
    """Check if Gmail OAuth2 is configured"""
    secrets_path = get_secrets_path()
    exists = secrets_path.exists()
    print(f"[Gmail Debug] Checking config at: {secrets_path}, exists: {exists}")
    return exists


def is_gmail_authorized():
    """Check if we have valid stored credentials"""
    creds = load_credentials_from_file()
    if creds is None:
        return False
    if creds.expired and creds.refresh_token:
        try:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            save_credentials_to_file(creds)
            return True
        except Exception:
            return False
    return not creds.expired


def send_gmail(to: str, subject: str, body: str, attachments: list = None) -> dict:
    """Send email via Gmail API using OAuth2"""
    creds = load_credentials_from_file()
    if not creds:
        return {"status": "error", "message": "Gmail not authorized. Please connect your Gmail account first."}

    try:
        from googleapiclient.discovery import build
        service = build('gmail', 'v1', credentials=creds)

        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        message.attach(MIMEText(body, 'plain'))

        for attachment in attachments or []:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.encode())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename=output.pdf')
            message.attach(part)

        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        body = {'raw': raw_message}

        # Send the message
        message = service.users().messages().send(userId='me', body=body).execute()
        return {"status": "success", "message": f"Email sent to {to}", "message_id": message['id']}

    except Exception as e:
        stored_credentials.pop('gmail', None)
        return {"status": "error", "message": str(e)}


@app.get("/")
def home():
    return {"message": "CareerPilot API", "status": "running"}


@app.get("/gmail/status")
def gmail_status():
    """Check Gmail OAuth2 status"""
    secrets_path = get_secrets_path()
    debug_info = {
        "secrets_path": str(secrets_path),
        "file_location": __file__,
        "parent_parent": str(Path(__file__).parent.parent)
    }
    if not secrets_path.exists():
        return {
            "configured": False,
            "authorized": False,
            "message": f"client_secret.json not found at {secrets_path}. Please download from Google Cloud Console.",
            "debug": debug_info
        }
    return {
        "configured": True,
        "authorized": is_gmail_authorized(),
        "message": "Connected" if is_gmail_authorized() else "Not connected. Click authorize to connect.",
        "debug": debug_info
    }


@app.get("/gmail/authorize")
def gmail_authorize():
    """Redirect user to Google OAuth2 consent page"""
    secrets_path = get_secrets_path()
    if not secrets_path.exists():
        raise HTTPException(status_code=500, detail=f"Gmail not configured. client_secret.json not found at {secrets_path}")

    try:
        auth_url = get_google_auth_url()
        return RedirectResponse(url=auth_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gmail authorization error: {str(e)}")


@app.get("/auth/callback")
def auth_callback(code: str = Query(...)):
    """Handle OAuth2 callback and save credentials"""
    try:
        save_credentials(code)
        return HTMLResponse(content="<html><body><h1>Gmail Connected!</h1><p>You can close this window and return to CareerPilot.</p></body></html>")
    except Exception as e:
        return HTMLResponse(content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>", status_code=500)


@app.post("/generate")
def generate_content(data: JobInput):
    try:
        if not data.job_description.strip() and not data.resume_text.strip():
            raise HTTPException(status_code=400, detail="Please provide either job description or resume text")

        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured in .env file")

        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))

        from backend.tasks.executor import execute_pipeline

        input_data = {
            "job_title": data.job_title,
            "company": data.company,
            "job_description": data.job_description,
            "resume_text": data.resume_text,
            "notes": data.notes
        }

        crew_result = execute_pipeline(input_data)

        if crew_result.get("status") == "error":
            raise HTTPException(status_code=500, detail=crew_result.get("error", "Pipeline error"))

        outputs = crew_result.get("outputs", {})

        # If outputs are empty but status is completed, try to get raw_result
        if not outputs:
            raw = crew_result.get("raw_result", "")
            if raw:
                outputs = {"raw_output": raw}
            else:
                raise HTTPException(status_code=500, detail="No outputs generated from pipeline")

        return {"status": "success", "outputs": outputs}

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/send-email")
def send_email(request: EmailRequest):
    """Send email via Gmail OAuth2"""
    secrets_path = get_secrets_path()
    if not secrets_path.exists():
        return {"status": "error", "message": f"Gmail not configured. Please download client_secret.json from Google Cloud Console and place it in the careerpilot directory."}

    if not is_gmail_authorized():
        return {"status": "error", "message": "Gmail not authorized. Please click 'Connect Gmail' button to authorize."}

    result = send_gmail(
        to=request.email,
        subject=request.subject,
        body=request.body,
        attachments=request.attachments
    )
    return result


@app.post("/generate-pdf")
def generate_pdf(data: dict):
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable, ListFlowable, ListItem
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        import io

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch, leftMargin=0.75*inch, rightMargin=0.75*inch)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1F2937'), spaceAfter=8, fontName='Helvetica-Bold', alignment=1)
        header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#4F46E5'), spaceAfter=6, fontName='Helvetica-Bold')
        section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=13, textColor=colors.HexColor('#1F2937'), spaceBefore=12, spaceAfter=6, fontName='Helvetica-Bold')
        subsection_style = ParagraphStyle('Subsection', parent=styles['Heading3'], fontSize=11, textColor=colors.HexColor('#374151'), spaceBefore=8, spaceAfter=4, fontName='Helvetica-Bold')
        body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=4)
        bullet_style = ParagraphStyle('Bullet', parent=styles['Normal'], fontSize=10, leading=14, leftIndent=20, spaceAfter=2)

        def parse_content(content):
            """Parse content with **bold** markers and bullet points"""
            lines = content.split('\n')
            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.startswith('─') or stripped.startswith('━'):
                    continue

                # Check if line starts with bullet
                if stripped.startswith('•'):
                    bullet_text = stripped[1:].strip()
                    # Parse bold markers in bullet
                    parts = bullet_text.split('**')
                    for i, part in enumerate(parts):
                        if i % 2 == 1:  # Bold part
                            story.append(Paragraph(part, subsection_style))
                        elif part.strip():
                            story.append(Paragraph(part, bullet_style))
                    continue

                # Parse bold markers
                parts = stripped.split('**')
                if len(parts) > 1:  # Has bold markers
                    for i, part in enumerate(parts):
                        if i % 2 == 1:  # Bold part
                            story.append(Paragraph(part, header_style))
                        elif part.strip():
                            story.append(Paragraph(part, body_style))
                else:
                    story.append(Paragraph(stripped, body_style))

        for section_name, content in data.get("sections", {}).items():
            # Section title
            story.append(Paragraph(section_name.upper(), title_style))
            story.append(Spacer(1, 0.15*inch))
            story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#4F46E5'), spaceAfter=0.2*inch))

            parse_content(content)
            story.append(Spacer(1, 0.3*inch))
            story.append(PageBreak())

        doc.build(story)
        buffer.seek(0)

        import base64
        return {"status": "success", "pdf": base64.b64encode(buffer.read()).decode('utf-8')}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))