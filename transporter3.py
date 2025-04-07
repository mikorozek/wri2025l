#!/usr/bin/env python3
from time import sleep
from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C
from ev3dev2.sensor import INPUT_3, INPUT_2, INPUT_4
from ev3dev2.sensor.lego import TouchSensor, ColorSensor
from ev3dev2.sound import Sound

BASE_SPEED = 50  # Base speed (percentage)
TURN_RATE = 50   # Turn rate coefficient
BLACK = 1        # Value for black color
WHITE = 6        # Value for white color
RED = 5          # Value for red color (pickup color)
BLUE = 3         # Value for blue color (dropoff color)
TURN_DURATION_90 = 1.05    # Duration for 90-degree turn
TURN_DURATION_50 = 0.6   # Duration for 75-degree turn

class RobotState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.running = False
        self.on_path_to_object_pickup = False   
        self.on_path_to_object_dropoff = False 
        self.after_picking_up_object = False  
        self.last_turn_direction = None

class LineFolowerRobot:
    def __init__(self):
        self.left_motor = LargeMotor(OUTPUT_B)  # Left track motor
        self.right_motor = LargeMotor(OUTPUT_C)  # Right track motor
        self.arm_motor = MediumMotor(OUTPUT_A)
        
        self.touch_sensor = TouchSensor(INPUT_4)  # Touch sensor to stop the program
        self.left_color = ColorSensor(INPUT_2)  # Left color sensor
        self.right_color = ColorSensor(INPUT_3)  # Right color sensor
        self.sound = Sound()
        
        self.state = RobotState()
        
    def set_motors(self, left_speed, right_speed):
        self.left_motor.on(left_speed)
        self.right_motor.on(right_speed)

    def stop_motors(self):
        self.left_motor.off()
        self.right_motor.off()

    def turn_left(self, duration=TURN_DURATION_90):
        self.set_motors(-BASE_SPEED, BASE_SPEED)
        sleep(duration)
        self.stop_motors()
        sleep(0.2)
        self.state.last_turn_direction = "left"

    def turn_right(self, duration=TURN_DURATION_90):
        self.set_motors(BASE_SPEED, -BASE_SPEED)
        sleep(duration)
        self.stop_motors()
        sleep(0.2)
        self.state.last_turn_direction = "right"

    def follow_line(self):
        left_color = self.left_color.color
        right_color = self.right_color.color

        if left_color == BLACK and right_color != BLACK:
            self.set_motors(-(BASE_SPEED + TURN_RATE), BASE_SPEED * 1.5)
        elif left_color != BLACK and right_color == BLACK:
            self.set_motors(BASE_SPEED * 1.5, -(BASE_SPEED + TURN_RATE))
        elif left_color == BLACK and right_color == BLACK:
            self.set_motors(33, 33)
        elif left_color != BLACK and right_color != BLACK:
            self.set_motors(33, 33)

    def check_for_red_junction_after_picking_up_object(self):
        left_color = self.left_color.color
        right_color = self.right_color.color
        
        if self.state.after_picking_up_object and self.state.on_path_to_object_pickup and (left_color == RED or right_color == RED):
            return True
        return False

    def handle_one_red_after_turn(self):
        self.stop_motors()
        sleep(0.2)
        
        if self.state.last_turn_direction == "left":
            self.turn_right(duration=TURN_DURATION_50)
        else:
            self.turn_left(duration=TURN_DURATION_50)

    def check_for_red_junction(self):
        if self.state.after_picking_up_object:
            return False

        left_color = self.left_color.color
        right_color = self.right_color.color
        
        if ((left_color == RED and right_color != RED) or 
            (right_color == RED and left_color != RED)) and not self.state.on_path_to_object_pickup:
            return True
        
        return False

    def check_for_blue_junction(self):
        if not self.state.after_picking_up_object or self.state.on_path_to_object_pickup:
            return False

        left_color = self.left_color.color
        right_color = self.right_color.color
        
        if ((left_color == BLUE and right_color != BLUE) or 
            (right_color == BLUE and left_color != BLUE)) and not self.state.on_path_to_object_dropoff:
            return True
        
        return False
    
    def handle_red_junction(self):
        left_color = self.left_color.color
        if left_color == RED:
            self.turn_left()
        else:
            self.turn_right()

    def handle_blue_junction(self):
        left_color = self.left_color.color
        if left_color == BLUE:
            self.turn_left()
        else:
            self.turn_right()

    def check_for_red_center(self):
        if self.state.after_picking_up_object:
            return False
            
        left_color = self.left_color.color
        right_color = self.right_color.color
        
        if left_color == RED and right_color == RED and self.state.on_path_to_object_pickup:
            return True
        return False

    def check_for_blue_center(self):
        if not self.state.after_picking_up_object or self.state.on_path_to_object_pickup:
            return False
            
        left_color = self.left_color.color
        right_color = self.right_color.color
        
        if left_color == BLUE and right_color == BLUE and self.state.on_path_to_object_dropoff:
            return True
        return False

    def handle_object_pickup(self):
        self.sound.beep()
        sleep(0.3)
        self.stop_motors()
        self.sound.beep()
        self.arm_motor.on_for_degrees(speed=100, degrees=-85)
        sleep(0.5)
        self.turn_left(duration=TURN_DURATION_90 * 2)

    def handle_object_dropoff(self):
        self.sound.beep()
        sleep(0.3)
        self.stop_motors()
        self.sound.beep()
        self.arm_motor.on_for_degrees(speed=100, degrees=85)
        sleep(0.5)
        self.set_motors(-40, -40)
        sleep(1.5)
        self.stop_motors()

    def handle_button_press(self):
            if self.state.running:
                self.stop_motors()
                self.state.reset()
                self.arm_motor.on_for_degrees(speed=100, degrees=85)
            else:
                self.state.running = True
            sleep(0.5)  # Debounce

    def check_for_black_after_turn(self):
        if self.state.after_picking_up_object and self.left_color.color == BLACK and self.right_color.color == BLACK and self.state.on_path_to_object_pickup:
            return True
        return False

    def handle_black_after_turn(self):
        self.stop_motors()
        sleep(0.2)
        
        if self.state.last_turn_direction == "left":
            self.turn_right(duration=TURN_DURATION_50)
        else:
            self.turn_left(duration=TURN_DURATION_50)

    def run(self):
        print("Line follower program started")
        print("Press touch sensor to start/stop")
        
        while True:
            if self.touch_sensor.is_pressed:
                self.handle_button_press()
            
            if self.state.running:
                if self.check_for_black_after_turn():
                    print("detected_two_blacks__after_picking_up_object")
                    self.state.on_path_to_object_pickup = False
                    self.handle_black_after_turn()

                elif self.check_for_red_junction_after_picking_up_object():
                    print("detected_red_junction_after_picking_up_object")
                    self.state.on_path_to_object_pickup = False
                    self.handle_one_red_after_turn()

                elif self.check_for_red_center():
                    print("detected_red_center")
                    self.state.after_picking_up_object = True
                    self.handle_object_pickup()

                elif self.check_for_blue_center():
                    print("detected_blue_center")
                    self.handle_object_dropoff()
                    self.state.reset()

                elif self.check_for_red_junction():
                    print("detected_red_junction")
                    self.state.on_path_to_object_pickup = True
                    self.handle_red_junction()
                    self.follow_line()

                elif self.check_for_blue_junction():
                    print("detected_blue_junction")
                    self.state.on_path_to_object_dropoff = True
                    self.handle_blue_junction()
                    self.follow_line()

                else:
                    self.follow_line()
            
            sleep(0.02)

if __name__ == "__main__":
    robot = LineFolowerRobot()
    robot.run()
