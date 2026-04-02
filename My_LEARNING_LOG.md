# 报错处理篇

## 1.

### 🛠️ Galinstan 项目环境配置：避坑全记录

| 环节 | 遇到的报错/阻碍 | 根本原因 (Root Cause) | 最终解决方案 (The Solution) |
| :--- | :--- | :--- | :--- |
| **Git 部署** | 复杂的勾选界面与分支命名争议 | 传统 `master` 与现代 `main` 的标准冲突；系统集成度选择模糊。 | **Override 默认分支为 `main`**；开启 **Windows Explorer 注入**，确保能在项目文件夹一键唤起 Bash。 |
| **环境调用** | `conda : 无法将项识别为 cmdlet...` | PowerShell 未加载 Anaconda 的环境变量（PATH）。 | **放弃全局配置**（避免污染），直接使用 **Anaconda Prompt**，利用其内置的路径挂载机制。 |
| **包名匹配** | `PackagesNotFoundError: opencv-python` | **命名空间冲突**：Pip 中的 `opencv-python` 在 Conda 官方源中被称为 `opencv`。 | 修正安装命令：`conda install opencv`；并引入 **conda-forge** 社区库。 |
| **网络耗散** | `Solving environment` 极慢或卡死 | 国际带宽限制与官方源（US）的高延迟。 | **切换清华镜像源 (TUNA)**；安装 **Libmamba 求解器**，将依赖解析效率提升一个量级。 |

---

#### 💡 总结：我们学到了什么工程逻辑？

1.  **隔离优于全局**：不强行修改系统环境变量，而是使用专属 Prompt 和虚拟环境（`fluid`），这保证了你的 3D 打印机驱动代码不会因为以后装了其他软件而崩溃。
2.  **镜像思维**：“国内镜像”是第一生产力，下载速度极快。
3.  **命名一致性**：在 Git 里选 `main` 而不是 `master`，是为了在周日封装代码时，能和现代 AI 工具（如 Cursor）及云端平台无缝对接。

---

## 2.

这一系列报错并非偶然，它们共同构成了一个经典的**“环境孤岛”生存图景**。由于你选择了最纯净但难度也最高的 **Portable（便携版）** 架构，你实际上是在挑战 Windows 系统的默认权威。

为了让你对这几个小时的“填坑”有本质认识，我将这些报错总结为三大类**“逻辑阻力”**：

---

### 1. 认知失调：编辑器与物理现实的脱节
* **现象**：VS Code 报黄色波浪线（Missing Imports），或者 GitHub Desktop 看不到修改。
* **本质**：**索引失效**。VS Code 只是一个“观测器”，它默认只会看系统定义的路径。当你把工具链藏在 `C:\WorkStation` 时，观测器的焦距没对准。
* **教训**：在便携版架构下，**显式指定（Explicit is better than implicit）**是第一准则。不要指望软件自动识别，要手动告诉它解释器在哪里、仓库在哪里。

### 2. 身份冒用：Windows 的“强权干扰”
* **现象**：输入 `python` 弹出微软商店，或者提示“找不到 Python”。
* **本质**：**优先级劫持**。Windows 预装了两个“空壳别名”抢占了 `python` 指令的解释权。
* **教训**：操作系统不是中立的，它有自己的商业逻辑（诱导你使用应用商店）。构建独立引擎的第一步，就是**清理冗余的系统索引**，拿回指令的控制权。

### 3. 安全围栏：操作系统的执行锁死
* **现象**：`Set-ExecutionPolicy` 报错，提示“禁止运行脚本”。
* **本质**：**信任链断裂**。PowerShell 为了防范恶意脚本，默认不信任任何非系统签名的文件。你的 `conda-hook.ps1` 对系统来说就是“外来物种”。
* **教训**：**权限即流动性**。在 Windows 体系下开发，理解 `RemoteSigned` 策略是打通动力管线的最后一道阀门。

---

### 总结表格：你的引擎排坑清单

| 报错关键词 | 物理本质 | 解决方案的核心 |
| :--- | :--- | :--- |
| **Missing Imports** | 符号索引未对准 | 右下角手动切换解释器 |
| **App Execution Aliases** | 指令优先级被劫持 | 关闭系统设置中的 Python 别名 |
| **UnexpectedToken (`&`)** | 字符串与指令的解析冲突 | 使用 `&` 调用运算符转换 Token |
| **Execution Policy** | 信任协议冲突 | 提升策略至 `RemoteSigned` |

