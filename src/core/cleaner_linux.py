"""
Linux cleaner implementation / Linux 清理器实现
"""
import os
import subprocess
import re
import shutil
import glob
from datetime import datetime
from typing import List, Optional, Tuple
from pathlib import Path

from .cleaner_base import (
    BaseCleaner, CleanResult, CleanStatus, DetectResult, CleanReport
)
from ..utils.logger import logger
from ..utils.config import get_config_dir

# 隐藏 subprocess 窗口的全局配置 / Global config to hide subprocess windows
# This was a leftover from Windows code - Linux doesn't need this
SUBPROCESS_FLAGS = 0  # Remove this as we use run_hidden from subprocess_utils instead

class LinuxCleaner(BaseCleaner):
    """Linux proxy cleaner / Linux 代理清理器"""
    
    # Proxy environment variable names / 代理环境变量名
    PROXY_ENV_VARS = [
        "http_proxy", "HTTP_PROXY",
        "https_proxy", "HTTPS_PROXY",
        "all_proxy", "ALL_PROXY",
        "no_proxy", "NO_PROXY",
        "ftp_proxy", "FTP_PROXY",
        "socks_proxy", "SOCKS_PROXY",
    ]
    
    # Config files that may contain proxy settings / 可能包含代理设置的配置文件
    ENV_FILES = [
        Path.home() / ".bashrc",
        Path.home() / ".bash_profile",
        Path.home() / ".profile",
        Path.home() / ".zshrc",
        Path.home() / ".config" / "fish" / "config.fish",
        Path("/etc/environment"),
    ]
    
    # APT proxy files / APT 代理文件
    APT_PROXY_FILE = Path("/etc/apt/apt.conf.d/proxy.conf")
    APT_PROXY_FILES = [
        Path("/etc/apt/apt.conf.d/proxy.conf"),
        Path("/etc/apt/apt.conf.d/00proxy"),
        Path("/etc/apt/apt.conf.d/01proxy"),
        Path("/etc/apt/apt.conf"),
    ]
    
    # Software source files / 软件源文件
    SOURCES_LIST = Path("/etc/apt/sources.list")
    SOURCES_LIST_D = Path("/etc/apt/sources.list.d/")
    
    # KDE config files / KDE 配置文件
    KDE_PROXY_RC = Path.home() / ".config" / "kioslaverc"
    KDE5_PROXY_RC = Path.home() / ".config" / "kiorc"
    
    # Other app configs / 其他应用配置
    NPM_RC = Path.home() / ".npmrc"
    YARN_RC = Path.home() / ".yarnrc"
    PIP_CONF = Path.home() / ".pip" / "pip.conf"
    PIP_CONF_ALT = Path.home() / ".config" / "pip" / "pip.conf"
    DOCKER_CONFIG = Path.home() / ".docker" / "config.json"
    WGET_RC = Path.home() / ".wgetrc"
    CURL_RC = Path.home() / ".curlrc"
    
    # Backup settings / 备份设置
    MAX_BACKUPS = 5
    
    def detect_all(self) -> List[DetectResult]:
        """Detect all proxy settings / 检测所有代理设置"""
        results = []
        
        # Detect GNOME/KDE system proxy / 检测 GNOME/KDE 系统代理
        results.append(self._detect_desktop_proxy())
        
        # Detect KDE apps proxy / 检测 KDE 应用代理
        results.append(self._detect_kde_apps_proxy())
        
        # Detect environment variables / 检测环境变量
        results.extend(self._detect_env_variables())
        
        # Detect Git proxy / 检测 Git 代理
        results.append(self._detect_git_proxy())
        
        # Detect APT proxy / 检测 APT 代理
        results.extend(self._detect_all_apt_proxy())
        
        # Detect sources.list proxy / 检测软件源代理
        results.append(self._detect_sources_proxy())
        
        # Detect npm/yarn/pip proxy / 检测 npm/yarn/pip 代理
        results.extend(self._detect_package_manager_proxy())
        
        # Detect wget/curl proxy / 检测 wget/curl 代理
        results.extend(self._detect_download_tools_proxy())
        
        return results
    
    def _detect_desktop_proxy(self) -> DetectResult:
        """Detect GNOME/KDE desktop proxy / 检测 GNOME/KDE 桌面代理"""
        # Try GNOME gsettings / 尝试 GNOME gsettings
        try:
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.system.proxy", "mode"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                mode = result.stdout.strip().strip("'")
                if mode != "none":
                    return DetectResult(
                        item="desktop_proxy",
                        found=True,
                        value=mode,
                        message_zh=f"GNOME 系统代理模式: {mode}",
                        message_en=f"GNOME system proxy mode: {mode}"
                    )
        except Exception:
            pass
        
        return DetectResult(
            item="desktop_proxy",
            found=False,
            message_zh="桌面代理未设置",
            message_en="Desktop proxy not set"
        )
    
    def _detect_env_variables(self) -> List[DetectResult]:
        """Detect proxy environment variables / 检测代理环境变量"""
        results = []
        for var in self.PROXY_ENV_VARS:
            value = os.environ.get(var)
            if value:
                results.append(DetectResult(
                    item=f"env_{var}",
                    found=True,
                    value=value,
                    message_zh=f"环境变量 {var}={value}",
                    message_en=f"Environment variable {var}={value}"
                ))
        return results
    
    def _detect_git_proxy(self) -> DetectResult:
        """Detect Git proxy / 检测 Git 代理"""
        try:
            result = subprocess.run(
                ["git", "config", "--global", "--get", "http.proxy"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return DetectResult(
                    item="git_proxy",
                    found=True,
                    value=result.stdout.strip(),
                    message_zh=f"Git 代理已设置: {result.stdout.strip()}",
                    message_en=f"Git proxy set: {result.stdout.strip()}"
                )
        except Exception as e:
            logger.debug(f"Git proxy detection failed: {e}")
        
        return DetectResult(
            item="git_proxy",
            found=False,
            message_zh="Git 代理未设置",
            message_en="Git proxy not set"
        )
    
    def _detect_apt_proxy(self) -> DetectResult:
        """Detect APT proxy / 检测 APT 代理"""
        if self.APT_PROXY_FILE.exists():
            try:
                content = self.APT_PROXY_FILE.read_text()
                if content.strip():
                    return DetectResult(
                        item="apt_proxy",
                        found=True,
                        value=content.strip()[:100],
                        message_zh="APT 代理已配置",
                        message_en="APT proxy configured"
                    )
            except Exception as e:
                logger.debug(f"APT proxy detection failed: {e}")
        
        return DetectResult(
            item="apt_proxy",
            found=False,
            message_zh="APT 代理未设置",
            message_en="APT proxy not set"
        )
    
    def clean_system_proxy(self) -> CleanResult:
        """Clean Linux desktop system proxy / 清理 Linux 桌面系统代理"""
        cleaned = False
        
        # Clean GNOME proxy / 清理 GNOME 代理
        try:
            subprocess.run(
                ["gsettings", "set", "org.gnome.system.proxy", "mode", "none"],
                capture_output=True, timeout=5
            )
            cleaned = True
            logger.info("GNOME proxy cleaned")
        except Exception as e:
            logger.debug(f"GNOME proxy clean failed: {e}")
        
        # Clean KDE proxy / 清理 KDE 代理
        try:
            kwriteconfig = "kwriteconfig5"
            subprocess.run(
                [kwriteconfig, "--file", "kioslaverc", "--group", "Proxy Settings",
                 "--key", "ProxyType", "0"],
                capture_output=True, timeout=5
            )
            cleaned = True
            logger.info("KDE proxy cleaned")
        except Exception as e:
            logger.debug(f"KDE proxy clean failed: {e}")
        
        if cleaned:
            return CleanResult(
                item="system_proxy",
                status=CleanStatus.SUCCESS,
                message_zh="桌面系统代理已清理",
                message_en="Desktop system proxy cleaned"
            )
        else:
            return CleanResult(
                item="system_proxy",
                status=CleanStatus.SKIPPED,
                message_zh="未检测到桌面代理设置",
                message_en="No desktop proxy settings detected"
            )
    
    def clean_env_variables(self) -> CleanResult:
        """Clean proxy environment variables / 清理代理环境变量"""
        cleaned_files = []
        
        # Clean from current process / 从当前进程清理
        for var in self.PROXY_ENV_VARS:
            if var in os.environ:
                del os.environ[var]
        
        # Clean from config files / 从配置文件清理
        for env_file in self.ENV_FILES:
            if env_file.exists() and self._can_write(env_file):
                try:
                    if self._clean_proxy_from_file(env_file):
                        cleaned_files.append(str(env_file))
                except PermissionError:
                    logger.warning(f"Permission denied when cleaning {env_file}, skipping...")
                except Exception as e:
                    logger.error(f"Failed to clean {env_file}: {e}")
        
        logger.info(f"Environment variables cleaned from: {cleaned_files}")
        return CleanResult(
            item="env_variables",
            status=CleanStatus.SUCCESS,
            message_zh=f"环境变量已清理 ({len(cleaned_files)} 个文件)",
            message_en=f"Environment variables cleaned ({len(cleaned_files)} files)",
            details=", ".join(cleaned_files) if cleaned_files else None
        )
    
    def _can_write(self, file_path: Path) -> bool:
        """Check if file is writable / 检查文件是否可写"""
        if file_path.exists():
            return os.access(file_path, os.W_OK)
        return os.access(file_path.parent, os.W_OK)
    
    def _clean_proxy_from_file(self, file_path: Path) -> bool:
        """Clean proxy settings from file / 从文件清理代理设置"""
        try:
            content = file_path.read_text()
            original_content = content
            
            # Pattern to match proxy export lines / 匹配代理导出行的模式
            proxy_patterns = [
                r'^export\s+(https?_proxy|HTTP_PROXY|HTTPS_PROXY|all_proxy|ALL_PROXY|no_proxy|NO_PROXY|ftp_proxy|FTP_PROXY)=.*$',
                r'^(https?_proxy|HTTP_PROXY|HTTPS_PROXY|all_proxy|ALL_PROXY|no_proxy|NO_PROXY|ftp_proxy|FTP_PROXY)=.*$',
            ]
            
            for pattern in proxy_patterns:
                content = re.sub(pattern, '', content, flags=re.MULTILINE)
            
            # Remove extra blank lines / 删除多余空行
            content = re.sub(r'\n{3,}', '\n\n', content)
            
            if content != original_content:
                file_path.write_text(content)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to clean proxy from {file_path}: {e}")
            return False
    
    def clean_git_proxy(self) -> CleanResult:
        """Clean Git proxy settings / 清理 Git 代理设置"""
        try:
            # Remove http.proxy / 删除 http.proxy
            subprocess.run(
                ["git", "config", "--global", "--unset", "http.proxy"],
                capture_output=True, timeout=5
            )
            
            # Remove https.proxy / 删除 https.proxy
            subprocess.run(
                ["git", "config", "--global", "--unset", "https.proxy"],
                capture_output=True, timeout=5
            )
            
            logger.info("Git proxy cleaned successfully")
            return CleanResult(
                item="git_proxy",
                status=CleanStatus.SUCCESS,
                message_zh="Git 代理已清理",
                message_en="Git proxy cleaned"
            )
        except FileNotFoundError:
            return CleanResult(
                item="git_proxy",
                status=CleanStatus.SKIPPED,
                message_zh="Git 未安装",
                message_en="Git not installed"
            )
        except Exception as e:
            logger.error(f"Failed to clean Git proxy: {e}")
            return CleanResult(
                item="git_proxy",
                status=CleanStatus.FAILED,
                message_zh=f"清理 Git 代理失败: {e}",
                message_en=f"Failed to clean Git proxy: {e}"
            )
    
    def clean_apt_proxy(self) -> CleanResult:
        """Clean APT proxy settings / 清理 APT 代理设置"""
        if not self.APT_PROXY_FILE.exists():
            return CleanResult(
                item="apt_proxy",
                status=CleanStatus.SKIPPED,
                message_zh="APT 代理文件不存在",
                message_en="APT proxy file does not exist"
            )
        
        try:
            # Need root permission / 需要 root 权限
            if os.name != 'nt' and os.geteuid() == 0:
                self.APT_PROXY_FILE.unlink()
                logger.info("APT proxy cleaned successfully")
                return CleanResult(
                    item="apt_proxy",
                    status=CleanStatus.SUCCESS,
                    message_zh="APT 代理已清理",
                    message_en="APT proxy cleaned"
                )
            else:
                return CleanResult(
                    item="apt_proxy",
                    status=CleanStatus.SKIPPED,
                    message_zh="需要 root 权限清理 APT 代理",
                    message_en="Root permission required to clean APT proxy"
                )
        except Exception as e:
            logger.error(f"Failed to clean APT proxy: {e}")
            return CleanResult(
                item="apt_proxy",
                status=CleanStatus.FAILED,
                message_zh=f"清理 APT 代理失败: {e}",
                message_en=f"Failed to clean APT proxy: {e}"
            )
    
    def clean_all(self) -> CleanReport:
        """Clean all proxy settings / 清理所有代理设置"""
        report = CleanReport()
        
        # Backup sources.list first / 先备份软件源
        backup_result = self.backup_sources_list()
        if backup_result:
            report.add_result(backup_result)
        
        # Clean system proxy / 清理系统代理
        report.add_result(self.clean_system_proxy())
        
        # Clean KDE apps proxy / 清理 KDE 应用代理
        report.add_result(self.clean_kde_apps_proxy())
        
        # Clean environment variables / 清理环境变量
        report.add_result(self.clean_env_variables())
        
        # Clean Git proxy / 清理 Git 代理
        report.add_result(self.clean_git_proxy())
        
        # Clean all APT proxy files / 清理所有 APT 代理文件
        report.add_result(self.clean_all_apt_proxy())
        
        # Clean sources.list proxy / 清理软件源代理
        report.add_result(self.clean_sources_proxy())
        
        # Clean npm/yarn/pip proxy / 清理 npm/yarn/pip 代理
        report.add_result(self.clean_npm_proxy())
        report.add_result(self.clean_pip_proxy())
        
        # Clean wget/curl proxy / 清理 wget/curl 代理
        report.add_result(self.clean_download_tools_proxy())
        
        return report
    
    # ========== NEW DETECTION METHODS / 新检测方法 ==========
    
    def _detect_kde_apps_proxy(self) -> DetectResult:
        """检测 KDE 应用代理设置 / Detect KDE apps proxy settings"""
        for kde_file in [self.KDE_PROXY_RC, self.KDE5_PROXY_RC]:
            if kde_file.exists():
                try:
                    content = kde_file.read_text()
                    if 'ProxyType' in content and 'ProxyType=0' not in content:
                        return DetectResult(
                            item="kde_apps_proxy",
                            found=True,
                            value=str(kde_file),
                            message_zh="KDE 应用代理已设置",
                            message_en="KDE apps proxy is set"
                        )
                except Exception:
                    pass
        
        return DetectResult(
            item="kde_apps_proxy",
            found=False,
            message_zh="KDE 应用代理未设置",
            message_en="KDE apps proxy not set"
        )
    
    def _detect_all_apt_proxy(self) -> List[DetectResult]:
        """检测所有 APT 代理文件 / Detect all APT proxy files"""
        results = []
        for apt_file in self.APT_PROXY_FILES:
            if apt_file.exists():
                try:
                    content = apt_file.read_text()
                    if 'Acquire::' in content and 'proxy' in content.lower():
                        results.append(DetectResult(
                            item=f"apt_proxy_{apt_file.name}",
                            found=True,
                            value=content.strip()[:100],
                            message_zh=f"APT 代理文件: {apt_file}",
                            message_en=f"APT proxy file: {apt_file}"
                        ))
                except Exception:
                    pass
        
        if not results:
            results.append(DetectResult(
                item="apt_proxy",
                found=False,
                message_zh="APT 代理未设置",
                message_en="APT proxy not set"
            ))
        return results
    
    def _detect_sources_proxy(self) -> DetectResult:
        """检测软件源是否使用代理 / Detect if sources.list uses proxy"""
        proxy_indicators = ['http://127.0.0.1', 'http://localhost', ':7890', ':1080', ':8080', ':10809']
        
        sources_files = [self.SOURCES_LIST]
        if self.SOURCES_LIST_D.exists():
            sources_files.extend(self.SOURCES_LIST_D.glob('*.list'))
        
        for src_file in sources_files:
            if src_file.exists():
                try:
                    content = src_file.read_text()
                    for indicator in proxy_indicators:
                        if indicator in content:
                            return DetectResult(
                                item="sources_proxy",
                                found=True,
                                value=f"{src_file}: {indicator}",
                                message_zh=f"软件源可能使用代理: {src_file}",
                                message_en=f"Sources may use proxy: {src_file}"
                            )
                except Exception:
                    pass
        
        return DetectResult(
            item="sources_proxy",
            found=False,
            message_zh="软件源未使用代理",
            message_en="Sources not using proxy"
        )
    
    def _detect_package_manager_proxy(self) -> List[DetectResult]:
        """检测 npm/yarn/pip 代理 / Detect npm/yarn/pip proxy"""
        results = []
        
        # NPM proxy
        if self.NPM_RC.exists():
            try:
                content = self.NPM_RC.read_text()
                if 'proxy' in content.lower():
                    results.append(DetectResult(
                        item="npm_proxy",
                        found=True,
                        value="~/.npmrc",
                        message_zh="NPM 代理已设置",
                        message_en="NPM proxy is set"
                    ))
            except Exception:
                pass
        
        # Yarn proxy
        if self.YARN_RC.exists():
            try:
                content = self.YARN_RC.read_text()
                if 'proxy' in content.lower():
                    results.append(DetectResult(
                        item="yarn_proxy",
                        found=True,
                        value="~/.yarnrc",
                        message_zh="Yarn 代理已设置",
                        message_en="Yarn proxy is set"
                    ))
            except Exception:
                pass
        
        # Pip proxy
        for pip_conf in [self.PIP_CONF, self.PIP_CONF_ALT]:
            if pip_conf.exists():
                try:
                    content = pip_conf.read_text()
                    if 'proxy' in content.lower():
                        results.append(DetectResult(
                            item="pip_proxy",
                            found=True,
                            value=str(pip_conf),
                            message_zh="Pip 代理已设置",
                            message_en="Pip proxy is set"
                        ))
                        break
                except Exception:
                    pass
        
        return results
    
    def _detect_download_tools_proxy(self) -> List[DetectResult]:
        """检测 wget/curl 代理 / Detect wget/curl proxy"""
        results = []
        
        # Wget
        if self.WGET_RC.exists():
            try:
                content = self.WGET_RC.read_text()
                if 'proxy' in content.lower():
                    results.append(DetectResult(
                        item="wget_proxy",
                        found=True,
                        value="~/.wgetrc",
                        message_zh="Wget 代理已设置",
                        message_en="Wget proxy is set"
                    ))
            except Exception:
                pass
        
        # Curl
        if self.CURL_RC.exists():
            try:
                content = self.CURL_RC.read_text()
                if 'proxy' in content.lower():
                    results.append(DetectResult(
                        item="curl_proxy",
                        found=True,
                        value="~/.curlrc",
                        message_zh="Curl 代理已设置",
                        message_en="Curl proxy is set"
                    ))
            except Exception:
                pass
        
        return results
    
    # ========== BACKUP METHODS / 备份方法 ==========
    
    def _get_backup_dir(self) -> Path:
        """获取备份目录 / Get backup directory"""
        backup_dir = get_config_dir() / "backups" / "sources"
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir
    
    def _cleanup_old_backups(self, backup_dir: Path) -> None:
        """清理旧备份，保留最新的5个 / Cleanup old backups, keep latest 5"""
        backups = sorted(backup_dir.glob("sources_*.tar.gz"), key=lambda x: x.stat().st_mtime, reverse=True)
        for old_backup in backups[self.MAX_BACKUPS:]:
            try:
                old_backup.unlink()
                logger.info(f"Removed old backup: {old_backup}")
            except Exception as e:
                logger.warning(f"Failed to remove old backup {old_backup}: {e}")
    
    def backup_sources_list(self) -> Optional[CleanResult]:
        """备份软件源 / Backup sources.list"""
        if not self.SOURCES_LIST.exists():
            return None
        
        try:
            import tarfile
            
            backup_dir = self._get_backup_dir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"sources_{timestamp}.tar.gz"
            
            with tarfile.open(backup_file, "w:gz") as tar:
                # Backup sources.list
                if self.SOURCES_LIST.exists():
                    tar.add(self.SOURCES_LIST, arcname="sources.list")
                
                # Backup sources.list.d
                if self.SOURCES_LIST_D.exists():
                    for f in self.SOURCES_LIST_D.glob("*.list"):
                        tar.add(f, arcname=f"sources.list.d/{f.name}")
            
            # Cleanup old backups
            self._cleanup_old_backups(backup_dir)
            
            logger.info(f"Sources backed up to: {backup_file}")
            return CleanResult(
                item="backup_sources",
                status=CleanStatus.SUCCESS,
                message_zh=f"软件源已备份: {backup_file.name}",
                message_en=f"Sources backed up: {backup_file.name}",
                details=str(backup_file)
            )
        except Exception as e:
            logger.error(f"Failed to backup sources: {e}")
            return CleanResult(
                item="backup_sources",
                status=CleanStatus.FAILED,
                message_zh=f"备份软件源失败: {e}",
                message_en=f"Failed to backup sources: {e}"
            )
    
    # ========== NEW CLEAN METHODS / 新清理方法 ==========
    
    def clean_kde_apps_proxy(self) -> CleanResult:
        """清理 KDE 应用代理 / Clean KDE apps proxy"""
        cleaned = False
        
        # Clean via kwriteconfig5/kwriteconfig6
        for kwrite in ["kwriteconfig6", "kwriteconfig5"]:
            try:
                # Set ProxyType to 0 (No Proxy)
                subprocess.run(
                    [kwrite, "--file", "kioslaverc", "--group", "Proxy Settings",
                     "--key", "ProxyType", "0"],
                    capture_output=True, timeout=5
                )
                subprocess.run(
                    [kwrite, "--file", "kiorc", "--group", "Proxy Settings",
                     "--key", "ProxyType", "0"],
                    capture_output=True, timeout=5
                )
                cleaned = True
                break
            except Exception:
                continue
        
        # Also clean config files directly
        for kde_file in [self.KDE_PROXY_RC, self.KDE5_PROXY_RC]:
            if kde_file.exists():
                try:
                    content = kde_file.read_text()
                    # Set ProxyType=0
                    content = re.sub(r'ProxyType=\d+', 'ProxyType=0', content)
                    kde_file.write_text(content)
                    cleaned = True
                except Exception as e:
                    logger.debug(f"Failed to clean {kde_file}: {e}")
        
        if cleaned:
            return CleanResult(
                item="kde_apps_proxy",
                status=CleanStatus.SUCCESS,
                message_zh="KDE 应用代理已清理",
                message_en="KDE apps proxy cleaned"
            )
        else:
            return CleanResult(
                item="kde_apps_proxy",
                status=CleanStatus.SKIPPED,
                message_zh="未检测到 KDE 应用代理",
                message_en="No KDE apps proxy detected"
            )
    
    def clean_all_apt_proxy(self) -> CleanResult:
        """清理所有 APT 代理文件 / Clean all APT proxy files"""
        cleaned = []
        need_root = False
        
        for apt_file in self.APT_PROXY_FILES:
            if apt_file.exists():
                try:
                    if self._can_write(apt_file):
                        # Read and clean proxy lines
                        content = apt_file.read_text()
                        new_content = re.sub(r'^Acquire::.*proxy.*$', '', content, flags=re.MULTILINE | re.IGNORECASE)
                        new_content = re.sub(r'\n{3,}', '\n\n', new_content)
                        
                        if new_content.strip():
                            apt_file.write_text(new_content)
                        else:
                            apt_file.unlink()
                        cleaned.append(str(apt_file))
                    else:
                        need_root = True
                except Exception as e:
                    logger.error(f"Failed to clean {apt_file}: {e}")
        
        if cleaned:
            return CleanResult(
                item="apt_proxy_all",
                status=CleanStatus.SUCCESS,
                message_zh=f"APT 代理已清理 ({len(cleaned)} 个文件)",
                message_en=f"APT proxy cleaned ({len(cleaned)} files)"
            )
        elif need_root:
            return CleanResult(
                item="apt_proxy_all",
                status=CleanStatus.SKIPPED,
                message_zh="需要 root 权限清理 APT 代理",
                message_en="Root permission required for APT proxy"
            )
        else:
            return CleanResult(
                item="apt_proxy_all",
                status=CleanStatus.SKIPPED,
                message_zh="未检测到 APT 代理",
                message_en="No APT proxy detected"
            )
    
    def clean_sources_proxy(self) -> CleanResult:
        """清理软件源中的代理地址 / Clean proxy addresses in sources.list"""
        # Note: This is risky, only clean obvious proxy patterns
        # 注意：这比较危险，只清理明显的代理模式
        proxy_patterns = [
            r'http://127\.0\.0\.1:\d+',
            r'http://localhost:\d+',
        ]
        
        cleaned_files = []
        
        sources_files = []
        if self.SOURCES_LIST.exists() and self._can_write(self.SOURCES_LIST):
            sources_files.append(self.SOURCES_LIST)
        
        for src_file in sources_files:
            try:
                content = src_file.read_text()
                original = content
                
                for pattern in proxy_patterns:
                    content = re.sub(pattern, '', content)
                
                if content != original:
                    src_file.write_text(content)
                    cleaned_files.append(str(src_file))
            except Exception as e:
                logger.error(f"Failed to clean sources proxy from {src_file}: {e}")
        
        if cleaned_files:
            return CleanResult(
                item="sources_proxy",
                status=CleanStatus.SUCCESS,
                message_zh=f"软件源代理已清理",
                message_en=f"Sources proxy cleaned"
            )
        else:
            return CleanResult(
                item="sources_proxy",
                status=CleanStatus.SKIPPED,
                message_zh="软件源无需清理",
                message_en="Sources need no cleaning"
            )
    
    def clean_npm_proxy(self) -> CleanResult:
        """清理 NPM/Yarn 代理 / Clean NPM/Yarn proxy"""
        cleaned = []
        
        # Clean npm config
        try:
            subprocess.run(["npm", "config", "delete", "proxy"], capture_output=True, timeout=5)
            subprocess.run(["npm", "config", "delete", "https-proxy"], capture_output=True, timeout=5)
            cleaned.append("npm")
        except Exception:
            pass
        
        # Clean npmrc file
        if self.NPM_RC.exists():
            try:
                content = self.NPM_RC.read_text()
                new_content = re.sub(r'^(https?-)?proxy=.*$', '', content, flags=re.MULTILINE)
                new_content = re.sub(r'\n{3,}', '\n\n', new_content)
                self.NPM_RC.write_text(new_content)
                cleaned.append(".npmrc")
            except Exception:
                pass
        
        # Clean yarnrc file
        if self.YARN_RC.exists():
            try:
                content = self.YARN_RC.read_text()
                new_content = re.sub(r'^(https?-)?proxy.*$', '', content, flags=re.MULTILINE)
                new_content = re.sub(r'\n{3,}', '\n\n', new_content)
                self.YARN_RC.write_text(new_content)
                cleaned.append(".yarnrc")
            except Exception:
                pass
        
        if cleaned:
            return CleanResult(
                item="npm_yarn_proxy",
                status=CleanStatus.SUCCESS,
                message_zh=f"NPM/Yarn 代理已清理",
                message_en=f"NPM/Yarn proxy cleaned"
            )
        else:
            return CleanResult(
                item="npm_yarn_proxy",
                status=CleanStatus.SKIPPED,
                message_zh="NPM/Yarn 代理未设置",
                message_en="NPM/Yarn proxy not set"
            )
    
    def clean_pip_proxy(self) -> CleanResult:
        """清理 Pip 代理 / Clean Pip proxy"""
        cleaned = []
        
        for pip_conf in [self.PIP_CONF, self.PIP_CONF_ALT]:
            if pip_conf.exists():
                try:
                    content = pip_conf.read_text()
                    new_content = re.sub(r'^proxy\s*=.*$', '', content, flags=re.MULTILINE)
                    new_content = re.sub(r'\n{3,}', '\n\n', new_content)
                    pip_conf.write_text(new_content)
                    cleaned.append(str(pip_conf))
                except Exception:
                    pass
        
        if cleaned:
            return CleanResult(
                item="pip_proxy",
                status=CleanStatus.SUCCESS,
                message_zh="Pip 代理已清理",
                message_en="Pip proxy cleaned"
            )
        else:
            return CleanResult(
                item="pip_proxy",
                status=CleanStatus.SKIPPED,
                message_zh="Pip 代理未设置",
                message_en="Pip proxy not set"
            )
    
    def clean_download_tools_proxy(self) -> CleanResult:
        """清理 wget/curl 代理 / Clean wget/curl proxy"""
        cleaned = []
        
        # Clean wgetrc
        if self.WGET_RC.exists():
            try:
                content = self.WGET_RC.read_text()
                new_content = re.sub(r'^(https?_proxy|use_proxy)\s*=.*$', '', content, flags=re.MULTILINE | re.IGNORECASE)
                new_content = re.sub(r'\n{3,}', '\n\n', new_content)
                self.WGET_RC.write_text(new_content)
                cleaned.append(".wgetrc")
            except Exception:
                pass
        
        # Clean curlrc
        if self.CURL_RC.exists():
            try:
                content = self.CURL_RC.read_text()
                new_content = re.sub(r'^(-x|--proxy|proxy)\s*.*$', '', content, flags=re.MULTILINE | re.IGNORECASE)
                new_content = re.sub(r'\n{3,}', '\n\n', new_content)
                self.CURL_RC.write_text(new_content)
                cleaned.append(".curlrc")
            except Exception:
                pass
        
        if cleaned:
            return CleanResult(
                item="download_tools_proxy",
                status=CleanStatus.SUCCESS,
                message_zh=f"Wget/Curl 代理已清理",
                message_en=f"Wget/Curl proxy cleaned"
            )
        else:
            return CleanResult(
                item="download_tools_proxy",
                status=CleanStatus.SKIPPED,
                message_zh="Wget/Curl 代理未设置",
                message_en="Wget/Curl proxy not set"
            )
