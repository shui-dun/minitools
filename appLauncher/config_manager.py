import os
import json
import sys

class ConfigManager:
    def __init__(self, config_file=None):
        if config_file is None:
            # 获取程序所在目录
            self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        else:
            self.config_file = config_file
            
        # 默认配置
        self.default_config = {
            "学习": [],
            "娱乐": []
        }
        
        # 加载配置
        self.config = self.load_config()
    
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {str(e)}")
                return self.default_config.copy()
        else:
            return self.default_config.copy()
    
    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {str(e)}")
            return False
    
    def get_categories(self):
        return list(self.config.keys())
    
    def get_apps_for_category(self, category):
        return self.config.get(category, [])
    
    def add_category(self, category):
        if category not in self.config:
            self.config[category] = []
            return True
        return False
    
    def remove_category(self, category):
        if category in self.config:
            del self.config[category]
            return True
        return False
    
    def add_app_to_category(self, category, app_path):
        if category in self.config and app_path not in self.config[category]:
            self.config[category].append(app_path)
            return True
        return False
    
    def remove_app_from_category(self, category, app_path):
        if category in self.config and app_path in self.config[category]:
            self.config[category].remove(app_path)
            return True
        return False
    
    def update_category_name(self, old_name, new_name):
        if old_name in self.config and new_name != old_name:
            self.config[new_name] = self.config.pop(old_name)
            return True
        return False
