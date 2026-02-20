"""
database.py - MySQL Database manager for AI Wash Guard
"""

import mysql.connector
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Handles MySQL connection and logging of incidents.
    """
    def __init__(self, host, user, password, database):
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database
        }
        self.conn = None
        self._initialize_db()

    def _get_connection(self):
        try:
            if self.conn is None or not self.conn.is_connected():
                self.conn = mysql.connector.connect(**self.config)
            return self.conn
        except mysql.connector.Error as err:
            logger.error(f"Eroare conectare MySQL: {err}")
            return None

    def _initialize_db(self):
        """Creates the necessary table if it doesn't exist."""
        conn = self._get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Wash_Incidents (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    bay_name VARCHAR(100),
                    vehicle_type VARCHAR(100),
                    timestamp DATETIME
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Wash_Sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    bay_name VARCHAR(100),
                    start_time DATETIME,
                    end_time DATETIME,
                    duration_seconds INT
                )
            """)
            conn.commit()
            logger.info("Baza de date și tabelele sunt pregătite.")
        except mysql.connector.Error as err:
            logger.error(f"Eroare inițializare tabelă: {err}")

    def log_incident(self, bay_name, vehicle_type):
        """Inserts a new incident record into the database."""
        conn = self._get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            query = "INSERT INTO Wash_Incidents (bay_name, vehicle_type, timestamp) VALUES (%s, %s, %s)"
            cursor.execute(query, (bay_name, vehicle_type, datetime.now()))
            conn.commit()
            logger.info(f"Incident salvat în DB pentru {bay_name}.")
        except mysql.connector.Error as err:
            logger.error(f"Eroare salvare incident în DB: {err}")

    def start_session(self, bay_name):
        """Logs the start of a wash session."""
        conn = self._get_connection()
        if not conn: return None
        
        try:
            cursor = conn.cursor()
            query = "INSERT INTO Wash_Sessions (bay_name, start_time) VALUES (%s, %s)"
            cursor.execute(query, (bay_name, datetime.now()))
            session_id = cursor.lastrowid
            conn.commit()
            return session_id
        except mysql.connector.Error as err:
            logger.error(f"Eroare pornire sesiune: {err}")
            return None

    def end_session(self, session_id):
        """Logs the end of a wash session and calculates duration."""
        conn = self._get_connection()
        if not conn or session_id is None: return
        
        try:
            cursor = conn.cursor()
            # Get start time to calculate duration
            cursor.execute("SELECT start_time FROM Wash_Sessions WHERE id = %s", (session_id,))
            result = cursor.fetchone()
            if not result: return
            
            start_time = result[0]
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())
            
            query = "UPDATE Wash_Sessions SET end_time = %s, duration_seconds = %s WHERE id = %s"
            cursor.execute(query, (end_time, duration, session_id))
            conn.commit()
            logger.info(f"Sesiune {session_id} încheiată. Durată: {duration} secunde.")
        except mysql.connector.Error as err:
            logger.error(f"Eroare închidere sesiune: {err}")

    def close(self):
        if self.conn and self.conn.is_connected():
            self.conn.close()
            logger.info("Conexiune MySQL închisă.")
