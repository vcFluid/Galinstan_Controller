import os
import json
import streamlit as st

# --- 1. 绝对路径锚定：消除空间坐标依赖 ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

def load_config():
    """读取底层物理协议参数"""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass # 规避 I/O 读写微秒级冲突
            
    # 出厂物理参数矩阵 (已剔除失效的视觉参数)
    return {
        "Kp": 0.4, "Ki": 0.01, "Kd": 0.1,
        "TARGET_X": 320.0, "Critical_V": 1.2
    }

def save_config(data):
    """持久化存储热更新参数"""
    with open(CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=4)

# --- 2. 前端渲染管线 ---
st.set_page_config(page_title="Galinstan 控制中枢", layout="centered") 
st.title("🔬 Galinstan 动力学参数寻优平台")
st.markdown("调整以下物理参数，系统将实时热更新底层的 `config.json` 协议。")

current_cfg = load_config()

# 构建控制面板：视觉已全自动剥离，全功率聚焦动力学
st.subheader("⚙️ 动力学控制律 (Brain PID)")
# Kp: 虚拟弹簧刚度，决定拉向目标点的初始爆发力
new_Kp = st.slider("比例系数 (Kp) - 刚度", 0.0, 5.0, current_cfg.get("Kp", 0.4), 0.1)
# Ki: 破冰锤，用于消除长时间悬停在目标点附近的静态误差
new_Ki = st.slider("积分系数 (Ki) - 稳态误差消除", 0.0, 1.0, current_cfg.get("Ki", 0.01), 0.01)
# Kd: 逻辑阻尼器，监测速度变化率，防止液滴刹不住车冲过头
new_Kd = st.slider("微分系数 (Kd) - 物理刹车", 0.0, 2.0, current_cfg.get("Kd", 0.1), 0.05)

st.subheader("📏 物理边界条件")
new_target = st.slider("目标位置坐标 (TARGET_X)", 50.0, 600.0, current_cfg.get("TARGET_X", 320.0), 10.0)
new_critical = st.slider("临界启动电压 (Critical_V) - 克服静摩擦死区", 0.0, 10.0, current_cfg.get("Critical_V", 1.2), 0.1)

# --- 3. 状态对比与指令下发 ---
updated_cfg = {
    "Kp": new_Kp, "Ki": new_Ki, "Kd": new_Kd, 
    "TARGET_X": new_target, "Critical_V": new_critical
}

# 物理张量发生位移时触发 I/O 写入
if updated_cfg != current_cfg:
    save_config(updated_cfg)
    st.success("✅ 协议已更新！底层控制引擎将实时捕获新参数。")