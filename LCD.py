"""
A robust and easy-to-use library for controlling LCD displays
with MicroPython on platforms like ESP32 and ESP8266.
"""

from machine import Pin
import time

class LCD:
    """
    Control an HD44780-compatible LCD display in 4-bit or 8-bit mode.
    """

    def __init__(self, cols, rows, rs, e, d4, d5, d6, d7, bit8=False, d0=None, d1=None, d2=None, d3=None, backlight_pin=None):
        """
        Initializes the LCD object with the given pin configurations.

        Args:
            cols (int): Number of columns on the LCD (e.g., 16).
            rows (int): Number of rows on the LCD (e.g., 2).
            rs (int): GPIO pin connected to the RS pin of the LCD.
            e (int): GPIO pin connected to the E pin of the LCD.
            d4-d7 (int): GPIO pins for the data lines.
            bit8 (bool): If True, enables 8-bit mode.
            d0-d3 (int, optional): Additional GPIO pins for 8-bit mode.
            backlight_pin (int, optional): GPIO pin for controlling the backlight.
        """
        # --- 1. Robust Input Validation (Error Handling) ---
        if not isinstance(bit8, bool):
            raise TypeError("The 'bit8' parameter must be a boolean (True or False).")
        if not isinstance(cols, int) or not isinstance(rows, int):
            raise TypeError("The 'cols' and 'rows' parameters must be integers.")

        if bit8 and (d0 is None or d1 is None or d2 is None or d3 is None):
            raise ValueError("In 8-bit mode, pins d0 to d3 must be provided.")

        all_pin_numbers = [rs, e, d4, d5, d6, d7]
        if bit8:
            all_pin_numbers.extend([d0, d1, d2, d3])
        if backlight_pin is not None:
            all_pin_numbers.append(backlight_pin)

        for pin_number in all_pin_numbers:
            if not isinstance(pin_number, int):
                raise TypeError(f"Pin number '{pin_number}' must be an integer.")

            # Common valid range for ESP32 and many other boards
            if not (0 <= pin_number <= 39):
                raise ValueError(f"Pin number '{pin_number}' is out of the valid range (0-39).")

        # --- 2. Pin Configuration ---
        self.pin_rs = Pin(rs, Pin.OUT)
        self.pin_e = Pin(e, Pin.OUT)
        self.cols = cols
        self.rows = rows
        self.bit8_mode = bit8
        self.backlight_pin = None
        if backlight_pin is not None:
            self.backlight_pin = Pin(backlight_pin, Pin.OUT)

        data_pin_numbers = [d4, d5, d6, d7]
        if bit8:
            data_pin_numbers = [d0, d1, d2, d3] + data_pin_numbers

        self.data_pins = [Pin(pin, Pin.OUT) for pin in data_pin_numbers]

    def _pulse_enable(self):
        """Generates a short pulse on the Enable pin to latch the data."""
        self.pin_e.value(0)
        time.sleep_us(1)
        self.pin_e.value(1)
        time.sleep_us(1)
        self.pin_e.value(0)
        time.sleep_us(100)

    def _send_byte(self, byte, mode):
        """
        Sends a full byte (8 bits) to the LCD.
        Args:
            byte (int): The byte to send.
            mode (int): 0 for command, 1 for data.
        """
        self.pin_rs.value(mode)

        if self.bit8_mode:
            for i in range(8):
                bit = (byte >> i) & 0x01
                self.data_pins[i].value(bit)
        else:
            # Send high nibble
            high_nibble = byte >> 4
            for i in range(4):
                bit = (high_nibble >> i) & 0x01
                self.data_pins[i].value(bit)
            self._pulse_enable()

            # Send low nibble
            low_nibble = byte & 0x0F
            for i in range(4):
                bit = (low_nibble >> i) & 0x01
                self.data_pins[i].value(bit)

        self._pulse_enable()

    def write_char(self, c):
        """
        Writes a single character to the LCD.
        Args:
            c (str): The character to write.
        """
        if not isinstance(c, str) or len(c) != 1:
            raise TypeError("The input must be a single character string.")

        self._send_byte(ord(c), 1)

    def command(self, cmd):
        """
        Sends a command byte to the LCD.
        Args:
            cmd (int): The command to send.
        """
        if not isinstance(cmd, int):
            raise TypeError("The command must be an integer.")

        self._send_byte(cmd, 0)

    def write(self, text, col=0, row=0, clear_line=True):
        """
        Writes a string to the LCD at a specified position.
        Args:
            text (str): The string to write.
            col (int): Starting column (0-indexed).
            row (int): Starting row (0-indexed).
            clear_line (bool): If True, clears the entire line before writing.
        """
        if not isinstance(text, str):
            raise TypeError("The 'text' parameter must be a string.")
        if not isinstance(col, int) or not isinstance(row, int):
            raise TypeError("The 'col' and 'row' parameters must be integers.")
        if not isinstance(clear_line, bool):
            raise TypeError("The 'clear_line' parameter must be a boolean.")

        if not (0 <= col < self.cols and 0 <= row < self.rows):
            raise ValueError(f"Position ({col}, {row}) is out of bounds for a {self.cols}x{self.rows} display.")

        if clear_line:
            self.position(0, row)
            for _ in range(self.cols):
                self.write_char(' ')

        self.position(col, row)

        current_col = col
        for char in text:
            if current_col >= self.cols:
                current_col = 0
                if row + 1 < self.rows:
                    row += 1
                    self.position(current_col, row)
                else:
                    break

            self.write_char(char)
            current_col += 1

    def clear(self):
        """
        Clears the entire LCD display and returns the cursor to the home position.
        """
        self.command(0x01)
        time.sleep_ms(2)

    def position(self, col, row):
        """
        Moves the cursor to the specified column and row.
        Args:
            col (int): The column number (0-indexed).
            row (int): The row number (0-indexed).
        """
        if not isinstance(col, int) or not isinstance(row, int):
            raise TypeError("The 'col' and 'row' parameters must be integers.")

        if not (0 <= col < self.cols and 0 <= row < self.rows):
            raise ValueError(f"Position ({col}, {row}) is out of bounds for a {self.cols}x{self.rows} display.")

        if row == 0:
            address = 0x80 + col
        elif row == 1:
            address = 0xC0 + col
        else:
            address = 0x80 + (0x40 * row) + col

        self.command(address)

    def init(self):
        """Initializes the LCD for operation by sending the required command sequence."""
        # Wait for the LCD to power up
        time.sleep_ms(15)

        if self.bit8_mode:
            # 8-bit mode initialization sequence
            self.command(0x38) # Function Set: 8-bit, 2 lines, 5x8 font
            self.command(0x0C) # Display On, Cursor Off, Blink Off
            self.command(0x06) # Entry Mode Set: Increment, No Shift
            self.command(0x01) # Clear Display
            time.sleep_ms(2)
        else:
            # 4-bit mode initialization sequence
            # This requires a specific sequence of sending only the high nibble
            self._send_byte(0x33, 0)
            self._send_byte(0x32, 0)
            self.command(0x28) # Function Set: 4-bit, 2 lines, 5x8 font
            self.command(0x0C) # Display On, Cursor Off, Blink Off
            self.command(0x06) # Entry Mode Set: Increment, No Shift
            self.command(0x01) # Clear Display
            time.sleep_ms(2)

    def home(self):
        """Returns the cursor to the home position (0, 0) without clearing the display."""
        self.command(0x02)
        time.sleep_ms(2)

    def display_on_off(self, state):
        """Turns the display on or off.
        Args:
            state (bool): True to turn the display on, False to turn it off.
        """
        if self.backlight_pin is None:
            raise ValueError("you dont enter backlight_pin")

        if not isinstance(state, bool):
            raise TypeError("The 'state' parameter must be a boolean.")

        if state:
            self.command(0x0C) # Display ON
        else:
            self.command(0x08) # Display OFF

    def backlight_on_off(self, state):
        """Turns the display backlight on or off, if a backlight pin was specified.
        Args:
            state (bool): True to turn the backlight on, False to turn it off.
        """
        if self.backlight_pin is None:
            raise ValueError("you dont enter backlight_pin")

        if not isinstance(state, bool):
            raise TypeError("The 'state' parameter must be a boolean.")

        if self.backlight_pin is not None:
            self.backlight_pin.value(state)
        else:
            print("Backlight pin was not configured in the constructor.")

    def write_line(self, text, row=0):
        """Writes a string to a specific line, automatically clearing it first."""
        if not isinstance(text, str):
            raise TypeError("The 'text' parameter must be a string.")
        if not isinstance(row, int):
            raise TypeError("The 'row' parameter must be an integer.")
        if not (0 <= row < self.rows):
            raise ValueError("The specified row is out of bounds.")

        self.write(text, col=0, row=row, clear_line=True)

    def create_char(self, location, char_map):
        """Creates a custom character in the LCD's CGRAM.
        Args:
            location (int): The memory location (0-7) to store the character.
            char_map (list): A list of 8 integers representing the pixel map.
        """
        if not isinstance(location, int) or not (0 <= location <= 7):
            raise ValueError("Location must be an integer between 0 and 7.")
        if not isinstance(char_map, list) or len(char_map) != 8:
            raise TypeError("Char map must be a list of 8 integers.")

        for byte in char_map:
            if not isinstance(byte, int) or not (0 <= byte <= 31):
                raise ValueError("Char map values must be integers between 0 and 31.")

        self.command(0x40 + (location << 3))
        for byte in char_map:
            self.write_char(chr(byte))

    def display_shift(self, direction):
        """Shifts the entire display content without changing the DDRAM address.
        Args:
            direction (str): 'left' or 'right'.
        """
        if direction == 'left':
            self.command(0x18)
        elif direction == 'right':
            self.command(0x1C)
        else:
            raise ValueError("Direction must be 'left' or 'right'.")