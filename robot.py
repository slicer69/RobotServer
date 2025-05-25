import math
import random
import time
import PicoAutonomousRobotics

# User facing functions
# reset - reset the robot's position and direction to (0,0) and 0 degrees and turn off lights
# halt  - stop everything
# update - check for objects in front or behind us, update coorindates
#          any other maintenance like flashing lights
# get_coordinates - return current (x,y)
# set_coordinates - set (x,y)
# get_speed - get current motor speed
# set_speed - set motor speed (0-100) - does not engage motor, but sets how fast it will go
# get_direction - compass direction estimate
# set_direction - set direction 0-359
# honk - beep the horn
# get_forward_distance - cm to anything in front of us
# get_backward_distance - cm to anything behind us
# forward_steps - move forward a given number of feet (30 cm)
# reverse_steps - move backward a given number of feet (30 cm)
# spin - spin in place to the left ("l") or right ("r")
# turn - turn left or right a specified number of degrees


# Constants
# How much power to send to the engine (as a percent).
# Usually 50 is good on wood floors. Carpet might require 75.
# Can be adjusted by the user when connected remotely
DEFAULT_SPEED = 50

# How close (in cm) do we get before we should stop?
TOO_CLOSE = 30
MIDDLE_DISTANCE = 60

# How bright should the lights be? 0-100 
LIGHT_LEVEL = 15

# Constants used to make it possible to reverse motor logic
FORWARD_DIRECTION = "f"
REVERSE_DIRECTION = "r"

# Sometimes the motors have different strengths. With
# 1.0 being "normal", this allows us to apply more or
# less power to the left or right motor to balance them.
# My left motor is about 15% weaker, so gets a 0.15 boost.
LEFT_MOTOR_ADJUST = 1.15
RIGHT_MOTOR_ADJUST = 1.0

# Adjust how much time we need to apply power to turn the buggy.
# Ideally, it should be 1.0, but if an engine is stronger or weaker
# we can adjust this. Smaller numbers make the turn angle smaller,
# larger numbers increase the turn.
RIGHT_TURN_MODIFIER = 0.90
LEFT_TURN_MODIFIER = 0.80

# From here on, do not change variables unless you need to make
# big changes to behaviour/logic.

# Actions the robot can perform on its own. The default is manual.
ACTION_MANUAL = 0
ACTION_WANDER = 1
ACTION_FOLLOW = 2
ACTION_HOME = 3
ACTION_LINE_BLACK = 4
ACTION_LINE_WHITE = 5
ACTION_AVOID = 6
ACTION_GOTO = 7



LIGHT_BARRIER = 35000
FOLLOW_LINE_STEP = 0.2
WANDER_STEP = 0.3

