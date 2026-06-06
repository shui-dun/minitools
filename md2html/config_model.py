from dataclasses import dataclass, field

# 含义参见config.template.toml
@dataclass
class Config:
    notes_dir: str
    output_dir: str
    site_name: str
    site_language: str
    theme_palette: str
    nginx_port: int
    docker_host_port: int
    ignore_dirs: list[str] = field(default_factory=list)
    server_remote: str = ""
    server_work_tree: str = ""
