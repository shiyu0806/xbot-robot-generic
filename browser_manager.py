"""
浏览器/Electron 应用管理模块

通过 CDP (Chrome DevTools Protocol) 连接或启动 AIoT 认证测试平台。

两种模式：
  - launch:  用 subprocess 启动应用（自动带 --remote-debugging-port），
             轮询等待 CDP 就绪，然后通过 Playwright CDP 连接
  - connect: 直接通过 CDP 连接已运行的应用（需要应用已带调试端口启动）

不依赖 playwright.electron（PyInstaller 打包后不可用），
不依赖 pyautogui/pygetwindow（不可靠）。
"""

import subprocess
import socket
import json
import time
import logging
from typing import Optional
from urllib.request import urlopen
from urllib.error import URLError

from playwright.sync_api import sync_playwright, BrowserContext, Page

logger = logging.getLogger(__name__)

DEFAULT_CDP_PORT = 9222


class BrowserManager:
    """管理 Electron 应用的连接和生命周期（通过 CDP）"""

    def __init__(self, config: dict):
        self.config = config
        self.app_config = config.get("app", {})
        self.timeout_config = config.get("timeout", {})

        self.cdp_port: int = self.app_config.get("cdp_port", DEFAULT_CDP_PORT)
        self.cdp_url: str = f"http://127.0.0.1:{self.cdp_port}"
        self.startup_timeout: int = self.app_config.get("startup_timeout", 30)

        self._playwright = None
        self._page: Optional[Page] = None
        self._context: Optional[BrowserContext] = None
        self._process: Optional[subprocess.Popen] = None

    @property
    def page(self) -> Page:
        """获取当前页面"""
        if self._page is None:
            raise RuntimeError("未连接到应用，请先调用 connect() 或 launch()")
        return self._page

    # ─── 底层工具方法 ──────────────────────────────────────────

    def _port_in_use(self) -> bool:
        """检查 CDP 端口是否已有程序监听"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            return sock.connect_ex(("127.0.0.1", self.cdp_port)) == 0
        finally:
            sock.close()

    def _cdp_is_ready(self) -> bool:
        """检查 CDP 服务是否就绪（通过 /json/version 端点）"""
        try:
            resp = urlopen(f"{self.cdp_url}/json/version", timeout=2)
            data = json.loads(resp.read())
            return "Browser" in data
        except Exception:
            return False

    def _wait_for_cdp(self, timeout: int = None) -> bool:
        """轮询等待 CDP 就绪，返回是否成功"""
        timeout = timeout or self.startup_timeout
        start = time.time()
        logger.info(f"等待应用 CDP 就绪 (超时: {timeout}s)...")
        while time.time() - start < timeout:
            if self._cdp_is_ready():
                logger.info("CDP 服务已就绪")
                return True
            time.sleep(1)
        return False

    def _connect_cdp(self) -> Page:
        """通过 Playwright CDP 连接已就绪的应用"""
        timeout_ms = self.timeout_config.get("element_wait", 10) * 1000
        browser = self._playwright.chromium.connect_over_cdp(
            self.cdp_url,
            timeout=timeout_ms,
        )
        self._context = browser.contexts[0]
        self._page = self._context.pages[0]
        logger.info(f"已连接到页面: {self._page.title()}")
        return self._page

    # ─── connect 模式 ──────────────────────────────────────────

    def connect(self) -> Page:
        """连接到已运行的 Electron 应用（需要应用已带 --remote-debugging-port 启动）"""
        logger.info(f"正在连接到已运行的应用 ({self.cdp_url}) ...")

        # 1. 检查端口是否在监听
        if not self._port_in_use():
            raise RuntimeError(
                f"无法连接：端口 {self.cdp_port} 未在监听。\n"
                f"\n"
                f"请确认以下两点：\n"
                f"  1. AIoT 认证测试平台已启动\n"
                f"  2. 启动时带了调试端口参数\n"
                f"\n"
                f"方法 A（推荐）：使用 --launch 模式自动启动\n"
                f"  AIoT-auto-test.exe --launch --app-path \"C:\\...\\AIoT Certification Studio.exe\"\n"
                f"\n"
                f"方法 B：修改应用快捷方式，目标改为：\n"
                f"  \"C:\\...\\AIoT Certification Studio.exe\" --remote-debugging-port={self.cdp_port}"
            )

        # 2. 端口在监听，尝试 CDP 连接
        self._playwright = sync_playwright().start()
        try:
            return self._connect_cdp()
        except Exception as e:
            raise RuntimeError(
                f"端口 {self.cdp_port} 在监听，但 CDP 连接失败: {e}\n"
                f"可能原因：\n"
                f"  - 该端口不是 Electron/Chromium 的调试端口\n"
                f"  - Playwright 版本与应用内核不兼容"
            )

    # ─── launch 模式 ───────────────────────────────────────────

    def launch(self) -> Page:
        """启动应用（自动带 --remote-debugging-port），等待 CDP 就绪后连接"""
        exe_path = self.app_config.get("exe_path")
        if not exe_path:
            raise ValueError(
                "未指定应用路径。请使用以下方式之一:\n"
                "  1. 命令行: AIoT-auto-test.exe --launch --app-path \"C:\\路径\\应用.exe\"\n"
                "  2. 配置文件: 修改 config.yaml 中的 app.exe_path"
            )

        # ── 1. 端口已占用？可能是应用已在运行 ──
        if self._port_in_use():
            if self._cdp_is_ready():
                logger.info(f"端口 {self.cdp_port} 已有 CDP 服务，直接连接...")
                self._playwright = sync_playwright().start()
                try:
                    return self._connect_cdp()
                except Exception:
                    logger.warning("CDP 服务在但连接失败，将重新启动应用")
            else:
                raise RuntimeError(
                    f"端口 {self.cdp_port} 已被其他程序占用，但不是 CDP 服务。\n"
                    f"请关闭占用该端口的程序，或在 config.yaml 中修改 app.cdp_port。"
                )

        # ── 2. 启动应用 ──
        logger.info(f"正在启动应用: {exe_path}")
        cmd = [exe_path, f"--remote-debugging-port={self.cdp_port}"]
        logger.debug(f"启动命令: {cmd}")

        try:
            # Windows: CREATE_NEW_PROCESS_GROUP 让子进程独立于父进程
            creationflags = 0
            try:
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            except AttributeError:
                pass  # 非 Windows

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
            )
        except FileNotFoundError:
            raise RuntimeError(
                f"找不到应用: {exe_path}\n"
                f"请检查路径是否正确。"
            )
        except Exception as e:
            raise RuntimeError(f"启动应用失败: {e}")

        # ── 3. 等待 CDP 就绪 ──
        if not self._wait_for_cdp():
            # 检查进程是否已退出
            if self._process and self._process.poll() is not None:
                raise RuntimeError(
                    f"应用启动后立即退出 (退出码: {self._process.returncode})。\n"
                    f"请检查应用路径: {exe_path}"
                )
            raise RuntimeError(
                f"应用启动超时 ({self.startup_timeout}s)，CDP 端口 {self.cdp_port} 未就绪。\n"
                f"可能原因：\n"
                f"  - 应用不支持 --remote-debugging-port 参数\n"
                f"  - 应用启动太慢，可增加 config.yaml 中 app.startup_timeout\n"
                f"  - 防火墙阻止了 localhost:{self.cdp_port}"
            )

        # ── 4. 通过 Playwright CDP 连接 ──
        logger.info("CDP 就绪，正在通过 Playwright 连接...")
        self._playwright = sync_playwright().start()
        try:
            page = self._connect_cdp()
            page.wait_for_load_state("domcontentloaded")
            return page
        except Exception as e:
            raise RuntimeError(
                f"应用已启动但 Playwright CDP 连接失败: {e}\n"
                f"CDP 端口 {self.cdp_port} 正常响应，可能是 Playwright 兼容性问题。"
            )

    # ─── 生命周期管理 ──────────────────────────────────────────

    def close(self):
        """关闭连接；如果是我们启动的进程，根据配置决定是否终止"""
        logger.info("正在关闭连接...")

        if self._playwright:
            try:
                self._playwright.stop()
            except Exception as e:
                logger.warning(f"停止 Playwright 时出错: {e}")

        if self._process and self._process.poll() is None:
            kill_on_exit = self.app_config.get("kill_on_exit", False)
            if kill_on_exit:
                logger.info("正在关闭已启动的应用...")
                try:
                    self._process.terminate()
                    self._process.wait(timeout=5)
                except Exception:
                    try:
                        self._process.kill()
                    except Exception:
                        pass
            else:
                logger.info("应用保持运行（如需自动关闭，设置 config: app.kill_on_exit: true）")

        self._page = None
        self._context = None
        self._process = None
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
