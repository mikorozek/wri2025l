#!/usr/bin/env python3
from time import sleep
from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C
from ev3dev2.sensor import INPUT_3, INPUT_2, INPUT_4
from ev3dev2.sensor.lego import TouchSensor, ColorSensor
from ev3dev2.sound import Sound

BASE_SPEED = 50
TURN_RATE = 50
DEFAULT_LINE_COLOR = 1
OBJECT_PICKUP_COLOR = 5
OBJECT_DROPOFF_COLOR = 3
TURN_DURATION_90 = 1.05
TURN_DURATION_50 = 0.6

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
        self.left_motor = LargeMotor(OUTPUT_B)
        self.right_motor = LargeMotor(OUTPUT_C)
        self.arm_motor = MediumMotor(OUTPUT_A)
        
        self.touch_sensor = TouchSensor(INPUT_4)
        self.left_color = ColorSensor(INPUT_2)
        self.right_color = ColorSensor(INPUT_3)
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

        if left_color == DEFAULT_LINE_COLOR and right_color != DEFAULT_LINE_COLOR:
            self.set_motors(-(BASE_SPEED + TURN_RATE), BASE_SPEED * 1.5)
        elif left_color != DEFAULT_LINE_COLOR and right_color == DEFAULT_LINE_COLOR:
            self.set_motors(BASE_SPEED * 1.5, -(BASE_SPEED + TURN_RATE))
        elif left_color == DEFAULT_LINE_COLOR and right_color == DEFAULT_LINE_COLOR:
            self.set_motors(33, 33)
        elif left_color != DEFAULT_LINE_COLOR and right_color != DEFAULT_LINE_COLOR:
            self.set_motors(33, 33)

    def check_for_pick_up_color_after_picking_up_object(self):
        left_color = self.left_color.color
        right_color = self.right_color.color
        
        if self.state.after_picking_up_object and self.state.on_path_to_object_pickup and (left_color == OBJECT_PICKUP_COLOR or right_color == OBJECT_PICKUP_COLOR):
            return True
        return False

    def handle_object_pickup_color_after_turn(self):
        self.stop_motors()
        sleep(0.2)
        
        if self.state.last_turn_direction == "left":
            self.turn_right(duration=TURN_DURATION_50)
        else:
            self.turn_left(duration=TURN_DURATION_50)

    def check_for_path_to_object_pickup(self):
        if self.state.after_picking_up_object:
            return False

        left_color = self.left_color.color
        right_color = self.right_color.color
        
        if ((left_color == OBJECT_PICKUP_COLOR and right_color != OBJECT_PICKUP_COLOR) or 
            (right_color == OBJECT_PICKUP_COLOR and left_color != OBJECT_PICKUP_COLOR)) and not self.state.on_path_to_object_pickup:
            return True
        
        return False

    def check_for_path_to_object_dropoff(self):
        if not self.state.after_picking_up_object or self.state.on_path_to_object_pickup:
            return False

        left_color = self.left_color.color
        right_color = self.right_color.color
        
        if ((left_color == OBJECT_DROPOFF_COLOR and right_color != OBJECT_DROPOFF_COLOR) or 
            (right_color == OBJECT_DROPOFF_COLOR and left_color != OBJECT_DROPOFF_COLOR)) and not self.state.on_path_to_object_dropoff:
            return True
        
        return False
    
    def handle_object_pickup_junction(self):
        left_color = self.left_color.color
        if left_color == OBJECT_PICKUP_COLOR:
            self.turn_left()
        else:
            self.turn_right()

    def handle_object_dropoff_junction(self):
        left_color = self.left_color.color
        if left_color == OBJECT_DROPOFF_COLOR:
            self.turn_left()
        else:
            self.turn_right()

    def check_for_pickup_tile(self):
        if self.state.after_picking_up_object:
            return False
            
        left_color = self.left_color.color
        right_color = self.right_color.color
        
        if left_color == OBJECT_PICKUP_COLOR and right_color == OBJECT_PICKUP_COLOR and self.state.on_path_to_object_pickup:
            return True
        return False

    def check_for_dropoff_tile(self):
        if not self.state.after_picking_up_object or self.state.on_path_to_object_pickup:
            return False
            
        left_color = self.left_color.color
        right_color = self.right_color.color
        
        if left_color == OBJECT_DROPOFF_COLOR and right_color == OBJECT_DROPOFF_COLOR and self.state.on_path_to_object_dropoff:
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
            sleep(0.5)

    def check_for_double_default_line_color_after_turn(self):
        if self.state.after_picking_up_object and self.left_color.color == DEFAULT_LINE_COLOR and self.right_color.color == DEFAULT_LINE_COLOR and self.state.on_path_to_object_pickup:
            return True
        return False

    def handle_double_default_line_color_after_turn(self):
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
                if self.check_for_double_default_line_color_after_turn():
                    print("detected double line default color after picking up object")
                    self.state.on_path_to_object_pickup = False
                    self.handle_double_default_line_color_after_turn()

                elif self.check_for_pick_up_color_after_picking_up_object():
                    print("detected pick up color after picking up object")
                    self.state.on_path_to_object_pickup = False
                    self.handle_object_pickup_color_after_turn()

                elif self.check_for_pickup_tile():
                    print("detected pickup tile")
                    self.state.after_picking_up_object = True
                    self.handle_object_pickup()

                elif self.check_for_dropoff_tile():
                    print("detected dropoff tile")
                    self.handle_object_dropoff()
                    self.state.reset()

                elif self.check_for_path_to_object_pickup():
                    print("detected path to object pickup")
                    self.state.on_path_to_object_pickup = True
                    self.handle_object_pickup_junction()
                    self.follow_line()

                elif self.check_for_path_to_object_dropoff():
                    print("detected path to object dropoff")
                    self.state.on_path_to_object_dropoff = True
                    self.handle_object_dropoff_junction()
                    self.follow_line()

                else:
                    self.follow_line()
            
            sleep(0.02)

if __name__ == "__main__":
    robot = LineFolowerRobot()
    robot.run()
