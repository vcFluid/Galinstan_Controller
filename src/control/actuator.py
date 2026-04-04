# src/control/actuator.py
import serial
import time

class HardwareController:
    def __init__(self, max_voltage=5.0, pwm_res=255):
        self.max_voltage = max_voltage
        self.pwm_res = pwm_res
        
    def generate_instruction(self, ideal_voltage):
        """
        将理想物理量映射为数字指令 
        """
        clamped_v = max(-self.max_voltage, min(self.max_voltage, ideal_voltage))
        pwm_val = int(abs(clamped_v) / self.max_voltage * self.pwm_res)
        direction = 1 if ideal_voltage > 0 else 0
        
        return f"DIR:{direction},PWM:{pwm_val}\n"

class SerialTransmitter:
    """
    物理层：负责将指令映射为串口电信号 
    """
    def __init__(self, port='COM3', baudrate=115200):
        self.ser = None
        try:
            # 尝试建立物理链路
            self.ser = serial.Serial(port, baudrate, timeout=1)
            # 给 Arduino 留出重置时间，防止第一条指令丢失
            time.sleep(2) 
            print(f"✅ 物理链路建立成功: {port}")
        except serial.SerialException as e:
            if "PermissionError" in str(e):
                print(f"❌ 拒绝访问: 端口 {port} 已被占用。")
                print("   请确认是否开启了 Arduino IDE 串口监视器，或是其他脚本未退出。")
            else:
                print(f"❌ 无法打开端口 {port}: {e}")
            # 主动抛出更有意义的错误信息
            raise SystemExit(1) 

    def send_command(self, command_str):
        if self.ser and self.ser.is_open:
            self.ser.write(command_str.encode('utf-8'))
            self.ser.flush()

            
            # --- 核心补全：添加关闭接口 ---
    def close(self):
        """
        优雅地关闭物理链路，释放系统句柄。
        """
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("📦 串口句柄已安全释放。")