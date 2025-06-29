import socket
import sys
import time
import machine
import network
import _thread
from machine import Pin
from robot import Robot


# Network credentials
DEFAULT_PORT = 40801
# Replace the values here with your own network login information.
NETWORK_NAME = "Pineapple"
NETWORK_PASSWORD = "Winter2024"

# The Pico board's LED
led = Pin("LED", Pin.OUT)
# Are we flashing the LED?
pico_blinking = 0

robot = Robot()


def enable_networking(wait_time):
  attempts = 0
  time.sleep(wait_time)
  wlan = network.WLAN(network.STA_IF)
  wlan.active(True)
  wlan.connect(NETWORK_NAME, NETWORK_PASSWORD)
      
  while wlan.status() != 3 and attempts < 10:
     time.sleep(1)
     attempts += 1
  
  if wlan.status() == 3:
     address = wlan.ifconfig()
     return address[0]
     
  return False



def display_help():
   send_string = "Tasks the Pico knows how to do:\n\n"
   send_string += "blink [times] - toggle LED <times> or enable/disable if no number specified\n"
   send_string += "echo [text] - repeats text back to client\n"
   send_string += "hello - say Hello to the client\n"
   send_string += "help - show this list of commands\n"
   send_string += "light <on/off> - turn the LED on or off\n"
   send_string += "sleep <seconds> - wait\n"
   send_string += "temp - try to sense temperature (somewhat inaccurate)\n"
   send_string += "exit - disconnect client\n\n"
   
   send_string += "Tasks the robot knows how to do:\n\n"
   send_string += "avoid - try to move away from nearby objects.\n"
   send_string += "circle <radius> - drive in a circle\n"
   send_string += "direction [degrees] - ask/tell the robot which way it is facing.\n"
   send_string += "distance - distance to nearest object in cm\n"
   send_string += "follow - try to follow moving objects in front of the buggy.\n"
   send_string += "forward [steps] - move the buggy forward.\n"
   send_string += "goto <x> <y> - move robot to x,y coordinates.\n"
   send_string += "halt - come to a complete stop\n"
   send_string += "home - the robot will try to find its way back to where it started.\n"
   send_string += "honk - beep the horn\n"
   send_string += "lights <colour> - change the colour of the LED lights on the buggy\n"
   send_string += "line [black/white] - follow a line on the floor. Defaults to black.\n"
   send_string += "manual - Have the robot stop what it is doing and await instructions\n"
   send_string += "pen [up|down] - raise or lower the pen\n"
   send_string += "position [x] [y] - Set the robots current (x,y) location.\n"
   send_string += "reverse [steps] - move the buggy backwards\n"
   send_string += "sensors [barrier]- report the light levels detected. Set light/dark barrier.\n"
   send_string += "speed [new_speed] - get the current speed or set engines to a new speed\n"
   send_string += "spin <left/right> - spin the buggy in place\n"
   send_string += "square [length] - move in a square (forward, right, forward, right)\n"
   send_string += "status - get status report from the buggy\n"
   send_string += "step [steps] - move the buggy forward.\n"
   send_string += "triangle [length] - move the buggy in the shape of a triangle.\n"
   send_string += "turn <degrees> - turn the buggy left or right a number of degrees\n"
   send_string += "wander - the robot will move about randomly. Do not leave unattended.\n"
   send_string += "where - have the robot report on its position and direction\n"
   
   send_string += "\n"
   return send_string
    

def do_blinking():
   global pico_blinking

   # Blink once for each number above zero
   if pico_blinking > 0:
      led.toggle()
      pico_blinking -= 1
   # Blink endlessly if below zero
   elif pico_blinking < 0:
       led.toggle()



def Reset_Everything():
    global pico_blinking
    global robot
    
    pico_blinking = 0
    led.value(1)     # Indicate we are ready for a new connection
    robot.lights_off()
    robot.halt()
    

def Update_Everything():
    global robot
    
    while True:
        do_blinking()
        robot.update()
        time.sleep(1)
    
    
    
def blink(command_line, socket):
    global pico_blinking
   
    if len(command_line) >= 2:
        try:
            blink_times = int(command_line[1])
            send_string = "Blinking " + str(blink_times) + " times.\n"
            pico_blinking = blink_times
        except:
            send_string = "I did not understand " + command_line[1] + "\n"

    else:
        # We did not get a number
        if pico_blinking == 0:
            pico_blinking = -1
            send_string = "Blinking is now enabled.\n"
        else:
            pico_blinking = 0
            send_string = "Blinking is now disabled.\n"
            
    return send_string



