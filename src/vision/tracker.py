import cv2
import sys

# 【替换你的视频路径】
VIDEO_PATH = r"C:\WorkStation\linshi\Galinstan_Controller\data\captures_20260409_193516\1_pre.avi"

cap = cv2.VideoCapture(VIDEO_PATH)
ret, frame = cap.read()
if not ret:
    print("无法读取视频")
    sys.exit()

frame = cv2.resize(frame, (640, 480))

# 创建 CSRT 追踪器 (抗形变、抗复杂背景最强的算法之一)
# 兼容性处理：不同版本的 OpenCV 调用方式略有不同
try:
    tracker = cv2.TrackerCSRT_create()
except AttributeError:
    tracker = cv2.legacy.TrackerCSRT_create()

print("[系统提示] 请用鼠标框选液滴（尽量贴合液滴边缘），按 SPACE 或 ENTER 确认")
bbox = cv2.selectROI("Vision Tracking", frame, showCrosshair=True, fromCenter=False)
cv2.destroyWindow("Vision Tracking")

# 如果没有框选有效区域，直接退出
if bbox[2] == 0 or bbox[3] == 0:
    print("未选择有效区域，退出程序。")
    sys.exit()

# 初始化追踪器，将第一帧和目标框喂给算法
tracker.init(frame, bbox)

print("\n[引擎启动] 正在全自动追踪... 按 'q' 键退出")

while True:
    ret, frame = cap.read()
    if not ret:
        print("视频播放完毕。")
        break
        
    frame = cv2.resize(frame, (640, 480))

    # 核心：更新追踪器，算法会自动寻找最相似的特征块
    success, bbox = tracker.update(frame)

    if success:
        # 提取边界框坐标
        x, y, w, h = [int(v) for v in bbox]
        # 计算物理质心
        cX = x + w // 2
        cY = y + h // 2

        # 绘制可视反馈
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.circle(frame, (cX, cY), 4, (0, 0, 255), -1)
        cv2.putText(frame, f"LOCKED: [{cX}, {cY}]", (cX - 40, cY - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    else:
        # 如果目标由于剧烈变形或遮挡丢失
        cv2.putText(frame, "LOST TARGET", (100, 80), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)

    cv2.imshow("Vision Tracking", frame)

    # 控制播放速度 (延迟 30ms)
    if cv2.waitKey(30) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()