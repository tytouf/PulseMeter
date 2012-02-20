// PulseMeter.ino
//
// Sample ADC value every 50ms. First get the value without the IR led to
// acquire the ambient light value and then get the value with the IR led
// switched on. Finaly send the difference on the serial line.
//
// Author: Christophe Augier <christophe.augier@gmail.com>
//
// This file is licensed under a Creative Commons Attribution 3.0 Unported
// License.
//
 
#define IR_LED     8
#define PULSE_LED  9

void setup() {
  Serial.begin(115200);
  pinMode(IR_LED, OUTPUT);
  digitalWrite(IR_LED, LOW);
}

void loop() {
  // First read ambient light
  digitalWrite(IR_LED, LOW);
  int ambient_val = analogRead(A0);
  
  // Now read with IR led switched on
  digitalWrite(IR_LED, HIGH);
  delay(1);
  int ir_val = analogRead(A0);
  Serial.println(ir_val - ambient_val);
  digitalWrite(IR_LED, LOW);
  
  // Wait for next sample
  delay(49);
}

