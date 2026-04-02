import cv2
from src.vision.tracker import GalinstanTracker # 1. 引入我们的视觉引擎 

def main():
    # 2. 初始化“在岗裁判”
    # 这里的 4 代表预留 4 秒缓存，30 代表摄像头的 FPS 
    referee = GalinstanTracker(buffer_sec=4, fps=30) 
    
    # 启动摄像头
    cap = cv2.VideoCapture(0)
    
    print("--- 视觉追踪系统启动 ---")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # 3. 调用类中的方法：处理当前帧
        # 这一步会完成：灰度化 -> 二值化 -> 质心计算 -> 存入缓存 
        pos = referee.process_frame(frame)
        
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