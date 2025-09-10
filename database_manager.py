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

    def get_all_students(self):
        """Fetches all students and their primary image path."""
        conn = self._connect()
        if not conn: return []
        cursor = conn.cursor(dictionary=True)
        # This query joins the students and images tables to get all necessary info
        query = """
        SELECT 
            s.student_id, 
            ANY_VALUE(s.name) as name, 
            ANY_VALUE(s.major) as major, 
            ANY_VALUE(s.year) as year, 
            ANY_VALUE(s.section) as section, 
            ANY_VALUE(i.image_path) as image_path 
        FROM students s 
        LEFT JOIN student_images i ON s.student_id = i.student_id
        GROUP BY s.student_id
        ORDER BY ANY_VALUE(s.name)
        """
        cursor.execute(query)
        students = cursor.fetchall()
        cursor.close()
        self._disconnect()
        return students

    def add_student(self, student_id, name, major, year, section, image_path):
        """Adds a new student and their image to the database."""
        conn = self._connect()
        if not conn: return False
        cursor = conn.cursor()
        try:
            # Add student details to the 'students' table
            cursor.execute(
                "INSERT INTO students (student_id, name, major, year, section) VALUES (%s, %s, %s, %s, %s)",
                (student_id, name, major, year, section)
            )
            # Add the image path to the 'student_images' table
            cursor.execute(
                "INSERT INTO student_images (student_id, image_path) VALUES (%s, %s)",
                (student_id, image_path)
            )
            conn.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            conn.rollback() # Rollback changes if an error occurs
            return False
        finally:
            cursor.close()
            self._disconnect()