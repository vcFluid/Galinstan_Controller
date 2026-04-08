"""
--- 主程序入口 ---
目的: 
1. 初始化视觉追踪器、物理大脑和硬件控制器
2. 连接摄像头，进入主循环
3. 在主循环中，持续获取视觉数据，进行物理演算，并发送控制指令
需要注意的是，虽然这个程序设计了多个功能模块，但在实际应用中可能仍然会受到一些误差的影响，例如：
1. 摄像头连接问题：如果摄像头被其他应用占用或者权限设置不当，可能会导致无法获取视频流，从而影响系统的正常运行。
2. 视觉追踪误差：GalinstanTracker 模块在处理视频帧时可能会受到光照变化、反光、背景杂乱等因素的干扰，导致追踪结果不准确，从而影响后续的物理演算和控制指令生成。
3. 物理演算误差：PhysicsBrain 模块的 PID 控制算法可能会受到参数设置不当、系统非线性特性、外部扰动等因素的影响，导致生成的理想控制电压与实际需求不匹配，从而影响系统的响应效果。
4. 串口通信误差：SerialTransmitter 模块在与 Arduino 建立串口连接或发送指令时，可能会遇到连接失败、数据丢失或指令解析错误等问题，这些都可能导致系统无法正确执行控制指令。
此外，引入的误差有
1. 摄像头连接错误：如果摄像头被其他应用占用或者权限设置不当，可能会导致无法获取视频流，从而影响系统的正常运行。
2. 视觉追踪误差：GalinstanTracker 模块在处理视频帧时可能会受到光照变化、反光、背景杂乱等因素的干扰，导致追踪结果不准确，从而影响后续的物理演算和控制指令生成。
3. 物理演算误差：PhysicsBrain 模块的 PID 控制算法可能会受到参数设置不当、系统非线性特性、外部扰动等因素的影响，导致生成的理想控制电压与实际需求不匹配，从而影响系统的响应效果。
4. 串口通信错误：SerialTransmitter 模块在与 Arduino 建立串口连接或发送指令时，可能会遇到连接失败、数据丢失或指令解析错误等问题，这些都可能导致系统无法正确执行控制指令。
"""

# src/main.py
import cv2 # OpenCV 库用于处理视频流和图像数据，提供了丰富的计算机视觉功能，在这个程序中主要用于从摄像头获取视频帧，并将其传递给 GalinstanTracker 模块进行处理。
import time # time 库用于在主循环中计算时间差（dt），以便 PhysicsBrain 模块能够根据实际的时间步长进行物理演算，确保控制算法的稳定性和响应速度。
import sys # sys 库用于修改 Python 的模块搜索路径，确保程序能够正确导入 src 目录下的模块，例如 vision.tracker、analysis.Brain、control.actuator 和 ui.dashboard。
# 确保导入路径与你的项目结构一致
from src.vision.tracker import GalinstanTracker # GalinstanTracker 模块是视觉处理的核心，负责从视频帧中检测和追踪液态金属球的位置，为后续的物理演算提供输入数据。
from src.analysis.Brain import PhysicsBrain # PhysicsBrain 模块是物理演算的核心，负责根据视觉输入和 PID 控制算法计算出理想的控制电压，为硬件控制器提供指导。
from src.control.actuator import HardwareController, SerialTransmitter # HardwareController 模块负责将理想控制电压转换为适合 Arduino 接收的串口指令格式，SerialTransmitter 模块负责与 Arduino 建立串口通信，发送控制指令以驱动硬件执行相应的动作。
from src.drivers.camera_check import get_available_cameras # get_available_cameras 函数用于检测系统中可用的摄像头设备，帮助程序在启动时选择正确的摄像头进行视频捕捉，避免因摄像头连接问题导致的程序崩溃。
import datetime # datetime 库用于生成时间戳，帮助程序在录制视频时创建唯一的文件夹和文件名，确保每次录制的数据都能被正确保存和区分。
import os # os 库用于处理文件和目录操作，例如创建保存视频的文件夹、构建视频文件的路径等，确保程序能够正确地管理录制的数据资产。


# --- 静态配置参数 ---
TARGET_X = 320.0        # 目标 X 坐标 (假设图像宽度 640)
FPS = 30                # 设定频率
COM_PORT = 'COM5'       # 实际串口，根据Arduino IDE中显示的端口号进行修改
MAX_V = 5.0             # 逻辑上限电压
TARGET_X = 320.0 


# --- 配置录制参数 ---
RECORD_DURATION = 4  # 秒
record_frames_limit = FPS * RECORD_DURATION # 这个变量定义了录制的帧数限制，根据设定的 FPS 和录制时长计算得出，例如如果 FPS 是 30，录制时长是 4 秒，那么 record_frames_limit 就是 120，表示在录制过程中最多保存 120 帧视频数据，以确保录制的时长符合预期，并且不会因为过多的帧数导致存储空间不足或处理性能下降。
recording_active = False # recording_active 变量用于控制录制状态的开关，当用户按下特定的键（例如 'r'）时，程序会将 recording_active 设置为 True，开始录制视频数据；当达到 record_frames_limit 或用户按下停止录制的键时，程序会将 recording_active 设置为 False，停止录制并保存视频文件。这个变量在主循环中被检查，以决定是否需要将当前帧写入视频文件中。
frame_counter = 0 # frame_counter 变量用于计数当前已经录制的帧数，每当 recording_active 为 True 时，程序会在主循环中将 frame_counter 加 1，并检查是否达到了 record_frames_limit，如果达到了限制，程序会自动停止录制并保存视频文件。这个变量帮助程序控制录制的时长，确保不会因为过多的帧数导致存储空间不足或处理性能下降。
video_writers = [] # video_writers 列表用于存储多个 cv2.VideoWriter 对象，每个对象对应一个视频文件的写入器。当用户开始录制时，程序会创建多个 VideoWriter 对象，并将它们添加到 video_writers 列表中；在主循环中，如果 recording_active 为 True，程序会使用这些 VideoWriter 对象将当前帧写入对应的视频文件中；当录制结束时，程序会关闭这些 VideoWriter 对象并清空 video_writers 列表。这个列表帮助程序管理多个视频文件的写入器，确保在录制过程中能够正确地保存每个视频流的数据。

