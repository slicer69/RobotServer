# RobotServer

Files and functions for running a command server on a Pico W which can, in turn, control
a Kitronic robot buggy.

Please note, for the robot to work, the PicoAutonomousRobotics.py file from
https://github.com/KitronikLtd/Kitronik-Pico-Autonomous-Robotics-Platform-MicroPython must be
installed on your Raspberry Pi Pico.

This repository contains the following files and functioanlity:

## main.py

This file contains the networking components and chat server for the Pico-powered robot. This file
must be installed on the Pico with the fielname "main.py" so that it runs when the Pico powers on.
This program connects to a local network using the credentials stored in the variables "ssid" and
"password", which are located near the top of the main.py file.

Once connected to the network this program waits for a network connection from a plain-text client,
such as telnet or nc. It then processes commands sent to it. The client can send the command "help"
to see a list of all supported commands.

Commands are parsed and then, as appropriate, sent to the Robot class to manipulate the Kitronik
robot.


## main.py.local

This program works almost exactly like the main.py program. The difference is this version of main.py
assumes we only have access to the Pico itself, not any other equipment or robot. The main.py.local
program will also set up a network connection and accept connections from plain-text clients. However,
its functionality is limited to what the Pico can do. This includes reading the temperature, flashing
its LED light, echoing back commands, and sleeping a specified amount of time. Run the "help"
command to see a complete list.


## robot.py

This file contains the Robot Python class which is responsible for interacting with the Kitronic
robot buggy. It handles managing the hardware - changing the light colour, detecting nearby
objects, turning on/off the motors. The user does not interact directly with the robot.py code
(user interaction is handled by main.py), but this is the middle layer between the user and
the PicoAutonomousRobotics.py library which controls the robot's hardware.


## send-batch

This is a shell script which accepts two parameters: a network IP address or hostname where the 
Pico can be found and the name of a text file. The text file can contain commands the main.py
service running on the Pico W can understand. Commands for the Pico are listed, one per line,
and sent to the Pico for processing. This provides a way to either test or demo the capabilities
of the Pico and (optionally) the robot.


## test-file

This is an example command file which can be sent to the Pico W by the send-batch script
mentioned above. It sends a few commands, blinks the Pico's light on/off, and then disconnects.

