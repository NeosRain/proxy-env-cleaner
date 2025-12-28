"""
Mirror source manager / 镜像源管理器
Supports APT, NPM, Pip, Snap mirror configuration
支持 APT、NPM、Pip、Snap 镜像源配置
"""
import os
import re
import json
import shutil
import tarfile
import subprocess
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..utils.logger import logger
from ..utils.config import get_config_dir


# 在线配置 URL / Online config URL
ONLINE_CONFIG_URL = "https://raw.githubusercontent.com/NeosRain/proxy-env-cleaner/main/mirrors.json"


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
    snap_url: str = ""
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
        snap_url="https://mirrors.tuna.tsinghua.edu.cn/snapcraft",
        git_url="https://mirrors.tuna.tsinghua.edu.cn/git"
    ),
    MirrorProvider.ALIYUN: MirrorConfig(
        name="Aliyun",
        name_zh="阿里云",
        apt_url="https://mirrors.aliyun.com",
        npm_registry="https://registry.npmmirror.com",
        pip_index="https://mirrors.aliyun.com/pypi/simple",
        pip_trusted_host="mirrors.aliyun.com",
        snap_url="",
        git_url=""
    ),
    MirrorProvider.USTC: MirrorConfig(
        name="USTC",
        name_zh="中国科技大学",
        apt_url="https://mirrors.ustc.edu.cn",
        npm_registry="https://registry.npmmirror.com",
        pip_index="https://mirrors.ustc.edu.cn/pypi/web/simple",
        pip_trusted_host="mirrors.ustc.edu.cn",
        snap_url="https://mirrors.ustc.edu.cn/snapcraft",
        git_url=""
    ),
    MirrorProvider.HUAWEI: MirrorConfig(
        name="Huawei",
        name_zh="华为云",
        apt_url="https://repo.huaweicloud.com",
        npm_registry="https://registry.npmmirror.com",
        pip_index="https://repo.huaweicloud.com/repository/pypi/simple",
        pip_trusted_host="repo.huaweicloud.com",
        snap_url="",
        git_url=""
    ),
    MirrorProvider.TENCENT: MirrorConfig(
        name="Tencent",
        name_zh="腾讯云",
        apt_url="https://mirrors.cloud.tencent.com",
        npm_registry="https://mirrors.cloud.tencent.com/npm/",
        pip_index="https://mirrors.cloud.tencent.com/pypi/simple",
        pip_trusted_host="mirrors.cloud.tencent.com",
        snap_url="",
        git_url=""
    ),
}


