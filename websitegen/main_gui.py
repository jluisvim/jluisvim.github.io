import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import subprocess
import shutil
import os
import csv
import requests
from bs4 import BeautifulSoup
from datetime import datetime

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

def get_weather_and_time(location):
    """Get weather and time for a given location using web scraping with wttr.in."""
    try:
        url = f"https://wttr.in/{location}" 
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract the text content
        pre_tag = soup.find('pre')
        if pre_tag is None:
            return f"Error retrieving weather data for {location}: <pre> tag not found"
        
        weather_text = pre_tag.text.strip()
        
        # Split the text to extract relevant information
        lines = weather_text.split('\n')
        
        # Extract time and weather condition
        time_line = lines[0].strip()
        condition_line = lines[1].strip()
        temp_line = lines[2].strip()
        
        # Extract time from the time line
        current_time = time_line.split(': ')[1] if ': ' in time_line else "Time not available"
        
        # Extract temperature from the temp line
        current_temp = temp_line.split(': ')[1] if ': ' in temp_line else "Temperature not available"
        
        # Extract condition from the condition line
        current_condition = condition_line.split(': ')[1] if ': ' in condition_line else "Condition not available"
        
        return f"Location: {location.replace('+', ' ').title()}\nTime: {current_time}\nTemperature: {current_temp}\nCondition: {current_condition}\n\n"
    except Exception as e:
        return f"Error retrieving weather data for {location}: {e}"

