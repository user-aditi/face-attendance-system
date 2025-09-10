import mysql.connector
from datetime import datetime
import configparser

class DatabaseManager:
    """Handles all interactions with the MySQL database."""
    def __init__(self, config_file='config.ini'):
        config = configparser.ConfigParser()
        config.read(config_file)
        self.db_config = config['database']
        self.connection = None

    def _connect(self):
        """Establishes a connection to the database."""
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            return self.connection
        except mysql.connector.Error as err:
            print(f"Error connecting to database: {err}")
            return None

    def _disconnect(self):
        """Closes the database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def create_tables(self):
        """Creates the necessary tables if they don't exist."""
        conn = self._connect()
        if not conn: return
        cursor = conn.cursor()
        print("Ensuring database tables exist...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            major VARCHAR(100),
            section VARCHAR(10),
            year INT,
            total_present INT DEFAULT 0,
            last_entry_time DATETIME DEFAULT '2000-01-01 00:00:00',
            daily_status VARCHAR(20) DEFAULT 'Absent'
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_images (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id VARCHAR(50) NOT NULL,
            image_path VARCHAR(255) NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id VARCHAR(50) NOT NULL,
            date DATE,
            entry_time DATETIME,
            exit_time DATETIME,
            status VARCHAR(20),
            FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
        )
        """)
        conn.commit()
        cursor.close()
        self._disconnect()