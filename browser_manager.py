"""
浏览器/Electron 应用管理模块

负责连接或启动 AIoT 认证测试平台（Electron 应用）
"""

import subprocess
import time
import logging
from typing import Optional, Any

from playwright.sync_api import sync_playwright, BrowserContext, Page

logger = logging.getLogger(__name__)


class BrowserManager:
    """管理 Electron 应用的连接和生命周期"""
    
    def __init__(self, config: dict):
        self.config = config
        self.app_config = config.get("app", {})
        self.timeout_config = config.get("timeout", {})
        
        self._playwright = None
        self._electron: Optional[Any] = None
        self._app = None
        self._page: Optional[Page] = None
        self._context: Optional[BrowserContext] = None
    
    @property
    def page(self) -> Page:
        """获取当前页面"""
        if self._page is None:
            raise RuntimeError("未连接到应用，请先调用 connect() 或 launch()")
        return self._page
    
    def connect(self) -> Page:
        """连接到已运行的 Electron 应用"""
        logger.info("正在连接到已运行的应用...")
        
        self._playwright = sync_playwright().start()
        
        # 通过 CDP 连接已运行的 Chromium/Electron 应用
        # 需要应用启动时带 --remote-debugging-port=9222 参数
        try:
            browser = self._playwright.chromium.connect_over_cdp(
                "http://127.0.0.1:9222",
                timeout=self.timeout_config.get("element_wait", 10) * 1000
            )
            self._context = browser.contexts[0]
            self._page = self._context.pages[0]
            logger.info(f"已连接到页面: {self._page.title()}")
            return self._page
        except Exception as e:
            logger.warning(f"CDP 直接连接失败: {e}")
            logger.info("尝试通过窗口查找并连接...")
            try:
                return self._connect_via_window()
            except Exception as e2:
                raise RuntimeError(
                    f"无法连接到应用。请确认:\n"
                    f"  1. AIoT 认证测试平台已启动\n"
                    f"  2. 应用启动时带了 --remote-debugging-port=9222 参数\n"
                    f"     例如: AIoT认证测试平台.exe --remote-debugging-port=9222\n"
                    f"  原始错误: {e2}"
                )
    
    def _connect_via_window(self) -> Page:
        """通过窗口标题查找并连接"""
        window_title = self.app_config.get("window_title", "认证测试平台")
        
        # 使用 pyautogui 查找窗口并激活
        try:
            import pyautogui
            import pygetwindow as gw
            
            windows = gw.getWindowsWithTitle(window_title)
            if not windows:
                raise RuntimeError(f"未找到标题包含 '{window_title}' 的窗口")
            
            target_window = windows[0]
            target_window.activate()
            time.sleep(1)
            
            # 通过 CDP 连接
            browser = self._playwright.chromium.connect_over_cdp(
                "http://127.0.0.1:9222",
                timeout=5000
            )
            self._context = browser.contexts[0]
            self._page = self._context.pages[0]
            logger.info(f"已连接到页面: {self._page.title()}")
            return self._page
            
        except ImportError:
            raise RuntimeError("需要安装 pyautogui 和 pygetwindow: pip install pyautogui pygetwindow")
        except Exception as e:
            raise RuntimeError(
                f"通过窗口连接失败: {e}\n"
                f"请确保应用以 --remote-debugging-port=9222 参数启动"
            )
    
    def launch(self) -> Page:
        """启动新的 Electron 应用实例"""
        exe_path = self.app_config.get("exe_path")
        if not exe_path:
            raise ValueError("配置中未指定 exe_path")
        
        logger.info(f"正在启动应用: {exe_path}")
        
        self._playwright = sync_playwright().start()
        
        # 启动 Electron 应用
        self._app = self._playwright.electron.launch(
            executable_path=exe_path,
            args=["--remote-debugging-port=9222"]
        )
        
        # 获取主窗口
        self._page = self._app.first_window
        self._page.wait_for_load_state("domcontentloaded")
        logger.info(f"应用已启动，页面: {self._page.title()}")
        return self._page
    
    def wait_for_page(self, title_keyword: str, timeout: Optional[int] = None) -> Page:
        """等待包含指定标题的页面出现"""
        timeout = timeout or self.timeout_config.get("page_load", 30)
        timeout_ms = timeout * 1000
        
        logger.info(f"等待页面 (标题包含: {title_keyword})...")
        
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            current_title = self.page.title()
            if title_keyword in current_title:
                logger.info(f"页面已就绪: {current_title}")
                return self.page
            time.sleep(0.5)
        
        raise TimeoutError(f"等待页面超时 ({timeout}s): {title_keyword}")
    
    def close(self):
        """关闭连接"""
        logger.info("正在关闭连接...")
        
        if self._app:
            try:
                self._app.close()
            except Exception as e:
                logger.warning(f"关闭应用时出错: {e}")
        
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception as e:
                logger.warning(f"停止 Playwright 时出错: {e}")
        
        self._page = None
        self._context = None
        self._app = None
        self._electron = None
        self._playwright = None
        
        logger.info("连接已关闭")
    
    def __enter__(self):
        """上下文管理器入口"""
        mode = self.app_config.get("connect_mode", "connect")
        if mode == "launch":
            self.launch()
        else:
            self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
        return False
