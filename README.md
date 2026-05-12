# AIoT 认证测试平台 - 自动化工具

通用框架版本，替代来也 RPA 机器人，在 Windows 上运行。

## 功能

自动化操作 AIoT 认证测试平台（Electron 应用）：

1. 点击表格中的操作按钮（圆形图标）
2. 在弹出的对话框中点击"上传报告"按钮
3. 等待操作完成

## 环境要求

- Windows 10/11
- Python 3.8+
- AIoT 认证测试平台已安装

## 安装

```bash
# 1. 克隆或下载项目
cd xbot_robot_generic

# 2. 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装 Playwright 浏览器驱动
playwright install chromium
```

## 配置

编辑 `config.yaml` 文件：

```yaml
# 目标应用配置
app:
  # Electron 应用路径（Windows）
  exe_path: "C:/Program Files/AIoT Certification Studio/AIoT Certification Studio.exe"
  # 或者通过窗口标题查找已运行的应用
  window_title: "认证测试平台"
  # 连接模式: "launch" 启动新实例 | "connect" 连接已运行实例
  connect_mode: "connect"

# 选择器配置
selectors:
  action_button:
    row_index: 2          # 表格行索引（从0开始）
    cell_index: 5         # 单元格索引（从0开始）
```

## 使用方法

### 基本用法

```bash
# 连接已运行的应用并执行
python main.py

# 启动新应用实例并执行
python main.py --launch

# 指定配置文件
python main.py --config my_config.yaml
```

### 高级用法

```bash
# 指定表格行和列
python main.py --row 2 --cell 5

# 启用调试模式
python main.py --debug

# 组合使用
python main.py --launch --row 3 --cell 6 --debug
```

## 命令行参数

| 参数 | 简写 | 说明 |
|------|------|------|
| `--config` | `-c` | 配置文件路径（默认: config.yaml） |
| `--launch` | `-l` | 启动新应用实例（默认连接已运行实例） |
| `--row` | `-r` | 表格行索引（从0开始） |
| `--cell` | | 表格单元格索引（从0开始） |
| `--debug` | `-d` | 启用调试模式 |

## 项目结构

```
xbot_robot_generic/
├── main.py                 # 主入口
├── browser_manager.py      # 浏览器/Electron 应用管理
├── actions.py              # 自动化操作实现
├── logger.py               # 日志配置
├── config.yaml             # 配置文件
├── requirements.txt        # Python 依赖
└── README.md               # 本文件
```

## 从原始来也 RPA 机器人迁移

原始机器人使用来也 xbot 引擎和 ACC（Windows Accessibility API）选择器。

本框架使用 Playwright 和 CSS 选择器，功能完全一致：

| 来也选择器 | 本框架选择器 |
|-----------|-------------|
| Graphic | `table tr:nth-child(3) td:nth-child(6) button svg.circle-icon` |
| Graphic_1 | `table tr:nth-child(7) td:nth-child(22) button svg.circle-icon` |
| PushButton_上传报告 | `.t-dialog__footer button.t-dialog__confirm` |

## 连接已运行应用

如果使用 `connect` 模式，需要在启动 AIoT 认证测试平台时添加调试端口：

```bash
# 方法1: 修改应用快捷方式，添加启动参数
"AIoT Certification Studio.exe" --remote-debugging-port=9222

# 方法2: 在 config.yaml 中配置 exe_path，使用 launch 模式
app:
  connect_mode: "launch"
  exe_path: "C:/Program Files/AIoT Certification Studio/AIoT Certification Studio.exe"
```

## 日志

日志文件保存在 `logs/automation.log`，可通过 `--debug` 参数启用详细日志。

## 故障排除

### 1. 找不到应用窗口

确保 AIoT 认证测试平台已启动，并且窗口标题包含"认证测试平台"。

### 2. 元素未找到

检查 `config.yaml` 中的选择器配置是否正确，可能需要根据实际页面调整行/列索引。

### 3. 连接超时

如果使用 `connect` 模式，确保应用启动时带 `--remote-debugging-port=9222` 参数。

## 许可证

内部工具，仅供团队使用。
