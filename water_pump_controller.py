```python
import RPi.GPIO as GPIO
import time

class PwmPumpController:
    """
    A controller for the water pump that uses PWM for soft-starts and soft-stops
    to prevent damaging inductive voltage spikes (slew rate control).
    """
    def __init__(self, pin: int, pwm_frequency: int = 100, ramp_time_ms: int = 100):
        """
        Initializes the pump controller and sets up GPIO for PWM.
        :param pin: The GPIO pin connected to the pump relay.
        :param pwm_frequency: The frequency for the PWM signal.
        :param ramp_time_ms: The duration for the power ramp up/down.
        """
        self.pin = pin
        self.pwm_frequency = pwm_frequency
        self.ramp_time_ms = ramp_time_ms
        self.ramp_steps = 20  # Number of steps for the ramp (e.g., 0, 5, 10...100)
        self.step_delay = (self.ramp_time_ms / 1000) / self.ramp_steps

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin, self.pwm_frequency)
        self.pwm.start(0) # Start PWM with 0% duty cycle (off)
        print("INFO: PWM Pump Controller initialized.")

    def _ramp_power(self, start_dc: int, end_dc: int):
        """Helper function to ramp the duty cycle up or down."""
        step_size = int(100 / self.ramp_steps)
        range_start = start_dc
        range_end = end_dc + (1 if end_dc > start_dc else -1)
        range_step = step_size if end_dc > start_dc else -step_size

        for dc in range(range_start, range_end, range_step):
            self.pwm.ChangeDutyCycle(dc)
            time.sleep(self.step_delay)
        self.pwm.ChangeDutyCycle(end_dc) # Ensure final value is set

    def start(self):
        """Soft-starts the pump by ramping power to 100%."""
        print("INFO: Ramping pump power UP...")
        self._ramp_power(0, 100)
        print("INFO: Pump at 100%.")

    def stop(self):
        """Soft-stops the pump by ramping power to 0%."""
        print("INFO: Ramping pump power DOWN...")
        self._ramp_power(100, 0)
        print("INFO: Pump stopped.")

    def cleanup(self):
        """Stops the PWM and cleans up GPIO resources."""
        self.pwm.stop()
        GPIO.cleanup()
        print("INFO: PWM and GPIO resources cleaned up.")

# --- Application Functions ---

MAX_AERATION_CYCLES = 50 # Safety limit for aeration pulses

def run_pump(controller: PwmPumpController, duration_seconds: int):
    """Activates pump for a duration using soft-start/stop."""
    print(f"\n--- Running pump for {duration_seconds} seconds ---")
    controller.start()
    time.sleep(duration_seconds)
    controller.stop()
    print("--- Pump cycle complete ---")

def pulse_pump_for_aeration(controller: PwmPumpController, cycles: int):
    """Pulses the pump using soft-start/stop for each pulse."""
    if cycles > MAX_AERATION_CYCLES:
        print(f"ERROR: Requested cycles ({cycles}) exceeds safety limit ({MAX_AERATION_CYCLES}). Aborting.")
        return
        
    print(f"\n--- Performing aeration pulse for {cycles} cycles ---")
    for i in range(cycles):
        print(f"  Pulse {i+1}/{cycles}...")
        controller.start()
        time.sleep(0.1) # Brief hold at full power
        controller.stop()
        time.sleep(0.4) # Wait between pulses
    print("--- Aeration pulse complete ---")

if __name__ == '__main__':
    pump_controller = None
    try:
        PUMP_PIN = 17
        pump_controller = PwmPumpController(pin=PUMP_PIN, ramp_time_ms=100)

        # Standard watering cycle with soft-start/stop
        run_pump(pump_controller, 5)

        # Aeration cycle with soft-start/stop
        pulse_pump_for_aeration(pump_controller, 5)

    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    finally:
        if pump_controller:
            pump_controller.cleanup()
        print("Exiting.")
```