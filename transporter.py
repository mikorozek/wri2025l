#!/usr/bin/env python3
from time import sleep
from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C
from ev3dev2.sensor import INPUT_3, INPUT_2, INPUT_4
from ev3dev2.sensor.lego import TouchSensor, ColorSensor
from ev3dev2.sound import Sound

# Constants
BASE_SPEED = 50  # Base speed (percentage)
TURN_RATE = 50   # Turn rate coefficient
BLACK = 1        # Value for black color
WHITE = 6        # Value for white color
RED = 5          # Value for red color (pickup color)
BLUE = 2         # Value for blue color (dropoff color)
TURN_DURATION_90 = 1.05    # Duration for 90-degree turn
TURN_DURATION_75 = 0.875   # Duration for 75-degree turn

class RobotState:
    """Class to manage robot state."""
    def __init__(self):
        self.running = False
        self.at_junction_edge = False   # True when one sensor detected red (at junction edge)
        self.after_180_turn = False     # True after the robot has made a 180-degree turn
        self.red_detected_after_turn = False  # True if red is detected again after 180-degree turn
        self.last_turn_direction = None  # 'left' or 'right', to remember which way we turned

class LineFolowerRobot:
    """Class to manage the line follower robot."""
    def __init__(self):
        # Initialize motors
        self.left_motor = LargeMotor(OUTPUT_B)  # Left track motor
        self.right_motor = LargeMotor(OUTPUT_C)  # Right track motor
        self.medium_motor = MediumMotor(OUTPUT_A)
        
        # Initialize sensors
        self.touch_sensor = TouchSensor(INPUT_4)  # Touch sensor to stop the program
        self.left_color = ColorSensor(INPUT_2)  # Left color sensor
        self.right_color = ColorSensor(INPUT_3)  # Right color sensor
        self.sound = Sound()
        
        # Initialize state
        self.state = RobotState()
        
        print("Line follower robot initialized")
        
    def set_motors(self, left_speed, right_speed):
        """Set speeds for both motors."""
        self.left_motor.on(left_speed)
        self.right_motor.on(right_speed)

    def stop_motors(self):
        """Stop both motors."""
        self.left_motor.off()
        self.right_motor.off()

    def turn_left(self, duration=TURN_DURATION_90):
        """Turn the robot left (counterclockwise)."""
        print("Turning left")
        self.set_motors(-BASE_SPEED, BASE_SPEED)
        sleep(duration)
        self.stop_motors()
        sleep(0.2)
        self.state.last_turn_direction = "left"

    def turn_right(self, duration=TURN_DURATION_90):
        """Turn the robot right (clockwise)."""
        print("Turning right")
        self.set_motors(BASE_SPEED, -BASE_SPEED)
        sleep(duration)
        self.stop_motors()
        sleep(0.2)
        self.state.last_turn_direction = "right"

    def follow_line(self):
        """Basic line following algorithm."""
        left_color = self.left_color.color
        right_color = self.right_color.color
        
        # Check for both black after a 180-degree turn
        if self.state.after_180_turn and left_color == BLACK and right_color == BLACK:
            print("Both sensors detected BLACK after 180-degree turn")
            self.stop_motors()
            sleep(0.2)
            
            # Turn 75 degrees in the same direction as the last 90-degree turn
            if self.state.last_turn_direction == "left":
                print("Turning 75 degrees left (same as previous turn)")
                self.turn_left(duration=TURN_DURATION_75)
            else:
                print("Turning 75 degrees right (same as previous turn)")
                self.turn_right(duration=TURN_DURATION_75)
        
        # Standard line following
        if left_color == BLACK and right_color != BLACK:
            # Line under left sensor - turn left
            self.set_motors(-(BASE_SPEED + TURN_RATE), BASE_SPEED * 1.5)
            print("Turning left")
        elif left_color != BLACK and right_color == BLACK:
            # Line under right sensor - turn right
            self.set_motors(BASE_SPEED * 1.5, -(BASE_SPEED + TURN_RATE))
            print("Turning right")
        elif left_color == BLACK and right_color == BLACK:
            # Both sensors see the line - go straight
            self.set_motors(33, 33)
            print("Moving straight (both sensors on line)")
        elif left_color != BLACK and right_color != BLACK:
            # No sensor sees the line - search by going straight
            self.set_motors(33, 33)
            print("Searching for line (both sensors off line)")

    def check_for_red_after_turn(self):
        """Check for red detection after a 180-degree turn."""
        left_color = self.left_color.color
        right_color = self.right_color.color
        
        # If after 180-degree turn and we detect red again
        if self.state.after_180_turn and (left_color == RED or right_color == RED):
            if not self.state.red_detected_after_turn:
                print("Red detected again after 180-degree turn - ignoring")
                self.state.red_detected_after_turn = True
            return True
            
        return False

    def check_for_red_junction(self):
        """Check if one color sensor detects red (at edge of junction)."""
        # If we're already after 180-degree turn or found red after turn, skip detection
        if self.state.after_180_turn:
            return False
            
        left_color = self.left_color.color
        right_color = self.right_color.color
        
        # Check if one sensor detects red and we're not already aware of the junction
        if ((left_color == RED and right_color != RED) or 
            (right_color == RED and left_color != RED)) and not self.state.at_junction_edge:
            print("Red junction edge detected")
            self.state.at_junction_edge = True
            
            if left_color == RED:
                print("Left sensor detected red")
                self.turn_left()
            else:
                print("Right sensor detected red")
                self.turn_right()
            
            return True
        
        return False

    def check_for_red_center(self):
        """Check if both color sensors detect red (at center of red tile)."""
        # If we're already after 180-degree turn, skip detection
        if self.state.after_180_turn:
            return False
            
        left_color = self.left_color.color
        right_color = self.right_color.color
        
        # Check if both sensors detect red and we've previously detected an edge
        if left_color == RED and right_color == RED and self.state.at_junction_edge:
            print("Center of red tile detected! Turning around 180 degrees...")
            self.sound.beep()
            self.stop_motors()
            self.medium_motor.on_for_degrees(20, 100)
            sleep(0.5)
            
            # Turn 180 degrees
            self.turn_left(duration=TURN_DURATION_90 * 2)  # Longer duration for full 180
            
            # Reset junction flags and set after_180_turn flag
            self.state.at_junction_edge = False
            self.state.after_180_turn = True
            self.state.red_detected_after_turn = False
            
            print("Turned 180 degrees, returning to line following")
            return True
        
        return False

    def handle_button_press(self):
        """Handle button press to start/stop the robot."""
        if self.touch_sensor.is_pressed:
            if self.state.running:
                self.state.running = False
                self.stop_motors()
                print("Stopping robot")
            else:
                self.state.running = True
                # Reset all state variables
                self.state.at_junction_edge = False
                self.state.after_180_turn = False
                self.state.red_detected_after_turn = False
                self.state.last_turn_direction = None
                print("Starting robot")
            sleep(0.5)  # Debounce
    
    def run(self):
        print("Line follower program started")
        print("Press touch sensor to start/stop")
        
        while True:
            self.handle_button_press()
            
            if self.state.running:
                # Check in priority order
                if self.check_for_red_after_turn():
                    # Red detected after 180-degree turn - continue line following
                    self.follow_line()
                elif self.check_for_red_center():
                    # At center of red tile, handled
                    pass
                elif self.check_for_red_junction():
                    # At edge of red junction, handled
                    pass
                else:
                    # Normal line following
                    self.follow_line()
            
            # Short delay
            sleep(0.02)

# Create and run robot
if __name__ == "__main__":
    robot = LineFolowerRobot()
    robot.run()
