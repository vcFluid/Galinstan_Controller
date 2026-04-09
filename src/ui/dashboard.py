"""
--- dashboard.py v1.0 ---
目的：
此程序为整台引擎的“驾驶舱”，负责提供一个基于 Streamlit 的交互式界面，让用户能够实时调整视觉处理参数和动力学控制律的 PID 参数。
功能：
1. 参数调整面板：通过滑动条等交互组件，用户可以方便地调整视觉处理的阈值、形态学核大小、最小面积等参数，以及动力学控制律的 Kp、Ki、Kd 和目标位置等参数。
2. 实时热更新：当用户调整参数时，程序会将新的参数值写入根目录下的 config.json 文件，底层引擎会实时读取这个文件并应用新的参数，无需重启引擎。
3. 错误容忍设计：在读取 config.json 时，如果遇到文件正在被写入导致的 JSONDecodeError，程序会忽略这个错误并继续使用旧的参数，确保前端界面不会因为短暂的文件访问冲突而崩溃。
4. 绝对路径寻址：通过动态获取脚本所在目录的绝对路径，确保无论用户从哪个目录启动 Streamlit，都能正确找到 config.json 文件，消除空间坐标依赖。
需要注意的是，虽然这个程序设计了多个功能模块，但在实际应用中可能仍然会受到一些误差的影响，例如：
1. 文件访问冲突：当用户频繁调整参数时，可能会导致 config.json 文件在被写入时被底层引擎读取，触发 JSONDecodeError。虽然程序设计了错误容忍机制，但频繁的访问冲突可能会导致参数更新不及时。
2. 参数调整误差：用户在调整滑动条时可能会不小心将参数设置为不合理的值，例如过高的 Kp 可能会导致系统过度振荡，过低的 Ki 可能无法消除稳态误差等，这些都可能影响系统的性能和稳定性。
此外，引入的误差有
1. 用户操作误差：用户在调整参数时可能会不小心将参数设置为不合理的值，例如过高的 Kp 可能会导致系统过度振荡，过低的 Ki 可能无法消除稳态误差等，这些都可能影响系统的性能和稳定性。
2. 文件访问冲突：当用户频繁调整参数时，可能会导致 config.json 文件在被写入时被底层引擎读取，触发 JSONDecodeError。虽然程序设计了错误容忍机制，但频繁的访问冲突可能会导致参数更新不及时。
"""
import streamlit as st # Streamlit 是一个用于构建交互式数据应用的 Python 库，提供了丰富的组件和布局功能，使得开发者能够快速创建用户友好的界面。
import json # json 库用于处理 JSON 格式的数据，在这个程序中主要用于读取和写入 config.json 文件，以实现参数的持久化存储和热更新功能。
import os # os 库用于处理文件路径和系统相关的操作，在这个程序中主要用于获取脚本所在目录的绝对路径，确保能够正确找到 config.json 文件，无论用户从哪个目录启动 Streamlit。

# --- 1. 绝对路径锚定：消除空间坐标依赖 ---
# 无论在哪个目录下执行 streamlit run，它都能精准找到根目录的 config.json
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
# 这两个全局变量的目的是确保程序能够正确找到 config.json 文件，无论用户从哪个目录启动 Streamlit。通过动态获取脚本所在目录的绝对路径，消除了空间坐标依赖，增强了程序的鲁棒性和可移植性。
# 详情可以搜索关键词 "Python os.path.abspath" 和 "Python os.path.dirname" 来了解更多关于如何在 Python 中处理文件路径的知识。

def load_config():
    if os.path.exists(CONFIG_PATH): # 检查 config.json 文件是否存在，如果存在则尝试读取并解析 JSON 数据，如果文件不存在则返回 None。
        try:
            with open(CONFIG_PATH, 'r') as f: # 使用 with 语句打开 config.json 文件，确保在读取完成后文件能够正确关闭。'r' 模式表示以只读方式打开文件。
                return json.load(f) # 使用 json.load() 方法将文件内容解析为 Python 字典对象，并返回这个对象供程序使用。
        except json.JSONDecodeError:
            # 物理极值情况：如果恰好撞上 main.py 正在写入文件的微秒间隙，
            # 忽略本次读取错误，防止前端崩溃
            # 详情可以搜索关键词 "Python json.JSONDecodeError" 来了解更多关于 JSONDecodeError 异常的原因和处理方法。
            pass
            
    # 默认出厂物理参数矩阵，可供未来版本迭代时进行实验拟合更新
    return {
        "Kp": 0.4, "Ki": 0.01, "Kd": 0.1,  # 动力学控制律 PID 参数
        "TARGET_X": 320.0, "Critical_V": 1.2, # 物理边界条件：目标位置坐标和临界启动电压
        "vis_thresh_C": 6, "vis_kernel_size": 7, "vis_min_area": 300 # 视觉处理参数：阈值灵敏度、形态学核大小、液滴面积下限
    }

def save_config(data): # 将新的参数数据写入 config.json 文件，覆盖原有内容，实现参数的持久化存储和热更新功能。
    with open(CONFIG_PATH, 'w') as f: # 使用 with 语句以写入模式 ('w') 打开 config.json 文件，如果文件不存在则会创建一个新的文件，如果文件已经存在则会覆盖原有内容。
        json.dump(data, f, indent=4) # 使用 json.dump() 方法将 Python 字典对象 data 转换为 JSON 格式，并写入到文件中。参数 indent=4 用于美化输出，使得 JSON 文件更易读，层级结构清晰。
        # 详情可以搜索关键词 "Python json.dump" 来了解更多关于 json.dump() 方法的用法和参数选项。

