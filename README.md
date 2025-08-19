MicroPython LCD Library
A robust and easy-to-use library for controlling character LCDs with MicroPython.
About The Project
This library allows you to effortlessly control HD44780-compatible LCD displays on MicroPython-enabled microcontrollers. It supports both 4-bit and 8-bit modes and includes essential functions for writing text, clearing the screen, controlling the cursor, and creating custom characters.
Key Features
• 4-bit and 8-bit Mode Support: High flexibility for different hardware setups.
• Essential Functions: Simple and intuitive functions like write(), clear(), and home().
• Advanced Features: Powerful capabilities like create_char() for custom characters and display_shift() for visual effects.
• Backlight Control: Easily turn the display's backlight on or off.
• Robust Input Validation: Built-in error handling to prevent common issues.
Getting Started
Installation
To use this library, simply copy the lcd.py file to your microcontroller's storage (e.g., using Thonny or ampy).
Wiring (4-Bit Mode)
LCD PinGPIO Pin (Example)
RS
26
E
27
D4
25
D5
33
D6
32
D7
35
VSS
GND
VDD
3.3V
Vo (Contrast)
Potentiometer or GND
A (Backlight Anode)
3.3V (with resistor)
K (Backlight Cathode)
GND
Usage Example
Here's a quick example to get started.
import time from lcd import LCD # Pin configuration for a 16x2 LCD in 4-bit mode. # Adjust the pin numbers to match your circuit. lcd = LCD( cols=16, rows=2, rs=26, e=27, d4=25, d5=33, d6=32, d7=35 ) # Turn on the backlight if configured lcd.backlight_on_off(True) # Initialize the display lcd.init() # Write a welcome message to the first line lcd.write("Hello, World!", row=0) # Move to the second line and write another message lcd.write("Future CEO!", row=1) # Create and display a custom character # Pixel map for a small heart heart_pattern = [0x00, 0x0A, 0x1F, 0x1F, 0x0E, 0x04, 0x00, 0x00] lcd.create_char(0, heart_pattern) # Display the custom character lcd.position(15, 0) lcd.write_char(chr(0)) # Shift the display content time.sleep(2) lcd.display_shift('left') 
API Reference
• LCD(cols, rows, ...): The class constructor.
• init(): Initializes the display for operation.
• write(text, col, row, ...): Writes a string to a specific position.
• clear(): Clears the entire display.
• position(col, row): Moves the cursor to a specific column and row.
• home(): Returns the cursor to position (0, 0).
• display_on_off(state): Turns the display on or off.
• backlight_on_off(state): Turns the backlight on or off.
• create_char(location, char_map): Creates a custom character in CGRAM.
• display_shift(direction): Shifts the display content left or right.
License
This project is licensed under the MIT License. See the LICENSE file for details.
© 2025 Mohammad Yasin Maleki
