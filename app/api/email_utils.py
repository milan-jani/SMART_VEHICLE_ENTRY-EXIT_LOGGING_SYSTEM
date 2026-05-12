import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load env
if os.path.exists(".env"):
    load_dotenv(".env")

# Email Config
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
DEFAULT_SENDER = os.getenv("DEFAULT_SENDER", SMTP_USER)

def send_visitor_notification(faculty_email, faculty_name, visitor_name, vehicle_no, purpose, address="-"):
    """Sends an email notification to the faculty member."""
    if not SMTP_USER or not SMTP_PASS or not faculty_email:
        print(f"[WARN] Email not sent: Config missing or no faculty email for {faculty_name}")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = DEFAULT_SENDER
        msg['To'] = faculty_email
        msg['Subject'] = f"Visitor Arrival: {visitor_name} to meet you"

        body = f"""
        Dear {faculty_name},

        A visitor has just arrived at the main gate and is coming to meet you.
        
        Details:
        - Visitor Name: {visitor_name}
        - Address: {address}
        - Vehicle No: {vehicle_no}
        - Purpose: {purpose}
        - Check-in Time: {os.popen('date /t').read().strip() if os.name == 'nt' else os.popen('date').read().strip()}

        This is an automated message from the Smart Gate System.

        Regards,
        Security Administration
        """
        
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        
        print(f"[SUCCESS] Notification email sent to {faculty_email}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False
