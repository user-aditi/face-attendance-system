import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import os
import shutil
from database_manager import DatabaseManager

# --- GUI Setup ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class AddStudentWindow(ctk.CTkToplevel):
    """A new window for the 'Add Student' form."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Add New Student")
        self.geometry("400x400")
        self.transient(master)  # Keep this window on top of the main app
        self.master = master  # Reference to the main App

        self.label = ctk.CTkLabel(self, text="Enter Student Details", font=("Arial", 18))
        self.label.pack(pady=15)
        
        self.id_entry = ctk.CTkEntry(self, placeholder_text="Student ID")
        self.id_entry.pack(pady=7, padx=20, fill="x")
        
        self.name_entry = ctk.CTkEntry(self, placeholder_text="Full Name")
        self.name_entry.pack(pady=7, padx=20, fill="x")

        self.major_entry = ctk.CTkEntry(self, placeholder_text="Major")
        self.major_entry.pack(pady=7, padx=20, fill="x")

        self.year_entry = ctk.CTkEntry(self, placeholder_text="Year (e.g., 1, 2, 3)")
        self.year_entry.pack(pady=7, padx=20, fill="x")

        self.section_entry = ctk.CTkEntry(self, placeholder_text="Section")
        self.section_entry.pack(pady=7, padx=20, fill="x")

        self.image_path = ""
        self.image_label = ctk.CTkLabel(self, text="No image selected")
        self.image_label.pack(pady=5)
        
        self.image_button = ctk.CTkButton(self, text="Select Image", command=self.select_image)
        self.image_button.pack(pady=5)

        self.save_button = ctk.CTkButton(self, text="Save Student", command=self.save_student)
        self.save_button.pack(pady=20)
        
    def select_image(self):
        self.image_path = filedialog.askopenfilename(title="Select Student Image")
        if self.image_path:
            self.image_label.configure(text=os.path.basename(self.image_path))

    def save_student(self):
        student_id = self.id_entry.get()
        name = self.name_entry.get()
        major = self.major_entry.get()
        year = self.year_entry.get()
        section = self.section_entry.get()

        if not all([student_id, name, major, year, section, self.image_path]):
            messagebox.showerror("Error", "All fields and an image are required.", parent=self)
            return

        try:
            year_int = int(year)
        except ValueError:
            messagebox.showerror("Error", "Year must be a number.", parent=self)
            return

        # Copy image to the Images directory
        images_dir = "Images"
        os.makedirs(images_dir, exist_ok=True)
        file_ext = os.path.splitext(self.image_path)[1]
        new_image_path = os.path.join(images_dir, f"{student_id}{file_ext}")
        shutil.copy(self.image_path, new_image_path)
        
        # Add student to the database
        success = self.master.db_manager.add_student(student_id, name, major, year_int, section, new_image_path)
        
        if success:
            messagebox.showinfo("Success", f"Student {name} added. Remember to regenerate encodings.", parent=self)
            self.master.refresh_student_list() # Refresh the list in the main window
            self.destroy()
        else:
            messagebox.showerror("Error", f"Student ID '{student_id}' may already exist.", parent=self)
            os.remove(new_image_path) # Clean up the copied image if DB insert fails

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Face Recognition Attendance System")
        self.geometry("800x500")
        
        self.db_manager = DatabaseManager()
        self.db_manager.create_tables()

        # Main layout: A navigation rail on the left and a content area on the right
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- Navigation Frame ---
        self.nav_frame = ctk.CTkFrame(self, width=150, corner_radius=0)
        self.nav_frame.grid(row=0, column=0, sticky="nsw")
        
        ctk.CTkLabel(self.nav_frame, text="Menu", font=("Arial", 18, "bold")).pack(pady=20, padx=20)
        self.dashboard_btn = ctk.CTkButton(self.nav_frame, text="Dashboard", command=self.show_dashboard_frame)
        self.dashboard_btn.pack(pady=10, padx=20)
        self.manage_btn = ctk.CTkButton(self.nav_frame, text="Manage Students", command=self.show_manage_frame)
        self.manage_btn.pack(pady=10, padx=20)

        # --- Content Frames ---
        self.dashboard_frame = self.create_dashboard_frame()
        self.manage_student_frame = self.create_manage_student_frame()

        self.show_dashboard_frame() # Show dashboard by default

    def create_dashboard_frame(self):
        frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        ctk.CTkLabel(frame, text="System Dashboard", font=("Arial", 20, "bold")).pack(pady=20)
        # We will fill this frame with more widgets later
        return frame

    def create_manage_student_frame(self):
        frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        top_bar = ctk.CTkFrame(frame)
        top_bar.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(top_bar, text="Student Roster", font=("Arial", 20, "bold")).pack(side="left", padx=10)
        ctk.CTkButton(top_bar, text="Add New Student", command=self.open_add_student_window).pack(side="right", padx=10)

        self.student_list_frame = ctk.CTkScrollableFrame(frame)
        self.student_list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        return frame
    
    def refresh_student_list(self):
        # Clear existing widgets from the scrollable frame
        for widget in self.student_list_frame.winfo_children():
            widget.destroy()
            
        students = self.db_manager.get_all_students()
        if not students:
            ctk.CTkLabel(self.student_list_frame, text="No students found. Add a new student to begin.").pack(pady=20)
        else:
            for i, student in enumerate(students):
                info = f"ID: {student['student_id']} | Name: {student['name']} | Major: {student['major']}"
                ctk.CTkLabel(self.student_list_frame, text=info).pack(anchor="w", pady=4, padx=10)

    def show_dashboard_frame(self):
        self.manage_student_frame.grid_forget()
        self.dashboard_frame.grid(row=0, column=1, sticky="nsew")

    def show_manage_frame(self):
        self.dashboard_frame.grid_forget()
        self.manage_student_frame.grid(row=0, column=1, sticky="nsew")
        self.refresh_student_list()
            
    def open_add_student_window(self):
        AddStudentWindow(self)


if __name__ == "__main__":
    app = App()
    app.mainloop()