def set_direction(command_line):
    global robot
    if len(command_line) < 2:
        # ask the robot what direction it is facing
        current_dir = robot.get_direction()
        send_string = "Facing " + str(current_dir) + " degrees.\n"
        return send_string
    # Try to set new direction
    try:
        new_dir = int(command_line[1])
        if new_dir < 0 or new_dir > 359:
            send_string = "Please specify a direction in the range of 0 to 359.\n"
            return send_string
    except:
        send_string = "Unable to convert " + command_line[1] + " to degrees.\n"
        return send_string
    robot.set_direction(new_dir)
    send_string = "Robot now facing " + command_line[1] + " degrees.\n"
    return send_string



def go_to_sleep(command_line, socket):
    sleep_time = 1.0
    if len(command_line) >= 2:
        try:
           sleep_time = float(command_line[1])
        except:
           send_string = "I did not understand " + command_line[1] + "\n"
           socket.send( send_string.encode() )

    send_string = "Sleeping for " + str(sleep_time) + " seconds.\n"
    socket.send( send_string.encode() )
    time.sleep(sleep_time)
    send_string = "Waking.\n"
    return send_string


def light_on_off(command_line):
   if len(command_line) >= 2:
      if command_line[1] == "on":
         led.value(1)
         return_string = "Turned on LED.\n"
      elif command_line[1] == "off":
         led.value(0)
         return_string = "Turned off LED.\n"
      else:
         return_string = "Command " + command_line[1] + " not recognized.\n"
   else:
      return_string = "Turn light on or off?\n"
   return return_string


def follow_line(command_line):
   global robot
   line_colour = "black"
   if len(command_line) >= 2:
      if command_line[1] == "white":
          line_colour = "white"

   robot.enter_line_follow_mode(line_colour)
   return_string = "Now following any " + line_colour + " line I can find.\n"
   return return_string


def change_lights(command_line):
    global robot
    colour = robot.buggy.WHITE

    if len(command_line) < 2:
        return_string = "Please provide the light colour, such as red, green, or blue.\n"
        return_string += "You can use on to enable auto lighting or off to disable lights.\n"
        return return_string
    if command_line[1] == "red":
        colour = robot.buggy.RED
    elif command_line[1] == "yellow":
        colour = robot.buggy.YELLOW
    elif command_line[1] == "green":
        colour = robot.buggy.GREEN
    elif command_line[1] == "blue":
        colour = robot.buggy.BLUE
    elif command_line[1] == "purple":
        colour = robot.buggy.PURPLE
    elif command_line[1] == "off":
        return_string = "Turning off buggy lights.\n"
        robot.lights_auto = False
        robot.lights_off()
        return return_string
    elif command_line[1] == "auto" or command_line[1] == "on":
        return_string = "Turning on buggy lights and settings to automatic.\n"
        robot.lights_auto = True
        return return_string
    else:
        return_string = "I did not understand the colour " + command_line[1] + "\n"
        return return_string
    return_string = "Setting the lights to " + command_line[1] + "\n"
    robot.lights_auto = False
    robot.set_lights([0,1,2,3], colour)
    return return_string



def sense_temperature():
    sensor_temp = machine.ADC(4)
    conversion_factor = 3.3 / (65535)
    try:
       reading = sensor_temp.read_u16() * conversion_factor
    except:
       send_string = "Unable to read temperature sensor.\n"
       return send_string
    
    try:
       temperature = round(27 - (reading - 0.706)/0.001721, 2)
       temperature -= 17.0
       send_string = "Current temperature: " + str(temperature) + "C\n"
    except:
        send_string = "Unable to convert temperature.\n"
    return send_string


def get_distance():
    global robot
    distance_in_cm = robot.forward_distance
    send_string = "Distance to nearest object in front is " + str(distance_in_cm) + ".\n"
    distance_in_cm = robot.reverse_distance
    send_string += "Distance to nearest object behind is " + str(distance_in_cm) + ".\n"
    return send_string


def spin_buggy(command_line):
    global robot
    
    robot.enter_manual_mode()
    direction = "r"
    send_string = "Spinning buggy to the right.\n" 
    
    if len(command_line) >= 2:
        if command_line[1] == "left":
            direction = "l"
            send_string = "Spinning buggy to the left.\n"
    
    robot.spin(direction)
    return send_string


