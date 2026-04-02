import cv2

def get_available_cameras(max_tests=5):
    """
    扫描系统硬件管线，返回所有可用摄像头的索引列表。
    """
    available_indices = []
    for i in range(max_tests):
        # 使用 DSHOW 后端在 Windows 上更稳定
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                available_indices.append(i)
            cap.release()
    return available_indices