def start_recording(frame_shape): # 这个函数用于开始录制视频数据，接受一个参数 frame_shape，表示视频帧的尺寸（高度和宽度）。在函数内部，程序会生成一个基于当前时间戳的唯一文件夹路径，用于保存录制的视频文件；然后根据设定的 FPS 和帧尺寸创建多个 cv2.VideoWriter 对象，并将它们添加到 video_writers 列表中；最后将 recording_active 设置为 True，表示开始录制，并重置 frame_counter 以便计数新的录制帧数。
    global recording_active, frame_counter, video_writers, TARGET_X 
    # 通过 global 关键字声明这些变量为全局变量，确保在函数内部能够访问和修改它们的值。
    # 等效于在外部大写定义这些变量，并在函数内部使用 global 声明来修改它们的值。
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # datetime.datetime.now() 获取当前的日期和时间，strftime("%Y%m%d_%H%M%S") 将其格式化为一个字符串，格式为 "年月日_时分秒"，例如 "20240427_153045"，确保每次录制的数据都能被正确保存和区分。
    folder = f"data/captures_{timestamp}" 
    # f-string 用于构建一个基于当前时间戳的文件夹路径，例如 "data/captures_20240427_153045"，这个文件夹将用于保存录制的视频文件，确保每次录制的数据都能被正确保存和区分。
    os.makedirs(folder, exist_ok=True)
    # os.makedirs() 函数用于创建目录，参数 folder 是要创建的目录路径，exist_ok=True 表示如果目录已经存在则不抛出异常，这样可以确保程序在每次录制时都能成功创建一个新的文件夹来保存视频数据。
# 以上是标准的 Python 文件和目录操作方法，详情可以搜索关键词 "Python os.makedirs" 来了解更多关于 os.makedirs() 函数的用法和参数选项。
    
    fourcc = cv2.VideoWriter_fourcc(*'XVID') # 定义视频编码格式，这里使用 XVID 编码，fourcc 是一个四字符代码，用于指定视频文件的编码方式，cv2.VideoWriter_fourcc(*'XVID') 将 'XVID' 转换为对应的四字符代码，确保视频文件能够被正确编码和保存。
    names = ["1_Pre", "2_Mask", "3_Blob", "4_Console"] # 定义了一个列表 names，包含了要保存的四个视频文件的基本名称，这些名称将用于构建最终的视频文件路径，例如 "data/captures_20240427_153045/1_Pre.avi"，确保每个视频流的数据都能被正确保存和区分。
    
    video_writers = [] # 在函数内部重新定义了 video_writers 列表，确保在每次调用 start_recording() 函数时都能创建一个新的列表来存储当前录制的 VideoWriter 对象，避免与之前的录制数据混淆。
    for name in names: # 遍历 names 列表，为每个视频文件创建一个 cv2.VideoWriter 对象，并将其添加到 video_writers 列表中。每个 VideoWriter 对象都使用相同的编码格式、帧率和帧尺寸，但保存到不同的文件路径中，确保每个视频流的数据都能被正确保存和区分。
        path = os.path.join(folder, f"{name}.avi") # 使用 os.path.join() 函数构建视频文件的完整路径，例如 "data/captures_20240427_153045/1_Pre.avi"，确保每个视频流的数据都能被正确保存和区分。
        # 注意：Mask 窗口是单通道，需转为三通道或指定颜色空间
        vw = cv2.VideoWriter(path, fourcc, FPS, (frame_shape[1], frame_shape[0])) # 创建一个 cv2.VideoWriter 对象，参数包括视频文件的路径、编码格式、帧率和帧尺寸，确保视频文件能够被正确编码和保存。frame_shape[1] 和 frame_shape[0] 分别表示视频帧的宽度和高度，确保创建的 VideoWriter 对象能够正确处理视频帧的数据。
        video_writers.append(vw) # 将创建的 VideoWriter 对象添加到 video_writers 列表中，确保在主循环中能够使用这些对象将当前帧写入对应的视频文件中。
    
    recording_active = True # 将 recording_active 设置为 True，表示开始录制，主循环中会检查这个变量的值来决定是否将当前帧写入视频文件中。
    frame_counter = 0 # 重置 frame_counter 以便计数新的录制帧数，确保在每次开始录制时都能正确地统计录制的帧数，并在达到 record_frames_limit 时自动停止录制。
    print(f"\n🔴 开始录制瞬态数据至: {folder}")

def main():
    # --- 核心修复点 ---
    global recording_active, frame_counter, video_writers, TARGET_X  # 声明这些变量为全局变量，确保在 main() 函数内部能够访问和修改它们的值。
    
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
    cap = cv2.VideoCapture(0)
    
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