def turn_buggy(command_line):
    global robot
    
    robot.enter_manual_mode()
    if len(command_line) < 2:
        send_string = "Please specify how many degrees to turn. Negative degrees for left.\n"
        return send_string

    try:
        degrees = int(command_line[1])
    except:
        send_string = "I did not understand " + command_line[1] + ". Please use a number.\n"
        return send_string

    status = robot.turn(degrees)
    if status:
       send_string = "Turning buggy " + str(degrees) + ".\n"
    else:
       send_string = "The buggy ran into a problem trying to turn.\n"
    return send_string



def halt_buggy():
    global robot
    # Put us in manual mode, which also stops the buggy.
    robot.enter_manual_mode()
    send_string = "Coming to a stop.\n"
    return send_string


def move_forward(command_line):
    global robot

    robot.enter_manual_mode()
    if len(command_line) < 2:
        status = robot.forward_steps(1.0)
        if status:
            send_string = "Moving forward one step.\n"
        else:
            send_string = "Cannot move forward, something is in the way.\n"
    else:
       # We were told how far to move
       steps = 1.0
       try:
           steps = float(command_line[1])
       except:
           send_string = "I did not understand " + command_line[1] + " steps.\n"
           return send_string
        
       status = robot.forward_steps(steps)
       if status:
          send_string = "Moved forward " + command_line[1] + " steps.\n"
       else:
          send_string = "Something is in the way, cannot move forward.\n"
           
    return send_string




def move_reverse(command_line):
    global robot
    
    robot.enter_manual_mode()
    if len(command_line) < 2:
        status = robot.reverse_steps(1.0)
        if status:
            send_string = "Moving backware one step.\n"
        else:
            send_string = "Cannot move backward, something is in the way.\n"
            
    else:
       # We were told how far to move
       steps = 1.0
       try:
           steps = float(command_line[1])
       except:
           send_string = "I did not understand " + command_line[1] + " steps.\n"
           return send_string
        
       status = robot.reverse_steps(steps)
       if status:
           send_string = "Moving in reverse.\n"
       else:
           send_string = "Cannot move in reverse.\n"
        
    return send_string


def move_in_circle(command_line):
  global robot
  robot.enter_manual_mode()

  if len(command_line) < 2:
     send_string = "Please provide the radius of the circle.\n"
     return send_string

  radius = 0.0
  try:
     radius = float(command_line[1])
  except:
     send_string = "Did not recognize " + command_line[1] + "\n"
     return send_string

  if radius < 0.1 or radius > 10.0:
     send_string = "Please specify a radius in the range of 0.1 to 10.0\n"
     return send_string

  # A hexagon is basically a crude circle with radian-length sides
  for side in range(6):
     robot.forward_steps(radius)
     time.sleep(1)
     robot.turn(60)
     time.sleep(1)

  send_string = "Finished driving in a circle.\n"
  return send_string



def move_in_square(command_line):
   global robot
   robot.enter_manual_mode()
   if len(command_line) < 2:
      send_string = "Please provide the length of the square's sides.\n"
      return send_string

   line_length = 0.0
   try:
      line_length = float(command_line[1])
   except:
      send_string = "Did not recognize " + command_line[1] + "\n"
      return send_string

   if line_length < 0.1 or line_length > 10.0:
      send_string = "Please specify a length in the range of 0.1 to 10.0\n"
      return send_string

   for sides in range(4):
      robot.forward_steps(line_length)
      time.sleep(1)
      robot.turn(90)
      time.sleep(1)
      
   send_string = "Finished outlining a square.\n"
   return send_string


def move_in_triangle(command_line):
   global robot
   robot.enter_manual_mode()
   if len(command_line) < 2:
      send_string = "Please provide the length of the triangle's sides.\n"
      return send_string

   line_length = 0.0
   try:
      line_length = float(command_line[1])
   except:
      send_string = "Did not recognize " + command_line[1] + "\n"
      return send_string

   if line_length < 0.1 or line_length > 10.0:
      send_string = "Please specify a length in the range of 0.1 to 10.0\n"
      return send_string

   robot.turn(30)
   time.sleep(1)
   robot.forward_steps(line_length)
   time.sleep(1)
   robot.turn(60)
   robot.turn(60)
   time.sleep(1)
   robot.forward_steps(line_length)
   time.sleep(1)
   robot.turn(60)
   robot.turn(60)
   time.sleep(1)
   robot.forward_steps(line_length)
   time.sleep(1)
   robot.turn(90)
   
   send_string = "Finished outlining a triangle.\n"
   return send_string



