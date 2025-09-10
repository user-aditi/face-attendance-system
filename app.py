import customtkinter as ctk
from database_manager import DatabaseManager

# Set the appearance and theme for the GUI
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Face Recognition Attendance System")
        self.geometry("600x400")

        # Initialize and prepare the database by creating tables if they don't exist
        self.db_manager = DatabaseManager()
        self.db_manager.create_tables()

        # Add a simple label to the main window
        self.label = ctk.CTkLabel(self, text="Control Panel", font=("Arial", 20, "bold"))
        self.label.pack(pady=40)

if __name__ == "__main__":
    app = App()
    app.mainloop()