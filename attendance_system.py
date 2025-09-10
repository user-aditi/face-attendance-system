import cv2
import pickle
import face_recognition
import numpy as np
import os
from database_manager import DatabaseManager
from datetime import datetime, timedelta

class AttendanceSystem:
    def __init__(self, mode="entry"):
        self.mode = mode
        self.db_manager = DatabaseManager()
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 640)
        self.cap.set(4, 480)
        
        self.UI_WIDTH, self.UI_HEIGHT = 1280, 720
        self.BG_COLOR = (21, 21, 21)
        self.UI_COLOR = (45, 45, 45)
        self.TEXT_COLOR = (255, 255, 255)
        self.SUCCESS_COLOR = (0, 255, 0)
        self.ERROR_COLOR = (0, 0, 255)

        self.load_encodings()

        self.mode_type = "active"
        self.counter = 0
        self.student_id = -1
        self.student_info = None
        self.status_message = ""
        self.is_running = False

    def load_encodings(self):
        try:
            with open('EncodeFile.p', 'rb') as file:
                self.encode_list_known, self.student_ids = pickle.load(file)
            print("Encode File Loaded.")
        except FileNotFoundError:
            self.encode_list_known, self.student_ids = [], []

    def _draw_ui(self, frame):
        ui_frame = np.full((self.UI_HEIGHT, self.UI_WIDTH, 3), self.BG_COLOR, np.uint8)
        frame_resized = cv2.resize(frame, (640, 480))
        ui_frame[120:600, 30:670] = frame_resized

        cv2.rectangle(ui_frame, (700, 0), (self.UI_WIDTH, self.UI_HEIGHT), self.UI_COLOR, cv2.FILLED)
        cv2.putText(ui_frame, f"MODE: {self.mode.upper()}", (720, 50), cv2.FONT_HERSHEY_DUPLEX, 1, self.TEXT_COLOR, 2)
        cv2.putText(ui_frame, datetime.now().strftime("%I:%M:%S %p"), (720, 100), cv2.FONT_HERSHEY_DUPLEX, 1, self.TEXT_COLOR, 2)
        
        if self.mode_type == "marked":
            cv2.putText(ui_frame, "MARKED", (720, 680), cv2.FONT_HERSHEY_DUPLEX, 2, self.SUCCESS_COLOR, 3)
        elif self.mode_type == "error":
            cv2.putText(ui_frame, self.status_message, (720, 680), cv2.FONT_HERSHEY_DUPLEX, 1.2, self.ERROR_COLOR, 2)
        
        if self.student_info:
            y0, dy = 200, 45
            cv2.putText(ui_frame, f"ID: {self.student_info['student_id']}", (720, y0), cv2.FONT_HERSHEY_PLAIN, 2.5, self.TEXT_COLOR, 2)
            cv2.putText(ui_frame, f"Name: {self.student_info['name']}", (720, y0 + dy), cv2.FONT_HERSHEY_PLAIN, 2.5, self.TEXT_COLOR, 2)
            cv2.putText(ui_frame, f"Major: {self.student_info['major']}", (720, y0 + 2*dy), cv2.FONT_HERSHEY_PLAIN, 2.5, self.TEXT_COLOR, 2)
            cv2.putText(ui_frame, f"Year: {self.student_info['year']}", (720, y0 + 3*dy), cv2.FONT_HERSHEY_PLAIN, 2.5, self.TEXT_COLOR, 2)
            cv2.putText(ui_frame, f"Present Days: {self.student_info['total_present']}", (720, y0 + 4*dy), cv2.FONT_HERSHEY_PLAIN, 2.5, self.TEXT_COLOR, 2)
        return ui_frame

    def run(self):
        self.is_running = True
        while self.is_running:
            success, img = self.cap.read()
            if not success: break
            
            ui_frame = self._draw_ui(img)

            if self.counter == 0:
                self.mode_type = "active"
                img_s = cv2.resize(img, (0, 0), None, 0.25, 0.25)
                img_s_rgb = cv2.cvtColor(img_s, cv2.COLOR_BGR2RGB)
                
                face_locations = face_recognition.face_locations(img_s_rgb)
                encode_cur_frame = face_recognition.face_encodings(img_s_rgb, face_locations)
                
                if face_locations:
                    self.process_face(encode_cur_frame)
            
            if self.counter > 0:
                self.counter += 1
                if self.counter > 25: # Display message for ~1 second
                    self.counter, self.student_info, self.status_message = 0, None, ""

            cv2.imshow("Face Attendance", ui_frame)
            if cv2.waitKey(1) == 27: self.stop()

    def process_face(self, encode_cur_frame):
        if not self.encode_list_known: return
        
        face_dis = face_recognition.face_distance(self.encode_list_known, encode_cur_frame[0])
        match_index = np.argmin(face_dis)
        
        if face_dis[match_index] < 0.50: # Stricter threshold
            self.student_id = self.student_ids[match_index]
            self.counter = 1
            # --- We will add the database logging logic in the next step ---
            self.mode_type = "marked"
            self.student_info = self.db_manager.get_student_info(self.student_id)

    def stop(self):
        self.is_running = False
        self.cap.release()
        cv2.destroyAllWindows()
      
    def process_face(self, encode_cur_frame):
        if not self.encode_list_known: return
        
        face_dis = face_recognition.face_distance(self.encode_list_known, encode_cur_frame[0])
        match_index = np.argmin(face_dis)
        
        if face_dis[match_index] < 0.50:
            self.student_id = self.student_ids[match_index]
            self.counter = 1 # Start the display timer

            # Log attendance and get the result
            status, info = self.db_manager.log_attendance(self.student_id, self.mode)
            self.student_info = info # Display the student's info regardless of status
            
            if status == "Success":
                self.mode_type = "marked"
            else:
                self.mode_type = "error"
                self.status_message = status # E.g., "Cooldown" or "Not Present"