class AcademicWebsiteBuilder:
    def __init__(self, root):
        self.root = root
        self.root.title("Academic Website Builder & CSV Editor")
        
        self.build_script = "build_site.py"
        self.destination = "../"
        self.git_operation = tk.BooleanVar(value=False)
        
        self.file_path = None
        self.data = []
        self.headers = []
        
        # Define variables for commit format and padding
        self.commit_format = "%h : %s"
        self.padding_x = 5
        self.padding_y = 5
        self.font_size = 9
        
        self.weather_info = ""
        
        self.create_widgets()
    
    def create_widgets(self):
        # Tab Control
        self.tab_control = ttk.Notebook(self.root)
        
        # Tab for Website Build & Deploy
        self.tab_build_deploy = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_build_deploy, text='Build & Deploy')
        
        # Tab for CSV Editor
        self.tab_csv_editor = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_csv_editor, text='CSV Editor')
        
        # Tab for Weather Information
        self.tab_weather = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_weather, text='Weather')
        
        self.tab_control.pack(expand=1, fill="both")
        
        # Build & Deploy Tab Widgets
        self.create_build_deploy_widgets()
        
        # CSV Editor Tab Widgets
        self.create_csv_editor_widgets()
        
        # Weather Tab Widgets
        self.create_weather_widgets()
    
    def create_build_deploy_widgets(self):
        # Main Frame for Build & Deploy Tab
        main_frame = ttk.Frame(self.tab_build_deploy)
        main_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Left Frame for Description
        left_frame = ttk.Frame(main_frame, borderwidth=2, relief="groove")
        left_frame.pack(side=tk.LEFT, padx=self.padding_x, pady=self.padding_y, fill=tk.BOTH, expand=True)
        
        # Description Label
        description_label = ttk.Label(
            left_frame,
            text=(
                "This tab allows you to build and deploy your academic website.\n\n"
                "- Select the build script (default: build_site.py).\n"
                "- Specify the destination directory to copy the build output.\n"
                "- Check the box to perform Git operations (add, commit, push).\n"
                "- Click 'Run Script' to execute the build, copy, and Git operations."
            ),
            wraplength=500,
            justify=tk.LEFT,
            font=("TkDefaultFont", self.font_size)
        )
        description_label.pack(pady=self.padding_y, padx=self.padding_x, fill=tk.BOTH, expand=True)
        
        # Separator
        separator = ttk.Separator(main_frame, orient="vertical")
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=self.padding_x)
        
        # Right Frame for Git Log
        right_frame = ttk.Frame(main_frame, borderwidth=2, relief="groove")
        right_frame.pack(side=tk.RIGHT, padx=self.padding_x, pady=self.padding_y, fill=tk.BOTH, expand=True)
        
        # Git Log Label
        git_log_label = ttk.Label(
            right_frame,
            text=self.get_git_log(format_str=self.commit_format),
            wraplength=500,
            justify=tk.LEFT,
            font=("TkDefaultFont", self.font_size)
        )
        git_log_label.pack(pady=self.padding_y, padx=self.padding_x, fill=tk.BOTH, expand=True)
        
        # Create a frame for selecting the build script
        build_script_frame = ttk.Frame(self.tab_build_deploy)
        build_script_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(build_script_frame, text="Build Script:").pack(side=tk.LEFT, padx=5)
        self.build_script_entry = ttk.Entry(build_script_frame, width=40)
        self.build_script_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.build_script_entry.insert(0, self.build_script)
        
        ttk.Button(build_script_frame, text="Browse", command=self.browse_build_script).pack(side=tk.LEFT, padx=5)
        
        # Create a frame for selecting the destination directory
        destination_frame = ttk.Frame(self.tab_build_deploy)
        destination_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(destination_frame, text="Destination Directory:").pack(side=tk.LEFT, padx=5)
        self.destination_entry = ttk.Entry(destination_frame, width=40)
        self.destination_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.destination_entry.insert(0, self.destination)
        
        ttk.Button(destination_frame, text="Browse", command=self.browse_destination).pack(side=tk.LEFT, padx=5)
        
        # Create a checkbox for Git operations
        git_frame = ttk.Frame(self.tab_build_deploy)
        git_frame.pack(pady=10, padx=10, fill=tk.X)
        
        self.git_checkbox = ttk.Checkbutton(git_frame, text="Perform Git Operations", variable=self.git_operation)
        self.git_checkbox.pack(side=tk.LEFT, padx=5)
        
        # Create a button to run the script
        run_button = ttk.Button(self.tab_build_deploy, text="Run Script", command=self.run_script)
        run_button.pack(pady=10)
        
        # Exit Button
        exit_button = ttk.Button(self.tab_build_deploy, text="Exit", command=self.exit_app)
        exit_button.pack(pady=self.padding_y)
    
    def create_csv_editor_widgets(self):
        # Main Frame for CSV Editor Tab
        main_frame = ttk.Frame(self.tab_csv_editor)
        main_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Left Frame for Description
        left_frame = ttk.Frame(main_frame, borderwidth=2, relief="groove")
        left_frame.pack(side=tk.LEFT, padx=self.padding_x, pady=self.padding_y, fill=tk.BOTH, expand=True)
        
        # Description Label
        description_label = ttk.Label(
            left_frame,
            text=(
                "This tab allows you to edit CSV files.\n\n"
                "- Open a CSV file.\n"
                "- View, add, edit, and delete rows in the CSV file.\n"
                "- Save changes to the CSV file."
            ),
            wraplength=500,
            justify=tk.LEFT,
            font=("TkDefaultFont", self.font_size)
        )
        description_label.pack(pady=self.padding_y, padx=self.padding_x, fill=tk.BOTH, expand=True)
        
        # Separator
        separator = ttk.Separator(main_frame, orient="vertical")
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=self.padding_x)
        
        # Right Frame for Git Log
        right_frame = ttk.Frame(main_frame, borderwidth=2, relief="groove")
        right_frame.pack(side=tk.RIGHT, padx=self.padding_x, pady=self.padding_y, fill=tk.BOTH, expand=True)
        
        # Git Log Label
        git_log_label = ttk.Label(
            right_frame,
            text=self.get_git_log(format_str=self.commit_format),
            wraplength=500,
            justify=tk.LEFT,
            font=("TkDefaultFont", self.font_size)
        )
        git_log_label.pack(pady=self.padding_y, padx=self.padding_x, fill=tk.BOTH, expand=True)
        
        # Create a frame for buttons
        button_frame = ttk.Frame(self.tab_csv_editor)
        button_frame.pack(pady=10)
        
        # Button to open a CSV file
        ttk.Button(button_frame, text="Open CSV", command=self.open_csv).grid(row=0, column=0, padx=5)
        # Button to save changes to the CSV file
        ttk.Button(button_frame, text="Save CSV", command=self.save_csv).grid(row=0, column=1, padx=5)
        
        # Create a Treeview to display CSV data
        self.tree = ttk.Treeview(self.tab_csv_editor, columns=("col1", "col2", "col3", "col4", "col5"), show='headings')
        self.tree.heading("col1", text="Column 1")
        self.tree.heading("col2", text="Column 2")
        self.tree.heading("col3", text="Column 3")
        self.tree.heading("col4", text="Column 4")
        self.tree.heading("col5", text="Column 5")
        self.tree.pack(pady=20, fill=tk.BOTH, expand=True)
        
        # Create a frame for action buttons
        action_frame = ttk.Frame(self.tab_csv_editor)
        action_frame.pack(pady=10)
        
        ttk.Button(action_frame, text="Add Row", command=self.add_row).grid(row=0, column=0, padx=5)
        ttk.Button(action_frame, text="Edit Row", command=self.edit_row).grid(row=0, column=1, padx=5)
        ttk.Button(action_frame, text="Delete Row", command=self.delete_row).grid(row=0, column=2, padx=5)
        
        # Exit Button
        exit_button = ttk.Button(self.tab_csv_editor, text="Exit", command=self.exit_app)
        exit_button.pack(pady=self.padding_y)
    
    def create_weather_widgets(self):
        # Main Frame for Weather Tab
        main_frame = ttk.Frame(self.tab_weather)
        main_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Left Frame for Description
        left_frame = ttk.Frame(main_frame, borderwidth=2, relief="groove")
        left_frame.pack(side=tk.LEFT, padx=self.padding_x, pady=self.padding_y, fill=tk.BOTH, expand=True)
        
        # Description Label
        description_label = ttk.Label(
            left_frame,
            text=(
                "This tab displays the current weather and time for different locations.\n\n"
                "- Click 'Update Weather and Time' to refresh the information."
            ),
            wraplength=500,
            justify=tk.LEFT,
            font=("TkDefaultFont", self.font_size)
        )
        description_label.pack(pady=self.padding_y, padx=self.padding_x, fill=tk.BOTH, expand=True)
        
        # Separator
        separator = ttk.Separator(main_frame, orient="vertical")
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=self.padding_x)
        
        # Right Frame for Weather Information
        right_frame = ttk.Frame(main_frame, borderwidth=2, relief="groove")
        right_frame.pack(side=tk.RIGHT, padx=self.padding_x, pady=self.padding_y, fill=tk.BOTH, expand=True)
        
        # Weather Info Label
        self.weather_info_label = ttk.Label(
            right_frame,
            text=self.weather_info,
            wraplength=500,
            justify=tk.LEFT,
            font=("TkDefaultFont", self.font_size)
        )
        self.weather_info_label.pack(pady=self.padding_y, padx=self.padding_x, fill=tk.BOTH, expand=True)
        
        # Frame for Buttons
        button_frame = ttk.Frame(self.tab_weather)
        button_frame.pack(pady=10)
        
        # Button to update weather and time
        update_button = ttk.Button(button_frame, text="Update Weather and Time", command=self.update_weather_and_time)
        update_button.pack(side=tk.LEFT, padx=5)
        
        # Exit Button
        exit_button = ttk.Button(button_frame, text="Exit", command=self.exit_app)
        exit_button.pack(side=tk.LEFT, padx=5)
    
    def get_git_log(self, format_str="%h : %s"):
        try:
            result = run_command(f"git log --pretty=format:'{format_str}' -n 3")
            if result.returncode == 0:
                commits = result.stdout.strip().split('\n')
                commits.reverse()  # Reverse the order of commits
                return "Recent Commits:\n" + "\n".join(commits)
            else:
                return "No Git repository found or unable to retrieve commits."
        except Exception as e:
            return f"Error retrieving Git log: {e}"
    
    def update_weather_and_time(self):
        locations = ["paris", "new+york"]
        weather_info = ""
        
        for location in locations:
            weather_info += get_weather_and_time(location)
        
        self.weather_info = weather_info
        self.weather_info_label.config(text=self.weather_info)
    
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
    
    def open_csv(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not self.file_path:
            return
        
        self.load_csv()
        self.update_treeview()
    
    def load_csv(self):
        with open(self.file_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            self.headers = next(reader)
            self.data = [row for row in reader]
    
    def update_treeview(self):
        # Clear the treeview
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        # Update the headings of the treeview according to the CSV columns
        self.tree['columns'] = self.headers
        for col in self.headers:
            self.tree.heading(col, text=col)
        
        # Insert data into the treeview
        for row in self.data:
            self.tree.insert("", tk.END, values=row)
    
    def save_csv(self):
        if self.file_path is None:
            messagebox.showwarning("Warning", "No file opened!")
            return
        
        with open(self.file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(self.headers)
            writer.writerows(self.data)
        
        messagebox.showinfo("Info", "File saved successfully!")
    
    def add_row(self):
        if self.data is None or not self.headers:
            messagebox.showwarning("Warning", "No file opened!")
            return
        
        AddRowDialog(self.root, self.headers, self.data, self.update_treeview)
    
    def edit_row(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "No row selected!")
            return
        
        row_index = self.tree.index(selected_item[0])
        EditRowDialog(self.root, self.headers, self.data, row_index, self.update_treeview)
    
    def delete_row(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "No row selected!")
            return
        
        row_index = self.tree.index(selected_item[0])
        del self.data[row_index]
        self.update_treeview()
    
    def exit_app(self):
        self.root.destroy()

class AddRowDialog:
    def __init__(self, parent, headers, data, callback):
        self.top = tk.Toplevel(parent)
        self.top.title("Add Row")
        
        self.headers = headers
        self.data = data
        self.callback = callback
        
        self.entries = []
        for i, col in enumerate(headers):
            label = ttk.Label(self.top, text=col)
            label.grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)
            
            entry = ttk.Entry(self.top)
            entry.grid(row=i, column=1, padx=5, pady=5)
            self.entries.append(entry)
        
        ttk.Button(self.top, text="Add", command=self.add_row).grid(row=len(headers), column=0, columnspan=2, pady=10)
    
    def add_row(self):
        new_row = [entry.get() for entry in self.entries]
        self.data.insert(0, new_row)  # Insert new row at the beginning
        self.callback()
        self.top.destroy()

class EditRowDialog:
    def __init__(self, parent, headers, data, row_index, callback):
        self.top = tk.Toplevel(parent)
        self.top.title("Edit Row")
        
        self.headers = headers
        self.data = data
        self.row_index = row_index
        self.callback = callback
        
        self.entries = []
        for i, col in enumerate(headers):
            label = ttk.Label(self.top, text=col)
            label.grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)
            
            entry = ttk.Entry(self.top)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entry.insert(0, data[row_index][i])
            self.entries.append(entry)
        
        ttk.Button(self.top, text="Update", command=self.update_row).grid(row=len(headers), column=0, columnspan=2, pady=10)
    
    def update_row(self):
        updated_row = [entry.get() for entry in self.entries]
        self.data[self.row_index] = updated_row
        self.callback()
        self.top.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AcademicWebsiteBuilder(root)
    root.mainloop()
