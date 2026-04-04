import numpy as np

Critical_V = 1.2 # 克服氧化层静摩擦的临界电压 (V)
K_FACTOR = 0.5 # 阻力与电势平方的无量纲转换系数

class PhysicsBrain:
    def __init__(self, Kp=1.0, Ki=0.0, Kd=0.0, target_x=0.0): # 默认 PID 参数和目标位置，可以在实例化时传入自定义值以适应不同的系统特性和控制需求。
        # 1. 控制学参数
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.target_x = target_x
        
        # 2. 物理学参数 (可供未来实验拟合更新)
        self.voltage_threshold = Critical_V # 克服氧化层静摩擦的临界电压 (V)
        self.k_factor = K_FACTOR          # 阻力与电势平方的无量纲转换系数
        
        # 3. 状态寄存器
        self.integral_error = 0.0 # PID 积分项的累积误差，用于消除稳态误差
        self.last_error = 0.0 # PID 微分项的上一个误差值，用于计算误差变化率
        
    def update_target(self, new_target_x):
        self.target_x = new_target_x
        self.integral_error = 0.0
        self.last_error = 0.0  # 核心：防止目标切换时的微分尖峰

    def think(self, current_pos, dt):
        """
        核心物理演算中枢
        输入: 物理坐标 current_pos [x], 时间步长 dt (秒)
        输出: 理想控制电压 V_ideal (伏特)
        """
        if current_pos is None or dt <= 1e-5:
            return 0.0

        curr_x = current_pos[0]
        error = self.target_x - curr_x
        
        # --- 步骤 A: 计算期望驱动力 (PID 算子) ---
        p_term = self.Kp * error
        
        self.integral_error += error * dt
        # 积分抗饱和 (Anti-windup): 限制积分上限，防止系统在被卡住时积累过大能量
        self.integral_error = np.clip(self.integral_error, -50, 50) 
        i_term = self.Ki * self.integral_error
        
        d_term = self.Kd * (error - self.last_error) / dt
        
        F_ideal = p_term + i_term + d_term
        
        # 状态更新
        self.last_error = error
        
        # --- 步骤 B: 物理反演 (Force -> Voltage) ---
        if abs(F_ideal) < 1e-4:
            return 0.0 # 极小误差直接判定为到达目标
            
        # 根据 Lippmann 方程与摩擦力模型进行非线性映射
        direction = 1 if F_ideal > 0 else -1
        
        # 驱动力转化 + 死区补偿
        V_magnitude = np.sqrt(self.k_factor * abs(F_ideal)) + self.voltage_threshold
        
        V_ideal = direction * V_magnitude
        
        return V_ideal