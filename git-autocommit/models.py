from dataclasses import dataclass
from datetime import datetime

@dataclass
class RepoConfig:
    path: str
    interval_minutes: int # 提交间隔（分钟）
    do_pull: bool = True # 是否拉取远程仓库最新代码，默认True
    do_push: bool = True # 是否推送到远程仓库，默认True

@dataclass
class RepoTask:
    config: RepoConfig
    next_run: datetime # 下次运行时间
    
    def __lt__(self, other):
        """定义小于比较，优先队列会用这个方法排序"""
        return self.next_run < other.next_run