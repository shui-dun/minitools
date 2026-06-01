import customtkinter as ctk
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

        self.list_frame = ctk.CTkScrollableFrame(self)
        self.list_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self._list_buttons = []
        self._selected_index = -1
        self.update_list_box()

        # Button row
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        launch_button = ctk.CTkButton(button_frame, text="启动", command=self.on_launch)
        launch_button.grid(row=0, column=0, padx=(0, 5), pady=0, sticky="ew")

        config_button = ctk.CTkButton(button_frame, text="配置", command=self.on_config)
        config_button.grid(row=0, column=1, padx=(5, 0), pady=0, sticky="ew")

        # Keyboard shortcuts: Ctrl+1 through Ctrl+9
        for i in range(1, 10):
            self.bind(f'<Control-Key-{i}>', lambda e, idx=i-1: self._launch_by_index(idx))

    def update_list_box(self):
        for btn in self._list_buttons:
            btn.destroy()
        self._list_buttons.clear()
        self._selected_index = -1

        for i, category in enumerate(self.categories):
            text = f"{i+1}. {category}" if i < 9 else f"   {category}"
            btn = ctk.CTkButton(
                self.list_frame,
                text=text,
                anchor="w",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                corner_radius=0,
                command=lambda idx=i: self._select_item(idx)
            )
            btn.bind('<Double-Button-1>', lambda e, idx=i: self._launch_by_index(idx))
            btn.pack(fill="x", padx=0, pady=1)
            self._list_buttons.append(btn)

    def _select_item(self, index):
        if 0 <= self._selected_index < len(self._list_buttons):
            self._list_buttons[self._selected_index].configure(fg_color="transparent")
        self._selected_index = index
        if 0 <= index < len(self._list_buttons):
            self._list_buttons[index].configure(fg_color=("gray75", "gray28"))

    def _launch_by_index(self, index):
        if index < len(self.categories):
            self._select_item(index)
            self.launch_selected_category()

    def launch_selected_category(self):
        if self._selected_index < 0 or self._selected_index >= len(self.categories):
            return

        category = self.categories[self._selected_index]
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

    def on_launch(self):
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
