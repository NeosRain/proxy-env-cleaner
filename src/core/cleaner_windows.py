"""
Windows cleaner implementation / Windows 清理器实现
"""
import os
import subprocess
import re
from typing import List, Optional
from pathlib import Path

from .cleaner_base import (
    BaseCleaner, CleanResult, CleanStatus, DetectResult, CleanReport
)
from ..utils.logger import logger


class WindowsCleaner(BaseCleaner):
    """Windows proxy cleaner / Windows 代理清理器"""
    
    # Proxy environment variable names / 代理环境变量名
    PROXY_ENV_VARS = [
        "http_proxy", "HTTP_PROXY",
        "https_proxy", "HTTPS_PROXY",
        "all_proxy", "ALL_PROXY",
        "no_proxy", "NO_PROXY",
        "ftp_proxy", "FTP_PROXY",
        "socks_proxy", "SOCKS_PROXY",
    ]
    
    # Config file paths / 配置文件路径
    NPM_RC = Path.home() / ".npmrc"
    YARN_RC = Path.home() / ".yarnrc"
    PIP_DIR = Path.home() / "pip"
    PIP_CONF = PIP_DIR / "pip.ini"
    APPDATA_PIP = Path(os.environ.get("APPDATA", "")) / "pip" / "pip.ini"
    
    def detect_all(self) -> List[DetectResult]:
        """Detect all proxy settings / 检测所有代理设置"""
        results = []
        
        # Detect system proxy / 检测系统代理
        results.append(self._detect_system_proxy())
        
        # Detect environment variables / 检测环境变量
        results.extend(self._detect_env_variables())
        
        # Detect Git proxy / 检测 Git 代理
        results.append(self._detect_git_proxy())
        
        # Detect npm/yarn/pip proxy / 检测 npm/yarn/pip 代理
        results.extend(self._detect_package_manager_proxy())
        
        # Detect UWP loopback / 检测 UWP 回环
        results.append(self._detect_uwp_loopback())
        
        return results
    
    def _detect_system_proxy(self) -> DetectResult:
        """Detect Windows system proxy / 检测 Windows 系统代理"""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                0, winreg.KEY_READ
            )
            
            proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
            proxy_server = ""
            try:
                proxy_server, _ = winreg.QueryValueEx(key, "ProxyServer")
            except FileNotFoundError:
                pass
            
            winreg.CloseKey(key)
            
            if proxy_enable:
                return DetectResult(
                    item="system_proxy",
                    found=True,
                    value=proxy_server,
                    message_zh=f"系统代理已启用: {proxy_server}",
                    message_en=f"System proxy enabled: {proxy_server}"
                )
            else:
                return DetectResult(
                    item="system_proxy",
                    found=False,
                    message_zh="系统代理未启用",
                    message_en="System proxy not enabled"
                )
        except Exception as e:
            logger.error(f"Failed to detect system proxy: {e}")
            return DetectResult(
                item="system_proxy",
                found=False,
                message_zh=f"检测失败: {e}",
                message_en=f"Detection failed: {e}"
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
    
    def clean_system_proxy(self) -> CleanResult:
        """Clean Windows system proxy / 清理 Windows 系统代理"""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                0, winreg.KEY_SET_VALUE
            )
            
            # Disable proxy / 禁用代理
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            
            # Clear proxy server / 清除代理服务器
            try:
                winreg.DeleteValue(key, "ProxyServer")
            except FileNotFoundError:
                pass
            
            # Clear proxy override / 清除代理例外
            try:
                winreg.DeleteValue(key, "ProxyOverride")
            except FileNotFoundError:
                pass
            
            winreg.CloseKey(key)
            
            # Notify system of changes / 通知系统设置已更改
            self._refresh_internet_settings()
            
            logger.info("System proxy cleaned successfully")
            return CleanResult(
                item="system_proxy",
                status=CleanStatus.SUCCESS,
                message_zh="系统代理已清理",
                message_en="System proxy cleaned"
            )
        except Exception as e:
            logger.error(f"Failed to clean system proxy: {e}")
            return CleanResult(
                item="system_proxy",
                status=CleanStatus.FAILED,
                message_zh=f"清理系统代理失败: {e}",
                message_en=f"Failed to clean system proxy: {e}"
            )
    
    def _refresh_internet_settings(self) -> None:
        """Refresh Windows internet settings / 刷新 Windows 网络设置"""
        try:
            import ctypes
            INTERNET_OPTION_REFRESH = 37
            INTERNET_OPTION_SETTINGS_CHANGED = 39
            
            internet_set_option = ctypes.windll.Wininet.InternetSetOptionW
            internet_set_option(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
            internet_set_option(0, INTERNET_OPTION_REFRESH, 0, 0)
        except Exception as e:
            logger.warning(f"Failed to refresh internet settings: {e}")
    
    def clean_env_variables(self) -> CleanResult:
        """Clean proxy environment variables / 清理代理环境变量"""
        cleaned = []
        failed = []
        
        for var in self.PROXY_ENV_VARS:
            try:
                # Clean from current process / 从当前进程清理
                if var in os.environ:
                    del os.environ[var]
                
                # Clean from user environment (registry) / 从用户环境清理（注册表）
                self._remove_user_env_var(var)
                cleaned.append(var)
            except Exception as e:
                logger.error(f"Failed to clean env var {var}: {e}")
                failed.append(var)
        
        if failed:
            return CleanResult(
                item="env_variables",
                status=CleanStatus.FAILED,
                message_zh=f"部分环境变量清理失败: {', '.join(failed)}",
                message_en=f"Some env vars failed to clean: {', '.join(failed)}"
            )
        
        logger.info(f"Environment variables cleaned: {cleaned}")
        return CleanResult(
            item="env_variables",
            status=CleanStatus.SUCCESS,
            message_zh="环境变量已清理",
            message_en="Environment variables cleaned"
        )
    
    def _remove_user_env_var(self, var_name: str) -> None:
        """Remove user environment variable from registry / 从注册表删除用户环境变量"""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Environment",
                0, winreg.KEY_SET_VALUE | winreg.KEY_READ
            )
            try:
                winreg.DeleteValue(key, var_name)
            except FileNotFoundError:
                pass  # Variable doesn't exist
            winreg.CloseKey(key)
        except Exception as e:
            logger.debug(f"Could not remove {var_name} from registry: {e}")
    
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
    
    # ========== NEW DETECTION METHODS / 新检测方法 ==========
    
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
        for pip_conf in [self.PIP_CONF, self.APPDATA_PIP]:
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
    
    def _detect_uwp_loopback(self) -> DetectResult:
        """检测 UWP 回环设置 / Detect UWP loopback settings"""
        try:
            result = subprocess.run(
                ["CheckNetIsolation", "LoopbackExempt", "-s"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                lines = [l for l in result.stdout.strip().split('\n') if l.strip()]
                if len(lines) > 1:  # Has exemptions
                    return DetectResult(
                        item="uwp_loopback",
                        found=True,
                        value=f"{len(lines)-1} apps",
                        message_zh=f"UWP 回环豁免: {len(lines)-1} 个应用",
                        message_en=f"UWP loopback exempt: {len(lines)-1} apps"
                    )
        except Exception:
            pass
        
        return DetectResult(
            item="uwp_loopback",
            found=False,
            message_zh="UWP 回环无豁免",
            message_en="No UWP loopback exemptions"
        )
    
    # ========== NEW CLEAN METHODS / 新清理方法 ==========
    
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
        
        for pip_conf in [self.PIP_CONF, self.APPDATA_PIP]:
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
    
    def flush_dns_cache(self) -> CleanResult:
        """刷新 DNS 缓存 / Flush DNS cache"""
        try:
            result = subprocess.run(
                ["ipconfig", "/flushdns"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                logger.info("DNS cache flushed successfully")
                return CleanResult(
                    item="dns_cache",
                    status=CleanStatus.SUCCESS,
                    message_zh="DNS 缓存已刷新",
                    message_en="DNS cache flushed"
                )
        except Exception as e:
            logger.error(f"Failed to flush DNS cache: {e}")
        
        return CleanResult(
            item="dns_cache",
            status=CleanStatus.FAILED,
            message_zh="刷新 DNS 缓存失败",
            message_en="Failed to flush DNS cache"
        )
    
    def reset_winsock(self) -> CleanResult:
        """重置 Winsock 目录 / Reset Winsock catalog"""
        try:
            # Note: This requires admin privileges / 注意：需要管理员权限
            result = subprocess.run(
                ["netsh", "winsock", "reset"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                logger.info("Winsock reset successfully")
                return CleanResult(
                    item="winsock_reset",
                    status=CleanStatus.SUCCESS,
                    message_zh="Winsock 已重置 (建议重启)",
                    message_en="Winsock reset (restart recommended)"
                )
        except Exception as e:
            logger.error(f"Failed to reset Winsock: {e}")
        
        return CleanResult(
            item="winsock_reset",
            status=CleanStatus.SKIPPED,
            message_zh="Winsock 重置需要管理员权限",
            message_en="Winsock reset requires admin"
        )
    
    def clean_all(self) -> CleanReport:
        """清理所有代理设置 / Clean all proxy settings"""
        report = CleanReport()
        
        # Clean system proxy / 清理系统代理
        report.add_result(self.clean_system_proxy())
        
        # Clean environment variables / 清理环境变量
        report.add_result(self.clean_env_variables())
        
        # Clean Git proxy / 清理 Git 代理
        report.add_result(self.clean_git_proxy())
        
        # Clean npm/yarn proxy / 清理 npm/yarn 代理
        report.add_result(self.clean_npm_proxy())
        
        # Clean pip proxy / 清理 pip 代理
        report.add_result(self.clean_pip_proxy())
        
        # Flush DNS cache / 刷新 DNS 缓存
        report.add_result(self.flush_dns_cache())
        
        return report
