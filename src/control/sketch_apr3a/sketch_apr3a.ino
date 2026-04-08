"""
--- Galinstan 执行器固件 ---
目的:
1. 接收来自上位机的指令，解析出 DIR 和 PWM 参数。
2. 根据 DIR 参数控制电机的转向（正转或反转），根据 PWM 参数控制电机的转速（通过改变电压大小）。
3. 将当前的 DIR 和 PWM 参数通过串口回传给上位机，以便在绘图器中实时可视化液滴的运动状态。
指令格式:
上位机发送的指令格式为 "DIR:x,PWM:y\n"，其中 x 是 0 或 1，表示转向；y 是 0-255 的整数，表示 PWM 占空比（电压大小）。例如 "DIR:1,PWM:128\n" 表示正转，PWM 占空比为 50%。
回传格式:
Arduino 在执行完指令后，会通过串口发送回 "Direction:300,PWM_Voltage:128\n" 这样的字符串，其中 Direction 的值是 DIR 参数放大了300倍（为了在绘图器中区分两条线），PWM_Voltage 的值是 PWM 参数的实际数值。
上位机可以解析这个回传字符串，提取出当前的 DIR 和 PWM 参数，并在绘图器中实时更新液滴的运动状态。 
"""

// 定义物理引脚 (根据实际连线修改)
const int DIR_PIN = 4;   // 决定正负极反转的数字引脚 (连接继电器或电机驱动的 DIR)
const int PWM_PIN = 5;   // 决定电压大小的 PWM 引脚 (连接 ENA)

String inputString = "";         // 用于缓存接收到的信件片段
bool stringComplete = false;     // 标记一封信是否接收完毕 (检测到 '\n')

void setup() {
  Serial.begin(115200);          // 与 Python 端保持完全一致的通讯速率
  
  pinMode(DIR_PIN, OUTPUT);
  pinMode(PWM_PIN, OUTPUT);
  
  // 初始状态清零，防止一上电液滴就乱跑
  digitalWrite(DIR_PIN, LOW);
  analogWrite(PWM_PIN, 0);       
}

void loop() {
  // 如果收到了一条完整的指令
  if (stringComplete) {
    parseAndExecute(inputString);
    
    // 清空缓存，准备迎接下一条指令
    inputString = "";
    stringComplete = false;
  }
}

// 串口中断事件：只要有数据从 USB 传过来，就会自动触发这个函数
void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read(); // 一个个字符读取
    inputString += inChar;             // 拼接到字符串中
    
    // 如果读到了换行符，说明上位机的一条指令发送完毕
    if (inChar == '\n') {
      stringComplete = true;
    }
  }
}

// 解析指令并驱动物理界面的核心函数
void parseAndExecute(String cmd) {
  int dirIndex = cmd.indexOf("DIR:");
  int pwmIndex = cmd.indexOf("PWM:");
  
  if (dirIndex != -1 && pwmIndex != -1) {
    int dirValue = cmd.substring(dirIndex + 4, cmd.indexOf(',')).toInt();
    int pwmValue = cmd.substring(pwmIndex + 4).toInt();
    
    pwmValue = constrain(pwmValue, 0, 255);
    
    digitalWrite(DIR_PIN, dirValue == 1 ? HIGH : LOW);
    analogWrite(PWM_PIN, pwmValue); 
    
    // --- 新增可视化回传逻辑 ---
    // 为了在绘图器中区分两条线，我们将 DIR 放大到 300
    Serial.print("Direction:");
    Serial.print(dirValue * 300); 
    Serial.print(",");
    Serial.print("PWM_Voltage:");
    Serial.println(pwmValue);
  }
}