"""
notifier.py - Email notification service using Gmail SMTP
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import cv2
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailNotifier:
    """
    Sends email alerts via Gmail SMTP.
    """
    def __init__(self, sender_email, app_password, recipient_email):
        self.sender_email = sender_email
        self.app_password = app_password
        self.recipient_email = recipient_email
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def update_credentials(self, sender, app_password, recipient):
        self.sender_email = sender
        self.app_password = app_password
        self.recipient_email = recipient
        logger.info("Email credentials updated.")

    def send_alert(self, bay_name, vehicle_type, frame=None):
        """
        Sends an alert email for a detection incident, optionally with an image.
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            subject = f"⚠️ ALARMĂ AI Wash Guard: {bay_name}"
            
            body = f"""
            DETECȚIE VEHICUL INTERZIS
            -------------------------
            Zonă: {bay_name}
            Vehicul: {vehicle_type}
            Data/Ora: {timestamp}
            
            Sistemul a întrerupt alimentarea cu energie și a capturat imaginea atașată.
            """

            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            # Attach image if provided
            if frame is not None:
                try:
                    # Encode frame as jpg
                    ret, buffer = cv2.imencode('.jpg', frame)
                    if ret:
                        img_attachment = MIMEImage(buffer.tobytes(), name=f"detecție_{bay_name}.jpg")
                        msg.attach(img_attachment)
                except Exception as img_err:
                    logger.error(f"Eroare la procesarea imaginii pentru email: {img_err}")

            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=12)
            server.starttls()
            server.login(self.sender_email, self.app_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, self.recipient_email, text)
            server.quit()

            logger.info(f"Email de alertă trimis către {self.recipient_email} pentru {bay_name}.")
            return True
        except Exception as e:
            logger.error(f"Eroare la trimiterea email-ului: {e}")
            return False

    def test_connection(self):
        """Sends a test email to verify credentials and recipient."""
        try:
            subject = "🛡️ Test Conexiune AI Wash Guard"
            body = "Acesta este un email de test pentru a verifica configurarea sistemului AI Wash Guard."
            
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
            server.starttls()
            server.login(self.sender_email, self.app_password)
            server.sendmail(self.sender_email, self.recipient_email, msg.as_string())
            server.quit()
            return True, "Email de test trimis cu succes!"
        except Exception as e:
            return False, str(e)
