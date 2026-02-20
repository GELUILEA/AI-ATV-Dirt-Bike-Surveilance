"""
notifier.py - Email notification service using Gmail SMTP
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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

    def send_alert(self, bay_name, vehicle_type):
        """
        Sends an alert email for a detection incident.
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
            Acțiune: Sistemul a întrerupt alimentarea cu energie.
            """

            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
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
