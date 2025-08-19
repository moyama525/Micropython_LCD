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

    def __init__(self, cols, rows, rs, e, d4, d5, d6, d7, bit8=False, d0=None, d1=None, d2=None, d3=None):
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
        """
        # --- 1. Robust Input Validation (Error Handling) ---
        if not isinstance(bit8, bool):
            raise TypeError("The 'bit8' parameter must be a boolean (True or False).")
        if not isinstance(cols, int) or not isinstance(rows, int):
            raise TypeError("The 'cols' and 'rows' parameters must be integers.")
        
        # Check for required pins in 8-bit mode
        if bit8 and (d0 is None or d1 is None or d2 is None or d3 is None):
            raise ValueError("In 8-bit mode, pins d0 to d3 must be provided.")

        # --- NEW: Validate Pin Numbers ---
        # این بخش اعتبار سنجی که قبلاً اضافه کردیم.
        all_pin_numbers = [rs, e, d4, d5, d6, d7]
        if bit8:
            all_pin_numbers.extend([d0, d1, d2, d3])

        for pin_number in all_pin_numbers:
            # First, check if the pin number is a valid integer.
            if not isinstance(pin_number, int):
                raise TypeError(f"Pin number '{pin_number}' must be an integer.")
            
            # Second, check if the pin number is within a common valid range.
            # We use a general range (e.g., 0-39 for ESP32) for this example.
            if not (0 <= pin_number <= 39):
                raise ValueError(f"Pin number '{pin_number}' is out of the valid range (0-39).")

        # --- 2. Pin Configuration ---
        self.pin_rs = Pin(rs, Pin.OUT)
        self.pin_e = Pin(e, Pin.OUT)
        self.cols = cols
        self.rows = rows
        self.bit8_mode = bit8

        # Build a list of data pin numbers based on the mode
        data_pin_numbers = [d4, d5, d6, d7]
        if bit8:
            data_pin_numbers = [d0, d1, d2, d3] + data_pin_numbers

        # Create the final list of Pin objects
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
        
    def write(self, text, col=0, row=0, clear_line=True, scroll=False):
        """
        Writes a string to the LCD at a specified position.
        Args:
            text (str): The string to write.
            col (int): Starting column (0-indexed).
            row (int): Starting row (0-indexed).
            clear_line (bool): If True, clears the entire line before writing.
            scroll (bool): If True, scrolls the text if it's too long.
        """
        # --- 1. Input Validation ---
        if not isinstance(text, str):
            raise TypeError("The 'text' parameter must be a string.")
        if not isinstance(col, int) or not isinstance(row, int):
            raise TypeError("The 'col' and 'row' parameters must be integers.")
        if not isinstance(clear_line, bool) or not isinstance(scroll, bool):
            raise TypeError("Boolean parameters must be a boolean (True or False).")

        # Check if the position is within the display bounds
        if not (0 <= col < self.cols and 0 <= row < self.rows):
            raise ValueError(f"Position ({col}, {row}) is out of bounds for a {self.cols}x{self.rows} display.")
        
        # --- 2. Logic to handle display output ---
        
        # Clear the line if requested
        if clear_line:
            self.position(0, row)
            for _ in range(self.cols):
                self.write_char(' ')
        
        # Set the cursor to the starting position
        self.position(col, row)
        
        # Write the text, wrapping to the next line if needed
        current_col = col
        for char in text:
            # Check for line break and wrap to the next line
            if current_col >= self.cols:
                current_col = 0
                if row + 1 < self.rows:
                    row += 1
                    self.position(current_col, row)
                else:
                    break # Stop if we've run out of lines
            
            self.write_char(char)
            current_col += 1
            
    def clear(self):
        """
        Clears the entire LCD display and returns the cursor to the home position.
        """
        self.command(0x01) # Clear display command
        time.sleep_ms(2)   # This command requires a delay

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

        # Calculate the DDRAM address
        if row == 0:
            address = 0x80 + col
        elif row == 1:
            address = 0xC0 + col
        else:
            # For 4-row displays, you could add:
            # if row == 2: address = 0x80 + 20 + col
            # if row == 3: address = 0xC0 + 20 + col
            # The calculation depends on the specific display model.
            address = 0x80 + (0x40 * row) + col 

        self.command(address)

    # --- توابع جدید و تکمیل شده ---

    def init(self):
        """Initializes the LCD for operation."""
        # This function sends a series of commands to set the bit mode,
        # turn on the display, and clear the screen.
        
        time.sleep_ms(100) # Initial delay after power-on

        if self.bit8_mode:
            # 8-bit mode initialization sequence
            self.command(0x30)
            time.sleep_us(50)
            self.command(0x30)
            time.sleep_us(50)
            self.command(0x30)
            time.sleep_us(50)
            self.command(0x38) # 8-bit mode, 2 lines, 5x8 font
        else:
            # 4-bit mode initialization sequence
            self.command(0x30)
            time.sleep_us(50)
            self.command(0x30)
            time.sleep_us(50)
            self.command(0x20)
            time.sleep_us(50)
            self.command(0x28) # 4-bit mode, 2 lines, 5x8 font
        
        # Common initialization commands
        self.command(0x0C) # Display ON, Cursor OFF, Blink OFF
        self.command(0x06) # Entry Mode Set: increment cursor, no display shift
        self.command(0x01) # Clear display
        time.sleep_ms(2)

    def home(self):
        """
        Returns the cursor to the home position (0, 0) without clearing the display.
        """
        self.command(0x02) # Home command
        time.sleep_ms(2)

    def display_on_off(self, state):
        """
        Turns the display on or off.

        Args:
            state (bool): True to turn on, False to turn off.
        """
        if not isinstance(state, bool):
            raise TypeError("The 'state' parameter must be a boolean (True or False).")
            
        cmd = 0x08 # Base command for Display OFF
        if state:
            cmd |= 0x04 # Add bit D to turn on the display
        
        self.command(cmd)

    def backlight_on_off(self, state):
        """
        Turns the display backlight on or off.
        Note: This function assumes the backlight is controlled via a separate pin.
              You need to add a 'bl' pin to the __init__ and self.pin_bl = Pin(bl, Pin.OUT)
        Args:
            state (bool): True to turn on, False to turn off.
        """
        # --- مهم: این تابع به یک پین اضافی در تابع __init__ نیاز دارد. ---
        # برای مثال، فرض می‌کنیم یک پین برای نور پس‌زمینه به کلاس اضافه شده است.
        # if not hasattr(self, 'pin_bl'):
        #     raise NotImplementedError("Backlight control pin was not configured in __init__.")
            
        if not isinstance(state, bool):
            raise TypeError("The 'state' parameter must be a boolean (True or False).")
            
        # self.pin_bl.value(1) if state else self.pin_bl.value(0)
        # به دلیل اینکه پین کنترل نور پس‌زمینه در تابع init وجود ندارد، این تابع فعلاً فقط اعتبار سنجی را انجام می‌دهد.
        pass