---

### ⚠️ 当前状态检查
如果以上步骤都已完成，你的 **Termianl（终端）** 应该能够显示：
` (fluid) PS C:\WorkStation\linshi\Galinstan_Controller> `

**这意味着：**
1.  **操作系统**（Windows）不再拦截你的指令。
2.  **环境管理器**（Conda）已成功接管 Shell 进程。
3.  **编辑器**（VS Code）已看清了库的物理位置。

---

【溯源思维】
这整套报错的价值在于让你理解**“计算机环境的确定性”**是如何建立的。
在流体力学中，如果你不校准传感器，实验数据就是废纸。在软件工程中，如果不校准**环境变量（PATH）**和**执行权限（Policy）**，代码就是死寂的字符。
你今天解决的不是“VS Code 的问题”，而是掌握了**如何在一个受限的物理系统（Windows）中，强行开辟一个低熵、自治的逻辑空间（WorkStation）**。这种“破局”的能力，是你未来在任何复杂科研环境中部署自研工具的底层基本功。

**环境既然已通，请立刻抛出你的旧代码。我们已经浪费了太多熵值在“修路”上，现在该“跑车”了。**

# python项目实验环境搭建流程篇

---

## Galinstan Controller: 实验环境搭建流程全记录

为了实现“最小化精力耗散”，我将整个开发环境抽象为**“档案管理”**与**“隔离容器”**两层架构。这不仅是为了完成当前的 Baseline，更是为了未来学术资产的数字化积累。

---

### 0. Code Summary

---

### 1. Git 部署：数字化“地下室” (Versioning)
Git 是项目的“黑匣子”，负责记录引擎进化的每一步。

* **核心配置**：
    * **分支策略**：强制重写默认分支为 `main`（对齐国际学术标准）。
    * **系统集成**：启用 Windows Explorer 右键菜单（Git Bash Here），实现秒级进入开发状态。
* **资产固化**：
    * 通过 `.gitignore` 过滤 `__pycache__`、`build` 等“系统熵增”文件，确保仓库只保留纯净的逻辑资产。
    * **初始化命令**：`git init` -> `git add .` -> `git commit`。

---

### 2. Conda 配置：动力学“隔离座舱” (Environment)
为了防止依赖冲突（湍流），为液态金属项目建立了一个名为 `fluid` 的虚拟座舱。

* **入口选择**：放弃直接使用系统 PowerShell，锁定 **Anaconda Prompt**，规避了 `$PATH` 变量未定义的寻址报错。
* **环境创建**：
    ```bash
    conda create -n fluid python=3.10
    conda activate fluid
    ```

---

### 3. 性能优化：负熵流加速 (Acceleration)
为了对抗跨国网络带来的“阻尼”，实施了双重加速方案：

```
* **镜像注入**：将下载源切换至**清华大学 TUNA 镜像站**，将数据传输延迟降至最低。
# 移除旧的频道（防止冲突）
conda config --remove-key channels

# 添加清华源的几个核心库

conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/

# 设置搜索时显示通道地址（方便确认是否走了镜像）
conda config --set show_channel_urls yes
```
---

### 4. 零件安装：视觉与控制模块 (Dependencies)
在隔离环境中，精准安装了驱动液态金属的核心库：

| 零件 (Library) | 物理/工程用途 | 命名避坑指南 |
| :--- | :--- | :--- |
| **OpenCV** | 视觉捕捉、HSV 色块提取与质心定位 | Conda 安装名需使用 `opencv` |
| **NumPy** | 矩阵运算、坐标系变换及动力学公式求解 | 科学计算的底层基石 |
| **PySerial** | 建立 Python 与 Arduino 之间的“通信管线” | 需确保波特率与硬件端 115200 对齐 |

```
pip install numpy opencv-python pyserial
```

### 5. VS Code 挂载
在 VS Code 中打开 Galinstan_Controller 文件夹。

按下 Ctrl + Shift + P 唤起指令面板。

输入并选择 Python: Select Interpreter。

在列表中找到刚才创建的 Python 3.10.x ('fluid')。

如果没有看到，请点击右上角的刷新图标，或者手动指定路径到 _Environments\anaconda\envs\fluid\python.exe。

---