# --- 2. 前端渲染管线 ---
st.set_page_config(page_title="Galinstan 控制中枢", layout="wide") 
st.title("🔬 Galinstan 动力学参数寻优平台")
st.markdown("调整以下物理与视觉参数，系统将实时热更新底层的 `config.json` 协议。")

"""
st.xxx() 是 Streamlit 提供的一个函数，用于设置页面的配置参数。
在这个程序中，
st.set_page_config() 被用来设置页面的标题和布局方式。
st.title() 用于在页面上显示一个大标题，st.markdown() 用于显示一段说明文本。
st.markdown() 支持 Markdown 语法，可以用来格式化文本内容，使得界面更美观和易读。
st.slider() 用于创建一个滑动条组件，允许用户在指定的范围内选择一个数值，这些数值将被用来更新 config.json 文件中的参数，实现实时热更新。
st.subheader() 用于在页面上显示一个小标题，帮助用户更好地理解不同参数的分类和作用。
st.columns() 用于创建多列布局，在这个程序中创建了两个等宽的列，分别用于放置视觉处理参数和动力学控制律的 PID 参数，通过这种布局方式，用户可以更清晰地看到不同类别的参数，并且在调整时不会混淆。
详情可以搜索关键词 "Streamlit st.set_page_config"、"Streamlit st.title" 和 "Streamlit st.markdown" 来了解更多关于这些 Streamlit 函数的用法和功能。
"""

# 加载当前状态
current_cfg = load_config() # 调用 load_config() 函数加载当前的参数配置，如果 config.json 文件存在且格式正确，则返回其中的参数数据；如果文件不存在或格式错误，则返回默认的参数矩阵。这个 current_cfg 变量将用于在前端界面上显示当前的参数值，并作为滑动条的初始值。

# 构建控制面板：将视觉与动力学解耦到左右两个象限
col1, col2 = st.columns(2) # Streamlit 的 st.columns() 函数用于创建多列布局，在这个程序中创建了两个等宽的列 col1 和 col2，分别用于放置视觉处理参数和动力学控制律的 PID 参数。通过这种布局方式，用户可以更清晰地看到不同类别的参数，并且在调整时不会混淆。

with col1:
    st.subheader("👁️ 视觉处理参数 (Tracker)")
    # 使用 .get() 方法：即使旧版 config.json 缺少这些键值，前端也不会崩溃报错
    new_C = st.slider("阈值灵敏度 (C) - 抵抗光照扰动", 0, 50, current_cfg.get("vis_thresh_C", 6))
    new_K = st.slider("形态学核大小 (Kernel) - 抹除物理杂质", 0, 15, current_cfg.get("vis_kernel_size", 7), step=2)
    new_area = st.slider("液滴面积下限 (Min Area) - 质量守恒过滤", 0, 5000, current_cfg.get("vis_min_area", 300))
    # st.slider() 函数的参数说明：
    # 第一个参数是滑动条的标签，第二个和第三个参数分别是滑动条的最小值和最大值，第四个参数是滑动条的初始值，这里使用 current_cfg.get() 方法从当前配置中获取对应的参数值，如果 config.json 中缺少这些键值，则使用默认值（例如 6、7、300）。step 参数用于指定滑动条的步长，例如 kernel 的步长为 2，确保用户只能选择奇数值。
    # 详情可以搜索关键词 "Streamlit st.slider" 来了解更多关于 st.slider() 函数的用法和参数选项。

with col2:
    st.subheader("⚙️ 动力学控制律 (Brain PID)")
    new_Kp = st.slider("比例系数 (Kp) - 刚度", 0.0, 5.0, current_cfg.get("Kp", 0.4), 0.1)
    new_Ki = st.slider("积分系数 (Ki) - 破冰锤", 0.0, 1.0, current_cfg.get("Ki", 0.01), 0.01)
    new_Kd = st.slider("微分系数 (Kd) - 阻尼器", 0.0, 2.0, current_cfg.get("Kd", 0.1), 0.05)
    
    st.subheader("📏 物理边界条件")
    new_target = st.slider("目标位置坐标 (TARGET_X)", 50.0, 600.0, current_cfg.get("TARGET_X", 320.0), 10.0)
    new_critical = st.slider("临界启动电压 (Critical_V)", 0.0, 10.0, current_cfg.get("Critical_V", 1.2), 0.1)

# --- 3. 状态对比与指令下发 ---
# 汇聚所有维度的状态张量
updated_cfg = {
    "Kp": new_Kp, "Ki": new_Ki, "Kd": new_Kd, 
    "TARGET_X": new_target, "Critical_V": new_critical,
    "vis_thresh_C": new_C, "vis_kernel_size": new_K, "vis_min_area": new_area
}
# 定义了updated_cfg字典，将用户通过滑动条调整后的参数值进行汇总，形成一个新的配置字典。
# 这个 updated_cfg 将用于与 current_cfg 进行对比，判断是否有参数发生了变化，从而决定是否需要将新的参数写入 config.json 文件，实现热更新。


# 只有当参数发生真实的物理位移时，才触发高耗能的 I/O 写入
if updated_cfg != current_cfg:
    save_config(updated_cfg)
    st.success("✅ 协议已更新！底层引擎将以新的物理参数运行。")