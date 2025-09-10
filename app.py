import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk
import os
import shutil
import csv
from database_manager import DatabaseManager
from face_encoder import generate_encodings
from attendance_system import AttendanceSystem
import threading
from datetime import datetime
from tkcalendar import DateEntry

# (AddStudentWindow remains the same)
class AddStudentWindow(ctk.CTkToplevel):
    # ... code is unchanged
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Add New Student")
        self.geometry("400x400")
        self.transient(master)
        self.master = master
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
        if self.image_path: self.image_label.configure(text=os.path.basename(self.image_path))
    def save_student(self):
        student_id = self.id_entry.get()
        name = self.name_entry.get()
        major = self.major_entry.get()
        year = self.year_entry.get()
        section = self.section_entry.get()
        if not all([student_id, name, major, year, section, self.image_path]):
            messagebox.showerror("Error", "All fields and an image are required.", parent=self)
            return
        try: year_int = int(year)
        except ValueError:
            messagebox.showerror("Error", "Year must be a number.", parent=self)
            return
        images_dir = "Images"; os.makedirs(images_dir, exist_ok=True)
        file_ext = os.path.splitext(self.image_path)[1]
        new_image_path = os.path.join(images_dir, f"{student_id}{file_ext}")
        shutil.copy(self.image_path, new_image_path)
        success = self.master.db_manager.add_student(student_id, name, major, year_int, section, new_image_path)
        if success:
            messagebox.showinfo("Success", f"Student {name} added.", parent=self)
            self.master.refresh_student_list()
            self.destroy()
        else:
            messagebox.showerror("Error", f"Student ID '{student_id}' may already exist.", parent=self)
            os.remove(new_image_path)

