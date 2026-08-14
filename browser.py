import sys
import json
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QSystemTrayIcon,
                             QMenu, QAction, QWidget, QVBoxLayout, QHBoxLayout,
                             QSlider, QLabel, QLineEdit, QPushButton, QCheckBox,
                             QMessageBox, QDialog, QListWidget, QListWidgetItem,
                             QInputDialog, QFrame, QGroupBox, QToolBar)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEnginePage
from PyQt5.QtCore import Qt, QTimer, QUrl, QRect, QPoint, QSize
from PyQt5.QtGui import QIcon, QPixmap, QColor, QCursor, QPainter

class BookmarkDialog(QDialog):
    """书签管理对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("书签管理")
        self.setFixedSize(500, 420)  # 调大尺寸

        layout = QVBoxLayout()

        # 书签列表
        self.bookmark_list = QListWidget()
        self.load_bookmarks()
        # 双击跳转
        self.bookmark_list.itemDoubleClicked.connect(self.goto_bookmark)

        # 按钮布局1 - 操作按钮
        btn_layout1 = QHBoxLayout()

        # 获取当前网页按钮
        get_current_btn = QPushButton("获取当前网页")
        get_current_btn.clicked.connect(self.get_current_page)
        get_current_btn.setStyleSheet("background-color: #4a90e2; color: white;")

        # 转到书签按钮
        goto_btn = QPushButton("转到选中书签")
        goto_btn.clicked.connect(self.goto_bookmark)
        goto_btn.setStyleSheet("background-color: #f39c12; color: white;")

        # 删除按钮
        delete_btn = QPushButton("删除选中")
        delete_btn.clicked.connect(self.delete_bookmark)
        delete_btn.setStyleSheet("background-color: #d32f2f; color: white;")

        btn_layout1.addWidget(get_current_btn)
        btn_layout1.addWidget(goto_btn)
        btn_layout1.addWidget(delete_btn)

        # 添加书签的输入区域
        add_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("输入网址 (例如: https://www.baidu.com)")
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("书签名称")
        add_button = QPushButton("手动添加")
        add_button.clicked.connect(self.add_bookmark)

        add_layout.addWidget(self.url_input)
        add_layout.addWidget(self.title_input)
        add_layout.addWidget(add_button)

        layout.addWidget(QLabel("书签列表（双击可跳转）:"))
        layout.addWidget(self.bookmark_list)
        layout.addLayout(btn_layout1)
        layout.addLayout(add_layout)

        self.setLayout(layout)

    def get_current_page(self):
        """获取当前浏览器页面的URL和标题"""
        if self.parent():
            browser = self.parent().browser
            url = browser.url().toString()
            title = browser.title()

            if url and not url.startswith("about:blank"):
                self.url_input.setText(url)
                if title:
                    self.title_input.setText(title)
                else:
                    self.title_input.setText(url)
            else:
                QMessageBox.warning(self, "提示", "当前页面无法获取或为空")

    def goto_bookmark(self):
        """跳转到选中的书签"""
        current_item = self.bookmark_list.currentItem()
        if current_item:
            data = current_item.data(Qt.UserRole)
            url = data['url']

            if self.parent():
                self.parent().load_url(url)
                self.accept()  # 关闭对话框
        else:
            QMessageBox.warning(self, "提示", "请先选择一个书签")

    def load_bookmarks(self):
        try:
            if os.path.exists("bookmarks.json"):
                with open("bookmarks.json", "r", encoding="utf-8") as f:
                    bookmarks = json.load(f)
                    for bm in bookmarks:
                        item = QListWidgetItem(f"{bm['title']} - {bm['url']}")
                        item.setData(Qt.UserRole, bm)
                        self.bookmark_list.addItem(item)
        except:
            pass

    def save_bookmarks(self):
        bookmarks = []
        for i in range(self.bookmark_list.count()):
            item = self.bookmark_list.item(i)
            bm = item.data(Qt.UserRole)
            bookmarks.append(bm)

        with open("bookmarks.json", "w", encoding="utf-8") as f:
            json.dump(bookmarks, f, ensure_ascii=False, indent=2)

    def add_bookmark(self):
        url = self.url_input.text().strip()
        title = self.title_input.text().strip()

        if not url:
            QMessageBox.warning(self, "错误", "请输入网址")
            return

        if not url.startswith("http"):
            url = "https://" + url

        if not title:
            title = url

        item = QListWidgetItem(f"{title} - {url}")
        item.setData(Qt.UserRole, {"url": url, "title": title})
        self.bookmark_list.addItem(item)

        self.save_bookmarks()
        self.url_input.clear()
        self.title_input.clear()

    def delete_bookmark(self):
        current_item = self.bookmark_list.currentItem()
        if current_item:
            row = self.bookmark_list.row(current_item)
            self.bookmark_list.takeItem(row)
            self.save_bookmarks()

class HistoryDialog(QDialog):
    """历史记录管理对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("历史记录")
        self.setFixedSize(550, 450)

        layout = QVBoxLayout()

        # 历史记录列表
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.jump_to_history)  # 双击跳转
        self.load_history()

        # 按钮布局
        btn_layout = QHBoxLayout()
        jump_btn = QPushButton("跳转到选中记录")
        jump_btn.clicked.connect(self.jump_to_history)
        clear_btn = QPushButton("清空历史记录")
        clear_btn.clicked.connect(self.clear_history)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)

        btn_layout.addWidget(jump_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)

        layout.addWidget(QLabel("访问历史:"))
        layout.addWidget(self.history_list)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_history(self):
        """加载历史记录"""
        try:
            if os.path.exists("history.json"):
                with open("history.json", "r", encoding="utf-8") as f:
                    history = json.load(f)
                    # 按时间倒序显示（最新的在前）
                    for item in reversed(history):
                        display_text = f"{item['time']} - {item['title']} - {item['url']}"
                        list_item = QListWidgetItem(display_text)
                        list_item.setData(Qt.UserRole, item)
                        self.history_list.addItem(list_item)
        except:
            pass

    def jump_to_history(self):
        """跳转到选中的历史记录"""
        current_item = self.history_list.currentItem()
        if current_item:
            data = current_item.data(Qt.UserRole)
            url = data['url']

            # 通知父窗口跳转
            if self.parent():
                self.parent().load_url(url)
                self.accept()  # 关闭对话框

    def clear_history(self):
        """清空历史记录"""
        reply = QMessageBox.question(self, "确认", "确定要清空所有历史记录吗？",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                if os.path.exists("history.json"):
                    os.remove("history.json")
                self.history_list.clear()
            except:
                pass

class SettingsDialog(QDialog):
    """设置对话框 - 带滑条，实时预览"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedSize(450, 420)

        layout = QVBoxLayout()

        # 透明度调节组
        opacity_group = QGroupBox("透明度调节")
        opacity_layout = QVBoxLayout()

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(1, 100)  # 修改最低为1%

        self.opacity_value = QLabel("100%")
        self.opacity_value.setAlignment(Qt.AlignCenter)
        self.opacity_value.setStyleSheet("font-weight: bold; font-size: 16px;")

        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_value)
        opacity_group.setLayout(opacity_layout)

        # 缩放调节组
        zoom_group = QGroupBox("页面缩放调节")
        zoom_layout = QVBoxLayout()

        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(50, 200)

        self.zoom_value = QLabel("100%")
        self.zoom_value.setAlignment(Qt.AlignCenter)
        self.zoom_value.setStyleSheet("font-weight: bold; font-size: 16px;")

        zoom_layout.addWidget(self.zoom_slider)
        zoom_layout.addWidget(self.zoom_value)
        zoom_group.setLayout(zoom_layout)

        # 默认地址
        url_group = QGroupBox("默认导航地址")
        url_layout = QVBoxLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://www.baidu.com")
        url_layout.addWidget(self.url_edit)
        url_group.setLayout(url_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        # 添加到主布局
        layout.addWidget(opacity_group)
        layout.addWidget(zoom_group)
        layout.addWidget(url_group)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # 连接信号 - 实时预览
        self.opacity_slider.valueChanged.connect(self.update_opacity_label)
        self.zoom_slider.valueChanged.connect(self.update_zoom_label)

        # 实时应用（通过父窗口）
        self.opacity_slider.valueChanged.connect(self.apply_opacity_realtime)
        self.zoom_slider.valueChanged.connect(self.apply_zoom_realtime)

    def update_opacity_label(self, value):
        self.opacity_value.setText(f"{value}%")

    def update_zoom_label(self, value):
        self.zoom_value.setText(f"{value}%")

    def apply_opacity_realtime(self, value):
        """实时应用透明度"""
        if self.parent():
            self.parent().set_opacity(value / 100.0)

    def apply_zoom_realtime(self, value):
        """实时应用缩放"""
        if self.parent():
            self.parent().set_zoom(value / 100.0)

    def apply_settings(self):
        """应用设置"""
        self.accept()

class CustomWebEnginePage(QWebEnginePage):
    """自定义WebEnginePage，处理导航请求"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_browser = parent

    def acceptNavigationRequest(self, url, type, isMainFrame):
        """拦截导航请求，确保在当前页面打开"""
        if isMainFrame:
            # 允许所有导航请求，在当前页面打开
            return True
        return False

    def createWindow(self, type):
        """新窗口只在当前页面打开"""
        return self.parent_browser.page()

class FloatingToolBar(QToolBar):
    """浮动工具栏 - 可拖动的小工具栏"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("浮动工具栏")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMovable(True)
        self.setFloatable(True)

        # 设置样式
        self.setStyleSheet("""
            QToolBar {
                background-color: rgba(45, 45, 45, 220);
                border-radius: 8px;
                padding: 5px;
                spacing: 5px;
            }
        """)

        # 添加按钮
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(30, 30)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
        """)
        settings_btn.clicked.connect(parent.show_settings)

        bookmark_btn = QPushButton("★")
        bookmark_btn.setFixedSize(30, 30)
        bookmark_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        bookmark_btn.clicked.connect(parent.show_bookmarks)

        hide_btn = QPushButton("×")
        hide_btn.setFixedSize(30, 30)
        hide_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f44336;
            }
        """)
        hide_btn.clicked.connect(self.hide)

        self.addWidget(settings_btn)
        self.addWidget(bookmark_btn)
        self.addWidget(hide_btn)

        # 允许拖动
        self.setMouseTracking(True)
        self.drag_start_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.globalPos() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drag_start_pos and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_start_pos)
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.drag_start_pos = None
        super().mouseReleaseEvent(event)

class TransparentBrowser(QMainWindow):
    """透明浏览器主窗口"""
    def __init__(self):
        super().__init__()
        self.default_url = "https://www.baidu.com"
        self.auto_hide = False  # 默认关闭自动隐藏
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_window)

        # 新增：显示定时器（2秒）
        self.show_timer = QTimer()
        self.show_timer.setSingleShot(True)
        self.show_timer.timeout.connect(self.show_window)

        # 浮动工具栏
        self.floating_toolbar = None

        # 历史记录列表（内存中）
        self.history_list = []

        self.init_ui()
        self.init_tray()
        self.load_settings()

    def init_ui(self):
        """初始化UI - 保留系统标题栏，竖长形状"""
        # 设置窗口属性 - 保留系统标题栏，保持置顶
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(1.0)

        # 移除最小尺寸限制
        self.setMinimumSize(1, 1)
        # 修改默认窗口大小为竖长形状（像手机）
        self.resize(400, 800)

        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 浏览器容器
        browser_container = QFrame()
        browser_container.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 230);
                border-radius: 0 0 8px 8px;
                border: 1px solid rgba(200, 200, 200, 100);
            }
        """)
        browser_layout = QVBoxLayout(browser_container)
        browser_layout.setContentsMargins(1, 1, 1, 1)

        # 创建浏览器
        self.browser = QWebEngineView()
        self.browser.setStyleSheet("""
            QWebEngineView {
                background-color: rgba(255, 255, 255, 255);
                border-radius: 0 0 7px 7px;
            }
        """)

        # 启用透明背景和必要的设置
        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.LinksIncludedInFocusChain, True)

        # 使用自定义WebEnginePage处理导航
        custom_page = CustomWebEnginePage(self.browser)
        self.browser.setPage(custom_page)

        # 连接页面加载完成信号，记录历史
        self.browser.urlChanged.connect(self.on_url_changed)
        self.browser.loadFinished.connect(self.on_load_finished)

        # 加载初始页面
        self.browser.load(QUrl(self.default_url))

        browser_layout.addWidget(self.browser)
        main_layout.addWidget(browser_container)

        # 鼠标跟踪
        self.setMouseTracking(True)
        self.browser.setMouseTracking(True)

        # 移动检测 - 2秒检测间隔
        self.last_mouse_pos = QCursor.pos()
        self.mouse_move_timer = QTimer()
        self.mouse_move_timer.setInterval(1000)  # 改为2秒检测
        self.mouse_move_timer.timeout.connect(self.check_mouse_move)
        self.mouse_move_timer.start()

        # 记录窗口位置（用于鼠标移回显示）
        self.last_window_rect = QRect()
        self.last_window_pos = QPoint()
        self.last_window_size = QSize()

    def init_tray(self):
        """初始化系统托盘 - 使用透明图标"""
        # 创建透明背景的pixmap
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)  # 填充透明背景

        # 在透明背景上绘制一个半透明的圆形
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        # 使用半透明的蓝色（RGBA中的A=120，表示半透明）
        painter.setBrush(QColor(74, 144, 226, 120))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 12, 12)  # 绘制圆形
        painter.end()

        self.tray_icon = QSystemTrayIcon(QIcon(pixmap), self)

        tray_menu = QMenu()

        # 显示/隐藏
        show_action = QAction("显示/隐藏", self)
        show_action.triggered.connect(self.toggle_show)
        tray_menu.addAction(show_action)

        # 自动隐藏开关
        self.auto_hide_action = QAction("自动隐藏", self, checkable=True)
        self.auto_hide_action.triggered.connect(self.toggle_auto_hide)
        tray_menu.addAction(self.auto_hide_action)

        # 恢复默认透明度
        default_opacity_action = QAction("恢复默认透明度（50%）", self)
        default_opacity_action.triggered.connect(self.restore_default_opacity)
        tray_menu.addAction(default_opacity_action)

        # 设置和书签
        tray_menu.addSeparator()
        settings_action = QAction("⚙ 设置", self)
        settings_action.triggered.connect(self.show_settings)
        tray_menu.addAction(settings_action)

        bookmark_action = QAction("★ 书签", self)
        bookmark_action.triggered.connect(self.show_bookmarks)
        tray_menu.addAction(bookmark_action)

        # 历史记录
        history_action = QAction("📜 历史记录", self)
        history_action.triggered.connect(self.show_history)
        tray_menu.addAction(history_action)

        # 浮动工具栏
        toolbar_action = QAction("显示浮动工具栏", self)
        toolbar_action.triggered.connect(self.toggle_floating_toolbar)
        tray_menu.addAction(toolbar_action)

        tray_menu.addSeparator()

        # 不显示在任务栏
        self.taskbar_action = QAction("不显示在任务栏", self, checkable=True)
        self.taskbar_action.triggered.connect(self.toggle_taskbar)
        tray_menu.addAction(self.taskbar_action)

        # 固定在最上层
        self.topmost_action = QAction("固定在最上层", self, checkable=True)
        self.topmost_action.triggered.connect(self.toggle_topmost)
        self.topmost_action.setChecked(True)
        tray_menu.addAction(self.topmost_action)

        # 退出
        tray_menu.addSeparator()
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.tray_activated)

    def load_settings(self):
        """加载保存的设置"""
        try:
            if os.path.exists("browser_settings.json"):
                with open("browser_settings.json", "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    self.default_url = settings.get("default_url", self.default_url)
                    self.auto_hide = settings.get("auto_hide", False)
                    opacity = settings.get("opacity", 1.0)
                    zoom = settings.get("zoom", 1.0)

                    self.set_opacity(opacity)
                    self.set_zoom(zoom)

                    # 设置自动隐藏菜单状态
                    if hasattr(self, 'auto_hide_action'):
                        self.auto_hide_action.setChecked(self.auto_hide)

                    if settings.get("no_taskbar", False):
                        self.setWindowFlags(self.windowFlags() | Qt.Tool)
                        self.taskbar_action.setChecked(True) if hasattr(self, 'taskbar_action') else None

                    if settings.get("topmost", True):
                        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
                        self.topmost_action.setChecked(True) if hasattr(self, 'topmost_action') else None

                    # 恢复窗口大小和位置
                    if "window_size" in settings:
                        size = settings["window_size"]
                        self.resize(size["width"], size["height"])
                    if "window_pos" in settings:
                        pos = settings["window_pos"]
                        self.move(pos["x"], pos["y"])
        except:
            pass

    def save_settings(self):
        """保存设置"""
        settings = {
            "default_url": self.default_url,
            "auto_hide": self.auto_hide,
            "opacity": self.windowOpacity(),
            "zoom": self.browser.zoomFactor(),
            "no_taskbar": bool(self.windowFlags() & Qt.Tool),
            "topmost": bool(self.windowFlags() & Qt.WindowStaysOnTopHint),
            "show_titlebar": True,  # 始终显示系统标题栏
            "window_size": {"width": self.width(), "height": self.height()},
            "window_pos": {"x": self.x(), "y": self.y()}
        }
        try:
            with open("browser_settings.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except:
            pass

    def on_url_changed(self, url):
        """URL改变时的回调（用于记录历史）"""
        # 这个方法在URL改变时触发，但页面可能还没加载完成
        pass

    def on_load_finished(self, ok):
        """页面加载完成时的回调（用于记录历史）"""
        if ok:
            url = self.browser.url().toString()
            title = self.browser.title()

            # 只记录有效的URL（不是空的，不是about:blank）
            if url and not url.startswith("about:blank"):
                self.add_to_history(url, title)

    def add_to_history(self, url, title):
        """添加到历史记录"""
        # 创建历史记录项
        history_item = {
            "url": url,
            "title": title if title else url,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # 读取现有历史记录
        history = []
        try:
            if os.path.exists("history.json"):
                with open("history.json", "r", encoding="utf-8") as f:
                    history = json.load(f)
        except:
            pass

        # 去重（保留最新的）
        history = [item for item in history if item["url"] != url]
        history.append(history_item)

        # 限制历史记录数量（最多50条）
        if len(history) > 50:
            history = history[-50:]

        # 保存到文件
        try:
            with open("history.json", "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except:
            pass

    def show_history(self):
        """显示历史记录对话框"""
        dialog = HistoryDialog(self)
        dialog.exec_()

    def load_url(self, url):
        """加载指定URL（用于历史记录跳转）"""
        if url:
            self.browser.load(QUrl(url))

    def toggle_auto_hide(self, checked):
        """切换自动隐藏功能 - 无消息通知"""
        self.auto_hide = checked
        self.save_settings()

    def restore_default_opacity(self):
        """恢复默认透明度（50%）"""
        self.set_opacity(0.5)
        self.save_settings()

    def show_settings(self):
        """显示设置对话框（带滑条，实时预览）"""
        dialog = SettingsDialog(self)

        # 加载当前设置
        dialog.opacity_slider.setValue(int(self.windowOpacity() * 100))
        dialog.zoom_slider.setValue(int(self.browser.zoomFactor() * 100))
        dialog.url_edit.setText(self.default_url)

        # 关键：让对话框透明度跟随网页透明度
        def sync_dialog_opacity(value):
            dialog.setWindowOpacity(value / 100.0)

        dialog.opacity_slider.valueChanged.connect(sync_dialog_opacity)

        # 对话框打开时的原始值
        original_opacity = self.windowOpacity()
        original_zoom = self.browser.zoomFactor()
        original_url = self.default_url

        if dialog.exec_() == QDialog.Accepted:
            # 确定：保存当前设置
            self.default_url = dialog.url_edit.text().strip() or "https://www.baidu.com"
            self.save_settings()
        else:
            # 取消：恢复原始值
            self.set_opacity(original_opacity)
            self.set_zoom(original_zoom)
            self.default_url = original_url

    def set_opacity(self, opacity):
        """设置透明度"""
        self.setWindowOpacity(opacity)
        # 同时调整浏览器容器的透明度
        if hasattr(self, 'centralWidget'):
            browser_container = self.centralWidget().findChild(QFrame)
            if browser_container:
                browser_container.setStyleSheet(f"""
                    QFrame {{
                        background-color: rgba(255, 255, 255, {int(230 * opacity)});
                        border-radius: 0 0 8px 8px;
                        border: 1px solid rgba(200, 200, 200, {int(100 * opacity)});
                    }}
                """)

    def set_zoom(self, zoom):
        """设置缩放"""
        self.browser.setZoomFactor(zoom)

    def set_default_url(self, url):
        """设置默认地址"""
        if url:
            self.default_url = url
            self.save_settings()

    def show_bookmarks(self):
        """显示书签"""
        dialog = BookmarkDialog(self)
        dialog.exec_()

    def toggle_show(self):
        """切换显示/隐藏"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()

    def toggle_floating_toolbar(self):
        """切换浮动工具栏显示"""
        if self.floating_toolbar and self.floating_toolbar.isVisible():
            self.floating_toolbar.hide()
        else:
            if not self.floating_toolbar:
                self.floating_toolbar = FloatingToolBar(self)
                # 放置在窗口右上角附近
                self.floating_toolbar.move(self.pos().x() + self.width() - 120, self.pos().y() + 40)
            self.floating_toolbar.show()

    def toggle_taskbar(self, checked):
        """切换任务栏显示"""
        # 保留系统标题栏
        flags = self.windowFlags() & ~Qt.Tool
        if checked:
            flags = flags | Qt.Tool
        self.setWindowFlags(flags)
        self.show()
        self.save_settings()

    def toggle_topmost(self, checked):
        """切换置顶"""
        # 保留系统标题栏
        flags = self.windowFlags() & ~Qt.WindowStaysOnTopHint
        if checked:
            flags = flags | Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()
        self.save_settings()

    def mousePressEvent(self, event):
        """鼠标点击事件 - 无拖动（保留系统标题栏）"""
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        # 确保浏览器容器填满可用空间
        self.set_opacity(self.windowOpacity())

    def check_mouse_move(self):
        """检查鼠标是否移动（用于自动隐藏和显示）"""
        current_pos = QCursor.pos()

        # 检测鼠标移动（用于2秒后隐藏）
        if self.auto_hide and self.isVisible():
            if current_pos != self.last_mouse_pos:
                self.last_mouse_pos = current_pos
                # 鼠标在窗口内，取消隐藏
                if self.hide_timer.isActive():
                    self.hide_timer.stop()

            # 检查鼠标是否在窗口外 - 2秒后隐藏
            global_pos = QCursor.pos()
            window_rect = self.frameGeometry()

            if not window_rect.contains(global_pos):
                # 鼠标在窗口外，2秒后隐藏（仅当auto_hide为True时）
                if self.auto_hide and not self.hide_timer.isActive():
                    self.hide_timer.start(1000)

        # 检测鼠标移回显示（当窗口隐藏时）
        if self.auto_hide and not self.isVisible():
            # 检查鼠标是否在窗口之前的位置范围内
            if hasattr(self, 'last_window_rect') and self.last_window_rect.isValid():
                global_pos = QCursor.pos()
                if self.last_window_rect.contains(global_pos):
                    # 鼠标移回窗口区域，2秒后显示
                    if not self.show_timer.isActive():
                        self.show_timer.start(1000)
                else:
                    # 鼠标移出窗口区域，取消显示定时器
                    if self.show_timer.isActive():
                        self.show_timer.stop()

    def hide_window(self):
        """隐藏窗口 - 记录位置用于鼠标移回显示"""
        if self.auto_hide and self.isVisible():
            # 记录窗口隐藏前的位置和大小
            self.last_window_pos = self.pos()
            self.last_window_size = self.size()
            # 记录窗口区域（扩大一点范围方便检测）
            rect = self.geometry()
            rect.adjust(-20, -20, 20, 20)  # 扩大20像素
            self.last_window_rect = rect

            self.hide()

    def show_window(self):
        """显示窗口（用于定时器调用）"""
        if not self.isVisible():
            self.show()
            self.activateWindow()
            # 清除记录，避免重复触发
            self.last_window_rect = QRect()

    def enterEvent(self, event):
        """鼠标进入窗口"""
        # 取消隐藏定时器
        if self.auto_hide and self.hide_timer.isActive():
            self.hide_timer.stop()

        # 如果窗口隐藏，取消显示定时器（因为鼠标已经在窗口内，不需要延迟显示）
        if self.auto_hide and not self.isVisible():
            if self.show_timer.isActive():
                self.show_timer.stop()
            # 立即显示
            self.show()
            self.activateWindow()

        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开窗口"""
        # 2秒后隐藏，仅当auto_hide为True时
        if self.auto_hide and self.isVisible():
            if not self.hide_timer.isActive():
                self.hide_timer.start(1000)
        super().leaveEvent(event)

    def tray_activated(self, reason):
        """托盘图标点击事件"""
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_show()

    def closeEvent(self, event):
        event.ignore()

        # 关键：关闭自动隐藏功能
        if self.auto_hide:
            self.auto_hide = False
            if hasattr(self, 'auto_hide_action'):
                self.auto_hide_action.setChecked(False)
            self.save_settings()

        # 停止所有隐藏相关的定时器
        if self.hide_timer.isActive():
            self.hide_timer.stop()
        if self.show_timer.isActive():
            self.show_timer.stop()

        # 隐藏窗口
        self.hide()

        # 记录位置（保留以备将来使用）
        self.last_window_pos = self.pos()
        self.last_window_size = self.size()
        rect = self.geometry()
        rect.adjust(-20, -20, 20, 20)
        self.last_window_rect = rect

    def quit_app(self):
        # 停止所有定时器
        if self.hide_timer.isActive():
            self.hide_timer.stop()
        if self.show_timer.isActive():
            self.show_timer.stop()
        if self.mouse_move_timer.isActive():
            self.mouse_move_timer.stop()

        # 隐藏浮动工具栏
        if self.floating_toolbar:
            self.floating_toolbar.hide()
        self.save_settings()
        self.tray_icon.hide()
        QApplication.quit()

def main():
    if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("小透明")
    app.setApplicationVersion("1.0")
    browser = TransparentBrowser()
    browser.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
