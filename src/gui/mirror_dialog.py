"""
Mirror settings dialog / 镜像源设置对话框
"""
from typing import Optional, List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QComboBox, QTextEdit, QMessageBox,
    QListWidget, QListWidgetItem, QTabWidget, QWidget,
    QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ..core.mirror_manager import (
    MirrorManager, MirrorProvider, MIRROR_PROVIDERS,
    get_available_providers
)
from ..utils.logger import logger


class MirrorSettingsDialog(QDialog):
    """Mirror settings dialog / 镜像源设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mirror_manager = MirrorManager()
        self._init_ui()
        self._refresh_status()
    
    def _init_ui(self) -> None:
        """Initialize UI / 初始化界面"""
        self.setWindowTitle("镜像源管理 / Mirror Settings")
        self.setMinimumSize(550, 500)
        self.resize(600, 550)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Tab widget / 选项卡
        tabs = QTabWidget()
        
        # Tab 1: Configure mirrors / 配置镜像源
        config_tab = self._create_config_tab()
        tabs.addTab(config_tab, "配置镜像源 / Configure")
        
        # Tab 2: Backup & Restore / 备份与恢复
        backup_tab = self._create_backup_tab()
        tabs.addTab(backup_tab, "备份恢复 / Backup")
        
        layout.addWidget(tabs)
        
        # Close button / 关闭按钮
        close_btn = QPushButton("关闭 / Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def _create_config_tab(self) -> QWidget:
        """Create configuration tab / 创建配置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Current status / 当前状态
        status_group = QGroupBox("当前镜像源状态 / Current Mirror Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMinimumHeight(80)
        self.status_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 3px;
                font-family: Consolas, Monaco, monospace;
                font-size: 12px;
            }
        """)
        status_layout.addWidget(self.status_text)
        
        refresh_btn = QPushButton("刷新状态 / Refresh")
        refresh_btn.clicked.connect(self._refresh_status)
        status_layout.addWidget(refresh_btn)
        
        layout.addWidget(status_group)
        
        # Provider selection / 镜像源选择
        select_group = QGroupBox("选择镜像源 / Select Mirror Provider")
        select_layout = QVBoxLayout(select_group)
        
        # APT Mirror
        apt_layout = QHBoxLayout()
        apt_label = QLabel("APT 源:")
        apt_label.setMinimumWidth(80)
        self.apt_combo = QComboBox()
        self.apt_combo.addItem("不修改 / Keep current", None)
        for provider, name, name_zh in get_available_providers():
            self.apt_combo.addItem(f"{name_zh} / {name}", provider)
        apt_layout.addWidget(apt_label)
        apt_layout.addWidget(self.apt_combo, 1)
        select_layout.addLayout(apt_layout)
        
        # NPM Mirror
        npm_layout = QHBoxLayout()
        npm_label = QLabel("NPM 源:")
        npm_label.setMinimumWidth(80)
        self.npm_combo = QComboBox()
        self.npm_combo.addItem("不修改 / Keep current", None)
        self.npm_combo.addItem("淘宝源 (npmmirror)", MirrorProvider.TSINGHUA)
        npm_layout.addWidget(npm_label)
        npm_layout.addWidget(self.npm_combo, 1)
        select_layout.addLayout(npm_layout)
        
        # Pip Mirror
        pip_layout = QHBoxLayout()
        pip_label = QLabel("Pip 源:")
        pip_label.setMinimumWidth(80)
        self.pip_combo = QComboBox()
        self.pip_combo.addItem("不修改 / Keep current", None)
        for provider, name, name_zh in get_available_providers():
            self.pip_combo.addItem(f"{name_zh} / {name}", provider)
        pip_layout.addWidget(pip_label)
        pip_layout.addWidget(self.pip_combo, 1)
        select_layout.addLayout(pip_layout)
        
        # Snap Mirror
        snap_layout = QHBoxLayout()
        snap_label = QLabel("Snap 源:")
        snap_label.setMinimumWidth(80)
        self.snap_combo = QComboBox()
        self.snap_combo.addItem("不修改 / Keep current", None)
        # 只添加支持 Snap 的镜像源
        self.snap_combo.addItem("清华大学 / Tsinghua", MirrorProvider.TSINGHUA)
        self.snap_combo.addItem("中国科技大学 / USTC", MirrorProvider.USTC)
        snap_layout.addWidget(snap_label)
        snap_layout.addWidget(self.snap_combo, 1)
        select_layout.addLayout(snap_layout)
        
        layout.addWidget(select_group)
        
        # Quick config buttons / 快速配置按钮
        quick_group = QGroupBox("快速配置 / Quick Config")
        quick_layout = QHBoxLayout(quick_group)
        
        tsinghua_btn = QPushButton("全部使用清华源\nAll Tsinghua")
        tsinghua_btn.clicked.connect(lambda: self._quick_config(MirrorProvider.TSINGHUA))
        quick_layout.addWidget(tsinghua_btn)
        
        aliyun_btn = QPushButton("全部使用阿里源\nAll Aliyun")
        aliyun_btn.clicked.connect(lambda: self._quick_config(MirrorProvider.ALIYUN))
        quick_layout.addWidget(aliyun_btn)
        
        ustc_btn = QPushButton("全部使用中科大\nAll USTC")
        ustc_btn.clicked.connect(lambda: self._quick_config(MirrorProvider.USTC))
        quick_layout.addWidget(ustc_btn)
        
        layout.addWidget(quick_group)
        
        # Apply button / 应用按钮
        apply_btn = QPushButton("应用配置 / Apply")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        apply_btn.clicked.connect(self._apply_config)
        layout.addWidget(apply_btn)
        
        # Log area / 日志区域
        self.config_log = QTextEdit()
        self.config_log.setReadOnly(True)
        self.config_log.setMaximumHeight(100)
        self.config_log.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
                color: #f0f0f0;
                border: 1px solid #444;
                border-radius: 3px;
                font-family: Consolas, Monaco, monospace;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.config_log)
        
        return widget
    
    def _create_backup_tab(self) -> QWidget:
        """Create backup/restore tab / 创建备份恢复选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Backup list / 备份列表
        list_group = QGroupBox("备份列表 / Backup List")
        list_layout = QVBoxLayout(list_group)
        
        self.backup_list = QListWidget()
        self.backup_list.setMaximumHeight(200)
        list_layout.addWidget(self.backup_list)
        
        refresh_backup_btn = QPushButton("刷新列表 / Refresh List")
        refresh_backup_btn.clicked.connect(self._refresh_backup_list)
        list_layout.addWidget(refresh_backup_btn)
        
        layout.addWidget(list_group)
        
        # Action buttons / 操作按钮
        action_layout = QHBoxLayout()
        
        backup_btn = QPushButton("立即备份 / Backup Now")
        backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        backup_btn.clicked.connect(self._do_backup)
        action_layout.addWidget(backup_btn)
        
        restore_btn = QPushButton("恢复选中备份 / Restore Selected")
        restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #d35400; }
        """)
        restore_btn.clicked.connect(self._do_restore)
        action_layout.addWidget(restore_btn)
        
        layout.addLayout(action_layout)
        
        # Restore log / 恢复日志
        self.restore_log = QTextEdit()
        self.restore_log.setReadOnly(True)
        self.restore_log.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
                color: #f0f0f0;
                border: 1px solid #444;
                border-radius: 3px;
                font-family: Consolas, Monaco, monospace;
            }
        """)
        layout.addWidget(self.restore_log)
        
        # Load backup list
        self._refresh_backup_list()
        
        return widget
    
    def _refresh_status(self) -> None:
        """Refresh current mirror status / 刷新当前镜像状态"""
        info = self.mirror_manager.get_current_mirror_info()
        distro, release = self.mirror_manager.detect_distro()
        
        status_lines = [
            f"系统 / System: {distro.value} {release}",
            f"APT 源 / APT: {info['apt']}",
            f"NPM 源 / NPM: {info['npm']}",
            f"Pip 源 / Pip: {info['pip']}",
            f"Snap 源 / Snap: {info['snap']}",
        ]
        self.status_text.setText("\n".join(status_lines))
    
    def _quick_config(self, provider: MirrorProvider) -> None:
        """Quick config all mirrors / 快速配置所有镜像"""
        self.apt_combo.setCurrentIndex(
            self.apt_combo.findData(provider)
        )
        self.npm_combo.setCurrentIndex(
            self.npm_combo.findData(provider)
        )
        self.pip_combo.setCurrentIndex(
            self.pip_combo.findData(provider)
        )
        # Snap 只有清华和中科大支持
        snap_index = self.snap_combo.findData(provider)
        if snap_index >= 0:
            self.snap_combo.setCurrentIndex(snap_index)
        else:
            self.snap_combo.setCurrentIndex(0)  # 不修改
        self._log(f"已选择: {MIRROR_PROVIDERS[provider].name_zh}")
        self._log(f"Selected: {MIRROR_PROVIDERS[provider].name}")
    
    def _apply_config(self) -> None:
        """Apply mirror configuration / 应用镜像配置"""
        apt_provider = self.apt_combo.currentData()
        npm_provider = self.npm_combo.currentData()
        pip_provider = self.pip_combo.currentData()
        snap_provider = self.snap_combo.currentData()
        
        if not any([apt_provider, npm_provider, pip_provider, snap_provider]):
            self._log("未选择任何镜像源 / No mirror selected")
            return
        
        # Confirm / 确认
        reply = QMessageBox.question(
            self,
            "确认 / Confirm",
            "将备份当前配置并应用新镜像源。\n"
            "This will backup current config and apply new mirrors.\n\n"
            "继续？ / Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self._log("开始配置... / Configuring...")
        
        results = self.mirror_manager.configure_all_mirrors(
            apt_provider=apt_provider,
            npm_provider=npm_provider,
            pip_provider=pip_provider,
            snap_provider=snap_provider
        )
        
        for key, success in results.items():
            status = "✅ 成功 / Success" if success else "❌ 失败 / Failed"
            self._log(f"{key}: {status}")
        
        self._refresh_status()
        self._log("配置完成 / Configuration completed")
    
    def _refresh_backup_list(self) -> None:
        """Refresh backup list / 刷新备份列表"""
        self.backup_list.clear()
        backups = self.mirror_manager.list_backups()
        
        for backup in backups:
            item = QListWidgetItem(backup.name)
            item.setData(Qt.ItemDataRole.UserRole, backup)
            self.backup_list.addItem(item)
        
        if not backups:
            self.backup_list.addItem("暂无备份 / No backups")
    
    def _do_backup(self) -> None:
        """Perform backup / 执行备份"""
        self._restore_log("正在备份... / Backing up...")
        
        backup_file = self.mirror_manager.backup_all_sources()
        
        if backup_file:
            self._restore_log(f"✅ 备份成功: {backup_file.name}")
            self._restore_log(f"✅ Backup success: {backup_file.name}")
            self._refresh_backup_list()
        else:
            self._restore_log("❌ 备份失败 / Backup failed")
    
    def _do_restore(self) -> None:
        """Perform restore / 执行恢复"""
        current_item = self.backup_list.currentItem()
        if not current_item:
            self._restore_log("请选择一个备份 / Please select a backup")
            return
        
        backup_path = current_item.data(Qt.ItemDataRole.UserRole)
        if not backup_path:
            return
        
        # Confirm / 确认
        reply = QMessageBox.question(
            self,
            "确认恢复 / Confirm Restore",
            f"将恢复备份: {backup_path.name}\n"
            f"Will restore: {backup_path.name}\n\n"
            "当前配置将被覆盖！\nCurrent config will be overwritten!\n\n"
            "继续？ / Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self._restore_log(f"正在恢复... / Restoring...")
        
        success = self.mirror_manager.restore_from_backup(backup_path)
        
        if success:
            self._restore_log("✅ 恢复成功 / Restore success")
        else:
            self._restore_log("❌ 恢复失败 / Restore failed")
    
    def _log(self, message: str) -> None:
        """Add log to config tab / 添加日志到配置选项卡"""
        self.config_log.append(message)
    
    def _restore_log(self, message: str) -> None:
        """Add log to backup tab / 添加日志到备份选项卡"""
        self.restore_log.append(message)
