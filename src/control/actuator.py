"""
--- actuator.py v1.0 ---
目的：
此程序为整台引擎的“肌肉”，负责将 Brain 模块输出的理想控制电压映射为具体的串口指令，驱动 Arduino 等微控制器执行相应的动作。
功能：
1. 将理想物理量映射为数字指令：根据 Brain 模块输出的理想控制电压，生成适合 Arduino 接收的串口指令格式，包括 PWM 信号值和方向信息。
2. 物理链路管理：通过 SerialTransmitter 类与 Arduino 建立串口通信，发送控制指令以驱动硬件执行相应的动作。
3. 资源管理：提供关闭接口，确保在程序结束时能够安全地释放串口连接资源，防止系统句柄泄漏。
4. 错误处理：在建立串口连接时，提供详细的错误信息，帮助用户排查问题，例如端口被占用或连接失败等情况。
需要注意的是，虽然这个程序设计了多个功能模块，但在实际应用中可能仍然会受到一些误差的影响，例如：
1. 串口通信延迟：在发送控制指令到 Arduino 时，可能会存在一定的通信延迟，这可能会影响系统的响应速度和控制精度。
2. 指令解析错误：如果 Arduino 端的指令解析逻辑存在问题，可能会导致控制指令无法正确执行，从而影响系统的性能。
3. 硬件限制：Arduino 的处理能力和 PWM 输出的分辨率可能会限制系统能够实现的控制精度和响应速度。
此外，引入的误差有
1. 串口通信错误：在与 Arduino 建立串口连接或发送指令时，可能会遇到连接失败、数据丢失或指令解析错误等问题，这些都可能导致系统无法正确执行控制指令。
2. 硬件响应误差：即使指令成功发送到 Arduino，硬件执行器可能由于物理限制、机械摩擦或电气噪声等因素而无法完全按照指令执行，从而引入控制误差。
"""

import serial # serial 库用于与 Arduino 等微控制器进行串口通信，发送控制指令以驱动硬件执行相应的动作。
import time # time 库用于在建立串口连接后添加延时，确保 Arduino 有足够的时间完成重置过程，防止第一条指令丢失。

# 参数定义
# max_voltage 定义了系统的逻辑上限电压，pwm_res 定义了 PWM 信号的分辨率（例如 8 位分辨率对应 255）。
# ideal_voltage 是从 Brain 模块输出的理想控制电压，HardwareController 的任务是将这个电压值转换为适合 Arduino 接收的串口指令格式。
# clamped_v 是将 ideal_voltage 限制在 -max_voltage 和 max_voltage 之间的值，确保输出电压不会超过系统的物理限制。
# pwm_val 是根据 clamped_v 计算出的 PWM 信号值，表示为一个整数，范围从 0 到 pwm_res，表示输出电压相对于 max_voltage 的比例。
# direction 是一个二进制值，表示控制信号的方向（正向或反向），根据 ideal_voltage 的符号确定。

PORT = 'COM3' # 请根据实际情况修改为你的 Arduino 连接的串口号，例如 Windows 上通常是 COM3、COM4 等，Linux 上可能是 /dev/ttyUSB0 或 /dev/ttyACM0。

class HardwareController: # 物理层：负责将指令映射为串口电信号
    def __init__(self, max_voltage=5.0, pwm_res=255): 
        # max_voltage 定义了系统的逻辑上限电压，pwm_res 定义了 PWM 信号的分辨率（例如 8 位分辨率对应 255）。
        # PWM信号是一种通过调整信号的占空比来控制电压输出的方法，pwm_res 的值决定了控制的精细程度。
        # 详情可以搜索关键词 "PWM control in microcontrollers" 来了解更多关于 PWM 的原理和应用。

        self.max_voltage = max_voltage
        self.pwm_res = pwm_res
        
    def generate_instruction(self, ideal_voltage): 
        # ideal_voltage 是从 Brain 模块输出的理想控制电压，HardwareController 的任务是将这个电压值转换为适合 Arduino 接收的串口指令格式。
        """
        将理想物理量映射为数字指令 
        """
        clamped_v = max(-self.max_voltage, min(self.max_voltage, ideal_voltage)) # clamped_v 是将 ideal_voltage 限制在 -max_voltage 和 max_voltage 之间的值，确保输出电压不会超过系统的物理限制。
        pwm_val = int(abs(clamped_v) / self.max_voltage * self.pwm_res)
        direction = 1 if ideal_voltage > 0 else 0
        
        return f"DIR:{direction},PWM:{pwm_val}\n"
        # 返回值是一个字符串，格式为 "DIR:{direction},PWM:{pwm_val}\n"，其中 direction 表示控制信号的方向（正向或反向），pwm_val 表示根据 ideal_voltage 计算出的 PWM 信号值，表示为一个整数，范围从 0 到 pwm_res，表示输出电压相对于 max_voltage 的比例。
        # 这个字符串将被 SerialTransmitter 模块发送到 Arduino，Arduino 将解析这个指令并相应地调整输出电压以驱动液态金属球的运动。
        """ 具体控制原理可以搜索关键词 "Arduino PWM control for motor" 来了解更多关于如何使用 Arduino 的 PWM 信号来控制电机或其他执行器的原理和实践。 """

