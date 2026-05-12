import smtplib
import os
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load env variables
load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
DEFAULT_SENDER = os.getenv("DEFAULT_SENDER", f"Smart Gate Admin <{SMTP_USER}>")

def send_visitor_notification(recipient_email, visitor_name, address, vehicle_no, purpose, time_str):
    """Sends an email notification in a background thread."""
    if not SMTP_USER or not SMTP_PASS:
        print("[Email] SMTP credentials not set. Skipping notification.")
        return

    def _send():
        try:
            msg = MIMEMultipart()
            msg['From'] = DEFAULT_SENDER
            msg['To'] = recipient_email
            msg['Subject'] = f"Visitor Alert: {visitor_name} is here to meet you"

            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
                    <div style="background-color: #0d9488; color: white; padding: 20px; text-align: center;">
                        <h2 style="margin: 0;">Smart Gate Notification</h2>
                    </div>
                    <div style="padding: 20px;">
                        <p>Hello,</p>
                        <p>This is an automated alert from the Smart Gate system. A visitor has just registered to meet you.</p>
                        
                        <div style="background-color: #f9fafb; padding: 15px; border-radius: 6px; margin: 20px 0;">
                            <p style="margin: 5px 0;"><strong>Visitor Name:</strong> {visitor_name}</p>
                            <p style="margin: 5px 0;"><strong>Address:</strong> {address}</p>
                            <p style="margin: 5px 0;"><strong>Vehicle No:</strong> {vehicle_no}</p>
                            <p style="margin: 5px 0;"><strong>Purpose:</strong> {purpose}</p>
                            <p style="margin: 5px 0;"><strong>Time:</strong> {time_str}</p>
                        </div>
                        
                        <p>Please take necessary actions at the gate if required.</p>
                        <p>Regards,<br>Security Team</p>
                    </div>
                    <div style="background-color: #f3f4f6; color: #666; padding: 10px; text-align: center; font-size: 12px;">
                        This is an automated system message. Please do not reply.
                    </div>
                </div>
            </body>
            </html>
            """
            msg.attach(MIMEText(body, 'html'))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
            print(f"[Email] Notification sent to {recipient_email}")
        except Exception as e:
            print(f"[Email] Failed to send email: {str(e)}")

    # Run in background
    thread = threading.Thread(target=_send)
    thread.start()