def fetch_online_mirrors() -> Optional[Dict]:
    """从网上获取最新镜像源配置 / Fetch latest mirror config from online"""
    try:
        req = urllib.request.Request(
            ONLINE_CONFIG_URL,
            headers={'User-Agent': 'ProxyEnvCleaner/1.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            logger.info("已获取在线镜像源配置 / Online mirror config fetched")
            return data
    except urllib.error.URLError as e:
        logger.warning(f"无法获取在线配置 / Cannot fetch online config: {e}")
    except json.JSONDecodeError as e:
        logger.warning(f"解析在线配置失败 / Failed to parse online config: {e}")
    except Exception as e:
        logger.warning(f"获取在线配置异常 / Error fetching online config: {e}")
    return None


def get_mirror_config(provider: MirrorProvider, online_data: Optional[Dict] = None) -> MirrorConfig:
    """获取镜像源配置，优先使用在线数据 / Get mirror config, prefer online data"""
    # 使用在线数据优先 / Use online data first
    if online_data and 'providers' in online_data:
        provider_key = provider.value
        if provider_key in online_data['providers']:
            p = online_data['providers'][provider_key]
            return MirrorConfig(
                name=p.get('name', MIRROR_PROVIDERS[provider].name),
                name_zh=p.get('name_zh', MIRROR_PROVIDERS[provider].name_zh),
                apt_url=p.get('apt_url', MIRROR_PROVIDERS[provider].apt_url),
                npm_registry=p.get('npm_registry', MIRROR_PROVIDERS[provider].npm_registry),
                pip_index=p.get('pip_index', MIRROR_PROVIDERS[provider].pip_index),
                pip_trusted_host=p.get('pip_trusted_host', MIRROR_PROVIDERS[provider].pip_trusted_host),
                snap_url=p.get('snap_url', MIRROR_PROVIDERS[provider].snap_url),
                git_url=p.get('git_url', MIRROR_PROVIDERS[provider].git_url),
            )
    # 回退到本地配置 / Fallback to local config
    return MIRROR_PROVIDERS[provider]


class MirrorManager:
    """Mirror source manager / 镜像源管理器"""
    
    # APT sources file paths / APT 源文件路径
    SOURCES_LIST = Path("/etc/apt/sources.list")
    SOURCES_LIST_D = Path("/etc/apt/sources.list.d/")
    
    # Other config paths / 其他配置路径
    NPM_RC = Path.home() / ".npmrc"
    PIP_CONF = Path.home() / ".pip" / "pip.conf"
    PIP_CONF_ALT = Path.home() / ".config" / "pip" / "pip.conf"
    # Windows pip config
    PIP_CONF_WIN = Path(os.environ.get("APPDATA", "")) / "pip" / "pip.ini"
    GIT_CONFIG = Path.home() / ".gitconfig"
    
    # Snap config / Snap 配置
    SNAP_AUTH_JSON = Path("/var/snap/snap-store/common/snap-auth.json")
    SNAPD_ENV = Path("/etc/environment")
    
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
        """获取所有包管理器当前镜像信息 / Get current mirror info for all package managers"""
        info = {
            "apt": "未检测到 / Not detected",
            "npm": "未检测到 / Not detected",
            "pip": "未检测到 / Not detected",
            "yarn": "未检测到 / Not detected",
            "snap": "未检测到 / Not detected",
        }
        
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        
        # APT - Linux only
        if os.name != 'nt' and self.SOURCES_LIST.exists():
            try:
                content = self.SOURCES_LIST.read_text()
                for line in content.splitlines():
                    if line.strip().startswith('deb ') and not line.strip().startswith('#'):
                        match = re.search(r'https?://([^/\s]+)', line)
                        if match:
                            info["apt"] = match.group(1)
                            break
            except Exception:
                pass
        elif os.name == 'nt':
            info["apt"] = "N/A (Windows)"
        
        # NPM - 多种检测方式
        npm_detected = False
        # 方法 1: npm config get registry
        try:
            result = subprocess.run(
                ["npm", "config", "get", "registry"],
                capture_output=True, text=True, timeout=10,
                creationflags=creationflags
            )
            if result.returncode == 0 and result.stdout.strip():
                registry = result.stdout.strip()
                if registry and registry != "undefined" and "http" in registry:
                    info["npm"] = registry
                    npm_detected = True
        except Exception:
            pass
        
        # 方法 2: 检查 .npmrc 文件
        if not npm_detected and self.NPM_RC.exists():
            try:
                content = self.NPM_RC.read_text()
                match = re.search(r'registry\s*=\s*"?([^"\s\n]+)', content)
                if match:
                    info["npm"] = match.group(1)
                    npm_detected = True
            except Exception:
                pass
        
        # 方法 3: npm config list 
        if not npm_detected:
            try:
                result = subprocess.run(
                    ["npm", "config", "list"],
                    capture_output=True, text=True, timeout=10,
                    creationflags=creationflags
                )
                if result.returncode == 0:
                    match = re.search(r'registry\s*=\s*"?([^"\s\n]+)', result.stdout)
                    if match:
                        info["npm"] = match.group(1)
            except Exception:
                pass
        
        # Pip - 多种检测方式
        pip_detected = False
        # 方法 1: pip config get global.index-url
        try:
            result = subprocess.run(
                ["pip", "config", "get", "global.index-url"],
                capture_output=True, text=True, timeout=10,
                creationflags=creationflags
            )
            if result.returncode == 0 and result.stdout.strip():
                url = result.stdout.strip()
                if "http" in url:
                    info["pip"] = url
                    pip_detected = True
        except Exception:
            pass
        
        # 方法 2: pip config list
        if not pip_detected:
            try:
                result = subprocess.run(
                    ["pip", "config", "list"],
                    capture_output=True, text=True, timeout=10,
                    creationflags=creationflags
                )
                if result.returncode == 0:
                    match = re.search(r"global\.index-url\s*=\s*'?([^'\s\n]+)", result.stdout)
                    if match:
                        info["pip"] = match.group(1)
                        pip_detected = True
            except Exception:
                pass
        
        # 方法 3: 检查配置文件
        if not pip_detected:
            pip_configs = [self.PIP_CONF, self.PIP_CONF_ALT]
            if os.name == 'nt':
                pip_configs.insert(0, self.PIP_CONF_WIN)
            
            for pip_conf in pip_configs:
                if pip_conf.exists():
                    try:
                        content = pip_conf.read_text()
                        match = re.search(r'index-url\s*=\s*(\S+)', content, re.IGNORECASE)
                        if match:
                            info["pip"] = match.group(1)
                            break
                    except Exception:
                        pass
        
        # Yarn 检测
        try:
            result = subprocess.run(
                ["yarn", "config", "get", "registry"],
                capture_output=True, text=True, timeout=10,
                creationflags=creationflags
            )
            if result.returncode == 0 and result.stdout.strip():
                registry = result.stdout.strip()
                if "http" in registry:
                    info["yarn"] = registry
        except Exception:
            pass
        
        # Snap - Linux only
        if os.name != 'nt':
            try:
                env_path = Path("/etc/environment")
                if env_path.exists():
                    content = env_path.read_text()
                    match = re.search(r'SNAPPY_FORCE_API_URL\s*=\s*"?([^"\n]+)', content)
                    if match:
                        info["snap"] = match.group(1)
                    elif re.search(r'SNAPPY_STORE_NO_CDN\s*=\s*1', content):
                        info["snap"] = "CDN 已禁用 / CDN disabled"
            except Exception:
                pass
        else:
            info["snap"] = "N/A (Windows)"
        
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
    
    def configure_snap_mirror(self, provider: MirrorProvider) -> bool:
        """配置 Snap 镜像源 / Configure Snap mirror"""
        if provider not in MIRROR_PROVIDERS:
            return False
        
        config = MIRROR_PROVIDERS[provider]
        
        if not config.snap_url:
            logger.warning(f"{config.name} 不支持 Snap 镜像 / {config.name} doesn't support Snap mirror")
            return False
        
        try:
            env_file = Path("/etc/environment")
            
            # Read existing content
            existing_content = ""
            if env_file.exists():
                existing_content = env_file.read_text()
            
            # Remove old snap settings
            lines = []
            for line in existing_content.splitlines():
                if not any(x in line for x in ['SNAPPY_STORE_NO_CDN', 'SNAPPY_FORCE_API_URL']):
                    lines.append(line)
            
            # Add new settings
            # Snap 使用国内源需要设置这两个变量
            lines.append(f'SNAPPY_FORCE_API_URL="{config.snap_url}"')
            lines.append('SNAPPY_STORE_NO_CDN=1')
            
            env_file.write_text("\n".join(lines) + "\n")
            logger.info(f"Snap mirror configured: {config.snap_url}")
            return True
        
        except PermissionError:
            logger.error("需要 root 权限 / Root permission required for Snap")
            return False
        except Exception as e:
            logger.error(f"Failed to configure Snap mirror: {e}")
            return False
    
    def configure_yarn_mirror(self, provider: MirrorProvider) -> bool:
        """配置 Yarn 镜像源 / Configure Yarn mirror"""
        if provider not in MIRROR_PROVIDERS:
            return False
        
        config = MIRROR_PROVIDERS[provider]
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        
        # 检查是否已经是目标镜像源
        try:
            result = subprocess.run(
                ["yarn", "config", "get", "registry"],
                capture_output=True, text=True, timeout=10,
                creationflags=creationflags
            )
            if result.returncode == 0:
                current = result.stdout.strip()
                if config.npm_registry in current:
                    logger.info(f"Yarn 已经是 {config.name} 镜像 / Yarn already using {config.name}")
                    return True
        except Exception:
            pass
        
        success = False
        
        # 方法 1: 使用命令行设置
        try:
            result = subprocess.run(
                ["yarn", "config", "set", "registry", config.npm_registry],
                capture_output=True, text=True, timeout=15,
                creationflags=creationflags
            )
            if result.returncode == 0:
                success = True
                logger.info(f"Yarn mirror set via command: {config.npm_registry}")
        except Exception as e:
            logger.warning(f"yarn config set failed: {e}")
        
        # 验证配置是否成功
        if success:
            try:
                result = subprocess.run(
                    ["yarn", "config", "get", "registry"],
                    capture_output=True, text=True, timeout=10,
                    creationflags=creationflags
                )
                if result.returncode == 0 and config.npm_registry in result.stdout:
                    logger.info("✅ Yarn 镜像配置验证成功 / Yarn mirror verified")
                    return True
            except Exception:
                pass
        
        return success

    def configure_all_mirrors(self, 
                              apt_provider: Optional[MirrorProvider] = None,
                              npm_provider: Optional[MirrorProvider] = None,
                              pip_provider: Optional[MirrorProvider] = None,
                              snap_provider: Optional[MirrorProvider] = None,
                              yarn_provider: Optional[MirrorProvider] = None) -> Dict[str, bool]:
        """配置所有镜像源 / Configure all mirrors"""
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
        
        # Configure Snap
        if snap_provider:
            results["snap"] = self.configure_snap_mirror(snap_provider)
        
        # Configure Yarn
        if yarn_provider:
            results["yarn"] = self.configure_yarn_mirror(yarn_provider)
        
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
