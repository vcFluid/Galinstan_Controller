// Galinstan_Actuator_Firmware.ino

// 定义物理引脚 (根据你的实际连线修改)
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