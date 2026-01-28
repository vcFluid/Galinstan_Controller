import cv2
FRAME_WIDTH = 1280      #分辨率参数
FRAME_HEIGHT = 720  
FPS = 60                #刷新率参数
CAMERA_INDEX = 0        #选择哪个摄像头（一般0是计算机自带摄像头，1、2...是外接摄像头

#前置函数，初始化摄像头
def Camera_Use(camera_index=0): #camera_index（摄像头索引号）=0（默认计算机自带摄像头）
    print("稍后将显示指定摄像头的实时画面")
    cap = cv2.VideoCapture(camera_index)
    #cap变量表示与摄像头的接口
    #.VideoCapture()函数，用于从相机读取视频；这个函数接受摄像头设备编号一个函数
    
    # 设置分辨率
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS)
    
    if not cap.isOpened():#.isOpened()：用于检查 cap 的状态，成功则返还True
        print(f"无法打开摄像头 {camera_index}")
        return#退出当前函数

    REAL_WIDTH=cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    REAL_HEIGHT=cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    REAL_FPS=cap.get(cv2.CAP_PROP_FPS)

    print(REAL_WIDTH, REAL_HEIGHT, REAL_FPS)
    
    print("按 'q' 键退出，按 's' 键保存图片")
    
    #执行摄像头读取循环
    while True:#无限循环
        ret, frame = cap.read() #.read()函数 返回一个布尔值，一个数组(BGR)
        #.read()
        if not ret:
            print("error.摄像头信号丢失.无法读取帧")
            break
        
        # 在电脑窗口中显示帧
        cv2.imshow(f'USB Camera {camera_index}', frame)
        #语法：cv2.imshow(winname, mat);winname作为窗口标题，mat为要显示的图像信息，此处分别对应括号内第一个变量与第二个变量

        key = cv2.waitKey(1) & 0xFF
        #cv2.waitKey(delay): 等待 delay 毫秒。如果在此期间有按键按下，返回该按键的 ASCII 码；
        #如果没有，返回 -1。delay=0 表示无限期等待。
        #waitKey() 是 OpenCV GUI 的核心，它会处理窗口事件队列。
        #如果没有它，imshow 创建的窗口将是空白的或无响应的。

        if key == ord('q'):#ord() 是 Python 的内置函数，返回单个字符的 ASCII 码或 Unicode 码点。
            break
        elif key == ord('s'):
            cv2.imwrite(f'capture_{camera_index}.jpg', frame)

            print("图片已保存")
    
    cap.release()
    cv2.destroyAllWindows()

# 使用第一个可用的摄像头
Camera_Use(CAMERA_INDEX)