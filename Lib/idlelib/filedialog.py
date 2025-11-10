import tkinter as tk
from tkinter import Listbox, Scrollbar
from tkinter import messagebox
from typing import Callable, Union
import os

class FileDialog(tk.Toplevel):
    LOCKED_DIR = os.path.expanduser("~")  # Home directory
    Open = 1
    Save = 2

    def __init__(self,root:Union[tk.Tk|tk.Toplevel],completion_handler: Callable,title="Open File",geometry="800x300",dialog_type=Open):
        super().__init__(root)
        self.transient(root)
        self.title(title)
        self.geometry(geometry)

        self.dialog_type = dialog_type

        #setup history
        self.history = [self.LOCKED_DIR]
        self.history_index=0

        # Navigation buttons
        nav_frame = tk.Frame(self)
        nav_frame.pack(fill="x")

        self.back_btn = tk.Button(nav_frame, text="←", command=self.go_back)
        self.back_btn.pack(side="left", padx=5, pady=5)
        self.back_btn.config(state="disabled")  # Initially disabled

        self.forward_btn = tk.Button(nav_frame, text="→", command=self.go_forward)
        self.forward_btn.pack(side="left", padx=5, pady=5)
        self.forward_btn.config(state="disabled")  # Initially disabled

        self.up_btn = tk.Button(nav_frame, text="Up", command=self.go_up)
        self.up_btn.pack(side="left", padx=5, pady=5)
        self.up_btn.config(state="disabled")  # Initially disabled

        self.current_path_display = tk.StringVar(master=self,value="/")
        current_path_box = tk.Entry(nav_frame, textvariable=self.current_path_display, state="readonly", width=200)
        current_path_box.pack(side="left", padx=5, pady=5, fill="x", expand=True)

        self.current_path = tk.StringVar(master=self,value=self.LOCKED_DIR)

        self.listbox = Listbox(self)
        self.listbox.pack(fill="both", expand=True)

        self.listbox.bind("<Double Button-1>",self.listbox_on_double_click)
        self.listbox.bind("<<ListboxSelect>>", lambda e: self.file_path_var.set(self.getselection() or ""))
        self.listbox.bind("<Return>",self.listbox_on_double_click)

        # OK/Cancel buttons
        actions_frame = tk.Frame(self)
        actions_frame.pack(fill="x")

        # File path entry
        tk.Label(actions_frame, text="File path:").pack(side="left",pady=(5, 0))
        self.file_path_var=tk.StringVar(master=self)
        self.entry = tk.Entry(actions_frame, textvariable=self.file_path_var, width=50)
        self.entry.pack(side="left",padx=5,pady=5)
        self.bind("<Return>", lambda e: self.goto(self.file_path_var.get()))

        self.ok_btn = tk.Button(actions_frame, text="OK", command=self.listbox_on_double_click)
        self.cancel_btn = tk.Button(actions_frame, text="Cancel", command=self.destroy)
        self.bind("<Escape>", lambda e:self.destroy())
        #pack the cancel button first, because we want it on the right
        #side="right" packs from right to left
        self.cancel_btn.pack(side="right", padx=5, pady=5)
        self.ok_btn.pack(side="right", padx=5, pady=5)

        self.list_files(self.LOCKED_DIR)

        self.completion_handler = completion_handler

    def list_files(self,path):
        self.listbox.delete(0, tk.END)
        for item in os.listdir(path):
            if item.startswith('.'): continue  # Skip hidden files
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                self.listbox.insert(tk.END, f"[DIR] {item}")
            else:
                self.listbox.insert(tk.END, item)

    def listbox_on_double_click(self,event=None):
        selection = self.getselection()
        if selection is None: return
        item = selection
        if item.startswith("[DIR] "):
            folder = item[6:]
            new_path = os.path.join(self.current_path.get(), folder)
            if os.path.commonpath([self.LOCKED_DIR, new_path]) == self.LOCKED_DIR:
                current=self.current_path.get()
                self.push_history(new_path)
                self.back_btn.config(state="normal")  # Enable back button
                self.forward_btn.config(state="disabled")  # Disable forward button
                if new_path.strip()==self.LOCKED_DIR.strip():
                    self.up_btn.config(state="disabled")
                else:
                    self.up_btn.config(state="normal")
                self.history.append(new_path)
                self.history_index+=1
                self.current_path.set(new_path)
                # lstripping / and then prepending / to ensure single leading /
                display_path='/'+(self.current_path.get().replace(self.LOCKED_DIR,'/')).lstrip('/')
                self.current_path_display.set(display_path)
                self.list_files(new_path)
        else:
            file_name = item
            file_path = os.path.join(self.current_path.get(), file_name)
            self.completion_handler(file_path)
            self.destroy()

    def getselection(self):
        selection = self.listbox.curselection()
        if not selection:
            return None
        return self.listbox.get(selection[0])

    def goto(self,in_path,mode=None):
        mode=mode or self.dialog_type
        if in_path.startswith('/'):
            path=os.path.join(self.LOCKED_DIR,in_path.lstrip('/'))
        else:
            path=os.path.join(self.current_path.get(),in_path)
        path=os.path.abspath(path)
        if os.path.commonpath([self.LOCKED_DIR, path]) != self.LOCKED_DIR:
            messagebox.showerror("Error",f"Path does not exist:\n{in_path}") # pretend it doesn't exist
            return
        for component in path.split('/'):
            component=component.strip()
            if component.startswith('.') and component not in ['..','.']:
                messagebox.showerror("Error",f"Path does not exist:\n{in_path}") # pretend it doesn't exist, disallow hidden folders
                return
        if os.path.isdir(path):
            self.current_path.set(path)
            current=self.current_path.get()
            self.push_history(path)
            self.list_files(path)
            if current.strip()==self.LOCKED_DIR.strip():
                self.up_btn.config(state="disabled")
            else:
                self.up_btn.config(state="normal")
            self.file_path_var.set("") # clear the entry box
            self.current_path.set(os.path.abspath(path))
            # lstripping / and then prepending / to ensure single leading /
            display_path='/'+(self.current_path.get().replace(self.LOCKED_DIR,'/')).lstrip('/')
            self.current_path_display.set(display_path)
        elif os.path.isfile(path):
            if self.dialog_type == self.Save:
                upperdir=display_path='/'+(os.path.dirname(path).replace(self.LOCKED_DIR,'/')).lstrip('/')
                self.goto(upperdir) # navigate only
                if messagebox.askquestion("Save File",f"Do you want to overwrite this file?\n{path}")=="yes":
                    self.completion_handler(path)
                    self.destroy()
            else:
                self.completion_handler(path)
                self.destroy()
        else:
            if self.dialog_type == self.Save:
                self.completion_handler(path)
                self.destroy()
            else:
                messagebox.showerror("Error",f"Path does not exist:\n{in_path}")


    def go_back(self):
        if self.history_index > 0:
            self.history_index-=1
            last_path = self.history[self.history_index]
            self.current_path.set(last_path)
            self.list_files(last_path)
            if self.history_index == 0: # if it becomes zero disable back button
                self.back_btn.config(state="disabled")
            self.forward_btn.config(state="normal")  # Enable forward button

    def go_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index+=1
            next_path = self.history[self.history_index]
            self.current_path.set(next_path)
            self.list_files(next_path)
            if self.history_index == len(self.history) - 1: # if it becomes zero disable back button
                self.forward_btn.config(state="disabled")
            self.back_btn.config(state="normal")  # Enable back button

    def go_up(self):
        upper_dir=os.path.dirname(self.current_path.get())
        if os.path.commonpath([self.LOCKED_DIR, upper_dir]) != self.LOCKED_DIR:
            return
        self.current_path.set(upper_dir)
        current=self.current_path.get()
        # lstripping / and then prepending / to ensure single leading /
        display_path='/'+(self.current_path.get().replace(self.LOCKED_DIR,'/')).lstrip('/')
        self.current_path_display.set(display_path)
        self.list_files(current)
        self.push_history(upper_dir)
        self.back_btn.config(state="normal")  # Enable back button
        self.forward_btn.config(state="disabled")  # Disable forward button
        if upper_dir.strip()==self.LOCKED_DIR.strip():
            self.up_btn.config(state="disabled")

    # history tools
    def push_history(self,path):
        if self.history_index!=len(self.history):
            self.history=self.history[:self.history_index+1]
        self.history.append(path)
        self.history_index=len(self.history)-1

    @staticmethod
    def open_file_dialog(root:Union[tk.Tk|tk.Toplevel],title="Open File",geometry="800x300"):
        result=None
        def completion_handler(path):
            nonlocal result
            result=path
        dialog=FileDialog(root,completion_handler,title,geometry,FileDialog.Open)
        root.wait_window(dialog)
        return result

    @staticmethod
    def save_file_dialog(root:Union[tk.Tk|tk.Toplevel],title="Save File",geometry="800x300"):
        result=None
        def completion_handler(path):
            nonlocal result
            result=path
        dialog=FileDialog(root,completion_handler,title,geometry,FileDialog.Save)
        root.wait_window(dialog)
        return result


if __name__ == "__main__":
    root = tk.Tk()
    #root.withdraw()  # Hide the root window

    print(FileDialog.open_file_dialog(root,title="Select a file to open"))

    root.mainloop()
