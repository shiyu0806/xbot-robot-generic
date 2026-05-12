"""
AIoT 认证测试平台 - 自动化工具

通用框架版本，替代来也 RPA 机器人
在 Windows 上运行，功能保持一致

使用方法:
    python main.py                    # 连接已运行的应用并执行
    python main.py --launch           # 启动新应用实例并执行
    python main.py --config config.yaml  # 指定配置文件
"""

import argparse
import os
import sys
import yaml
import logging
from pathlib import Path

from browser_manager import BrowserManager
from actions import AutomationActions
from logger import setup_logger


def get_app_dir() -> Path:
    """获取应用根目录（兼容 PyInstaller 打包和开发环境）"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后，_MEIPASS 是临时解压目录
        # 但用户目录更合适存放可修改的配置文件
        return Path(os.path.dirname(sys.executable))
    return Path(__file__).parent


def get_bundle_dir() -> Path:
    """获取打包资源目录"""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

logger = logging.getLogger(__name__)


def load_config(config_path: str = None) -> dict:
    """加载配置文件
    
    查找顺序：
    1. 用户指定的路径
    2. EXE 同目录下的 config.yaml（用户可修改）
    3. 打包资源中的 config.yaml（默认模板）
    """
    if config_path:
        # 用户明确指定了路径
        config_file = Path(config_path)
        if not config_file.exists():
            logger.error(f"配置文件不存在: {config_path}")
            sys.exit(1)
    else:
        # 自动查找
        app_dir = get_app_dir() / "config.yaml"
        bundle_dir = get_bundle_dir() / "config.yaml"
        
        if app_dir.exists():
            config_file = app_dir
        elif bundle_dir.exists():
            config_file = bundle_dir
            # 如果 EXE 目录没有，自动从打包资源复制一份
            try:
                import shutil
                shutil.copy2(str(bundle_dir), str(app_dir))
                logger.info(f"已从打包资源复制默认配置到: {app_dir}")
            except Exception as e:
                logger.warning(f"无法复制默认配置文件: {e}")
        else:
            logger.error(
                f"配置文件不存在！请在以下位置放置 config.yaml:\n"
                f"  {app_dir}\n"
                f"或使用 --config 参数指定路径"
            )
            sys.exit(1)
        config_file = app_dir if app_dir.exists() else bundle_dir
    
    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    logger.info(f"已加载配置: {config_file}")
    return config


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="AIoT 认证测试平台自动化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python main.py                          # 连接已运行的应用
    python main.py --launch                 # 启动新实例
    python main.py --row 2 --cell 5         # 指定行和列
    python main.py --config my_config.yaml  # 使用自定义配置
        """
    )
    
    parser.add_argument(
        "--config", "-c",
        default=None,
        help="配置文件路径 (默认: 自动查找 EXE 目录或打包资源中的 config.yaml)"
    )
    
    parser.add_argument(
        "--launch", "-l",
        action="store_true",
        help="启动新的应用实例（默认连接已运行实例）"
    )
    
    parser.add_argument(
        "--row", "-r",
        type=int,
        default=None,
        help="表格行索引（从0开始），覆盖配置文件值"
    )
    
    parser.add_argument(
        "--cell",
        type=int,
        default=None,
        help="表格单元格索引（从0开始），覆盖配置文件值"
    )
    
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="启用调试模式"
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 调试模式覆盖日志级别
    if args.debug:
        config.setdefault("logging", {})["level"] = "DEBUG"
    
    # 初始化日志
    setup_logger(config)
    
    logger.info("=" * 60)
    logger.info("AIoT 认证测试平台 - 自动化工具启动")
    logger.info("=" * 60)
    
    # 确定连接模式
    if args.launch:
        config["app"]["connect_mode"] = "launch"
        logger.info("模式: 启动新实例")
    else:
        config["app"]["connect_mode"] = "connect"
        logger.info("模式: 连接已运行实例")
    
    try:
        # 连接/启动应用
        with BrowserManager(config) as browser:
            page = browser.page
            
            # 创建自动化操作实例
            actions = AutomationActions(page, config)
            
            # 显示当前页面信息
            title = actions.get_page_title()
            logger.info(f"当前页面: {title}")
            
            # 执行完整工作流
            actions.execute_full_workflow(
                row_index=args.row,
                cell_index=args.cell
            )
            
            logger.info("所有操作已完成")
            
    except KeyboardInterrupt:
        logger.info("用户中断操作")
        sys.exit(0)
    except RuntimeError as e:
        logger.error(f"执行失败:\n{e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("程序结束")


if __name__ == "__main__":
    main()
