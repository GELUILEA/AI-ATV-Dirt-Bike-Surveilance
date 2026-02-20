"""
database.py - MySQL Database manager for AI Wash Guard
"""

import mysql.connector
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Handles MySQL connection and logging of incidents with lazy initialization.
    """
    def __init__(self, host, user, password, database):
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database
        }
        self.conn = None

    def _get_connection(self):
        """Lazy connection establishment."""
        try:
            if self.conn is None or not self.conn.is_connected():
                logger.info(f"Încercare conectare la baza de date: {self.config.get('host')}")
                self.conn = mysql.connector.connect(
                    host=self.config['host'],
                    user=self.config['user'],
                    password=self.config['password'],
                    database=self.config['database'],
                    connect_timeout=3
                )
                self._initialize_db_tables()
            return self.conn
        except Exception as err:
            logger.error(f"Eroare conectare MySQL: {err}")
            return None

    def _initialize_db_tables(self):
        """Creates the necessary tables if they don't exist. Called after successful connection."""
        if not self.conn or not self.conn.is_connected(): return
        
        try:
            cursor = self.conn.cursor()
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
            self.conn.commit()
            cursor.close()
            logger.info("Baza de date și tabelele sunt pregătite.")
        except mysql.connector.Error as err:
            logger.error(f"Eroare inițializare tabelă: {err}")

    def log_incident(self, bay_name, vehicle_type):
        conn = self._get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            query = "INSERT INTO Wash_Incidents (bay_name, vehicle_type, timestamp) VALUES (%s, %s, %s)"
            cursor.execute(query, (bay_name, vehicle_type, datetime.now()))
            conn.commit()
            cursor.close()
            logger.info(f"Incident salvat în DB pentru {bay_name}.")
        except mysql.connector.Error as err:
            logger.error(f"Eroare salvare incident în DB: {err}")

    def start_session(self, bay_name):
        conn = self._get_connection()
        if not conn: return None
        
        try:
            cursor = conn.cursor()
            query = "INSERT INTO Wash_Sessions (bay_name, start_time) VALUES (%s, %s)"
            cursor.execute(query, (bay_name, datetime.now()))
            session_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            return session_id
        except mysql.connector.Error as err:
            logger.error(f"Eroare pornire sesiune: {err}")
            return None

    def end_session(self, session_id):
        conn = self._get_connection()
        if not conn or session_id is None: return
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT start_time FROM Wash_Sessions WHERE id = %s", (session_id,))
            result = cursor.fetchone()
            if not result: 
                cursor.close()
                return
            
            start_time = result[0]
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())
            
            query = "UPDATE Wash_Sessions SET end_time = %s, duration_seconds = %s WHERE id = %s"
            cursor.execute(query, (end_time, duration, session_id))
            conn.commit()
            cursor.close()
            logger.info(f"Sesiune {session_id} încheiată. Durată: {duration} secunde.")
        except mysql.connector.Error as err:
            logger.error(f"Eroare închidere sesiune: {err}")

    def update_config(self, host, user, password, database):
        """Updates config. Connection will happen lazily on next use."""
        self.config['host'] = host
        self.config['user'] = user
        self.config['password'] = password
        self.config['database'] = database
        self.close() # Reset connection to force lazy reconnect

    @staticmethod
    def test_connection(host, user, password, database):
        """Quickly check if the database configuration is valid and reachable."""
        try:
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                connect_timeout=5
            )
            if conn.is_connected():
                conn.close()
                return True, "Conexiune la baza de date reușită!"
            return False, "Nu s-a putut stabili conexiunea."
        except Exception as e:
            return False, str(e)

    def close(self):
        if self.conn and self.conn.is_connected():
            try:
                self.conn.close()
                logger.info("Conexiune MySQL închisă.")
            except:
                pass
        self.conn = None
