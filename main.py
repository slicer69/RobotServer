import machine
import network
import socket
import sys
import _thread
import time
from machine import Pin
from robot import Robot


# Network credentials
default_port = 40801
ssid = "Pineapple"
password = "Winter2024"

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
  wlan.connect(ssid, password)
  while wlan.status() != 3 and attempts < 10:
     time.sleep(1)
     attempts += 1

  if wlan.status() == 3:
     address = wlan.ifconfig()
     return address[0]
  else:
     
     return False



def help():
   send_string = "Tasks the Pico knows how to do:\n\n"
   send_string += "blink [times] - toggle LED on/off <times> or enable/disable if not number specified\n"
   send_string += "echo [text] - repeats text back to client\n"
   send_string += "hello - say Hello to the client\n"
   send_string += "help - show this list of commands\n"
   send_string += "light <on/off> - turn the LED on or off\n"
   send_string += "sleep <seconds> - wait\n"
   send_string += "temp - try to sense temperature (somewhat inaccurate)\n"
   send_string += "exit - disconnect client\n\n"
   
   send_string += "Tasks the robot knows how to do:\n\n"
   send_string += "distance - distance to nearest object in cm\n"
   send_string += "forward [steps] - move the buggy forward until it reaches a wall.\n"
   send_string += "halt - come to a complete stop\n"
   send_string += "honk - beep the horn\n"
   send_string += "lights <colour> - change the colour of the LED lights on the buggy\n"
   send_string += "reverse - move the buggy backwards\n"
   send_string += "speed [new_speed] - get the current speed or set engines to a new speed\n"
   send_string += "spin <left/right> - spin the buggy in place\n"
   send_string += "status - get status report from the buggy\n"
   send_string += "turn <degrees> - turn the buggy left or right a number of degrees\n"
   
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



def change_lights(command_line):
    global robot
    colour = robot.buggy.WHITE

    if len(command_line) < 2:
        return_string = "Please provide the light colour, such as red, yellow, green, blue, or purple.\n"
        return_string += "You can use on or auto to enable automatic lighting or off to disable lights.\n"
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
    distance_in_cm = robot.get_forward_distance()
    send_string = "Distance to nearest object is " + str(distance_in_cm) + ".\n"
    return send_string


def spin_buggy(command_line):
    global robot
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
    if len(command_line) < 2:
        send_string = "Please specify how many degrees to turn. Negative degrees for left.\n"
        return send_string

    if not command_line[1].isnumeric():
        send_string = "I did not understand " + command_line[1] + ". Please use a number.\n"
        return send_string

    degrees = int(command_line[1])
    status = robot.turn(degrees)
    if status:
       send_string = "Turning buggy " + str(degrees) + ".\n"
    else:
       send_string = "The buggy ran into a problem trying to turn.\n"
    return send_string



def halt_buggy():
    global robot
    robot.halt()
    send_string = "Coming to a stop.\n"
    return send_string


def move_forward(command_line):
    global robot

    if len(command_line) < 2:
        status = robot.forward()
        if status:
            send_string = "Moving forward.\n"
        else:
            send_string = "Cannot move forward, something is in the way.\n"
    else:
       # We were told how far to move
       if command_line[1].isnumeric():
           steps = int(command_line[1])
           status = robot.forward_steps(steps)
           if status:
              send_string = "Moved forward " + command_line[1] + " steps.\n"
           else:
              send_string = "Something is in the way, cannot move forward.\n"
       else:
           send_string = "I did not understand " + command_line[1] + " steps.\n"
     
    return send_string




def move_reverse():
    global robot
    status = robot.reverse()
    if status:
        send_string = "Moving in reverse.\n"
    else:
        send_string = "Cannot move in reverse.\n"
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
    send_string += "Distance to nearest object: " + str(robot.forward_distance) + "cm\n"
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
    elif cmd == "distance":
        send_string = get_distance()
    elif cmd == "echo":
       send_string = command + "\n"
    elif cmd == "exit":
       send_string = "Good-bye\n"
       return_value = False
    elif cmd == "forward":
        send_string = move_forward(command_and_args)
    elif cmd == "halt":
        send_string = halt_buggy()
    elif cmd == "hello":
       send_string = "Hello\n"
    elif cmd == "help":
        send_string = help()
    elif cmd == "honk":
        robot.honk()
        send_string = "Beep beep\n"
    elif cmd == "blink":
        send_string = blink(command_and_args, client_socket)
    elif cmd == "light":
        send_string = light_on_off(command_and_args)
    elif cmd == "lights":
        send_string = change_lights(command_and_args)
    elif cmd == "reverse":
        send_string = move_reverse()
    elif cmd == "sleep":
       send_string = go_to_sleep(command_and_args, client_socket)
    elif cmd == "speed":
        send_string = set_speed(command_and_args)
    elif cmd == "spin":
        send_string = spin_buggy(command_and_args)
    elif cmd == "status":
        send_string = get_status()
    elif cmd == "temp":
        send_string = sense_temperature()
    elif cmd == "turn":
        send_string = turn_buggy(command_and_args)
    else:
       send_string = "Command not recognized.\n"

    client_socket.send( send_string.encode() )
    return return_value



def create_network_service(host='0.0.0.0', port=default_port):
    server_running = True
    
    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the host and port
    server_socket.bind( (host, port) )

    # Listen for incoming connections
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    _thread.start_new_thread(Update_Everything, ())
    while server_running:
        # Accept new connections
        client_socket, address = server_socket.accept()
        print(f"Connected to {address}")
        client_socket.send( "Type 'help' to get a list of recognized commands.\n".encode() )

        Reset_Everything()
        
        # Receive data from the client
        keep_running = True
        while keep_running:
            client_socket.send( "Ready> ".encode() )
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
        


def signal_handler(my_signal, temp):
   sys.exit(0)


def main():
    
    # Init pico
    delay = 1
    my_address = enable_networking(delay)
    if my_address:
       print("My IP address ", my_address)
       led.value(1)
       # Set up listening socket and parse commands
       create_network_service(my_address, default_port)

    else:
       print("Unable to connect to network.")
       led.value(0)

    

if __name__ == "__main__":
   main()

