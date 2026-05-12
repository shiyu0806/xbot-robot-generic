# AIoT 认证测试平台 - 自动化工具

通用框架版本，替代来也 RPA 机器人，在 Windows 上运行。

## 功能

自动化操作 AIoT 认证测试平台（Electron 应用）：

1. 点击表格中的操作按钮（圆形图标）
2. 在弹出的对话框中点击"上传报告"按钮
3. 等待操作完成

## 环境要求

- Windows 10/11
- AIoT 认证测试平台已安装

## 使用 EXE（推荐）

从 [GitHub Actions](https://github.com/shiyu0806/xbot-robot-generic/actions) 下载最新构建产物 `AIoT-auto-test-win64`，解压后使用。

### 方式一：自动启动应用（推荐）

EXE 会自动启动 AIoT 认证测试平台（带调试端口），无需手动操作：

```cmd
AIoT-auto-test.exe --launch --app-path "C:\Users\时雨\AIoT Certification Studio\AIoT Certification Studio.exe"
```

### 方式二：连接已运行的应用

如果应用已经在运行，需要确保启动时带了 `--remote-debugging-port=9222` 参数：

```cmd
AIoT-auto-test.exe
```

### 指定表格行和列

```cmd
AIoT-auto-test.exe --launch --app-path "C:\...\AIoT Certification Studio.exe" --row 2 --cell 5
```

## 命令行参数

| 参数 | 简写 | 说明 |
|------|------|------|
| `--config` | `-c` | 配置文件路径（默认: EXE 同目录的 config.yaml） |
| `--launch` | `-l` | 启动新应用实例（默认连接已运行实例） |
| `--app-path` | `-a` | 目标应用 EXE 路径（用于 --launch 模式） |
| `--row` | `-r` | 表格行索引（从0开始） |
| `--cell` | | 表格单元格索引（从0开始） |
| `--debug` | `-d` | 启用调试模式 |

## 配置文件

`config.yaml`（首次运行自动从 EXE 中复制到 EXE 同目录，可自行修改）：

```yaml
app:
  exe_path: "C:/Program Files/AIoT Certification Studio/AIoT Certification Studio.exe"
  connect_mode: "connect"
  cdp_port: 9222               # CDP 调试端口
  startup_timeout: 30          # 启动等待超时（秒）
  kill_on_exit: false          # 退出时是否关闭应用

timeout:
  page_load: 30
  element_wait: 10
  dialog_wait: 5
  action_delay: 1

selectors:
  table:
    container: ".ctrl-table .t-table__content table.t-table--layout-fixed"
  action_button:
    row_index: 2
    cell_index: 5
  upload_report:
    css: ".t-dialog__footer button.t-dialog__confirm"
```

## 从源码运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 安装 Playwright 浏览器驱动
playwright install chromium

# 3. 运行
python main.py --launch --app-path "C:\...\AIoT Certification Studio.exe"
```

## 项目结构

```
xbot_robot_generic/
├── main.py                 # 主入口
├── browser_manager.py      # CDP 连接管理（subprocess + Playwright）
├── actions.py              # 自动化操作实现
├── logger.py               # 日志配置
├── config.yaml             # 配置文件
├── requirements.txt        # Python 依赖（仅 playwright + pyyaml）
└── README.md               # 本文件
```

## 故障排除

### 1. "端口未在监听"
应用未启动，或未带 `--remote-debugging-port` 参数。使用 `--launch` 模式自动处理。

### 2. "CDP 连接失败"
端口被其他程序占用。检查 `netstat -ano | findstr 9222`，或在 config.yaml 中换一个端口。

### 3. "应用启动超时"
应用启动太慢，增加 config.yaml 中的 `app.startup_timeout` 值。

### 4. 元素未找到
检查 config.yaml 中的选择器配置是否与实际页面匹配，可能需要调整行/列索引。

## 许可证

内部工具，仅供团队使用。
