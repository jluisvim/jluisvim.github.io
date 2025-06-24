import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import subprocess
import shutil
import os

def run_command(command, check=True):
    """Run a shell command and handle errors."""
    try:
        result = subprocess.run(command, check=check, shell=True, text=True, capture_output=True)
        print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        print(e.stderr)
        return False

class AcademicWebsiteBuilder:
    def __init__(self, root):
        self.root = root
        self.root.title("Academic Website Build & Deploy Script")
        
        self.build_script = "build_site.py"
        self.destination = ""
        self.git_operation = tk.BooleanVar(value=False)
        
        self.create_widgets()
    
    def create_widgets(self):
        # Create a frame for selecting the build script
        build_script_frame = ttk.Frame(self.root)
        build_script_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(build_script_frame, text="Build Script:").pack(side=tk.LEFT, padx=5)
        self.build_script_entry = ttk.Entry(build_script_frame, width=40)
        self.build_script_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.build_script_entry.insert(0, self.build_script)
        
        ttk.Button(build_script_frame, text="Browse", command=self.browse_build_script).pack(side=tk.LEFT, padx=5)
        
        # Create a frame for selecting the destination directory
        destination_frame = ttk.Frame(self.root)
        destination_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(destination_frame, text="Destination Directory:").pack(side=tk.LEFT, padx=5)
        self.destination_entry = ttk.Entry(destination_frame, width=40)
        self.destination_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.destination_entry.insert(0, self.destination)
        
        ttk.Button(destination_frame, text="Browse", command=self.browse_destination).pack(side=tk.LEFT, padx=5)
        
        # Create a checkbox for Git operations
        git_frame = ttk.Frame(self.root)
        git_frame.pack(pady=10, padx=10, fill=tk.X)
        
        self.git_checkbox = ttk.Checkbutton(git_frame, text="Perform Git Operations", variable=self.git_operation)
        self.git_checkbox.pack(side=tk.LEFT, padx=5)
        
        # Create a button to run the script
        run_button = ttk.Button(self.root, text="Run Script", command=self.run_script)
        run_button.pack(pady=20)
    
    def browse_build_script(self):
        file_path = filedialog.askopenfilename(filetypes=[("Python Scripts", "*.py")])
        if file_path:
            self.build_script_entry.delete(0, tk.END)
            self.build_script_entry.insert(0, file_path)
    
    def browse_destination(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.destination_entry.delete(0, tk.END)
            self.destination_entry.insert(0, dir_path)
    
    def run_script(self):
        self.build_script = self.build_script_entry.get().strip()
        self.destination = self.destination_entry.get().strip()
        git_operation = self.git_operation.get()  # Get the boolean value from the BooleanVar
        
        # Validate build script
        if not self.build_script:
            self.build_script = "build_site.py"
        
        if not os.path.isfile(self.build_script):
            messagebox.showerror("Error", f"The build script '{self.build_script}' does not exist.")
            return
        
        # Run the build script
        print(f"Running build script: {self.build_script}")
        build_result = run_command(f"python3 {self.build_script}")
        if not build_result:
            messagebox.showerror("Error", "Build failed. Exiting.")
            return
        
        # Copy the build output if a destination is specified
        if self.destination:
            source_dir = 'dist'  # Assuming the build output is in the 'dist' directory
            if not os.path.exists(source_dir):
                messagebox.showerror("Error", f"Source directory '{source_dir}' does not exist. Exiting.")
                return
            
            print(f"Copying build output to: {self.destination}")
            try:
                shutil.copytree(source_dir, self.destination, dirs_exist_ok=True)
            except Exception as e:
                messagebox.showerror("Error", f"Copy failed: {e}")
                return
        
        # Perform Git operations if requested
        if git_operation:
            print("Performing git operations...")
            
            # Git status
            if not run_command("git status"):
                messagebox.showerror("Error", "Git status failed. Exiting.")
                return
            
            # Git add
            if not run_command("git add -A"):
                messagebox.showerror("Error", "Git add failed. Exiting.")
                return
            
            # Ask for commit message
            commit_msg = simpledialog.askstring("Commit Message", "Enter commit message:", initialvalue="Automated commit")
            if commit_msg is None:
                messagebox.showerror("Error", "Commit message cannot be empty. Exiting.")
                return
            
            # Git commit
            if not run_command(f"git commit -m \"{commit_msg}\""):
                messagebox.showerror("Error", "Git commit failed. Exiting.")
                return
            
            # Git push
            if not run_command("git push"):
                messagebox.showerror("Error", "Git push failed. Exiting.")
                return
        
        messagebox.showinfo("Success", "Script completed successfully.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AcademicWebsiteBuilder(root)
    root.mainloop()
