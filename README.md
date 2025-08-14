# RobotServer

Files and functions for running a command server on a Pico W which can, in turn, control
a Kitronic robot buggy.

Please note, for the robot to work, the PicoAutonomousRobotics.py file from
https://github.com/KitronikLtd/Kitronik-Pico-Autonomous-Robotics-Platform-MicroPython must be
installed on your Raspberry Pi Pico.

If you plan to connect to the robot over a wireless network, you must create a file called
network.txt on your Pico W and save your credentials in the text file. The first line should
contain the network's name and the secone line should hold the password.

This repository contains the following files and functioanlity:

## main.py

This file contains the networking components and chat server for the Pico-powered robot. This file
must be installed on the Pico with the fielname "main.py" so that it runs when the Pico powers on.
This program connects to a local network using the credentials stored in a file file called
"network.txt". The network.txt file should place the wireless network name on the first line and the
wifi password on the second file.

Once connected to the network this program waits for a network connection from a plain-text client,
such as telnet or nc. It then processes commands sent to it. The client can send the command "help"
to see a list of all supported commands.

By default, the Pico W registers itself on the local network with the hostname "picow"
and listens on network port 40801. Connecting to it is usually as easy as running
"telnet picow 40801".

Commands are parsed and then, as appropriate, sent to the Robot class to manipulate the Kitronik
robot.

The Pico W can also accept Bluetooth connections and instructions over Bluetooth. This is helpful
when the robot is in environments without wi-fi access. The Android app "Serial Bluetooth Terminal
(also known as de.kai.morich.serial_bluetooth_terminal) can be used to connect to the robot. The
robot displays the Bluetooth name "r-robot".


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

There are some variables in the robot.py file, near the top, which can be altered to
fine-tune the robot's behaviour. DEFAULT_SPEED sets the robot's initial throttle, for
example in the range of 0-100. The LEFT_MOTOR_ADJUST and RIGHT_MOTOR_ADJUST can be
used to fine-tune robot movement when one motor is more powerful than the other. In these
cases the robot tends to slowly turn when trying to drive in a straight line. Changing
these variables higher gives the lagging engine more power.

The LIGHT_LEVEL variable adjusts how bright the LED lights are. This value is in the
range of 0-100.


## remote.py

This program allows the Kitronik robot to be remotely piloted using a Nintendo Switch
pro controller. The program tried to connect to the robot over the wi-fi network,
looking for the hostname "picow" and the network port 40801.

When a connection is made the Nintendo controller can be used to send navigation commands
to the robot. The two axis sticks turn the robot and drive it forward or backward.
The A, B, Y, and X buttons change the colour of the robot's lights.

The left button (L) puts the robot into automated Wander mode while the right button (R)
raises and lowers the robot's pen arm if one is attached. The two trigger buttons tell the
robot to stop/halt. The connection can be dropped by pressing + or -. A list of
commands is displayed in the terminal.

The remote.py program requires the pygame Python module which can usually be installed
from your distribution's repositories.


## send-batch

This is a shell script which accepts two parameters: a network IP address or hostname where the 
Pico can be found and the name of a text file. The text file can contain commands the main.py
service running on the Pico W can understand. Commands for the Pico are listed, one per line,
and sent to the Pico for processing. This provides a way to either test or demo the capabilities
of the Pico and (optionally) the robot.


## test-file

This is an example command file which can be sent to the Pico W by the send-batch script
mentioned above. It sends a few commands, blinks the Pico's light on/off, and then disconnects.


## ble_simple_peripheral.py and ble_advertising.py

These two libraries handle setting up and receiving Bluetooth connections. They do not
get run directly, but are used as dependencies to main.py.

