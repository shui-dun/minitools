import customtkinter as ctk
import tkinter as tk
import subprocess
import sys
import shlex
from tkinter import messagebox
from config_manager import ConfigManager
from config_editor import ConfigEditor

class AppLauncherFrame(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("应用启动器")
        self.geometry("400x500")

        self.config_manager = ConfigManager()
        self.categories = self.config_manager.get_categories()

        # Grid layout
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # Title label
        title_label = ctk.CTkLabel(self, text="一键启动器",
                                   font=ctk.CTkFont(size=18, weight="bold"))
        title_label.grid(row=0, column=0, padx=10, pady=10)

        # Category listbox
        self.list_box = tk.Listbox(self, height=15, exportselection=False,
                                   font=("Microsoft YaHei UI", 14))
        self.update_list_box()
        self.list_box.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # Button row
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        launch_button = ctk.CTkButton(button_frame, text="启动", command=self.on_launch)
        launch_button.grid(row=0, column=0, padx=(0, 5), pady=0, sticky="ew")

        config_button = ctk.CTkButton(button_frame, text="配置", command=self.on_config)
        config_button.grid(row=0, column=1, padx=(5, 0), pady=0, sticky="ew")

        # Bind events
        self.list_box.bind('<Double-Button-1>', self.on_launch)

        # Keyboard shortcuts: Ctrl+1 through Ctrl+9
        for i in range(1, 10):
            self.bind(f'<Control-Key-{i}>', lambda e, idx=i-1: self.launch_by_index(idx))

    def update_list_box(self):
        self.list_box.delete(0, tk.END)
        for i, category in enumerate(self.categories):
            if i < 9:
                self.list_box.insert(tk.END, f"{i+1}. {category}")
            else:
                self.list_box.insert(tk.END, f"   {category}")

    def launch_by_index(self, index):
        if index < len(self.categories):
            self.list_box.selection_clear(0, tk.END)
            self.list_box.selection_set(index)
            self.list_box.see(index)
            self.launch_selected_category()

    def launch_selected_category(self):
        selection = self.list_box.curselection()
        if selection:
            idx = selection[0]
            category = self.categories[idx]
            apps = self.config_manager.get_apps_for_category(category)

            launch_success = True
            for app_command in apps:
                try:
                    if sys.platform == 'win32':
                        subprocess.Popen(app_command, shell=True)
                    else:
                        args = shlex.split(app_command)
                        subprocess.Popen(args)
                except Exception as e:
                    launch_success = False
                    messagebox.showerror("错误", f"无法启动应用 {app_command}: {str(e)}")

            if launch_success:
                self.destroy()

    def on_launch(self, event=None):
        self.launch_selected_category()

    def on_config(self):
        config_editor = ConfigEditor(self, self.config_manager)
        config_editor.show_modal()
        self.categories = self.config_manager.get_categories()
        self.update_list_box()


def run_app():
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = AppLauncherFrame()
    app.mainloop()


if __name__ == "__main__":
    run_app()
