# tests/test_offline_replay.py
import cv2
import numpy as np
import time
import os
import sys
import json

# --- 1. 绝对路径与模块寻址 ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR) # 赋予 Python 寻找 src 模块的视野

from src.vision.tracker import GalinstanTracker

# ⚠️ 确保此处的文件夹名与你实际数据资产匹配
DATA_FOLDER = os.path.join(BASE_DIR, "data", "captures_20260408_145115") 
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
FPS = 30
FRAME_DELAY = int(1000 / FPS)

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return None

def main():
    video_names = ["1_Pre.avi", "2_Mask.avi", "3_Blob.avi", "4_Console.avi"]
    caps = []

    print("🔌 正在连接离线数据资产...")
    for name in video_names:
        path = os.path.join(DATA_FOLDER, name)
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            print(f"❌ 严重错误: 无法打开 {path}")
            return
        caps.append(cap)
        
    print("🚀 数字孪生风洞已启动 | 监听 UI 参数中 | 按 [q] 退出")
    
    # 实例化视觉大脑
    tracker = GalinstanTracker(buffer_sec=2, fps=FPS)

    try:
        while True:
            frames = []
            for cap in caps:
                ret, frame = cap.read()
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()
                frames.append(frame)

            # --- 2. 实时热更新参数 ---
            cfg = load_config()
            if cfg:
                tracker.update_params({
                    "C": cfg.get("vis_thresh_C", 6),
                    "kernel": cfg.get("vis_kernel_size", 7),
                    "min_area": cfg.get("vis_min_area", 300)
                })

            # --- 3. 截断式物理仿真 ---
            # 直接提取第一路视频（预处理后的图像），还原为灰度图输入算法
            gray_input = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
            
            # 手动调用底层方法以测试参数响应
            mask = tracker._segment(gray_input, debug=False)
            pos, blob_canvas = tracker._find_blob(mask, debug=False)

            # --- 4. 动态面板渲染 ---
            # 将掩膜图转为彩色以便拼接
            mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            
            top_row = np.hstack((frames[0], mask_bgr))
            bottom_row = np.hstack((blob_canvas, frames[3]))
            dashboard = np.vstack((top_row, bottom_row))

            cv2.imshow("Galinstan Offline Simulation", cv2.resize(dashboard, (0, 0), fx=0.7, fy=0.7))

            if cv2.waitKey(FRAME_DELAY) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("\n检测到中断。")
    finally:
        for cap in caps: cap.release()
        cv2.destroyAllWindows()
        print("📦 仿真流已安全关闭。")

if __name__ == "__main__":
    main()