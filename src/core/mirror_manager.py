"""
Mirror source manager / 镜像源管理器
Supports APT, NPM, Pip, Git mirror configuration
支持 APT、NPM、Pip、Git 镜像源配置
"""
import os
import re
import shutil
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..utils.logger import logger
from ..utils.config import get_config_dir


class DistroType(Enum):
    """Linux distribution type / Linux 发行版类型"""
    DEBIAN = "debian"
    UBUNTU = "ubuntu"
    UNKNOWN = "unknown"


class ReleaseType(Enum):
    """Release type / 发行版本类型"""
    STABLE = "stable"
    TESTING = "testing"
    UNSTABLE = "unstable"
    SID = "sid"
    # Ubuntu releases
    FOCAL = "focal"         # 20.04
    JAMMY = "jammy"         # 22.04
    NOBLE = "noble"         # 24.04
    ORACULAR = "oracular"   # 24.10
    UNKNOWN = "unknown"


class MirrorProvider(Enum):
    """Mirror provider / 镜像源提供商"""
    TSINGHUA = "tsinghua"       # 清华源
    ALIYUN = "aliyun"           # 阿里源
    USTC = "ustc"               # 中科大源
    HUAWEI = "huawei"           # 华为源
    TENCENT = "tencent"         # 腾讯源
    OFFICIAL = "official"       # 官方源


@dataclass
class SourceInfo:
    """Source information / 源信息"""
    distro: DistroType
    release: str
    components: List[str]
    is_deb_src: bool = False


@dataclass
class MirrorConfig:
    """Mirror configuration / 镜像配置"""
    name: str
    name_zh: str
    apt_url: str
    npm_registry: str
    pip_index: str
    pip_trusted_host: str
    git_url: str = ""


# Mirror providers configuration / 镜像源提供商配置
MIRROR_PROVIDERS: Dict[MirrorProvider, MirrorConfig] = {
    MirrorProvider.TSINGHUA: MirrorConfig(
        name="Tsinghua",
        name_zh="清华大学",
        apt_url="https://mirrors.tuna.tsinghua.edu.cn",
        npm_registry="https://registry.npmmirror.com",
        pip_index="https://pypi.tuna.tsinghua.edu.cn/simple",
        pip_trusted_host="pypi.tuna.tsinghua.edu.cn",
        git_url="https://mirrors.tuna.tsinghua.edu.cn/git"
    ),
    MirrorProvider.ALIYUN: MirrorConfig(
        name="Aliyun",
        name_zh="阿里云",
        apt_url="https://mirrors.aliyun.com",
        npm_registry="https://registry.npmmirror.com",
        pip_index="https://mirrors.aliyun.com/pypi/simple",
        pip_trusted_host="mirrors.aliyun.com",
        git_url=""
    ),
    MirrorProvider.USTC: MirrorConfig(
        name="USTC",
        name_zh="中国科技大学",
        apt_url="https://mirrors.ustc.edu.cn",
        npm_registry="https://registry.npmmirror.com",
        pip_index="https://mirrors.ustc.edu.cn/pypi/web/simple",
        pip_trusted_host="mirrors.ustc.edu.cn",
        git_url=""
    ),
    MirrorProvider.HUAWEI: MirrorConfig(
        name="Huawei",
        name_zh="华为云",
        apt_url="https://repo.huaweicloud.com",
        npm_registry="https://registry.npmmirror.com",
        pip_index="https://repo.huaweicloud.com/repository/pypi/simple",
        pip_trusted_host="repo.huaweicloud.com",
        git_url=""
    ),
    MirrorProvider.TENCENT: MirrorConfig(
        name="Tencent",
        name_zh="腾讯云",
        apt_url="https://mirrors.cloud.tencent.com",
        npm_registry="https://mirrors.cloud.tencent.com/npm/",
        pip_index="https://mirrors.cloud.tencent.com/pypi/simple",
        pip_trusted_host="mirrors.cloud.tencent.com",
        git_url=""
    ),
}


