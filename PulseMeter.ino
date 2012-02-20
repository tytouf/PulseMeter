/* version 1
 */
 
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
  delay(99);
}

/* version 0
 *
void setup() {
  Serial.begin(115200);
  pinMode(8, OUTPUT);
  digitalWrite(8, HIGH);
}

void loop() {
  int sensorValue = analogRead(A1);
  Serial.println(sensorValue);
  delay(100);
}
*/
