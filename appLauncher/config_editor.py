import customtkinter as ctk
import tkinter as tk
import os
from tkinter import messagebox

class ConfigEditor(ctk.CTkToplevel):
    def __init__(self, parent, config_manager):
        super().__init__(parent)
        self.title("配置编辑器")
        self.geometry("800x500")

        self.config_manager = config_manager
        self.result = None

        # Make dialog modal
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

        # Grid layout
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ---- Category bar (row 0) ----
        category_frame = ctk.CTkFrame(self, fg_color="transparent")
        category_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        category_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(category_frame, text="选择分类：").grid(
            row=0, column=0, padx=5, pady=5, sticky="w")

        self._category_values = self.config_manager.get_categories()
        self.category_choice = ctk.CTkOptionMenu(
            category_frame, values=self._category_values,
            command=self.on_category_selected)
        self.category_choice.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(category_frame, text="添加分类",
                      command=self.on_add_category).grid(
                          row=0, column=2, padx=5, pady=5)
        ctk.CTkButton(category_frame, text="重命名",
                      command=self.on_rename_category).grid(
                          row=0, column=3, padx=5, pady=5)
        ctk.CTkButton(category_frame, text="删除分类",
                      command=self.on_remove_category).grid(
                          row=0, column=4, padx=5, pady=5)

        # ---- App list label (row 1) ----
        ctk.CTkLabel(self, text="该分类中的应用:").grid(
            row=1, column=0, padx=5, pady=(0, 0), sticky="w")

        # ---- App listbox (row 2) ----
        self.app_listbox = tk.Listbox(self, height=10, exportselection=False,
                                      font=("Microsoft YaHei UI", 14))
        self.app_listbox.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
        self.app_listbox.bind('<<ListboxSelect>>', self.on_app_selected)

        # ---- Path entry row (row 3) ----
        path_frame = ctk.CTkFrame(self, fg_color="transparent")
        path_frame.grid(row=3, column=0, padx=5, pady=5, sticky="ew")
        path_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(path_frame, text="应用路径:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w")

        self.path_text = ctk.CTkEntry(path_frame)
        self.path_text.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # ---- App button row (row 4) ----
        app_button_frame = ctk.CTkFrame(self, fg_color="transparent")
        app_button_frame.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
        app_button_frame.grid_columnconfigure(0, weight=1)
        app_button_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(app_button_frame, text="添加应用",
                      command=self.on_add_app).grid(
                          row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(app_button_frame, text="删除应用",
                      command=self.on_remove_app).grid(
                          row=0, column=1, padx=5, pady=5, sticky="ew")

        # ---- Bottom button row (row 5) ----
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=5, column=0, padx=5, pady=(5, 10), sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(bottom_frame, text="保存",
                      command=self.on_save).grid(
                          row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(bottom_frame, text="取消",
                      command=self.on_cancel).grid(
                          row=0, column=1, padx=5, pady=5, sticky="ew")

        # Initialize app list
        self.update_app_list()

    def show_modal(self):
        self.grab_set()
        self.wait_window()
        return self.result

    def _get_category_selection_index(self):
        """Return the selected index in category values, or -1 if none/empty."""
        if not self._category_values:
            return -1
        val = self.category_choice.get()
        try:
            return self._category_values.index(val)
        except ValueError:
            return -1

    def update_app_list(self):
        self.app_listbox.delete(0, tk.END)
        sel = self._get_category_selection_index()
        if sel != -1:
            category = self._category_values[sel]
            for app in self.config_manager.get_apps_for_category(category):
                self.app_listbox.insert(tk.END, app)

    def on_category_selected(self, value):
        self.update_app_list()

    def on_add_category(self):
        dialog = ctk.CTkInputDialog(text="输入新分类名称:", title="添加分类")
        category_name = dialog.get_input()
        if category_name:
            category_name = category_name.strip()
            if self.config_manager.add_category(category_name):
                self._category_values.append(category_name)
                self.category_choice.configure(values=self._category_values)
                self.category_choice.set(category_name)
                self.update_app_list()
            else:
                messagebox.showinfo("提示", "分类已存在")

    def on_remove_category(self):
        sel = self._get_category_selection_index()
        if sel != -1:
            category = self._category_values[sel]
            if messagebox.askyesno("确认", f"确定要删除分类 '{category}' 吗?"):
                if self.config_manager.remove_category(category):
                    del self._category_values[sel]
                    self.category_choice.configure(values=self._category_values)
                    if self._category_values:
                        self.category_choice.set(self._category_values[0])
                    self.update_app_list()

    def on_rename_category(self):
        sel = self._get_category_selection_index()
        if sel != -1:
            old_name = self._category_values[sel]
            dialog = ctk.CTkInputDialog(text="输入新分类名称:", title="重命名分类")
            new_name = dialog.get_input()
            if new_name:
                new_name = new_name.strip()
                if new_name and new_name != old_name:
                    if self.config_manager.update_category_name(old_name, new_name):
                        self._category_values[sel] = new_name
                        self.category_choice.configure(values=self._category_values)
                        self.category_choice.set(new_name)
                        self.update_app_list()

    def on_app_selected(self, event=None):
        selection = self.app_listbox.curselection()
        if selection:
            app_path = self.app_listbox.get(selection[0])
            self.path_text.delete(0, tk.END)
            self.path_text.insert(0, app_path)

    def on_add_app(self):
        sel = self._get_category_selection_index()
        if sel != -1:
            category = self._category_values[sel]
            app_path = self.path_text.get().strip()
            if app_path:
                if self.config_manager.add_app_to_category(category, app_path):
                    self.app_listbox.insert(tk.END, app_path)
                    self.path_text.delete(0, tk.END)
                else:
                    messagebox.showinfo("提示", "该应用已存在")
            else:
                messagebox.showinfo("提示", "请输入有效的应用路径")

    def on_remove_app(self):
        category_idx = self._get_category_selection_index()
        app_sel = self.app_listbox.curselection()
        if category_idx != -1 and app_sel:
            app_idx = app_sel[0]
            category = self._category_values[category_idx]
            app_path = self.app_listbox.get(app_idx)
            if self.config_manager.remove_app_from_category(category, app_path):
                self.app_listbox.delete(app_idx)
                self.path_text.delete(0, tk.END)

    def on_save(self):
        if self.config_manager.save_config():
            messagebox.showinfo("成功", "配置已保存")
            self.result = True
            self.destroy()
        else:
            messagebox.showerror("错误", "保存配置失败")

    def on_cancel(self):
        self.config_manager.load_config()
        self.result = False
        self.destroy()
