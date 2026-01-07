# AIR780E USB 短信 CLI 工具

这是一个用于 **AIR780E（USB 版本）** 的命令行工具，支持 **发送和接收短信（SMS）**。

* **接收短信**：自动监听模块的短信通知，并转发保存到本地文件
* **发送短信**：通过命令行直接向指定手机号发送短信

## 使用说明

### 准备工作

请确保当前用户有权限访问串口设备（`/dev/tty*`）：

```bash
sudo usermod -aG dialout $USER
```

执行完成后，**注销并重新登录**，使用户组变更生效。

### Python 运行环境

本项目使用 `uv` 进行 Python 虚拟环境和依赖管理。

在项目根目录下运行：

```bash
uv sync
```

该命令会创建虚拟环境并安装所需依赖。

### 监听并接收短信

启动短信监听服务，将收到的短信写入本地文件 `messages.jsonl`：

```bash
uv run air780e listen
```

程序会持续运行，实时解析并记录模块收到的短信。

### 发送测试短信

向指定手机号发送一条短信：

```bash
uv run air780e send-sms --phone 1234567890 --message "Hello, World!"
```

* `--phone`：目标手机号码
* `--message`：短信内容（文本模式）

## 当前固件与兼容性说明

* 当前版本基于 **AIR780E 固件 v7.2**
* 使用的 AT 指令集版本为 **v1.6.7**
  👉 参考文档：
  [上海合宙 AT命令手册V1.6.7.pdf](https://docs.openluat.com/cdn/上海合宙Cat.1模块%28移芯EC618&EC716&EC718平台系列%29AT命令手册V1.6.7.pdf)


### 测试环境

* 操作系统：Ubuntu 24.04
* Python 版本：Python 3.12

## 历史版本说明

旧版本代码保存在以下分支中：

```
archive/v2.0
```

* 该历史分支`archive/v2.0`与较新的 AIR780E 固件不兼容
* 原因：AIR780E 新固件的 **AT 指令集发生了较大变更**

如果你使用的是 **当前或较新的固件版本**，请务必使用 `main` 分支中的最新实现。

## 参考文档

- [AT Command Intro (合宙模组典型上网业务的 AT 上网流程)](https://docs.openluat.com/air780e/common/Air_AT/)
- [AT Command Set (Air780E模块AT指令手册)](https://docs.openluat.com/air780e/at/app/at_command/)
