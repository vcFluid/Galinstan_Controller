# src/ui/dashboard.py
import streamlit as st
import json
import os

CONFIG_PATH = "../config.json" # 确保路径与你的 main.py 统一

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    # 默认出厂参数
    return {"Kp": 0.4, "Ki": 0.01, "Kd": 0.1, "TARGET_X": 320.0, "Critical_V": 1.2}

def save_config(data):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=4)

st.set_page_config(page_title="Galinstan 控制中枢", layout="wide")
st.title("🔬 Galinstan 动力学参数寻优平台")
st.markdown("调整以下物理参数，系统将实时热更新底层动力学引擎。")





# 加载当前状态
current_cfg = load_config()

# 构建控制面板
col1, col2 = st.columns(2)

with col1:
    st.subheader("控制律算子 (PID)")
    new_Kp = st.slider("比例系数 (Kp) - 刚度", 0.0, 5.0, current_cfg["Kp"], 0.1)
    new_Ki = st.slider("积分系数 (Ki) - 破冰", 0.0, 1.0, current_cfg["Ki"], 0.01)
    new_Kd = st.slider("微分系数 (Kd) - 阻尼", 0.0, 2.0, current_cfg["Kd"], 0.05)

with col2:
    st.subheader("物理边界条件")
    new_target = st.slider("目标位置坐标 (TARGET_X)", 50.0, 600.0, current_cfg["TARGET_X"], 10.0)
    new_critical = st.slider("临界启动电压 (Critical_V)", 0.0, 3.0, current_cfg["Critical_V"], 0.1)

# 检测状态变化并下发指令
if (new_Kp != current_cfg["Kp"] or 
    new_Ki != current_cfg["Ki"] or 
    new_Kd != current_cfg["Kd"] or 
    new_target != current_cfg["TARGET_X"] or
    new_critical != current_cfg["Critical_V"]):
    
    updated_cfg = {
        "Kp": new_Kp, "Ki": new_Ki, "Kd": new_Kd, 
        "TARGET_X": new_target, "Critical_V": new_critical
    }
    save_config(updated_cfg)
    st.success("✅ 参数已热更新至底层物理引擎！")