class MirrorManager:
    """Mirror source manager / 镜像源管理器"""
    
    # APT sources file paths / APT 源文件路径
    SOURCES_LIST = Path("/etc/apt/sources.list")
    SOURCES_LIST_D = Path("/etc/apt/sources.list.d/")
    
    # Other config paths / 其他配置路径
    NPM_RC = Path.home() / ".npmrc"
    PIP_CONF = Path.home() / ".pip" / "pip.conf"
    PIP_CONF_ALT = Path.home() / ".config" / "pip" / "pip.conf"
    GIT_CONFIG = Path.home() / ".gitconfig"
    
    # Backup settings / 备份设置
    MAX_BACKUPS = 5
    
    def __init__(self):
        self.backup_dir = self._get_backup_dir()
    
    def _get_backup_dir(self) -> Path:
        """Get backup directory / 获取备份目录"""
        backup_dir = get_config_dir() / "backups" / "mirrors"
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir
    
    # ========== DETECTION / 检测 ==========
    
    def detect_distro(self) -> Tuple[DistroType, str]:
        """Detect Linux distribution / 检测 Linux 发行版"""
        try:
            os_release = Path("/etc/os-release")
            if os_release.exists():
                content = os_release.read_text()
                
                if "debian" in content.lower():
                    # Get version codename
                    match = re.search(r'VERSION_CODENAME=(\w+)', content)
                    codename = match.group(1) if match else "stable"
                    return DistroType.DEBIAN, codename
                
                elif "ubuntu" in content.lower():
                    match = re.search(r'VERSION_CODENAME=(\w+)', content)
                    codename = match.group(1) if match else "jammy"
                    return DistroType.UBUNTU, codename
        except Exception as e:
            logger.error(f"Failed to detect distro: {e}")
        
        return DistroType.UNKNOWN, "unknown"
    
    def detect_current_sources(self) -> List[SourceInfo]:
        """Detect current APT sources / 检测当前 APT 源"""
        sources = []
        
        if not self.SOURCES_LIST.exists():
            return sources
        
        try:
            content = self.SOURCES_LIST.read_text()
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Parse deb/deb-src line
                match = re.match(
                    r'^(deb(?:-src)?)\s+(?:\[.*?\]\s+)?(\S+)\s+(\S+)\s+(.+)$',
                    line
                )
                if match:
                    is_src = match.group(1) == "deb-src"
                    url = match.group(2)
                    release = match.group(3)
                    components = match.group(4).split()
                    
                    # Detect distro from URL
                    distro = DistroType.UNKNOWN
                    if "debian" in url.lower():
                        distro = DistroType.DEBIAN
                    elif "ubuntu" in url.lower():
                        distro = DistroType.UBUNTU
                    
                    sources.append(SourceInfo(
                        distro=distro,
                        release=release,
                        components=components,
                        is_deb_src=is_src
                    ))
        except Exception as e:
            logger.error(f"Failed to detect sources: {e}")
        
        return sources
    
    def get_current_mirror_info(self) -> Dict[str, str]:
        """Get current mirror info for all package managers / 获取所有包管理器当前镜像信息"""
        info = {
            "apt": "未检测到 / Not detected",
            "npm": "未检测到 / Not detected",
            "pip": "未检测到 / Not detected",
        }
        
        # APT
        if self.SOURCES_LIST.exists():
            try:
                content = self.SOURCES_LIST.read_text()
                for line in content.splitlines():
                    if line.strip().startswith('deb '):
                        match = re.search(r'https?://([^/\s]+)', line)
                        if match:
                            info["apt"] = match.group(1)
                            break
            except Exception:
                pass
        
        # NPM
        if self.NPM_RC.exists():
            try:
                content = self.NPM_RC.read_text()
                match = re.search(r'registry\s*=\s*(\S+)', content)
                if match:
                    info["npm"] = match.group(1)
            except Exception:
                pass
        
        # Pip
        for pip_conf in [self.PIP_CONF, self.PIP_CONF_ALT]:
            if pip_conf.exists():
                try:
                    content = pip_conf.read_text()
                    match = re.search(r'index-url\s*=\s*(\S+)', content)
                    if match:
                        info["pip"] = match.group(1)
                        break
                except Exception:
                    pass
        
        return info
    
    # ========== BACKUP / 备份 ==========
    
    def backup_all_sources(self) -> Optional[Path]:
        """Backup all source configurations / 备份所有源配置"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"mirrors_backup_{timestamp}.tar.gz"
            
            with tarfile.open(backup_file, "w:gz") as tar:
                # Backup APT sources
                if self.SOURCES_LIST.exists():
                    tar.add(self.SOURCES_LIST, arcname="apt/sources.list")
                
                if self.SOURCES_LIST_D.exists():
                    for f in self.SOURCES_LIST_D.glob("*.list"):
                        tar.add(f, arcname=f"apt/sources.list.d/{f.name}")
                
                # Backup NPM
                if self.NPM_RC.exists():
                    tar.add(self.NPM_RC, arcname="npm/.npmrc")
                
                # Backup Pip
                if self.PIP_CONF.exists():
                    tar.add(self.PIP_CONF, arcname="pip/pip.conf")
                elif self.PIP_CONF_ALT.exists():
                    tar.add(self.PIP_CONF_ALT, arcname="pip/pip.conf")
            
            # Cleanup old backups / 清理旧备份
            self._cleanup_old_backups()
            
            logger.info(f"Backup created: {backup_file}")
            return backup_file
        
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None
    
    def _cleanup_old_backups(self) -> None:
        """Clean up old backups / 清理旧备份"""
        backups = sorted(
            self.backup_dir.glob("mirrors_backup_*.tar.gz"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        for old_backup in backups[self.MAX_BACKUPS:]:
            try:
                old_backup.unlink()
                logger.info(f"Removed old backup: {old_backup}")
            except Exception as e:
                logger.warning(f"Failed to remove old backup: {e}")
    
    def list_backups(self) -> List[Path]:
        """List all backups / 列出所有备份"""
        return sorted(
            self.backup_dir.glob("mirrors_backup_*.tar.gz"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
    
    def restore_from_backup(self, backup_file: Path) -> bool:
        """Restore from backup / 从备份恢复"""
        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_file}")
            return False
        
        try:
            with tarfile.open(backup_file, "r:gz") as tar:
                # Extract to temp dir first
                temp_dir = self.backup_dir / "temp_restore"
                temp_dir.mkdir(exist_ok=True)
                tar.extractall(temp_dir)
                
                # Restore APT sources
                apt_sources = temp_dir / "apt" / "sources.list"
                if apt_sources.exists():
                    shutil.copy2(apt_sources, self.SOURCES_LIST)
                    logger.info("Restored: sources.list")
                
                apt_sources_d = temp_dir / "apt" / "sources.list.d"
                if apt_sources_d.exists():
                    for f in apt_sources_d.glob("*.list"):
                        shutil.copy2(f, self.SOURCES_LIST_D / f.name)
                        logger.info(f"Restored: {f.name}")
                
                # Restore NPM
                npm_rc = temp_dir / "npm" / ".npmrc"
                if npm_rc.exists():
                    shutil.copy2(npm_rc, self.NPM_RC)
                    logger.info("Restored: .npmrc")
                
                # Restore Pip
                pip_conf = temp_dir / "pip" / "pip.conf"
                if pip_conf.exists():
                    self.PIP_CONF.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(pip_conf, self.PIP_CONF)
                    logger.info("Restored: pip.conf")
                
                # Cleanup temp dir
                shutil.rmtree(temp_dir)
            
            logger.info(f"Restore completed from: {backup_file}")
            return True
        
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    # ========== CONFIGURE MIRRORS / 配置镜像源 ==========
    
    def configure_apt_mirror(self, provider: MirrorProvider) -> bool:
        """Configure APT mirror / 配置 APT 镜像源"""
        if provider not in MIRROR_PROVIDERS:
            logger.error(f"Unknown provider: {provider}")
            return False
        
        config = MIRROR_PROVIDERS[provider]
        distro, release = self.detect_distro()
        
        if distro == DistroType.UNKNOWN:
            logger.error("Cannot detect Linux distribution")
            return False
        
        try:
            # Read current sources
            if self.SOURCES_LIST.exists():
                original_content = self.SOURCES_LIST.read_text()
                
                # Comment out original lines / 注释掉原来的源
                commented_lines = []
                for line in original_content.splitlines():
                    if line.strip() and not line.strip().startswith('#'):
                        commented_lines.append(f"# [Original/原始] {line}")
                    else:
                        commented_lines.append(line)
                
                # Build new sources / 构建新源
                new_lines = [
                    f"# Mirror source configured by ProxyEnvCleaner",
                    f"# 镜像源由 ProxyEnvCleaner 配置",
                    f"# Provider: {config.name} / 提供商: {config.name_zh}",
                    f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    "",
                ]
                
                if distro == DistroType.DEBIAN:
                    base_url = f"{config.apt_url}/debian"
                    security_url = f"{config.apt_url}/debian-security"
                    
                    new_lines.extend([
                        f"deb {base_url} {release} main contrib non-free non-free-firmware",
                        f"deb {base_url} {release}-updates main contrib non-free non-free-firmware",
                        f"deb {base_url} {release}-backports main contrib non-free non-free-firmware",
                        f"deb {security_url} {release}-security main contrib non-free non-free-firmware",
                    ])
                
                elif distro == DistroType.UBUNTU:
                    base_url = f"{config.apt_url}/ubuntu"
                    
                    new_lines.extend([
                        f"deb {base_url} {release} main restricted universe multiverse",
                        f"deb {base_url} {release}-updates main restricted universe multiverse",
                        f"deb {base_url} {release}-backports main restricted universe multiverse",
                        f"deb {base_url} {release}-security main restricted universe multiverse",
                    ])
                
                # Combine new sources with commented original
                new_lines.extend(["", "# ========== Original Sources / 原始源 =========="])
                new_lines.extend(commented_lines)
                
                # Write new sources.list
                self.SOURCES_LIST.write_text("\n".join(new_lines))
                logger.info(f"APT mirror configured: {config.name}")
                return True
            
        except PermissionError:
            logger.error("需要 root 权限 / Root permission required")
            return False
        except Exception as e:
            logger.error(f"Failed to configure APT mirror: {e}")
            return False
        
        return False
    
    def configure_npm_mirror(self, provider: MirrorProvider) -> bool:
        """Configure NPM mirror / 配置 NPM 镜像源"""
        if provider not in MIRROR_PROVIDERS:
            return False
        
        config = MIRROR_PROVIDERS[provider]
        
        try:
            # Read existing config or create new
            existing_content = ""
            if self.NPM_RC.exists():
                existing_content = self.NPM_RC.read_text()
            
            # Remove old registry line
            lines = [l for l in existing_content.splitlines() 
                     if not l.strip().startswith('registry')]
            
            # Add new registry
            lines.insert(0, f"registry={config.npm_registry}")
            
            self.NPM_RC.write_text("\n".join(lines))
            logger.info(f"NPM mirror configured: {config.npm_registry}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to configure NPM mirror: {e}")
            return False
    
    def configure_pip_mirror(self, provider: MirrorProvider) -> bool:
        """Configure Pip mirror / 配置 Pip 镜像源"""
        if provider not in MIRROR_PROVIDERS:
            return False
        
        config = MIRROR_PROVIDERS[provider]
        
        try:
            pip_conf = self.PIP_CONF
            pip_conf.parent.mkdir(parents=True, exist_ok=True)
            
            content = f"""[global]