def set_speed(command_line):
    global robot
    if len(command_line) < 2:
        old_speed = robot.get_speed()
        send_string = "Current speed: " + str(old_speed) + "\n"
        return send_string
    new_speed = int(command_line[1])
    if new_speed < 0 or new_speed > 100:
        send_string = "Speed needs to be in the range of 0-100\n"
        return send_string
    robot.set_speed(new_speed)
    send_string = "Set new speed to " + str(new_speed) + "\n"
    return send_string




def avoid_mode():
   global robot
   robot.enter_avoid_mode()
   send_string = "Robot is entering Avoid mode.\n"
   return send_string


def follow_mode():
   global robot
   robot.enter_follow_mode()
   send_string = "Robot is entering Follow mode.\n"
   return send_string



def goto_mode(command_line):
    global robot

    if len(command_line) < 3:
        send_string = "The goto command requiers two parameters, an X and Y coordinate.\n"
        send_string = "For example, goto 3.5 5.0\n"
        return send_string

    try:
       x = float(command_line[1])
       y = float(command_line[2])
    except:
       send_string = "Did not recognize numbers " + command_line[1] + " or " + command_line[2] + "\n"
       return send_string

    robot.enter_goto_mode(x, y)
    send_string = "Robot is attempting to travel to " + str(x) + ", " + str(y) + "\n"
    return send_string



def home_mode():
    global robot
    robot.enter_home_mode()
    send_string = "Robot is entering Home mode.\n"
    return send_string


def manual_mode():
   global robot
   robot.enter_manual_mode()
   send_string = "Robot has stopped and is awaiting instructions.\n"
   return send_string


def wander_mode():
   global robot
   robot.enter_wander_mode()
   send_string = "Robot is entering Wander mode.\n"
   return send_string


def set_position(command_line):
    global robot
    
    if len(command_line) < 3:
        send_string = "Please provide two coordinates. For example: position 1.5 -2.3\n"
        return send_string
    try:
        x = float(command_line[1])
        y = float(command_line[2])
    except:
        send_string = "Did not understand " + command_line[1] + " " + command_line[2] + "\n"
        return send_string
    x = round(x, 1)
    y = round(y, 1)
    robot.set_coordinates(x, y)
    send_string = "Set new position to (" + str(x) + ", " + str(y) + ")\n"
    return send_string


def get_status():
    global robot
    send_string = "Status report from buggy...\n"
    send_string += "Speed: " + str(robot.speed) + "\n"
    send_string += "Left engine: "
    if robot.left_motor == 0:
        send_string += "off\n"
    elif robot.left_motor < 0:
        send_string += "reverse\n"
    else:
        send_string += "forward\n"
    send_string += "Right engine: "
    if robot.right_motor == 0:
        send_string += "off\n"
    elif robot.right_motor < 0:
        send_string += "reverse\n"
    else:
        send_string += "forward\n"
    send_string += "Distance to nearest forward object: " + str(robot.forward_distance) + "cm\n"
    send_string += "Distance to nearest rear object: " + str(robot.reverse_distance) + "cm\n"
    send_string += light_sensors([0])
    if robot.lights_auto:
        send_string += "Lights: managed automatically.\n"
    else:
        send_string += "Lights: managed manually.\n"
    mode = robot.get_mode()
    send_string += "Mode: " + mode + "\n"
    send_string += where_report()
    mode = robot.get_pen_position()
    send_string += "Pen position: " + mode + "\n"
    return send_string



def where_report():
   global robot
   x_and_y = robot.get_coordinates()
   direction = robot.get_direction()
   return_string = "Direction: " + str(direction) + "\n"
   return_string += "Position: " + str(x_and_y) + "\n"
   return return_string



def light_sensors(command_line):
    global robot
    
    if len(command_line) >= 2:
        try:
            new_level = int(command_line[1])
            robot.set_light_barrier_level(new_level)
            send_string = "Set new light level to: " + command_line[1] + "\n"
            return send_string
        except:
            send_string = "Unable to set light level barrier to " + command_line[1] + "\n"
            send_string += "Please provide a value in the range of 0 to 65000.\n"
            return send_string
        
    left_eye = robot.buggy.getRawLFValue("l")
    right_eye = robot.buggy.getRawLFValue("r")
    centre_eye = robot.buggy.getRawLFValue("c")
    send_string = "Light levels: Left (" + str(left_eye) + ") "
    send_string += "Centre (" + str(centre_eye) + ") "
    send_string += "Right (" + str(right_eye) + ")\n"
    send_string += "Light barrier between light and dark: " + str(robot.light_barrier) + "\n"
    return send_string



