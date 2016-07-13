#include <uarm_library.h>

void setup(){
  Serial.begin(9600);
}

void loop(){
  uarm.calXYZ();
  Serial.print("X: ");
  Serial.println(uarm.getCalX());
  Serial.print("Y: ");
  Serial.println(uarm.getCalY());
  Serial.print("Z: ");
  Serial.println(uarm.getCalZ()); 
  Serial.println();
  delay(500);   
}

