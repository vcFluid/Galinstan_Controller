# Galinstan_Controller: 借助视觉反馈的液态金属控制平台

> **“将连续的物理流场离散化为数字信号，再将逻辑决策还原为物理界面的定向运动。”**
> 本项目利用改装的 3D 打印平台与计算机视觉，构建了一个针对 NaOH 溶液中液态金属（Galinstan）电毛细效应（Electrocapillarity）的软硬闭环控制系统。
> 在 B 站 UP 主 [大鱼DIY] 的 3D 打印机开源项目基础上，本团队根据需求删繁就简，进行了独创。
> 原创跳转链接：[大鱼DIY 空间](https://space.bilibili.com/488684813/upload/video)

---

## 1. 核心思想与物理基础
本项目拒绝纯粹的“黑盒调参”，坚持以流体力学第一性原理为驱动：
* **物理内核**：基于 **Lippmann 方程**，界面张力 $\gamma$ 与电势差 $V$ 的关系可表述为：
  $$\gamma = \gamma_0 - \frac{1}{2} c V^2$$
  通过控制电极电势产生张力梯度 $\nabla \gamma$，驱动液滴产生 **Marangoni 流动**，从而实现非接触式驱动。
* **工程架构**：采用感知-分析-执行（Sense-Think-Act）解耦架构，实现底层硬件与高层控制律的物理隔离。
* **开发原则**：最小化精力耗散。通过本项目最大化学习模块化开发范式，所有建议服务于“最终前往一个尊重自由思想和基础学术的地方”这一长远目标。

## 2. 系统架构 (System Architecture)
系统由四个高度解耦的模块构成，通过 `config.json` 协议实现软总线通讯：

* **[Init] 硬件驱动层 (`/drivers`)**：封装底层硬件（摄像头、Arduino 串口通讯）的初始化，屏蔽通讯细节。
* **[Sense] 视觉捕捉层 (`src/vision`)**：利用 OpenCV 连续时域观测器。引入 CLAHE 增强与双边滤波，将液滴降维映射为状态空间的坐标矩阵 $(x, y, t)$。
* **[Think] 动力学分析 (`src/analysis`)**：物理引擎层。计算误差 $e(t) = x_{target} - x(t)$，利用带积分抗饱和的 PID 算子将位移偏差反演为理想电压指令。
* **[Act] 物理执行层 (`src/control`)**：将数字逻辑映射为物理电极的 PWM 电信号，包含安全限幅与死区补偿逻辑。
* **[Bus] 共享协议层 (`config.json`)**：作为系统的“共享寄存器”，支撑视觉阈值与控制律参数的实时热更新。



## 3. 知识资产树 (Directory Structure)
```text
├── README.md               # 项目白皮书与架构说明
├── environment.yml         # Conda 'fluid' 运行环境镜像
├── config.json             # 核心协议层：实时参数寻优接口
├── /drivers                # 硬件接口封装：camera_check
├── /src                    # 核心逻辑源码
│   ├── vision/             # tracker.py: 动态追踪与滤波算法
│   ├── analysis/           # Brain.py: 电驱动力与粘性阻力演算模型
│   ├── control/            # actuator.py: 串口通信与执行器映射
│   └── ui/                 # dashboard.py: Streamlit 交互式参数寻优平台
└── /tests                  # 离线仿真与模块测试
    └── test_offline_replay.py # 数字孪生回放系统：支持实验数据回溯
```

## 4. 演进路线图 (Evolution Roadmap)
* **阶段一：离散开环（已完成）**
  * 建立 Baseline：输入坐标 $\rightarrow$ 物理建模 $\rightarrow$ 执行输出。
* **阶段二：一维闭环反馈（当前攻坚）**
  * 引入实时视觉误差补偿，建立闭环反馈系统，克服氧化层演变带来的非线性摩擦力干扰。
* **阶段三：二维矢量合成（未来资产）**
  * 对平板电极进行空间离散化，合成指向目标坐标的合力矢量 $\vec{F}_{total}$，实现复杂轨迹运动。

## 5. 部署与复现 (Deployment & Reproduction)
### 软件环境
```bash
# 创建并激活物理仿真环境
conda env create -f environment.yml
conda activate fluid
```
### 引擎启动
1. **启动控制中枢（仪表盘）**：
   ```bash
   streamlit run src/ui/dashboard.py
   ```
2. **唤醒执行引擎**：
   ```bash
   python src/main.py
   ```
* **快捷键操作**：按下 `[t]` 切换目标点，按下 `[s]` 启动 **4秒瞬态捕捉**（同步录制 Raw/Mask/Blob 数据）。

## 6. 收获与反思 (Gains & Reflections)
* **物理模型的不确定性**：开环控制的失效让我深刻认识到液态金属非定常动力学过程的复杂性。Feedback 的引入是将理论公式拉回现实物理世界的必要“锚点”。
* **架构解耦的价值**：通过构建可视化的调参前端，成功将“工程架构设计”与“参数敏感度分析”解耦，极大提高了科研效率与系统的鲁棒性。
* **数字孪生的意义**：通过 `test_offline_replay.py` 实现的离线回放，让我们在脱离实验室硬件的情况下，依然能对算法进行“干跑”优化。
