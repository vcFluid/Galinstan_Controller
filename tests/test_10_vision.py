import cv2
import sys
import time
from collections import deque
from src.drivers.camera_check import get_available_cameras 
from src.vision.tracker import GalinstanTracker 

def save_video_stream(buffer, suffix, fps=30):
    """
    通用保存函数，支持彩色和灰度流
    """
    if not buffer: return
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"cap_{timestamp}_{suffix}.avi"
    
    h, w = buffer[0].shape[:2]
    # 判断是否为灰度图（2维），若是则需转换或指定颜色空间
    is_color = len(buffer[0].shape) == 3
    
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(filename, fourcc, fps, (w, h), is_color)
    
    for f in buffer:
        # VideoWriter 在 Windows 下通常期望 BGR 格式
        # 如果是灰度图，我们在此处进行一次逻辑转换
        write_f = f if is_color else cv2.cvtColor(f, cv2.COLOR_GRAY2BGR)
        out.write(write_f)
    
    out.release()
    print(f"✅ 已保存: {filename}")

def main():
    # --- 1. 初始化参数 ---
    fps = 30
    buf_len = fps * 4
    # 建立三路同步缓冲区
    raw_buf = deque(maxlen=buf_len)
    pre_buf = deque(maxlen=buf_len)
    msk_buf = deque(maxlen=buf_len)

    # ... (之前的摄像头初始化代码) ...
    indices = get_available_cameras()
    selected_idx = indices[0] # 简化演示，实际请保留交互逻辑
    cap = cv2.VideoCapture(selected_idx, cv2.CAP_DSHOW)
    referee = GalinstanTracker(buffer_sec=4, fps=fps)

    print("--- 多路同步追踪系统启动 | [s] 保存全部流 | [q] 退出 ---")

    while True:
        ret, frame = cap.read()
        if not ret: continue

        # --- 2. 剥离执行管线以获取中间值 ---
        # 我们手动调用内部方法，以获取要保存的 debug 图像
        processed = referee._preprocess(frame, debug=True)
        mask = referee._segment(processed, debug=True)
        pos = referee._find_blob(mask)

        # --- 3. 同步压入缓存 ---
        raw_buf.append(frame.copy())      # 原始色彩流
        pre_buf.append(processed.copy())  # 预处理灰度流
        msk_buf.append(mask.copy())       # 二值化掩模流

        # --- 4. 实时反馈 ---
        display_frame = frame.copy()
        if pos is not None:
            cv2.circle(display_frame, (int(pos[0]), int(pos[1])), 6, (0, 0, 255), -1)
        cv2.imshow("Main_Tracking", display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            # 一次按下，三路齐发
            print("\n🚀 正在同步导出多路实验数据...")
            save_video_stream(list(raw_buf), "1_raw", fps)
            save_video_stream(list(pre_buf), "2_pre", fps)
            save_video_stream(list(msk_buf), "3_msk", fps)
            print("✨ 数据持久化完成。\n")
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()