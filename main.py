# 
# Project IoT Smart Mailbox II a.k.a. Bernard de Brievenbuschecker II                                                                            
#                                                                   _______       
# /|              __.....__                _..._                    \  ___ `'.    
# ||          .-''         '.            .'     '.                   ' |--.\  \   
# ||         /     .-''"'-.  `. .-,.--. .   .-.   .          .-,.--. | |    \  '  
# ||  __    /     /________\   \|  .-. ||  '   '  |    __    |  .-. || |     |  ' 
# ||/'__ '. |                  || |  | ||  |   |  | .:--.'.  | |  | || |     |  | 
# |:/`  '. '\    .-------------'| |  | ||  |   |  |/ |   \ | | |  | || |     ' .' 
# ||\    / '  `.             .' | |     |  |   |  | .'.''| | | |    /_______.'/   
# |/\'..' /     `''-...... -'   | |     |  |   |  |/ /   | |_| |    \_______|/    
# '  `'-'`  you've got mail     |_|     |  |   |  |\ \._,\ '/|_|                  
#                                       '--'   '--' `--'  `"                      
# 
# hardware platform  : Pimoroni Pici Lipo
#                    : Dual ARM Cortex M0+ running at up to 133Mhz
#                    : VCNL4040 Proximity sensor
#                    : LPWAN SFM10R1 SigFox Module
#                    : REED switch (inner door)
# 
# Power              : 3.7v - 4400 mAh (dual 18650) LiPo
# codebase           : MicroPython 1.22
# 
# (2024) JinjiroSan
# Bernard-de-Brievenbuschecker.py : v3.4 - refactor c0.0.1
#

from machine import Pin, ADC, I2C, lightsleep, UART
import time
import vcnl4040

# Constants and Setup
PROXIMITY_THRESHOLD = 2
DEBOUNCE_HITS_REQUIRED = 3
DEBOUNCE_INTERVAL = 200  # Milliseconds for debouncing
MAIL_DETECTED = False  # Flag to track mail detection status
MAIL_COLLECTED = False  # Flag to track if mail was collected
DOOR_OPEN = False  # Flag to track if the door is open
CHARGING = False  # Flag to track charging status
last_time = time.ticks_ms()  # Initialize last time for debouncing

# Initialize hardware components
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
sensor = vcnl4040.VCNL4040(i2c)
door_sensor = Pin(8, Pin.IN, Pin.PULL_UP)
charging_pin = Pin(24, Pin.IN)  # Assuming GP24 for charging status

# Initialize serial Port
lora = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

# Battery monitoring setup
vsys = ADC(3)  # Use ADC(3) as per successful setup
ADC_MAX_VOLTAGE = 3.3  # Assuming no voltage divider
conversion_factor = (ADC_MAX_VOLTAGE / 65535) * 63  # Adjusted conversion factor
time.sleep(1)  # Delay to stabilize ADC after power-up

FULL_BATTERY_VOLTAGE = 4.2
EMPTY_BATTERY_VOLTAGE = 3.0

def read_battery_voltage():
    raw_adc = vsys.read_u16()
    measured_voltage = raw_adc * conversion_factor
    return measured_voltage

def read_battery_percentage():
    measured_voltage = read_battery_voltage()
    if measured_voltage < EMPTY_BATTERY_VOLTAGE:
        return 0
    elif measured_voltage > FULL_BATTERY_VOLTAGE:
        return 99  # Limit to 99 instead of 100
    else:
        percentage = (measured_voltage - EMPTY_BATTERY_VOLTAGE) / (FULL_BATTERY_VOLTAGE - EMPTY_BATTERY_VOLTAGE) * 100
        percentage = min(99, max(0, int(percentage)))  # Ensure percentage is within 0-99%
        return percentage

def door_status_change(pin):
    global MAIL_DETECTED, MAIL_COLLECTED, DOOR_OPEN, last_time, CHARGING
    current_time = time.ticks_ms()
    current_state = pin.value()
    if time.ticks_diff(current_time, last_time) > DEBOUNCE_INTERVAL:
        DOOR_OPEN = current_state == 1
        if DOOR_OPEN:
            print("Door opened! Detected change on pin:", pin)
            if MAIL_DETECTED:
                MAIL_COLLECTED = True  # Mail is collected only if previously detected
                MAIL_DETECTED = False  # Reset after sending the collection message
                battery_percentage = read_battery_percentage()
                SigfoxSend(MAIL_DETECTED, MAIL_COLLECTED, battery_percentage, 0, CHARGING)
                MAIL_COLLECTED = False  # Reset after sending the collection message
            print("Mail detection reset.")
        else:
            print("Door closed! Detected change on pin:", pin)
        last_time = current_time

door_sensor.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=door_status_change)

def detect_mail_drop(sensor, threshold, required_hits):
    global MAIL_DETECTED
    hits = 0
    while not MAIL_DETECTED:
        if DOOR_OPEN:  # Check door state each cycle to ensure it's closed before detecting mail
            return False
        proximity_value = sensor.proximity
        if proximity_value > threshold:
            hits += 1
        else:
            hits = 0  # Reset hit count if any reading falls below the threshold

        if hits >= required_hits:
            MAIL_DETECTED = True
            return True
        time.sleep(0.1)