### --- NEW EDIT STUDENT WINDOW CLASS --- ###
class EditStudentWindow(ctk.CTkToplevel):
    def __init__(self, master, student_data, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Edit Student")
        self.geometry("400x400")
        self.transient(master)
        self.master = master
        self.student_data = student_data
        
        # (Layout is similar to AddStudentWindow, but pre-filled with data)
        self.label = ctk.CTkLabel(self, text="Edit Student Details", font=("Arial", 18))
        self.label.pack(pady=15)
        self.id_entry = ctk.CTkEntry(self); self.id_entry.insert(0, self.student_data['student_id']); self.id_entry.pack(pady=7, padx=20, fill="x")
        self.name_entry = ctk.CTkEntry(self); self.name_entry.insert(0, self.student_data['name']); self.name_entry.pack(pady=7, padx=20, fill="x")
        self.major_entry = ctk.CTkEntry(self); self.major_entry.insert(0, self.student_data['major']); self.major_entry.pack(pady=7, padx=20, fill="x")
        self.year_entry = ctk.CTkEntry(self); self.year_entry.insert(0, str(self.student_data['year'])); self.year_entry.pack(pady=7, padx=20, fill="x")
        self.section_entry = ctk.CTkEntry(self); self.section_entry.insert(0, self.student_data['section']); self.section_entry.pack(pady=7, padx=20, fill="x")

        self.new_image_path = None
        self.image_label = ctk.CTkLabel(self, text=os.path.basename(self.student_data['image_path']))
        self.image_label.pack(pady=5)
        self.image_button = ctk.CTkButton(self, text="Select New Image (Optional)", command=self.select_image)
        self.image_button.pack(pady=5)
        self.save_button = ctk.CTkButton(self, text="Save Changes", command=self.save_changes)
        self.save_button.pack(pady=20)

    def select_image(self):
        self.new_image_path = filedialog.askopenfilename(title="Select New Student Image")
        if self.new_image_path: self.image_label.configure(text=os.path.basename(self.new_image_path))

    def save_changes(self):
        original_id = self.student_data['student_id']
        new_details = {
            'student_id': self.id_entry.get(),
            'name': self.name_entry.get(),
            'major': self.major_entry.get(),
            'year': int(self.year_entry.get()),
            'section': self.section_entry.get()
        }
        
        # Handle image update
        if self.new_image_path:
            # Delete old image
            if os.path.exists(self.student_data['image_path']): os.remove(self.student_data['image_path'])
            # Save new image
            images_dir = "Images"
            file_ext = os.path.splitext(self.new_image_path)[1]
            new_image_path_final = os.path.join(images_dir, f"{new_details['student_id']}{file_ext}")
            shutil.copy(self.new_image_path, new_image_path_final)
            new_details['image_path'] = new_image_path_final

        success = self.master.db_manager.update_student(original_id, new_details)
        if success:
            messagebox.showinfo("Success", "Student details updated.", parent=self)
            self.master.refresh_student_list()
            self.destroy()
        else:
            messagebox.showerror("Error", "Failed to update student. ID may conflict with an existing student.", parent=self)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Face Recognition Attendance System")
        self.geometry("1100x600")
        self.db_manager = DatabaseManager()
        self.db_manager.create_tables()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # (Navigation Frame remains the same)
        self.nav_frame = ctk.CTkFrame(self, width=150, corner_radius=0)
        self.nav_frame.grid(row=0, column=0, sticky="nsw")
        ctk.CTkLabel(self.nav_frame, text="Menu", font=("Arial", 18, "bold")).pack(pady=20, padx=20)
        self.dashboard_btn = ctk.CTkButton(self.nav_frame, text="Dashboard", command=self.show_dashboard_frame)
        self.dashboard_btn.pack(pady=10, padx=20)
        self.manage_btn = ctk.CTkButton(self.nav_frame, text="Manage Students", command=self.show_manage_frame)
        self.manage_btn.pack(pady=10, padx=20)
        self.reports_btn = ctk.CTkButton(self.nav_frame, text="Reports", command=self.show_reports_frame)
        self.reports_btn.pack(pady=10, padx=20)
        
        self.dashboard_frame = self.create_dashboard_frame()
        self.manage_student_frame = self.create_manage_student_frame()
        self.reports_frame = self.create_reports_frame()
        self.show_dashboard_frame()

    def create_dashboard_frame(self):
        # (Unchanged)
        frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        ctk.CTkLabel(frame, text="System Dashboard", font=("Arial", 20, "bold")).pack(pady=20)
        launch_frame = ctk.CTkFrame(frame); launch_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(launch_frame, text="Real-Time Attendance", font=("Arial", 16)).pack(pady=5)
        self.mode_var = ctk.StringVar(value="entry")
        ctk.CTkRadioButton(launch_frame, text="Entry", variable=self.mode_var, value="entry").pack(side="left", padx=20, pady=10)
        ctk.CTkRadioButton(launch_frame, text="Exit", variable=self.mode_var, value="exit").pack(side="left", padx=20, pady=10)
        ctk.CTkButton(launch_frame, text="Start Camera", command=self.start_attendance).pack(side="right", padx=20, pady=10)
        manage_frame = ctk.CTkFrame(frame); manage_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(manage_frame, text="System Management", font=("Arial", 16)).pack(pady=5)
        ctk.CTkButton(manage_frame, text="Generate Face Encodings", command=self.run_encoding).pack(pady=10, fill="x")
        ctk.CTkButton(manage_frame, text="Daily Attendance Reset", command=self.run_daily_reset).pack(pady=10, fill="x")
        return frame

    def create_manage_student_frame(self):
        # (Unchanged)
        frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        top_bar = ctk.CTkFrame(frame); top_bar.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(top_bar, text="Student Roster", font=("Arial", 20, "bold")).pack(side="left", padx=10)
        ctk.CTkButton(top_bar, text="Add New Student", command=self.open_add_student_window).pack(side="right", padx=10)
        self.student_list_frame = ctk.CTkScrollableFrame(frame)
        self.student_list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        return frame

    def create_reports_frame(self):
        # (Unchanged)
        frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        filter_frame = ctk.CTkFrame(frame)
        filter_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        filter_frame.grid_columnconfigure(3, weight=1) 
        ctk.CTkLabel(filter_frame, text="Report Date:").grid(row=0, column=0, padx=(10, 5), pady=10)
        self.report_date_entry = DateEntry(filter_frame, width=12, background='blue', foreground='white', borderwidth=2, date_pattern='y-mm-dd')
        self.report_date_entry.grid(row=0, column=1, padx=5, pady=10)
        ctk.CTkLabel(filter_frame, text="Search:").grid(row=0, column=2, padx=(20, 5), pady=10)
        self.search_entry = ctk.CTkEntry(filter_frame, placeholder_text="Type name or ID...")
        self.search_entry.grid(row=0, column=3, padx=5, pady=10, sticky="ew")
        ctk.CTkButton(filter_frame, text="Search", command=self.search_daily_report).grid(row=0, column=4, padx=5, pady=10)
        ctk.CTkButton(filter_frame, text="Clear", command=self.clear_filters).grid(row=0, column=5, padx=5, pady=10)
        ctk.CTkButton(filter_frame, text="Export to CSV", command=self.export_to_csv).grid(row=0, column=6, padx=(20, 10), pady=10)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2a2d2e", foreground="white", fieldbackground="#343638", borderwidth=0, rowheight=25)
        style.map('Treeview', background=[('selected', '#22559b')])
        style.configure("Treeview.Heading", background="#565b5e", foreground="white", relief="flat", font=('Calibri', 10,'bold'))
        style.map("Treeview.Heading", background=[('active', '#3484F0')])
        tree_frame = ctk.CTkFrame(frame, fg_color="transparent")
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        columns = ("id", "name", "section", "status", "entry_time", "exit_time")
        self.log_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        for col in columns: self.log_tree.heading(col, text=col.replace("_", " ").title(), command=lambda c=col: self.sort_treeview_column(c, False))
        self.log_tree.column("id", width=100, anchor="center")
        self.log_tree.column("name", width=200)
        self.log_tree.column("section", width=100, anchor="center")
        self.log_tree.column("status", width=120, anchor="center")
        self.log_tree.column("entry_time", width=120, anchor="center")
        self.log_tree.column("exit_time", width=120, anchor="center")
        self.log_tree.grid(row=0, column=0, sticky="nsew")
        return frame

    ### --- MODIFIED refresh_student_list --- ###
    def refresh_student_list(self):
        for widget in self.student_list_frame.winfo_children(): widget.destroy()
        
        students = self.db_manager.get_all_students()
        if not students:
            ctk.CTkLabel(self.student_list_frame, text="No students found.").pack(pady=20)
            return

        for student in students:
            # Create a "card" for each student
            card = ctk.CTkFrame(self.student_list_frame)
            card.pack(fill="x", pady=5, padx=5)
            card.grid_columnconfigure(0, weight=1)

            info = f"ID: {student['student_id']} | Name: {student['name']} | Major: {student['major']}"
            ctk.CTkLabel(card, text=info, anchor="w").grid(row=0, column=0, padx=10, pady=10, sticky="w")
            
            # Use a lambda function to pass the current student's data to the command
            edit_btn = ctk.CTkButton(card, text="Edit", width=60, command=lambda s=student: self.open_edit_student_window(s))
            edit_btn.grid(row=0, column=1, padx=5, pady=5)
            
            delete_btn = ctk.CTkButton(card, text="Delete", width=60, fg_color="#D2691E", hover_color="#8B4513", command=lambda id=student['student_id']: self.delete_student(id))
            delete_btn.grid(row=0, column=2, padx=(0, 10), pady=5)
    
    # (show frames methods remain the same)
    def show_dashboard_frame(self):
        self.manage_student_frame.grid_forget()
        self.reports_frame.grid_forget()
        self.dashboard_frame.grid(row=0, column=1, sticky="nsew")
    def show_manage_frame(self):
        self.dashboard_frame.grid_forget()
        self.reports_frame.grid_forget()
        self.manage_student_frame.grid(row=0, column=1, sticky="nsew")
        self.refresh_student_list()
    def show_reports_frame(self):
        self.dashboard_frame.grid_forget()
        self.manage_student_frame.grid_forget()
        self.reports_frame.grid(row=0, column=1, sticky="nsew")
        self.search_daily_report()
    
    # (report methods remain the same)
    def clear_filters(self):
        self.search_entry.delete(0, 'end')
        self.report_date_entry.set_date(datetime.now())
        self.search_daily_report()
    def search_daily_report(self):
        for item in self.log_tree.get_children(): self.log_tree.delete(item)
        report_date = self.report_date_entry.get_date()
        search_term = self.search_entry.get()
        report_data = self.db_manager.get_daily_report(report_date, search_term)
        for record in report_data:
            entry_time = record['entry_time'].strftime('%I:%M:%S %p') if record['entry_time'] else "---"
            exit_time = record['exit_time'].strftime('%I:%M:%S %p') if record['exit_time'] else "---"
            self.log_tree.insert("", "end", values=(record['student_id'], record['name'], record['section'], record['status'], entry_time, exit_time))
    def sort_treeview_column(self, col, reverse):
        data_list = [(self.log_tree.set(k, col), k) for k in self.log_tree.get_children('')]
        try: data_list.sort(key=lambda t: int(t[0]), reverse=reverse)
        except ValueError: data_list.sort(key=lambda t: t[0], reverse=reverse)
        for index, (val, k) in enumerate(data_list): self.log_tree.move(k, '', index)
        self.log_tree.heading(col, command=lambda: self.sort_treeview_column(col, not reverse))
    def export_to_csv(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not filepath: return
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([self.log_tree.heading(c)["text"] for c in self.log_tree["columns"]])
                for item_id in self.log_tree.get_children(): writer.writerow(self.log_tree.item(item_id)["values"])
            messagebox.showinfo("Success", f"Data exported to {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {e}")
            
    ### --- NEW METHODS FOR EDIT/DELETE --- ###
    def open_add_student_window(self):
        AddStudentWindow(self)

    def open_edit_student_window(self, student_data):
        EditStudentWindow(self, student_data)
        
    def delete_student(self, student_id):
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to permanently delete student {student_id}?"):
            if self.db_manager.delete_student(student_id):
                messagebox.showinfo("Success", f"Student {student_id} has been deleted.")
                self.refresh_student_list()
            else:
                messagebox.showerror("Error", f"Failed to delete student {student_id}.")

    # (Button Command Methods remain unchanged)
    def start_attendance(self):
        mode = self.mode_var.get()
        if not os.path.exists('EncodeFile.p'):
            messagebox.showerror("Error", "EncodeFile.p not found.")
            return
        def run_system():
            attendance_app = AttendanceSystem(mode=mode)
            attendance_app.run()
        attendance_thread = threading.Thread(target=run_system)
        attendance_thread.daemon = True
        attendance_thread.start()
        messagebox.showinfo("Info", f"Camera starting in '{mode}' mode.", parent=self)
    def run_encoding(self):
        if messagebox.askyesno("Confirm", "This will encode all images. Continue?"):
            if generate_encodings(): messagebox.showinfo("Success", "Face encodings generated.")
            else: messagebox.showwarning("Warning", "Encoding failed.")
    def run_daily_reset(self):
        if messagebox.askyesno("Confirm", "Reset daily status for all students?"):
            rows = self.db_manager.daily_reset()
            messagebox.showinfo("Success", f"Daily status reset for {rows} students.")


if __name__ == "__main__":
    app = App()
    app.mainloop()