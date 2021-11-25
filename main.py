# This will auto import everything in lib, * means all 
from lib import *
# This will auto import everything in lib, * means all 

from lib import measureSensors
from lib import onewire;

# To use a function in the file you need to use dot notation, so filename ./dot function, then it will auto-import
measureSensors.foo;
# To use a function in the file you need to use dot notation, so filename/ class ./dot function, in a hirachy

onewire.DS18X20.isbusy


from machine import RTC
from machine import Pin
import pycom
import time
import machine
from network import LoRa
import socket
import binascii
import ubinascii
import struct
from lib import ustruct;
import config
import utime




pycom.heartbeat(False) # stop the heartbeat


# Set up the Real Time Clock (RTC)
rtc = RTC()
print(rtc.now()) # This will print date and time if it was set before going
# to deepsleep.  The RTC keeps running in deepsleep.

# rtc.init((2020, 7, 30, 15, 39)) # manually set the time

print("wake reason (wake_reason, gpio_list):",machine.wake_reason())
'''   PWRON_WAKE -- 0
      PIN_WAKE -- 1
      RTC_WAKE -- 2
      ULP_WAKE -- 3
 '''

print("Now getting messageNumber from NVRAM")
messageNumber=pycom.nvs_get('messageNumber')+1   # messageNumber is incremented
print("messageNumber=", messageNumber)
pycom.nvs_set('messageNumber',messageNumber) # now write messageNumber into NVRAM

# blink the led
for cycles in range(2): # stop after 2 cycles
    pycom.rgbled(0x007f00) # green
    time.sleep(1)
    pycom.rgbled(0x7f7f00) # yellow
    time.sleep(1)
    pycom.rgbled(0x7f0000) # red
    time.sleep(1)

# Initialise LoRa in LORAWAN mode.
# Please pick the region that matches where you are using the device:
# Asia = LoRa.AS923
# Australia = LoRa.AU915
# Europe = LoRa.EU868
# United States = LoRa.US915
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)

# Restore the LoRaWAN state (joined status, network keys, packet counters, etc)
# from non-volatile memory.
lora.nvram_restore()

# create an OTAA authentication parameters, change them to the provided credentials
app_eui = ubinascii.unhexlify('70B3D57ED00325E1')
app_key = ubinascii.unhexlify('9AC25474E81FABF7840D1F3A0BDED7C5')
dev_eui = ubinascii.unhexlify('007AACA35D428EC3')

print('lora.has_joined()=',lora.has_joined())

if not lora.has_joined():
    # join a network using OTAA (Over the Air Activation)
    lora.join(activation=LoRa.OTAA, auth=(dev_eui, app_eui, app_key), timeout=0)
    # wait until the module has joined the network
    while not lora.has_joined():
        time.sleep(2.5)
        print('Not yet joined...')

    print('Joined')

# create a LoRa socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

# set the LoRaWAN data rate
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)

# make the socket non-blocking
# (because if there's no data received it will block forever...)
s.setblocking(False)

# Measure the sensors
# batteryVoltage,kPa1,kPa2,kPa3,soilTempCelsius,temperatureC,pressurehPa,relHumidity=measureTest(messageNumber)
batteryVoltage,kPa1,kPa2,kPa3,soilTempCelsius,temperatureC,pressurehPa,relHumidity=measure(messageNumber)


# create 22-bytes payload
# first rescale and convert to integers
MessageNumber=0 # we need to create payload for upload but have no data
batmV=int(batteryVoltage*1000+0.5) # convert to mV; '+0.5' is to round to nearest integer
hPa1=int(kPa1*10+0.5)
hPa2=int(kPa2*10+0.5)
hPa3=int(kPa3*10+0.5)
soilTempCentigradeCelsius=int(soilTempCelsius*100+0.5)
TempCentigrade=int(temperatureC*100+0.5)
pressurehPa=int(pressurehPa+0.5)
relHumiditypermil=int(relHumidity*10+0.5)
unixtimesecs=utime.time() # 32bit signed integer
print('unixtimesecs:',unixtimesecs)
# next encode in bytes
# '>'=big endian;
# 'b'=signed integer 1 byte = int:8; 'B'= unsigned integer 1 byte = uint:8;
# 'h'=short signed integer 2 bytes = int:16 'H'=short unsigned integer 2 bytes = uint:16
# 'i'=long signed integer 4 bytes = int:32 'I'=long unsigned integer 4 bytes = int:32
# 'f'=float (single precision real number) 4 bytes
# 'd'=double (double precision real number) 8 bytes
payload=ustruct.pack(">HhhhhhhhhI",messageNumber,batmV,hPa1,hPa2,hPa3,soilTempCentigradeCelsius,TempCentigrade,pressurehPa,relHumiditypermil,unixtimesecs)

def sendpayload(payload):
    print('Sending:', payload)
    s.send(payload)
    time.sleep(4)
    rx, port = s.recvfrom(256)
    if rx:
        print('Received: {}, on port: {}'.format(rx, port))
        stats=lora.stats()
        print(stats)
        # counterfrom,counterto=ustruct.unpack(">hh",rx) # example on how to decode
        # signal successful receipt of downlink with green led for 10 seconds
        pycom.heartbeat(False) # stop the heartbeat
        pycom.rgbled(0x007f00) # green
        time.sleep(10)
        pycom.rgbled(0) # switch led off
        pycom.heartbeat(True) # start the heartbeat
    time.sleep(6)

# Now send the payload
sendpayload(payload)

# Save the LoRaWAN state (joined status, network keys, packet counters, etc)
# in non-volatile memory in order to be able to restore the state when coming
# out of deepsleep or a power cycle
lora.nvram_save()

print("Time to go to sleep ....")
sleepSeconds=1200  # set deepsleep time in seconds

machine.deepsleep(sleepSeconds*1000) # time in ms
# Note that when it wakes from deepsleep it reboots, but the RTC keeps time during deepsleep
# You can always interrupt the deep sleep with the reset button on the LoPy4