def SigfoxInfo():        
    sf_info = dict()
    print("Get Status - should be OK")
    lora.write("AT\r\n")      # Write AT Command
    time.sleep(2)
    sf_status = lora.read(2)  # Response Should be OK
    sf_info['Status'] = sf_status
    print(sf_status)

    print("Get ID")
    lora.write("AT$I=10\r\n") # Send Command to Get ID
    time.sleep(2)
    sf_id = lora.read(10)
    sf_info['ID'] = sf_id
    print(sf_id)

    print("Get PAC")
    lora.write("AT$I=11\r\n") # Send Command to Get ID
    time.sleep(2)
    sf_pac = lora.read(18)
    sf_info['PAC'] = sf_pac
    print(sf_pac)
    
    return sf_info

# Function to send the results to SigFox for mail notification
def SigfoxSend(mail_detected, mail_collected, battery_percentage, proximity, charging):
    try:
        print("Initiating Sigfox Transmission...")

        # Ensure data fits within their respective fields
        battery_percentage = min(99, battery_percentage)  # Ensure percentage is 0-99
        proximity = min(99, proximity)  # Scale proximity if necessary

        # Calculate the individual component bit-shifts and packing
        # Pack the values into an integer:
        # 1. Start with charging, which will be the least significant bit.
        # 2. Follow with proximity, which is 7 bits.
        # 3. Battery percentage is next, another 7 bits.
        # 4. Mail Collected and Mail Detected are each 1 bit.
        message = (charging |
                   (proximity << 1) |
                   (battery_percentage << 8) |
                   (mail_collected << 15) |
                   (mail_detected << 16))

        # Construct message payload, ensuring correct byte alignment
        payload = '{:06x}'.format(message)  # 6 hex digits for 3 bytes (24 bits used of 4-byte message)

        print("Sending to Sigfox:")
        print(f"Payload: {payload}")
        print(f"  - Mail Detected: {'Yes' if mail_detected else 'No'}")
        print(f"  - Mail Collected: {'Yes' if mail_collected else 'No'}")
        print(f"  - Battery Percentage: {battery_percentage}%")
        print(f"  - Proximity: {proximity}")
        print(f"  - Charging: {'Yes' if charging else 'No'}")
        
        # Send the command to the Sigfox module
        command = "AT$SF={}\r\n".format(payload)
        print("Command to be sent:", command)
        lora.write(command.encode('utf-8'))  # Encoding to bytes for UART
        time.sleep(6)

        # Read the response from the Sigfox module
        response = lora.read()
        if response:
            print("Response after send:", response.decode().strip())
        else:
            print("No response from the Sigfox module.")

        print("Sigfox message sent successfully.")
    except Exception as e:
        print("Failed to send Sigfox message:", str(e))
    finally:
        global MAIL_COLLECTED
        MAIL_COLLECTED = False

def SigfoxTest():
    # This sets the most significant bit of the first byte
    message = 1 << 15  # Corresponds to 'mail_detected' being True
    payload = '{:04x}'.format(message)  # Ensure four hex digits
    command = "AT$SF={}\r\n".format(payload)
    print("Command to be sent:", command)
    lora.write(command)
    time.sleep(6)
    response = lora.read()
    print("Response from Sigfox:", response)

def test_adc_with_known_voltage():
    print("Testing ADC with a known voltage source...")
    known_voltage_adc = ADC(2)  # Assume ADC(2) is connected to a known voltage source
    raw_adc = known_voltage_adc.read_u16()
    measured_voltage = raw_adc * conversion_factor
    print(f"Known Voltage Source - Raw ADC: {raw_adc}, Measured Voltage: {measured_voltage:.2f}V")
    
    # Directly measure the battery voltage on the same ADC pin for verification
    raw_adc_vsys = vsys.read_u16()
    measured_voltage_vsys = raw_adc_vsys * conversion_factor
    print(f"Battery Voltage Source - Raw ADC: {raw_adc_vsys}, Measured Voltage: {measured_voltage_vsys:.2f}V")

def main():
    global CHARGING
    test_adc_with_known_voltage()  # Test with known voltage source for verification
    while True:
        # Read current proximity and lux values from sensor
        current_proximity = sensor.proximity
        current_lux = sensor.lux
        CHARGING = charging_pin.value()
        
        if detect_mail_drop(sensor, PROXIMITY_THRESHOLD, DEBOUNCE_HITS_REQUIRED) and not MAIL_COLLECTED:
            print(f"Current Proximity: {current_proximity}, Lux: {current_lux}")
            print("Mail has been detected!")
            battery_percentage = read_battery_percentage()
            battery_voltage = read_battery_voltage()  # Ensure this function is defined and used correctly
            print(f"Battery Voltage: {battery_voltage:.2f}V, Percentage: {battery_percentage}%")
            SigfoxSend(MAIL_DETECTED, MAIL_COLLECTED, battery_percentage, current_proximity, CHARGING)
            # SigfoxTest()
        time.sleep(1)  # Sleep to reduce CPU load and power consumption

if __name__ == "__main__":
    main()

