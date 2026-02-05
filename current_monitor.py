#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
current_monitor.py

Description:
A diagnostic script to monitor motor current in real-time and perform an
emergency shutdown if a specified threshold is exceeded for a sustained period.

Author: Code Monkey (Senior Software Engineer)
Date: 2023-10-27

Usage:
python3 current_monitor.py --max-current 2.5 --sample-rate 10

Dependencies:
- adafruit-circuitpython-ina219
- RPi.GPIO (or equivalent for your platform, e.g., Jetson.GPIO)
"""

import time
import argparse
import sys

# H/W INTERFACE PLACEHOLDERS - REQUIRE EE CONFIRMATION
# =================================================================
# Assume INA219 sensor on the default I2C bus
# The I2C address can be 0x40, 0x41, 0x44, or 0x45
I2C_ADDRESS = 0x40  # <--- CONFIRM WITH EE

# Assume motor driver enable is connected to a GPIO pin
# Using BCM numbering for Raspberry Pi as a placeholder
MOTOR_ENABLE_PIN = 18 # <--- CONFIRM WITH EE
# =================================================================

# Attempt to import hardware-specific libraries
try:
    import board
    import busio
    from adafruit_ina219 import INA219
except ImportError:
    print("ERROR: Hardware libraries not found. Please install them:")
    print("pip3 install adafruit-circuitpython-ina219 RPi.GPIO")
    sys.exit(1)

try:
    import RPi.GPIO as GPIO
except ImportError:
    # Create a dummy GPIO object for testing on non-Pi platforms
    class DummyGPIO:
        BCM = 0
        OUT = 0
        HIGH = 1
        LOW = 0
        def setmode(self, mode): print(f"DummyGPIO: Set mode to {mode}")
        def setup(self, pin, mode): print(f"DummyGPIO: Setup pin {pin} to mode {mode}")
        def output(self, pin, state): print(f"DummyGPIO: Set pin {pin} to state {state}")
        def cleanup(self): print("DummyGPIO: Cleanup")
    GPIO = DummyGPIO()
    print("WARNING: RPi.GPIO not found. Using dummy interface.")


class MotorController:
    """A simple class to abstract motor control via GPIO."""
    def __init__(self, enable_pin):
        self._pin = enable_pin
        GPIO.setmode(GPIO.BCM)
        # Set pin as output and start with motor enabled
        GPIO.setup(self._pin, GPIO.OUT)
        GPIO.output(self._pin, GPIO.HIGH)
        print(f"Motor controller initialized on GPIO pin {self._pin}. Motor ENABLED.")

    def disable(self):
        """Disables the motor driver."""
        GPIO.output(self._pin, GPIO.LOW)
        print(f"CRITICAL: Motor DISABLED on GPIO pin {self._pin}.")

    def cleanup(self):
        """Clean up GPIO resources."""
        GPIO.cleanup()


class CurrentMonitor:
    """A class to monitor current and trigger a shutdown if it exceeds a limit."""
    def __init__(self, max_current, sample_rate, shutdown_delay_s):
        self._max_current_a = max_current
        self._sample_period_s = 1.0 / sample_rate
        self._shutdown_delay_s = shutdown_delay_s
        self._overcurrent_start_time = None

        print("Initializing I2C and INA219 sensor...")
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self._sensor = INA219(i2c, I2C_ADDRESS)
            print(f"INA219 sensor found at address {hex(I2C_ADDRESS)}.")
        except (ValueError, RuntimeError) as e:
            print(f"ERROR: Failed to initialize INA219 sensor at address {hex(I2C_ADDRESS)}.")
            print(f"  -> {e}")
            print("  -> Check I2C address and wiring.")
            sys.exit(1)

        self._motor = MotorController(MOTOR_ENABLE_PIN)

    def run(self):
        """Starts the monitoring loop."""
        print("\n--- Starting Current Monitor ---")
        print(f"  Max Current Threshold: {self._max_current_a:.2f} A")
        print(f"  Sample Rate: {1.0/self._sample_period_s:.1f} Hz")
        print(f"  Shutdown Delay: {self._shutdown_delay_s} s")
        print("----------------------------------\n")

        try:
            while True:
                try:
                    current_ma = self._sensor.current
                    # The INA219 library returns current in mA. Convert to A.
                    current_a = current_ma / 1000.0 if current_ma is not None else 0.0
                except OSError:
                    # This can happen if the I2C bus has a momentary glitch
                    current_a = -1.0 # Use a negative value to indicate read error
                
                if current_a < 0:
                    print("WARN: Failed to read from I2C sensor.", flush=True)
                else:
                    self._check_current(current_a)

                time.sleep(self._sample_period_s)

        except KeyboardInterrupt:
            print("\nMonitoring stopped by user.")
        finally:
            self._motor.cleanup()
            print("GPIO resources cleaned up.")

    def _check_current(self, current_a):
        """Checks the current against the threshold and manages shutdown logic."""
        
        # Using a carriage return to keep the output on a single line
        print(f"  Current: {current_a: 5.2f} A", end='\r', flush=True)

        if current_a > self._max_current_a:
            if self._overcurrent_start_time is None:
                # First time we've seen an overcurrent condition
                self._overcurrent_start_time = time.monotonic()
                print(f"\nWARNING: Current {current_a:.2f} A exceeds threshold of {self._max_current_a:.2f} A. Starting shutdown timer...", flush=True)
            else:
                # Overcurrent condition persists, check timer
                elapsed = time.monotonic() - self._overcurrent_start_time
                if elapsed >= self._shutdown_delay_s:
                    print(f"\nCRITICAL SHUTDOWN: Overcurrent condition persisted for {elapsed:.1f}s.")
                    self._motor.disable()
                    self._motor.cleanup()
                    sys.exit(2) # Exit with a specific error code
        else:
            # Current is normal, reset the timer if it was running
            if self._overcurrent_start_time is not None:
                print("\nINFO: Current has returned to normal levels. Resetting shutdown timer.", flush=True)
                self._overcurrent_start_time = None


def main():
    parser = argparse.ArgumentParser(description="Motor Current Monitor and Safety Shutdown Tool")
    parser.add_argument(
        '-c', '--max-current',
        type=float,
        required=True,
        help="Maximum allowed current in Amps before triggering shutdown timer."
    )
    parser.add_argument(
        '-r', '--sample-rate',
        type=int,
        default=10,
        help="Samples per second to read the current sensor (Hz)."
    )
    parser.add_argument(
        '-d', '--delay',
        type=float,
        default=1.0,
        help="Duration in seconds the current must exceed the max before shutdown."
    )
    args = parser.parse_args()

    if args.max_current <= 0 or args.sample_rate <= 0 or args.delay <= 0:
        print("ERROR: All arguments must be positive values.")
        sys.exit(1)

    monitor = CurrentMonitor(
        max_current=args.max_current,
        sample_rate=args.sample_rate,
        shutdown_delay_s=args.delay
    )
    monitor.run()


if __name__ == "__main__":
    main()