def hold_pen(command_line):
   global robot

   robot.enter_manual_mode()

   if len(command_line) < 2:
      send_string = "Please provide 'up' or 'down' to indicate if the pen should be raised or lowered.\n"
      return send_string

   if command_line[1] == "up":
      robot.pen_up()
      send_string = "Raising the pen arm.\n"
   elif command_line[1] == "down":
      robot.pen_down()
      send_string = "Lowering the pen arm.\n"
   else:
      send_string = "I did not understand. Please specify 'pen up' or 'pen down'.\n"
   return send_string



def parse_incoming_command(command, client_socket):
    global robot
    command_and_args = command.split()
    return_value = True
    args_length = len(command_and_args)

    if args_length >= 1:
      cmd = command_and_args[0].lower()

    if args_length < 1:
       send_string = "Nothing received\n"
    elif cmd == "avoid":
        send_string = avoid_mode()
    elif cmd == "direction":
        send_string = set_direction(command_and_args)
    elif cmd == "distance":
        send_string = get_distance()
    elif cmd == "echo":
       send_string = command + "\n"
    elif cmd == "exit":
       send_string = "Good-bye\n"
       return_value = False
    elif cmd == "follow":
        send_string = follow_mode()
    elif cmd == "forward":
        send_string = move_forward(command_and_args)
    elif cmd == "goto":
        send_string = goto_mode(command_and_args)
    elif cmd == "halt":
        send_string = halt_buggy()
    elif cmd == "hello":
       send_string = "Hello\n"
    elif cmd == "help":
        send_string = display_help()
    elif cmd == "home":
        send_string = home_mode()
    elif cmd == "honk":
        robot.honk()
        send_string = "Beep beep\n"
    elif cmd == "blink":
        send_string = blink(command_and_args, client_socket)
    elif cmd == "light":
        send_string = light_on_off(command_and_args)
    elif cmd == "lights":
        send_string = change_lights(command_and_args)
    elif cmd == "line":
        send_string = follow_line(command_and_args)
    elif cmd == "manual":
        send_string = manual_mode()
    elif cmd == "pen":
        send_string = hold_pen(command_and_args)
    elif cmd == "position":
        send_string = set_position(command_and_args)
    elif cmd == "reverse":
        send_string = move_reverse(command_and_args)
    elif cmd == "sensors":
        send_string = light_sensors(command_and_args)
    elif cmd == "sleep":
       send_string = go_to_sleep(command_and_args, client_socket)
    elif cmd == "speed":
        send_string = set_speed(command_and_args)
    elif cmd == "spin":
        send_string = spin_buggy(command_and_args)
    elif cmd == "square":
        send_string = move_in_square(command_and_args)
    elif cmd == "status":
        send_string = get_status()
    elif cmd == "step":
        send_string = move_forward(command_and_args)
    elif cmd == "temp":
        send_string = sense_temperature()
    elif cmd == "triangle":
        send_string = move_in_triangle(command_and_args)
    elif cmd == "turn":
        send_string = turn_buggy(command_and_args)
    elif cmd == "wander":
        send_string = wander_mode()
    elif cmd == "where":
        send_string = where_report()
    else:
       send_string = "Command not recognized.\n"

    client_socket.send( send_string.encode() )
    return return_value



def create_network_service(host='0.0.0.0', port=DEFAULT_PORT):
    server_running = True
    
    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind( (host, port) )
                      
    # Listen for incoming connections
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    _thread.start_new_thread(Update_Everything, ())
    while server_running:
        # Accept new connections
        client_socket, address = server_socket.accept()
        print(f"Connected to {address}")
        client_socket.send( "Hello, I am Ron the robot!\n".encode() )
        client_socket.send( "Type 'help' to get a list of recognized commands.\n".encode() )

        Reset_Everything()
        
        # Receive data from the client
        keep_running = True
        while keep_running:
            client_socket.send( "Ron is ready> ".encode() )
            data = client_socket.recv(1024)
            if data:
               print(f"Received: {data.decode()}")
               status = parse_incoming_command(data.decode(), client_socket)
               keep_running = status
            else:
               keep_running = False

        # Close the client socket
        Reset_Everything()
        client_socket.close()
        


def main():
    
    # Init pico
    delay = 1
    my_address = enable_networking(delay)
    if my_address:
       print("My IP address ", my_address)
       led.value(1)
       # Set up listening socket and parse commands
       create_network_service(my_address, DEFAULT_PORT)

    else:
       print("Unable to connect to network.")
       led.value(0)

    

if __name__ == "__main__":
   main()

