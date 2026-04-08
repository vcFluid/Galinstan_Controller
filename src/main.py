# src/main.py
import cv2
import time
import sys
# 确保导入路径与你的项目结构一致
from src.vision.tracker import GalinstanTracker
from src.analysis.Brain import PhysicsBrain
from src.control.actuator import HardwareController, SerialTransmitter
from src.drivers.camera_check import get_available_cameras
import datetime
import os


# --- 静态配置参数 ---
TARGET_X = 320.0        # 目标 X 坐标 (假设图像宽度 640)
FPS = 30                # 设定频率
COM_PORT = 'COM5'       # 你的串口
MAX_V = 5.0             # 逻辑上限电压

TARGET_X = 320.0 

# --- 配置录制参数 ---
RECORD_DURATION = 4  # 秒
record_frames_limit = FPS * RECORD_DURATION
recording_active = False
frame_counter = 0
video_writers = []

def start_recording(frame_shape):
    global recording_active, frame_counter, video_writers, TARGET_X
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = f"data/captures_{timestamp}"
    os.makedirs(folder, exist_ok=True)
    
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    names = ["1_Pre", "2_Mask", "3_Blob", "4_Console"]
    
    video_writers = []
    for name in names:
        path = os.path.join(folder, f"{name}.avi")
        # 注意：Mask 窗口是单通道，需转为三通道或指定颜色空间
        vw = cv2.VideoWriter(path, fourcc, FPS, (frame_shape[1], frame_shape[0]))
        video_writers.append(vw)
    
    recording_active = True
    frame_counter = 0
    print(f"\n🔴 开始录制瞬态数据至: {folder}")

def main():
    # --- 核心修复点 ---
    global recording_active, frame_counter, video_writers, TARGET_X  
    
    try:
        transmitter = SerialTransmitter(port=COM_PORT, baudrate=115200)
        actuator = HardwareController(max_voltage=MAX_V)
    except Exception as e:
        print(f"❌ 硬件初始化失败: {e}")
        return

    # 现在这里可以正常访问全局变量了
    tracker = GalinstanTracker(buffer_sec=2, fps=FPS) 
    brain = PhysicsBrain(Kp=0.4, Ki=0.01, Kd=0.1, target_x=TARGET_X)

    # 3. 初始化视觉流
    print("正在尝试唤醒视觉传感器...")
    
    # 尝试直接使用默认后端打开 0 号摄像头（通常是笔记本自带或第一个 USB 摄像头）
    cap = cv2.VideoCapture(1)
    
    # 如果 0 号打不开，尝试 1 号
    if not cap.isOpened():
        cap = cv2.VideoCapture(1)

    # 强硬的物理状态断言
    if not cap.isOpened():
        print("❌ 致命错误：视觉传感器唤醒失败！")
        print("   排查建议：")
        print("   1. 摄像头是否被其他软件（如微信、钉钉、网页会议）占用？")
        print("   2. Windows 设置 -> 隐私和安全性 -> 摄像头，是否允许了 Python 访问？")
        # 如果摄像头瞎了，直接中止引擎，不进入循环
        if 'transmitter' in locals():
            transmitter.close()
        return
    
    # 强行丢弃前 5 帧（摄像头刚启动时的曝光和白平衡通常是错乱的）
    for _ in range(5):
        cap.read()
        
    print(f"🚀 引擎已就绪 | 目标 X: {TARGET_X} | [q] 退出 | [t] 切换目标")
    
    print(f"🚀 引擎已就绪 | 目标 X: {TARGET_X} | [q] 退出 | [t] 切换目标")

    last_time = time.time()
    
    last_time = time.perf_counter() # 使用高精度物理时钟
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret: continue

            current_time = time.perf_counter()
            dt = current_time - last_time
            last_time = current_time

            # --- Sense ---
            pos = tracker.process_frame(frame, debug=True) 
            
            # --- Think ---
            if pos is not None:
                curr_x = pos[0]
                v_ideal = brain.think([curr_x, 0], dt=dt) 
            else:
                curr_x = 0.0
                v_ideal = 0.0

            # --- Act ---
            cmd = actuator.generate_instruction(v_ideal)
            transmitter.send_command(cmd)

            # 清理系统底层串口积压，防止 Windows 缓冲区撑爆
            if transmitter.ser and transmitter.ser.in_waiting > 0:
                transmitter.ser.reset_input_buffer()

            # 👇 --- 核心修复 1：终端硬核监测流 --- 👇
            # 使用 \r 覆盖同一行，打造实时数字仪表盘，绝对不会被视觉画面遮挡
            print(f"\r[Engine] Target:{TARGET_X:>5.1f} | Pos:{curr_x:>5.1f} | dt:{dt:.3f}s | Out: {v_ideal:>5.2f}V   ", end="", flush=True)

            # 👇 --- 核心修复 2：抗背景干扰的高对比度 UI --- 👇
            cv2.line(frame, (int(TARGET_X), 0), (int(TARGET_X), 480), (0, 255, 0), 2)
            if pos:
                cv2.circle(frame, (int(pos[0]), int(pos[1])), 8, (0, 0, 255), -1)
            
            # 画一个纯黑色的实心矩形作为“底座”，隔绝白纸背景
            cv2.rectangle(frame, (5, 5), (260, 45), (0, 0, 0), -1)
            # 在黑板上用高亮的荧光绿 (0, 255, 0) 写字
            cv2.putText(frame, f"V_out: {v_ideal:.2f}V", (15, 32), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            cv2.imshow("Galinstan Controller Console", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'): break
            elif key == ord('t'):
                TARGET_X = 450.0 if TARGET_X == 150.0 else 150.0
                brain.update_target(TARGET_X)

            # 捕捉 S 键启动录制
            if key == ord('s') and not recording_active:
                start_recording(frame.shape)
                # 同时保存当前时刻的一组高清快照 (JPG)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                cv2.imwrite(f"data/snap_{timestamp}_1.jpg", tracker.debug_frames["preprocessed"])
                cv2.imwrite(f"data/snap_{timestamp}_2.jpg", tracker.debug_frames["mask"])
                cv2.imwrite(f"data/snap_{timestamp}_3.jpg", tracker.debug_frames["blob"])
                cv2.imwrite(f"data/snap_{timestamp}_4.jpg", frame) # Console 帧

            if recording_active:
                # 准备四路数据
                # 技巧：cv2.cvtColor 将灰度图转为 BGR 才能写入彩色视频流
                f1 = cv2.cvtColor(tracker.debug_frames["preprocessed"], cv2.COLOR_GRAY2BGR)
                f2 = cv2.cvtColor(tracker.debug_frames["mask"], cv2.COLOR_GRAY2BGR)
                f3 = tracker.debug_frames["blob"]
                f4 = frame # 已经带有 UI 覆盖层的最终画面
                
                for writer, f in zip(video_writers, [f1, f2, f3, f4]):
                    writer.write(f)
                    
                frame_counter += 1
                if frame_counter >= record_frames_limit:
                    recording_active = False
                    for w in video_writers: w.release()
                    print("\n✅ 4s 瞬态捕捉完成。")

                pass


    except KeyboardInterrupt:
        print("\n检测到用户中断...")
    finally:
        # 安全停机逻辑：必须保证退出时电极电压为 0
        print("正在执行安全降熵：归零电压，释放资源...")
        if 'transmitter' in locals() and 'actuator' in locals():
            transmitter.send_command(actuator.generate_instruction(0.0))
            transmitter.close()
        cap.release()
        cv2.destroyAllWindows()

        

if __name__ == "__main__":
    main()