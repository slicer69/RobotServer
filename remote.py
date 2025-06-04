import pygame
import socket
import signal
import sys
import time


DEFAULT_PORT = 40801
NETWORK_NAME = "picow"
SLEEP_DELAY = 0.1

# Initialize Pygame
pygame.init()


def signal_handler(my_signal, temp):
   sys.exit(0)



def display_help():
   print("Controls for the robot:\n")
   print("Left axis - turn and drive the robot with small adjustments.")
   print("Right axis - turn and drive the robot with larger adjustments.")
   print("Triggers - stop the robot.")
   print("Left button - tell robot to wander.")
   print("Right button - tell robot to return to where it started.")
   print("Y button - turn lights yellow.")
   print("B button - turn lights blue.")
   print("A button - turn lights green.")
   print("X button - turn lights red.")
   print("+ or - button - disconnect.")
   print("")


def connect_to_robot(robot_address, robot_port):
   try:
      clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      clientsocket.connect((robot_address, robot_port))
   except:
      print("Unable to connect to ", robot_address, "\n")
      clientsocket = False

   return clientsocket


def send_message(to_socket, the_message):
   # print("Sending command: ", the_message)
   to_socket.send( the_message.encode() )


# Buttons are translated into commands the robot knows.
def button_to_message(the_button):
   text = " \n"
   if the_button == 0:
      text = "lights yellow\n"
   elif the_button == 1:
      text = "lights blue\n"
   elif the_button == 2:
      text = "lights green\n"
   elif the_button == 3:
      text = "lights red\n"
   elif the_button == 4:
      text = "wander\n"
   elif the_button == 5:
      text = "home\n"
   elif the_button == 6 or the_button == 7:
      text = "halt\n"
   elif the_button == 8 or the_button == 9:
      text = "exit\n"
   # print("Translated ", the_button, " into ", text, "\n")
   return text


def main():

  signal.signal(signal.SIGINT, signal_handler)
  client_socket = connect_to_robot(NETWORK_NAME, DEFAULT_PORT)
  if not client_socket:
     sys.exit(1)

  print("Connected to Ron the Robot!\n")
  keep_going = True
 
  # Set up the controller
  joysticks = pygame.joystick.get_count()
  print(f"Found joystick.")
  display_help()
  if joysticks > 0:
      controller = pygame.joystick.Joystick(0)
      controller.init()

      while keep_going:
          send_direction = False
          for event in pygame.event.get():
              if event.type == pygame.QUIT:
                  send_message(client_socket, "exit\n")
                  # client_socket.close()
                  pygame.quit()
                  sys.exit(0)
              elif event.type == pygame.JOYBUTTONDOWN:
                  button = controller.get_button(event.button)
                  if button:
                      # print(f"Button {event.button} pressed.")
                      message = button_to_message(event.button)
                      send_message(client_socket, message)
                      if message == "exit\n":
                         time.sleep(1)
                         # client_socket.close()
                         pygame.quit()
                         sys.exit(0)
                      time.sleep(1)

          # Detect axis input
          left_stick_x = controller.get_axis(0)
          left_stick_y = controller.get_axis(1)
          right_stick_x = controller.get_axis(2)
          right_stick_y = controller.get_axis(3)

          # Determine direction of left stick
          if left_stick_x < -0.5:
              send_direction = "turn -45\n"
          elif left_stick_x > 0.5:
              send_direction = "turn 45\n"

          if left_stick_y < -0.5:
              send_direction = "forward 0.4\n"
          elif left_stick_y > 0.5:
              send_direction = "reverse 0.4\n"

          # Determine direction of right stick
          if right_stick_x < -0.5:
              send_direction = "turn -90\n"
          elif right_stick_x > 0.5:
              send_direction = "turn 90\n"

          if right_stick_y < -0.5:
              send_direction = "forward 0.8\n"
          elif right_stick_y > 0.5:
              send_direction = "reverse 0.8\n"

          if send_direction:
             send_message(client_socket, send_direction)
             time.sleep(1)
          else:
             time.sleep(SLEEP_DELAY)

      # end of while loop
  else:
      print("No joysticks found.")

  if client_socket:
     client_socket.close()


if __name__ == "__main__":
   main()

