```python
# ultrasonic_avoidance.py
# Aegis Gardener Obstacle Avoidance Module
#
# Description:
# This script provides active obstacle avoidance using a forward-facing
# HC-SR04 ultrasonic sensor. It runs in a continuous loop to monitor
# distance and will command the motor controller to halt all motion
# if an object is detected within the defined safety threshold.
#
# Pinout (BCM numbering):
# - TRIGGER_PIN: GPIO 23
# - ECHO_PIN:    GPIO 24

import RPi.GPIO as GPIO
import time
# Assuming a motor controller module exists with a stop() function.
# from motor_controller import stop_motors 

# --- Configuration ---
TRIGGER_PIN = 23
ECHO_PIN = 24
STOP_DISTANCE_CM = 20.0  # Safety threshold in centimeters.
LOOP_DELAY_S = 0.1       # Delay between sensor readings.

def setup_sensor():
    """Initializes GPIO pins for the ultrasonic sensor."""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIGGER_PIN, GPIO.OUT)
    GPIO.setup(ECHO_PIN, GPIO.IN)
    # Ensure trigger is low to start
    GPIO.output(TRIGGER_PIN, False)
    print("Ultrasonic sensor pins initialized.")
    time.sleep(1)

def get_distance():
    """
    Triggers the sensor and reads the echo to calculate distance.
    Returns the distance in centimeters.
    """
    # Send a 10us pulse to trigger the sensor
    GPIO.output(TRIGGER_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIGGER_PIN, False)

    pulse_start_time = time.time()
    pulse_end_time = time.time()

    # Record the last low timestamp for the echo pin
    while GPIO.input(ECHO_PIN) == 0:
        pulse_start_time = time.time()

    # Record the last high timestamp for the echo pin
    while GPIO.input(ECHO_PIN) == 1:
        pulse_end_time = time.time()

    pulse_duration = pulse_end_time - pulse_start_time
    
    # Speed of sound is ~34300 cm/s.
    # Distance = (time * speed_of_sound) / 2 (for there and back)
    distance = (pulse_duration * 34300) / 2
    
    return distance

def main():
    """Main execution loop for obstacle avoidance."""
    print("Starting Obstacle Avoidance Protocol...")
    setup_sensor()
    try:
        while True:
            distance = get_distance()
            print(f"Distance: {distance:.2f} cm")

            if distance < STOP_DISTANCE_CM:
                print(f"!!! OBSTACLE DETECTED at {distance:.2f} cm. Halting motors. !!!")
                # stop_motors() # UNCOMMENT THIS LINE TO INTEGRATE WITH MOTOR CONTROLLER
                
                # Optional: Add a small delay after stopping to prevent rapid start/stop cycles
                time.sleep(1)

            time.sleep(LOOP_DELAY_S)

    except KeyboardInterrupt:
        print("Obstacle Avoidance Protocol stopped by user.")
    finally:
        GPIO.cleanup()
        print("GPIO cleanup complete.")

if __name__ == '__main__':
    main()
```