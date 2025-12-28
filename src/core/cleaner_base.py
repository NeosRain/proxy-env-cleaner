"""
Base cleaner class / 清理器基类
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class CleanStatus(Enum):
    """Clean status enum / 清理状态枚举"""
    SUCCESS = "success"         # 成功 / Success
    FAILED = "failed"           # 失败 / Failed
    SKIPPED = "skipped"         # 跳过 / Skipped
    NOT_FOUND = "not_found"     # 未找到 / Not found


@dataclass
class CleanResult:
    """Clean result / 清理结果"""
    item: str                   # 清理项目 / Clean item
    status: CleanStatus         # 状态 / Status
    message_zh: str             # 中文消息 / Chinese message
    message_en: str             # 英文消息 / English message
    details: Optional[str] = None  # 详细信息 / Details
    
    def get_message(self) -> str:
        """Get bilingual message / 获取双语消息"""
        return f"{self.message_zh} / {self.message_en}"


@dataclass
class DetectResult:
    """Detection result / 检测结果"""
    item: str                   # 检测项目 / Detection item
    found: bool                 # 是否找到 / Found
    value: Optional[str] = None # 当前值 / Current value
    message_zh: str = ""        # 中文消息 / Chinese message
    message_en: str = ""        # 英文消息 / English message


@dataclass
class CleanReport:
    """Clean report / 清理报告"""
    results: List[CleanResult] = field(default_factory=list)
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    
    def add_result(self, result: CleanResult) -> None:
        """Add clean result / 添加清理结果"""
        self.results.append(result)
        if result.status == CleanStatus.SUCCESS:
            self.success_count += 1
        elif result.status == CleanStatus.FAILED:
            self.failed_count += 1
        else:
            self.skipped_count += 1
    
    def get_summary_zh(self) -> str:
        """Get Chinese summary / 获取中文摘要"""
        return f"清理完成: 成功 {self.success_count}, 失败 {self.failed_count}, 跳过 {self.skipped_count}"
    
    def get_summary_en(self) -> str:
        """Get English summary / 获取英文摘要"""
        return f"Clean completed: Success {self.success_count}, Failed {self.failed_count}, Skipped {self.skipped_count}"
    
    def get_summary(self) -> str:
        """Get bilingual summary / 获取双语摘要"""
        return f"{self.get_summary_zh()}\n{self.get_summary_en()}"


class BaseCleaner(ABC):
    """Base cleaner abstract class / 清理器抽象基类"""
    
    @abstractmethod
    def detect_all(self) -> List[DetectResult]:
        """Detect all proxy settings / 检测所有代理设置"""
        pass
    
    @abstractmethod
    def clean_system_proxy(self) -> CleanResult:
        """Clean system proxy / 清理系统代理"""
        pass
    
    @abstractmethod
    def clean_env_variables(self) -> CleanResult:
        """Clean environment variables / 清理环境变量"""
        pass
    
    @abstractmethod
    def clean_git_proxy(self) -> CleanResult:
        """Clean Git proxy / 清理 Git 代理"""
        pass
    
    def clean_all(self) -> CleanReport:
        """Clean all proxy settings / 清理所有代理设置"""
        report = CleanReport()
        
        # Clean system proxy / 清理系统代理
        report.add_result(self.clean_system_proxy())
        
        # Clean environment variables / 清理环境变量
        report.add_result(self.clean_env_variables())
        
        # Clean Git proxy / 清理 Git 代理
        report.add_result(self.clean_git_proxy())
        
        return report
