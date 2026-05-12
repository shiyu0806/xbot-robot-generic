"""
自动化操作模块

实现 AIoT 认证测试平台的具体自动化操作
对应原始来也 RPA 机器人的功能
"""

import time
import logging
from typing import Optional

from playwright.sync_api import Page, Locator, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)


class AutomationActions:
    """AIoT 认证测试平台自动化操作"""
    
    def __init__(self, page: Page, config: dict):
        self.page = page
        self.config = config
        self.timeout_config = config.get("timeout", {})
        self.selector_config = config.get("selectors", {})
        
        # 超时设置（毫秒）
        self.element_timeout = self.timeout_config.get("element_wait", 10) * 1000
        self.dialog_timeout = self.timeout_config.get("dialog_wait", 5) * 1000
        self.action_delay = self.timeout_config.get("action_delay", 1)
    
    def _get_table_selector(self) -> str:
        """获取表格容器选择器"""
        return self.selector_config.get("table", {}).get(
            "container",
            ".ctrl-table .t-table__content table.t-table--layout-fixed"
        )
    
    def _get_action_button_selector(self, row_index: int = None, cell_index: int = None) -> str:
        """获取操作按钮选择器"""
        action_config = self.selector_config.get("action_button", {})
        row = row_index if row_index is not None else action_config.get("row_index", 2)
        cell = cell_index if cell_index is not None else action_config.get("cell_index", 5)
        
        table = self._get_table_selector()
        # nth-child 是 1-based，所以 +1
        return f"{table} tr:nth-child({row + 1}) td:nth-child({cell + 1}) button.operation-icon svg.circle-icon"
    
    def _get_upload_button_selector(self) -> str:
        """获取上传报告按钮选择器"""
        return self.selector_config.get("upload_report", {}).get(
            "css",
            ".t-dialog__footer button.t-dialog__confirm"
        )
    
    def click_table_action_button(self, row_index: int = None, cell_index: int = None):
        """
        点击表格中的操作按钮（圆形图标）
        
        对应原始选择器: Graphic / Graphic_1
        
        Args:
            row_index: 行索引（从0开始），默认使用配置值
            cell_index: 单元格索引（从0开始），默认使用配置值
        """
        selector = self._get_action_button_selector(row_index, cell_index)
        logger.info(f"点击表格操作按钮: row={row_index}, cell={cell_index}")
        logger.debug(f"选择器: {selector}")
        
        try:
            # 等待元素出现
            button = self.page.locator(selector).first
            button.wait_for(state="visible", timeout=self.element_timeout)
            
            # 滚动到元素位置
            button.scroll_into_view_if_needed()
            time.sleep(0.3)
            
            # 点击
            button.click()
            logger.info("已点击操作按钮")
            
            # 等待操作生效
            time.sleep(self.action_delay)
            
        except PlaywrightTimeout:
            logger.error(f"操作按钮未找到或不可见 (超时: {self.timeout_config.get('element_wait', 10)}s)")
            raise
        except Exception as e:
            logger.error(f"点击操作按钮失败: {e}")
            raise
    
    def click_upload_report_button(self):
        """
        点击"上传报告"按钮
        
        对应原始选择器: PushButton_上传报告
        该按钮位于弹出的对话框底部
        """
        selector = self._get_upload_button_selector()
        logger.info("点击上传报告按钮...")
        
        try:
            # 等待对话框出现
            dialog = self.page.locator(".t-dialog__footer")
            dialog.wait_for(state="visible", timeout=self.dialog_timeout)
            
            # 查找并点击按钮
            button = self.page.locator(selector)
            button.wait_for(state="visible", timeout=self.element_timeout)
            
            # 确认按钮文本
            button_text = button.text_content()
            logger.info(f"按钮文本: {button_text}")
            
            # 点击
            button.click()
            logger.info("已点击上传报告按钮")
            
            # 等待操作生效
            time.sleep(self.action_delay)
            
        except PlaywrightTimeout:
            logger.error("上传报告按钮未找到或对话框未弹出")
            raise
        except Exception as e:
            logger.error(f"点击上传报告按钮失败: {e}")
            raise
    
    def wait_for_dialog_close(self, timeout: Optional[int] = None):
        """等待对话框关闭"""
        timeout_ms = (timeout or self.timeout_config.get("dialog_wait", 5)) * 1000
        
        try:
            self.page.locator(".t-dialog__ctx").wait_for(state="hidden", timeout=timeout_ms)
            logger.info("对话框已关闭")
        except PlaywrightTimeout:
            logger.warning("对话框未在预期时间内关闭")
    
    def get_table_row_count(self) -> int:
        """获取表格行数"""
        table_selector = self._get_table_selector()
        rows = self.page.locator(f"{table_selector} tbody tr")
        count = rows.count()
        logger.info(f"表格行数: {count}")
        return count
    
    def get_page_title(self) -> str:
        """获取当前页面标题"""
        title = self.page.title()
        logger.info(f"页面标题: {title}")
        return title
    
    def execute_full_workflow(self, row_index: int = None, cell_index: int = None):
        """
        执行完整的自动化工作流
        
        对应原始来也 RPA 机器人的 main 流程：
        1. 点击表格中的操作按钮
        2. 等待对话框弹出
        3. 点击上传报告按钮
        4. 等待对话框关闭
        
        Args:
            row_index: 行索引（从0开始）
            cell_index: 单元格索引（从0开始）
        """
        logger.info("=" * 50)
        logger.info("开始执行自动化工作流")
        logger.info("=" * 50)
        
        try:
            # 步骤1: 点击操作按钮
            logger.info("[步骤 1/4] 点击表格操作按钮...")
            self.click_table_action_button(row_index, cell_index)
            
            # 步骤2: 等待对话框
            logger.info("[步骤 2/4] 等待对话框弹出...")
            time.sleep(1)  # 给对话框动画时间
            
            # 步骤3: 点击上传报告
            logger.info("[步骤 3/4] 点击上传报告按钮...")
            self.click_upload_report_button()
            
            # 步骤4: 等待完成
            logger.info("[步骤 4/4] 等待操作完成...")
            self.wait_for_dialog_close()
            
            logger.info("=" * 50)
            logger.info("工作流执行完成")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            raise
