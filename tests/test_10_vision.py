import cv2
from src.vision.tracker import GalinstanTracker # 1. 引入我们的视觉引擎 

# 这里from指向的路径是相对于当前文件的位置，src.vision.tracker 是指在 src 文件夹下的 vision 子文件夹中的 tracker.py 文件。
# 目的是从我们写好的 src/vision/tracker.py 中导入 GalinstanTracker 类，注意到这个类包含了我们实现的液态金属追踪算法。

# 我们的GalinstanTracker类需要的参数分别是：buffer_sec（缓存时间，单位：秒）和 fps（帧率，单位：帧/秒）
# 可以实现的功能包括：预处理图像、提取液滴、计算质心位置，并将这些信息存入缓存中，以便后续计算速度和加速度等运动状态。
# 可以通过快捷键 Ctrl + 鼠标左键 点击这个类的定义，快速跳转到 src/vision/tracker.py 文件中查看具体实现细节。

def main():
    # 2. 初始化“在岗裁判”
    # 这里的 4 代表预留 4 秒缓存，30 代表摄像头的 FPS 
    referee = GalinstanTracker(buffer_sec=4, fps=30) 
    
    # referee 是我们创建的 GalinstanTracker 类的一个实例，代表我们的视觉追踪系统中的“在岗裁判”。通过这个实例，我们可以调用类中定义的方法来处理图像帧并获取液态金属球的位置和运动状态。
    # buffer_sec=4 表示我们希望在缓存中保留最近 4 秒
    # fps=30 表示我们假设摄像头的帧率为 30 帧/秒，这样我们就可以计算出缓存的最大长度为 buffer_sec * fps，即 4 秒 * 30 帧/秒 = 120 帧。这意味着我们的缓存将最多保留最近 120 帧的坐标数据，以便进行速度和加速度的计算。

    # 启动摄像头
    cap = cv2.VideoCapture(0)
    
    print("--- 视觉追踪系统启动 ---")
    
    while True:
        ret, frame = cap.read()
        if cv2.waitKey(1) & 0xFF == ord('q'): break
            
    # while True 是一个无限循环，表示我们希望持续地从摄像头获取图像帧并进行处理，直到用户选择退出。
    # cap.read() 是 OpenCV 中用于从摄像头捕获图像帧的方法。它返回两个值：ret 和 frame。
    # ret 是一个布尔值，表示是否成功捕获到图像帧
    # frame 是捕获到的图像帧，通常是一个 NumPy 数组，包含了图像的像素数据。
    # 如果 ret 为 False，表示没有成功捕获到图像帧，可能是摄像头出现了问题或者已经被关闭了。在这种情况下，我们使用 break 语句退出循环，停止程序的运行。
    # 同时，我们在循环中使用 cv2.waitKey(1) 来监听键盘输入，如果用户按下 'q' 键（对应的 ASCII 码是 113），我们也会退出循环，结束程序的运行。这是一种常见的方式来允许用户通过键盘输入来控制程序的退出。


        # 3. 调用类中的方法：处理当前帧
        # 这一步会完成：灰度化 -> 二值化 -> 质心计算 -> 存入缓存 
        pos = referee.process_frame(frame)

        # pos 是调用 referee 实例的 process_frame 方法处理当前帧 frame 的结果。这个方法会执行一系列图像处理步骤，包括灰度化、二值化、质心计算，并将计算得到的坐标存入缓存中。
        # process_frame是我们在 GalinstanTracker 类中定义的方法，负责处理输入的图像帧并返回液态金属球的质心位置。
        # 如果成功检测到液态金属球，pos 将是一个包含 [x, y] 坐标的列表；如果没有检测到，则 pos 将是 None。
        
        if pos is not None:
            # 这里的 pos 就是你需要的 [x, y] 实时几何中心 
            x, y = pos
            print(f"检测到液态金属质心: X={x:.2f}, Y={y:.2f}")
            
            # 在画面上画一个红点，直观验证“裁判”有没有看走眼
            cv2.circle(frame, (int(x), int(y)), 5, (0, 0, 255), -1)
        
        # 显示实时画面
        cv2.imshow("Galinstan Tracking (Press 'q' to quit)", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()