class SerialTransmitter: # 物理链路：负责与 Arduino 建立串口通信，发送控制指令以驱动硬件执行相应的动作。
    """
    物理层：负责将指令映射为串口电信号 
    """
    def __init__(self, port=PORT, baudrate=115200):
        self.ser = None # ser 属性将用于存储串口连接对象，确保在类的其他方法中可以访问和管理这个连接。
        try:
            # 尝试建立物理链路
            self.ser = serial.Serial(port, baudrate, timeout=2) 
            # port定义在全局变量PORT中，同时在__init__方法中接受一个可选的port参数，允许在实例化时指定不同的串口号。
            # baudrate设置为115200，这是一个常见的串口通信速率，timeout设置为1秒，确保在读取数据时不会无限等待。
            # serial.Serial() 方法用于创建一个新的串口连接对象，如果指定的端口不存在或被占用，将抛出 serial.SerialException 异常。
            # 详情可以搜索关键词 "pyserial Serial class" 来了解更多关于 pyserial 库中 Serial 类的用法和异常处理。

            time.sleep(2) 

            print(f"✅ 物理链路建立成功: {port}")

        except serial.SerialException as e: # 处理串口连接错误，提供更具体的错误信息，帮助用户排查问题。
            # except A as e: 是 Python 中的异常处理语法，用于捕获在 try 块中发生的特定类型的异常（这里是 serial.SerialException），并将异常对象赋值给变量 e，以便在 except 块中使用。
            # 通过检查异常信息中的关键词 "PermissionError"，可以判断是否是由于端口被占用导致的连接失败，并提供相应的排查建议。
            # 如果捕获到的异常不是 PermissionError，则输出更通用的错误信息，提示用户检查端口号和连接状态。
            # if "PermissionError" in str(e): 是一种简单的字符串检查方法，用于判断异常信息中是否包含 "PermissionError" 这个关键词，以此来识别特定类型的错误。
            # 详情可以搜索关键词 "pyserial SerialException handling" 来了解更多关于如何处理 pyserial 中的 SerialException 异常以及如何提供有用的错误信息给用户。
            if "PermissionError" in str(e):
                print(f"❌ 拒绝访问: 端口 {port} 已被占用。")
                print("   请确认是否开启了 Arduino IDE 串口监视器，或是其他脚本未退出。")
            else:
                print(f"❌ 无法打开端口 {port}: {e}")
            # 主动抛出更有意义的错误信息
            raise SystemExit(1) # 直接退出程序，返回状态码 1，表示发生了错误。这个状态码可以在命令行或其他调用环境中被捕获，以便进行相应的错误处理或日志记录。

    def send_command(self, command_str):
        if self.ser and self.ser.is_open:  
            # 检查串口连接是否存在且处于打开状态，确保在发送指令之前连接是有效的。
            # 这是一种标准化的资源管理实践，可以防止在连接未建立或已关闭的情况下尝试发送数据，从而避免引发异常。
            # 详情可以搜索关键词 "pyserial Serial is_open" 来了解更多关于 pyserial 中 Serial 对象的 is_open 属性以及如何正确管理串口连接的状态。
            self.ser.write(command_str.encode('utf-8'))
            # 将 command_str 字符串编码为 UTF-8 字节流，并通过 ser.write() 方法发送到 Arduino。这个方法会将数据写入串口缓冲区，Arduino 将从这个缓冲区读取数据并执行相应的控制指令。
            # 详情可以搜索关键词 "pyserial Serial write method" 来了解更多关于 pyserial 中 Serial 对象的 write() 方法的用法和注意事项。
            self.ser.flush()
            # flush() 方法用于确保所有缓冲区中的数据都被发送出去，特别是在发送完指令后立即关闭连接时，这可以防止数据丢失。
            # 详情可以搜索关键词 "pyserial Serial flush method" 来了解更多关于 pyserial 中 Serial 对象的 flush() 方法的作用和使用场景。

            
            # --- 核心补全：添加关闭接口 ---
    def close(self):
        """
        关闭物理链路，释放系统句柄。
        """
        if self.ser and self.ser.is_open: # 检查串口连接是否存在且处于打开状态，确保在尝试关闭连接之前连接是有效的。
            self.ser.close() 
            # close() 方法用于关闭串口连接，释放系统资源，确保在程序结束时不会留下未关闭的串口连接，这是一种良好的资源管理实践。
            print("📦 串口句柄已安全释放。")


"""
学习资源：[2026/4/8日前可安全访问的在线资源，此后不保证链接安全性]
PySerial官方文档 https://pythonhosted.org/pyserial/
进阶指南 https://www.google.com/search?q=https://realpython.com/python-serial/
Arduino官方PWM教程 https://www.arduino.cc/en/Tutorial/Foundations/PWM
硬件驱动参考 https://learn.sparkfun.com/tutorials/pulse-width-modulation/all
Arduino Reference  https://www.google.com/search?q=https://www.arduino.cc/reference/en/language/functions/communication/serial/readstringuntil/
电机制动与极性  https://learn.adafruit.com/adafruit-arduino-lesson-13-dc-motors/overview
Python异常处理 https://docs.python.org/3/library/exceptions.html
资源管理  https://www.google.com/search?q=%5Bhttps://realpython.com/python-with-statement/%5D(https://realpython.com/python-with-statement/)
"""