index-url = {config.pip_index}
trusted-host = {config.pip_trusted_host}

[install]
trusted-host = {config.pip_trusted_host}
"""
            pip_conf.write_text(content)
            logger.info(f"Pip mirror configured: {config.pip_index}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to configure Pip mirror: {e}")
            return False
    
    def configure_all_mirrors(self, 
                              apt_provider: Optional[MirrorProvider] = None,
                              npm_provider: Optional[MirrorProvider] = None,
                              pip_provider: Optional[MirrorProvider] = None) -> Dict[str, bool]:
        """Configure all mirrors / 配置所有镜像源"""
        results = {}
        
        # Backup first / 先备份
        backup = self.backup_all_sources()
        results["backup"] = backup is not None
        
        # Configure APT
        if apt_provider:
            results["apt"] = self.configure_apt_mirror(apt_provider)
        
        # Configure NPM
        if npm_provider:
            results["npm"] = self.configure_npm_mirror(npm_provider)
        
        # Configure Pip
        if pip_provider:
            results["pip"] = self.configure_pip_mirror(pip_provider)
        
        return results


def get_mirror_manager() -> MirrorManager:
    """Get mirror manager instance / 获取镜像源管理器实例"""
    return MirrorManager()


def get_available_providers() -> List[Tuple[MirrorProvider, str, str]]:
    """Get available mirror providers / 获取可用的镜像源提供商"""
    return [
        (provider, config.name, config.name_zh)
        for provider, config in MIRROR_PROVIDERS.items()
    ]
