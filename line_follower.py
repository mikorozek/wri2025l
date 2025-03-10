#!/usr/bin/env python3
from time import sleep
from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C
from ev3dev2.sensor import INPUT_3, INPUT_2, INPUT_4
from ev3dev2.sensor.lego import TouchSensor, ColorSensor

BASE_SPEED = 20  # Base speed (percentage)
TURN_RATE = 33   # Turn rate coefficient
BLACK = 1        # Value for black color
WHITE = 6        # Value for white color

m1 = LargeMotor(OUTPUT_B)  # Left track motor
m2 = LargeMotor(OUTPUT_C)  # Right track motor
#m3 = MediumMotor(OUTPUT_C)

s1 = TouchSensor(INPUT_4)  # Touch sensor to stop the program
s2 = ColorSensor(INPUT_2)  # Left color sensor
s3 = ColorSensor(INPUT_3)  # Right color sensor

print("Line follower program started")
print("Press touch sensor to stop")

running = False

while True:
    if s1.is_pressed:
        running = True
    sleep(0.2)
    while running:
        if s1.is_pressed:
           running = False
        left_color = s2.color
        right_color = s3.color

        if left_color == BLACK and right_color != BLACK:
           # Line under left sensor - turn left
           left_speed = BASE_SPEED - TURN_RATE
           right_speed = BASE_SPEED + TURN_RATE
           print("Turning left")
        elif left_color != BLACK and right_color == BLACK:
           # Line under right sensor - turn right
           left_speed = BASE_SPEED + TURN_RATE
           right_speed = BASE_SPEED - TURN_RATE
           print("Turning right")
        elif left_color == BLACK and right_color == BLACK:
           # Both sensors see the line - go straight
           left_speed = BASE_SPEED
           right_speed = BASE_SPEED
           print("Moving straight (both sensors on line)")
        elif left_color != BLACK and right_color != BLACK:
           # No sensor sees the line - search for line by turning in place
           left_speed = BASE_SPEED
           right_speed = BASE_SPEED
           print("Searching for line (both sensors off line)")

        m1.on(left_speed)
        m2.on(right_speed)

        sleep(0.01)