class Robot:

   def __init__(self):
       # Init the buggy, make sure it is stopped, quiet, and dark
       self.buggy = PicoAutonomousRobotics.KitronikPicoRobotBuggy()
       self.halt() 
       self.reset()
       self.buggy.setMeasurementsTo("cm")


   def reset(self):
       self.x = 0
       self.y = 0
       self.goto_x = 0.0
       self.goto_y = 0.0
       self.direction = 0
       self.get_forward_distance()
       self.get_reverse_distance()
       self.set_lights([0,1,2,3], self.buggy.GREEN)
       self.lights_auto = True
       self.buggy.setBrightness(LIGHT_LEVEL)
       self.buggy.show()
       self.buggy.silence()
       self.speed = 0
       self.light_barrier = LIGHT_BARRIER
       self.action = ACTION_MANUAL
     

   def halt(self):
       self.buggy.motorOff("l")
       self.buggy.motorOff("r")
       self.left_motor = 0
       self.right_motor = 0



   def avoid(self):
      # This function is basically the opposite of the "follow" function.
      # We try to move away from any object which is closer than MIDDLE_DISTANCE
      front_distance = self.forward_distance
      rear_distance = self.reverse_distance
      steps = 0.3

      # There are a few possibilities...
      # It is possible something is close to us in front and in back
      # We should turn
      if front_distance < MIDDLE_DISTANCE and rear_distance < MIDDLE_DISTANCE:
         number = random.randint(0,1)
         if number == 0:
            degrees = -45
         else:
            degress = 45
         self.turn(degrees)

      # Something is close behind us, but not close in front of us.
      # Meaning we should move forward.
      elif rear_distance < MIDDLE_DISTANCE:
         if front_distance > MIDDLE_DISTANCE or front_distance < 0:
            self.forward_steps(steps)
      # Another option is something is close in front of us, and nothing is behind us.
      elif front_distance < MIDDLE_DISTANCE:
         if rear_distance > MIDDLE_DISTANCE or rear_distance < 0:
            self.reverse_steps(steps)

      # The lat option is there is nothing in front or behind us and we can just stay
      # Where we are.

 


   def follow(self):
      # This function is called about once a second from the update function.
      # Try to follow objects in front of us.
      # We know the update function just checked the distance in
      # front of us. So wait about half a second, check to see if things
      # are moving away. 
      old_distance = self.forward_distance
      time.sleep(0.3)
      new_distance = self.get_forward_distance()

      # If they are further away, move forward an amount
      # proportional with the object's movement.
      # Make sure distance is not an error/infinite
      if new_distance >= 0 and old_distance >= 0:
         if new_distance > old_distance:
             delta_distance = new_distance - old_distance
             # Put a cap on the max distance we will chase
             if delta_distance > MIDDLE_DISTANCE:
                 delta_distance = MIDDLE_DISTANCE
             elif delta_distance < 0.5:
                 # Only move if the distance change is significant
                 return
             # A reasonable amount of steps to move is probably about half a foot
             steps = 0.3
             self.forward_steps(steps)
      # If things are closer, do nothing.
      # If nothing is moving, do nothing, for now


   def follow_line(self):
      # Try to follow a line on the floor.
      left_eye = self.buggy.getRawLFValue("l")
      centre_eye = self.buggy.getRawLFValue("c")
      right_eye = self.buggy.getRawLFValue("r")
    
      on_line = False
      # Black should be a high value, around 30,000 or higher
      # White should be low, below 25,000
      if self.action == ACTION_LINE_BLACK and centre_eye > self.light_barrier:
          on_line = True
      elif self.action == ACTION_LINE_WHITE and centre_eye <= self.light_barrier:
          on_line = True

      # We are on the line, move forward a little
      if on_line:
          self.forward_steps(FOLLOW_LINE_STEP)
      else:
          # We are off the line, check to see if we can find it to the left or right
          # If black, follow higher value senor
          if self.action == ACTION_LINE_BLACK:
             if left_eye > right_eye and left_eye > centre_eye:
                 self.turn(-20)
             elif left_eye < right_eye and left_eye < centre_eye:
                 self.turn(20)
             else:
                 self.forward_steps(FOLLOW_LINE_STEP)
   
          elif self.action == ACTION_LINE_WHITE:
             if left_eye < right_eye and left_eye < centre_eye:
                 self.turn(-20)
             elif left_eye > right_eye and left_eye > centre_eye:
                 self.turn(20)
             else:
                 self.forward_steps(FOLLOW_LINE_STEP)


   def home(self):
       # Try to find our way back to goto_x and goto_y
       # get distance from home point
       distance = math.sqrt( (self.x - self.goto_x)**2 + (self.y - self.goto_y)**2 )
       distance = round(distance, 2)
       # if close to home, stop moving
       if distance < 0.4:
           self.enter_manual_mode()
           return
        
       # If necessary, turn toward home
       target_direction = 0
       # We are "in front" of home, turn back
       if self.y > self.goto_y:
           target_direction = 180
       # We are left of home, turn right
       if self.x < self.goto_x:
           if target_direction == 0:
               target_direction += 45
           else:
               target_direction -= 45
       else:
           # We are right of home, turn left
           if target_direction == 0:
               target_direction -= 45
           else:
               target_direction += 45
               
       # We know which way we want to go, compare that to our current course
       delta_direction = round(target_direction - self.direction, 0)
       if abs(delta_direction) > 20:
           # We are off course, need to turn
           self.turn(delta_direction)
           return
        
       # Pointed in the right direction, move toward home
       move_status = self.forward_steps(0.5)
       if move_status:
           return
       # Something is in the way, wander for now, try to find home later.
       self.wander()
       
       

   def wander(self):
      # This is called about once a second by the update function.
      # Move about, more or less randomly.
      new_action = random.randint(0, 3)
      if new_action == 0:
          # turn left
          degrees = random.randint(60, 90)
          self.turn(-degrees)
      elif new_action == 2:
          # turn right
          degrees = random.randint(60, 90)
          self.turn(degrees)
      else:
          if self.forward_distance < TOO_CLOSE and self.reverse_distance > TOO_CLOSE:
              # Something in the way, attempt to reverse
              self.reverse_steps(WANDER_STEP)
          # try to move forward
          # There is space for us to move forward
          elif self.forward_distance > MIDDLE_DISTANCE:
              move_steps = random.randint(4, 6)
              move_steps = float(move_steps / 10)
              self.forward_steps(move_steps)
          else:
              # We do not have space to move forward or backward, try turning left or right
              turn = random.randint(0, 1)
              degrees = random.randint(60, 90)
              if turn == 0:
                  self.turn(-degrees)
              else:
                 self.turn(degrees)
      return


   def update(self):
       front_distance = self.buggy.getDistance(FORWARD_DIRECTION)
       self.forward_distance = front_distance
       rear_distance = self.buggy.getDistance(REVERSE_DIRECTION)
       self.reverse_distance = rear_distance
       if front_distance <= TOO_CLOSE and front_distance > 1:
           if self.lights_auto:
                self.set_lights([0,1,2,3], self.buggy.RED)
           # if we are moving forward, check for objects
           if self.left_motor > 0 and self.right_motor > 0:
               self.halt()
       elif rear_distance <= TOO_CLOSE and rear_distance > 1:
           if self.lights_auto:
                self.set_lights([0,1,2,3], self.buggy.RED)
                
       elif front_distance > TOO_CLOSE and front_distance < MIDDLE_DISTANCE:
           if self.lights_auto:
              self.set_lights([0,1,2,3], self.buggy.BLUE)
       elif rear_distance > TOO_CLOSE and rear_distance < MIDDLE_DISTANCE:
           if self.lights_auto:
               self.set_lights([0,1,2,3], self.buggy.BLUE)
       else:
          if self.lights_auto:
              self.set_lights([0,1,2,3], self.buggy.GREEN)
             
       if self.action == ACTION_WANDER:
           self.wander()
       elif self.action == ACTION_FOLLOW:
           self.follow()
       elif self.action == ACTION_HOME or self.action == ACTION_GOTO:
           self.home()
       elif self.action == ACTION_LINE_BLACK or self.action == ACTION_LINE_WHITE:
           self.follow_line()
       elif self.action == ACTION_AVOID:
           self.avoid()



   def set_lights(self, light_array, colour):
       for light in light_array:
           if light >= 0 and light <= 3:
               self.buggy.setLED(light, colour)
               
       self.buggy.show()


   def lights_off(self):
       for light in range(4):
           self.buggy.clear(light)
       self.buggy.show()
       
       
   def get_direction(self):
       return self.direction


   def set_direction(self, new_direction):
       if new_direction >= 0 and new_direction < 360:
           self.direction = new_direction
           return True
       return False


   def get_coordinates(self):
       position = (self.x, self.y)       
       return position


   def set_coordinates(self, x, y):
       self.x = x
       self.y = y
       return True


   def get_speed(self):
       return self.speed


   def set_speed(self, new_speed):
      if new_speed >= 0 and new_speed <= 100:
           self.speed = new_speed
           # if motors are running, engage them at new speed
           if self.left_motor < 0:
               self.buggy.motorOn("l", REVERSE_DIRECTION, self.speed * LEFT_MOTOR_ADJUST)
           elif self.left_motor > 0:
               self.buggy.motorOn("l", FORWARD_DIRECTION, self.speed * LEFT_MOTOR_ADJUST)
           else:
               self.buggy.motorOff("l")
           if self.right_motor < 0:
               self.buggy.motorOn("r", REVERSE_DIRECTION, self.speed * RIGHT_MOTOR_ADJUST)
           elif self.left_motor > 0:
               self.buggy.motorOn("r", FORWARD_DIRECTION, self.speed * RIGHT_MOTOR_ADJUST)
           else:
               self.buggy.motorOff("r")
           return True
      return False


   def set_light_barrier_level(self, new_barrier):
       if new_barrier >= 0 and new_barrier <= 65000:
           self.light_barrier = new_barrier
           
   def get_light_barrier_level(self):
       return self.light_barrier
    

   def honk(self):
      self.buggy.beepHorn()


   def get_mode(self):
       if self.action == ACTION_WANDER:
           return "Wandering"
       if self.action == ACTION_FOLLOW:
           return "Following"
       if self.action == ACTION_HOME:
           return "Returning Home"
       if self.action == ACTION_LINE_WHITE:
           return "Following white line"
       if self.action == ACTION_LINE_BLACK:
           return "Following black line"
       return "Manual"
        


   def enter_avoid_mode(self):
       self.action = ACTION_AVOID
       self.halt()


   def enter_goto_mode(self, new_x, new_y):
       self.action = ACTION_GOTO
       self.halt()
       self.goto_x = new_x
       self.goto_y = new_y

        
   def enter_home_mode(self):
       self.action = ACTION_HOME
       self.halt()
       self.goto_x = 0.0
       self.goto_y = 0.0
 

   def enter_line_follow_mode(self, colour):
       if colour == "white":
           self.action = ACTION_LINE_WHITE
       else:
           self.action = ACTION_LINE_BLACK
       self.halt()


   def enter_manual_mode(self):
       self.action = ACTION_MANUAL
       self.halt()
       self.goto_x = 0.0
       self.goto_y = 0.0
       
       
   def enter_wander_mode(self):
       self.halt()
       self.action = ACTION_WANDER
       

   def enter_follow_mode(self):
       self.halt()
       self.action = ACTION_FOLLOW


   def get_forward_distance(self):
       self.forward_distance = self.buggy.getDistance(FORWARD_DIRECTION)
       return self.forward_distance

   def get_reverse_distance(self):
       self.reverse_distance = self.buggy.getDistance(REVERSE_DIRECTION)
       return self.reverse_distance


   def forward(self):
       # check there is nothing in front of us
       distance = self.forward_distance
       if distance > MIDDLE_DISTANCE or distance < 0:
           # Check if we need to engage throttle
           if self.speed <= 0:
              self.set_speed(DEFAULT_SPEED)
              
           self.left_motor = 1
           self.right_motor = 1
           # Logic is reversed to handle broken motor
           self.buggy.motorOn("r", FORWARD_DIRECTION, self.speed * RIGHT_MOTOR_ADJUST)
           self.buggy.motorOn("l", FORWARD_DIRECTION, self.speed * LEFT_MOTOR_ADJUST)
           return True
       # we are too close to things in front, stop
       return False



   # Nove forward approximately number_of_steps feet
   # Return True if we moved or False if we cannot move.
   def forward_steps(self, number_of_steps):
      self.halt()
     
      if number_of_steps > 10.0:
         return False
      if number_of_steps < 0.1:
          number_of_steps = FOLLOW_LINE_STEP
          
      # Avoid divide by zero error
      if self.speed <= 0:
              self.set_speed(DEFAULT_SPEED)
      time_to_wait = (100 / self.speed) * number_of_steps
      time_to_wait /= 2.0
      status = self.forward()
      if status:
          time.sleep(time_to_wait)
          self.halt()
          self.update_position(number_of_steps)
      return status



   def reverse(self):
       distance = self.reverse_distance
       if distance > MIDDLE_DISTANCE or distance < 0:
           if self.speed <= 0:
               self.set_speed(DEFAULT_SPEED)
       
           self.left_motor = -1
           self.right_motor = -1
           self.buggy.motorOn("r", REVERSE_DIRECTION, self.speed * RIGHT_MOTOR_ADJUST)
           self.buggy.motorOn("l", REVERSE_DIRECTION, self.speed * LEFT_MOTOR_ADJUST)
           return True
       # Not enough room to back up, refuse. 
       return False
   
   # Nove backward approximately number_of_steps feet
   # Return True if we moved or False if we cannot move.
   def reverse_steps(self, number_of_steps):
      self.halt()
     
      if number_of_steps > 10.0:
         return False
      if number_of_steps < 0.1:
          number_of_steps = FOLLOW_LINE_STEP
      
      # Avoid divide by zero error
      if self.speed <= 0:
              self.set_speed(DEFAULT_SPEED)
      time_to_wait = (100 / self.speed) * number_of_steps
      time_to_wait /= 2.0
      status = self.reverse()
      if status:
          time.sleep(time_to_wait)
          self.halt()
          self.update_position(number_of_steps)
      return status



   def spin(self, left_right):
       # Stop before we do the next action
       self.halt()
       # Spin in place
       if self.speed <= 0:
           self.set_speed(DEFAULT_SPEED) 

       if left_right == "r":   # spin right
          self.buggy.motorOn("l", FORWARD_DIRECTION, self.speed * LEFT_MOTOR_ADJUST)
       else:    # spin left
          self.buggy.motorOn("r", FORWARD_DIRECTION, self.speed * RIGHT_MOTOR_ADJUST)


   # Work out how long it will take us to turn
   # N degrees. Then decide if we want to turn left or right.
   # Use the "spin" function to get us moving, then sleep
   # while we turn, then stop the engines.
   def turn(self, degrees):
       self.halt()
       if degrees > 359 or degrees < -359:
          return False
       # Estimated time it will take to turn us in a circle
       # The bot turns a little slower than 360 degrees per second.
       # About 270 at default speed.
       degrees_per_second = 270

       # Update which way we think we are pointing.
       self.update_direction(degrees)

       degrees_to_turn = abs(degrees)
       sleep_time = degrees_to_turn / degrees_per_second
       if degrees < 0:
          self.spin("l")
          sleep_time *= LEFT_TURN_MODIFIER
       else:
          self.spin("r")
          sleep_time *= RIGHT_TURN_MODIFIER
       time.sleep(sleep_time)
       self.halt()
       return True


   # Figure out which way the buggy is pointing.
   def update_direction(self, degrees):
       self.direction += degrees
       while self.direction < 0:
          self.direction += 360
       while self.direction > 360:
          self.direction -= 360    


   # Based on where we were, which way we are pointing
   # and how fast we are going, try to determine where we
   # are relative wot where we started.
   def update_position(self, steps_taken):
       # Convert direction from degrees to radians
       rads = math.radians(self.direction)
       # Calculate new position
       new_y = self.y + steps_taken * math.cos(rads)
       new_x = self.x + steps_taken * math.sin(rads)
       self.x = round(new_x, 2)
       self.y = round(new_y, 2)
  
      
