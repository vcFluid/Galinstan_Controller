# src/ui/dashboard.py
import streamlit as st
import json
import os

# --- 1. 绝对路径锚定：消除空间坐标依赖 ---
# 无论你在哪个目录下执行 streamlit run，它都能精准找到根目录的 config.json
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # 物理极值情况：如果恰好撞上 main.py 正在写入文件的微秒间隙，
            # 忽略本次读取错误，防止前端崩溃
            pass
            
    # 默认出厂物理参数矩阵
    return {
        "Kp": 0.4, "Ki": 0.01, "Kd": 0.1, 
        "TARGET_X": 320.0, "Critical_V": 1.2,
        "vis_thresh_C": 6, "vis_kernel_size": 7, "vis_min_area": 300
    }

def save_config(data):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=4)

# --- 2. 前端渲染管线 ---
st.set_page_config(page_title="Galinstan 控制中枢", layout="wide")
st.title("🔬 Galinstan 动力学参数寻优平台")
st.markdown("调整以下物理与视觉参数，系统将实时热更新底层的 `config.json` 协议。")

# 加载当前状态
current_cfg = load_config()

# 构建控制面板：将视觉与动力学解耦到左右两个象限
col1, col2 = st.columns(2)

with col1:
    st.subheader("👁️ 视觉处理参数 (Tracker)")
    # 使用 .get() 方法：即使旧版 config.json 缺少这些键值，前端也不会崩溃报错
    new_C = st.slider("阈值灵敏度 (C) - 抵抗光照扰动", 2, 20, current_cfg.get("vis_thresh_C", 6))
    new_K = st.slider("形态学核大小 (Kernel) - 抹除物理杂质", 3, 15, current_cfg.get("vis_kernel_size", 7), step=2)
    new_area = st.slider("液滴面积下限 (Min Area) - 质量守恒过滤", 50, 5000, current_cfg.get("vis_min_area", 300))

with col2:
    st.subheader("⚙️ 动力学控制律 (Brain PID)")
    new_Kp = st.slider("比例系数 (Kp) - 刚度", 0.0, 5.0, current_cfg.get("Kp", 0.4), 0.1)
    new_Ki = st.slider("积分系数 (Ki) - 破冰锤", 0.0, 1.0, current_cfg.get("Ki", 0.01), 0.01)
    new_Kd = st.slider("微分系数 (Kd) - 阻尼器", 0.0, 2.0, current_cfg.get("Kd", 0.1), 0.05)
    
    st.subheader("📏 物理边界条件")
    new_target = st.slider("目标位置坐标 (TARGET_X)", 50.0, 600.0, current_cfg.get("TARGET_X", 320.0), 10.0)
    new_critical = st.slider("临界启动电压 (Critical_V)", 0.0, 3.0, current_cfg.get("Critical_V", 1.2), 0.1)

# --- 3. 状态对比与指令下发 ---
# 汇聚所有维度的状态张量
updated_cfg = {
    "Kp": new_Kp, "Ki": new_Ki, "Kd": new_Kd, 
    "TARGET_X": new_target, "Critical_V": new_critical,
    "vis_thresh_C": new_C, "vis_kernel_size": new_K, "vis_min_area": new_area
}

# 只有当参数发生真实的物理位移时，才触发高耗能的 I/O 写入
if updated_cfg != current_cfg:
    save_config(updated_cfg)
    st.success("✅ 协议已更新！底层引擎将以新的物理边界运行。")