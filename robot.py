import PicoAutonomousRobotics
import time

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
# forward - move forward at set speed until told to stop or we get too close to something
# forward_steps - move forward a given number of feet (30 cm)
# spin - spin in place to the left ("l") or right ("r")
# turn - turn left or right a specified number of degrees


# Constants
DEFAULT_SPEED = 50
TOO_CLOSE = 30
MIDDLE_DISTANCE = 60
LIGHT_LEVEL = 15
 
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
       self.direction = 0
       self.get_forward_distance()
       self.set_lights([0,1,2,3], self.buggy.GREEN)
       self.lights_auto = True
       self.buggy.setBrightness(LIGHT_LEVEL)
       self.buggy.show()
       self.buggy.silence()
       self.speed = 0
     

   def halt(self):
       self.buggy.motorOff("l")
       self.buggy.motorOff("r")
       self.left_motor = 0
       self.right_motor = 0




   def update(self):
       # Logic is reversed to put sensor on rear
       self.forward_distance = self.buggy.getDistance("r")
       if self.forward_distance <= TOO_CLOSE and self.forward_distance > 1:
           if self.lights_auto:
                self.set_lights([0,1,2,3], self.buggy.RED)
           # if we are moving forward, check for objects
           if self.left_motor > 0 and self.right_motor > 0:
               self.halt()
       elif self.forward_distance > TOO_CLOSE and self.forward_distance < MIDDLE_DISTANCE:
           if self.lights_auto:
              self.set_lights([0,1,2,3], self.buggy.BLUE)
       else:
          if self.lights_auto:
              self.set_lights([0,1,2,3], self.buggy.GREEN)
             


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
           # The directions are all reversed to handle broken motor
           if self.left_motor < 0:
               self.buggy.motorOn("l", "f", self.speed)
           elif self.left_motor > 0:
               self.buggy.motorOn("l", "r", self.speed)
           else:
               self.buggy.motorOff("l")
           if self.right_motor < 0:
               self.buggy.motorOn("r", "f", self.speed)
           elif self.left_motor > 0:
               self.buggy.motorOn("r", "r", self.speed)
           else:
               self.buggy.motorOff("r")
           return True
      return False


   def honk(self):
      self.buggy.beepHorn()


   def get_forward_distance(self):
       # Logic is reversed to read sensor on rear
       self.forward_distance = self.buggy.getDistance("r")
       return self.forward_distance




   def forward(self):
       # First, stop what we are doing
       self.halt()
       # check there is nothing in front of us
       distance = self.forward_distance
       if distance > TOO_CLOSE or distance < 0:
           # Check if we need to engage throttle
           if self.speed <= 0:
              self.set_speed(DEFAULT_SPEED)
              
           self.left_motor = 1
           self.right_motor = 1
           # Logic is reversed to handle broken motor
           self.buggy.motorOn("r", "r", self.speed)
           self.buggy.motorOn("l", "r", self.speed)
           return True
       else:    # we are too close to things in front, stop
          return False



   # Nove forward approximately number_of_steps feet
   # Return True if we moved or False if we cannot move.
   def forward_steps(self, number_of_steps):
      self.halt()
     
      if number_of_steps < 1 or number_of_steps > 10:
         return False
      time_to_wait = (100 / speed) * number_of_steps
      time_to_wait /= 2.0
      status = self.forward()
      if (status):
          time.sleep(time_to_wait)
          self.halt()
      return status



   def reverse(self):
       self.halt()
       if self.speed <= 0:
           self.set_speed(DEFAULT_SPEED)
       
       self.left_motor = -1
       self.right_motor = -1
       # Logic is reversed to handle broken motor
       self.buggy.motorOn("r", "f", self.speed)
       self.buggy.motorOn("l", "f", self.speed)
       return True
    

   def spin(self, left_right):
       # Stop before we do the next action
       self.halt()
       # Spin in place
       if self.speed <= 0:
           self.set_speed(DEFAULT_SPEED) 

       if left_right == "r":   # spin right
          self.buggy.motorOn("r", "r", self.speed)
          # self.buggy.motorOn("r", "f", self.speed)
       else:    # spin left
          self.buggy.motorOn("l", "r", self.speed)


   # Work out how long it will take us to turn
   # N degrees. Then decide if we want to turn left or right.
   # Use the "spin" function to get us moving, then sleep
   # while we turn, then stop the engines.
   def turn(self, degrees):
       self.halt()
       if degrees > 359 or degrees < -359:
          return False
       # Estimated time it will take to turn us in a circle
       degrees_per_second = 360
       degrees_to_turn = abs(degrees)
       sleep_time = degrees_to_turn / degrees_per_second
       if degrees < 0:
          self.spin("l")
       else:
          self.spin('r")
       time.sleep(sleep_time)
       self.halt()
       return True

