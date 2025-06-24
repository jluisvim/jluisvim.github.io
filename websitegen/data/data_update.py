import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import os

class CSVEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Editor")
        
        self.file_path = None
        self.data = []
        self.headers = []
        
        self.create_widgets()
    
    def create_widgets(self):
        # Create a frame for buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)
        
        # Button to open a CSV file
        ttk.Button(button_frame, text="Open CSV", command=self.open_csv).grid(row=0, column=0, padx=5)
        # Button to save changes to the CSV file
        ttk.Button(button_frame, text="Save CSV", command=self.save_csv).grid(row=0, column=1, padx=5)
        
        # Create a Treeview to display CSV data
        self.tree = ttk.Treeview(self.root, columns=("col1", "col2", "col3", "col4", "col5"), show='headings')
        self.tree.heading("col1", text="Column 1")
        self.tree.heading("col2", text="Column 2")
        self.tree.heading("col3", text="Column 3")
        self.tree.heading("col4", text="Column 4")
        self.tree.heading("col5", text="Column 5")
        self.tree.pack(pady=20, fill=tk.BOTH, expand=True)
        
        # Create a frame for action buttons
        action_frame = ttk.Frame(self.root)
        action_frame.pack(pady=10)
        
        ttk.Button(action_frame, text="Add Row", command=self.add_row).grid(row=0, column=0, padx=5)
        ttk.Button(action_frame, text="Edit Row", command=self.edit_row).grid(row=0, column=1, padx=5)
        ttk.Button(action_frame, text="Delete Row", command=self.delete_row).grid(row=0, column=2, padx=5)
    
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
    app = CSVEditor(root)
    root.mainloop()
