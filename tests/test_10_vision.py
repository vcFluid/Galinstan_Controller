import cv2
import sys
from src.drivers.camera_check import get_available_cameras 
from src.vision.tracker import GalinstanTracker 

def main():
    # --- 1. 硬件探测与交互 ---
    indices = get_available_cameras()
    if not indices:
        print("❌ 错误：未检测到任何可用摄像头。")
        return

    print(f"✅ 检测到以下摄像头索引: {indices}")
    
    if len(indices) == 1:
        selected_idx = indices[0]
    else:
        try:
            user_input = input(f"请输入索引 {indices} (直接回车默认 {indices[0]}): ").strip()
            selected_idx = int(user_input) if user_input else indices[0]
        except ValueError:
            selected_idx = indices[0]

    # --- 2. 初始化环境 ---
    # 修正：使用用户选择的 selected_idx，并加入 DSHOW 后端提高 Windows 兼容性
    cap = cv2.VideoCapture(selected_idx, cv2.CAP_DSHOW)
    
    # 初始化“在岗裁判”
    referee = GalinstanTracker(buffer_sec=4, fps=30) 
    
    print(f"--- 视觉追踪系统在索引 {selected_idx} 启动 ---")
    
    while True:
        # --- 3. 物理数据采集 ---
        ret, frame = cap.read()
        
        # 🛡️ 物理防线：确保上游水源（数据流）未断
        if not ret or frame is None:
            print("⚠️ 警告：丢失帧数据，正在重试...")
            continue 

        # --- 4. 视觉处理逻辑 ---
        pos = referee.process_frame(frame)
        
        if pos is not None:
            x, y = pos
            # 实时输出，方便溯源
            print(f"检测到质心: X={x:.2f}, Y={y:.2f}")
            # 绘制视觉反馈
            cv2.circle(frame, (int(x), int(y)), 6, (0, 0, 255), -1)
            cv2.putText(frame, f"({int(x)},{int(y)})", (int(x)+10, int(y)-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # --- 5. 交互与渲染 ---
        cv2.imshow("Galinstan Tracking (Press 'q' to quit)", frame)
        
        # 仅保留一个 waitKey，保持 1ms 监听频率
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # --- 6. 停机解构 ---
    cap.release()
    cv2.destroyAllWindows()
    print("--- 系统已安全关闭 ---")

if __name__ == "__main__":
    main()