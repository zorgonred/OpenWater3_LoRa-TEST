def  measureTest(messageNumber):
    batteryVoltage=-9.99
    kPa1=-99.9
    kPa2=-99.9
    kPa3=-99.9
    soilTempCelsius=-9.99
    temperatureC=-9.99
    pressurehPa=-999
    relHumidity=-99.9
    return(batteryVoltage,kPa1,kPa2,kPa3,soilTempCelsius,temperatureC,pressurehPa,relHumidity)

def foo():
    print "foo!"

    
def measure(messageNumber):
    from machine import I2C, Pin, SD
    import ads1x15, time, machine, pycom, sys, utime, os
    from adsx15read import adsx15read
    import adcR # module needed in library for reading ADC and converting it to voltage
    import watermark # module needed in library for reading Watermark sensors (written by Jan D)
    from math import sqrt
    import bme280_float # library for BME280 humidity/temperature/presser sensor
    from onewire import OneWire, DS18X20

    # Settings
    printForDebugging=True

    p20=Pin('P20',mode=Pin.OPEN_DRAIN,pull=None) # set pin to open drain to provide ground to sensors
    p20.hold(0)   # release hold that was set before deepsleep
    p20.value(0)  # set to open drain (=to ground) so sensors are now powered


    # Measurement of Vbat
    # *******************
    # using built-in ADC calibration  apin.value_to_voltage() and adjusted vref of ADC

    attn=2 # chose attenuation of ADC
    # attn=0 (default) is 0 dB (0-1.1V) with internal reference voltage of ADC being (about) 1.1V
    # attn=1 is 2.5 dB         (0-1.5V)
    # attn=2 is 6 dB           (0-2.2V)
    # attn=3 is 11 dB          (0-3.9V)

    bits=12 #'Bits' can take integer values between 9 and 12 and selects the number of bits of resolution of the ADC

    adc = machine.ADC(bits=bits)  # create an ADC object and specify resolution.

    # Adjust vref of ADC with the value stored in NVRAM memory if available (see script in 'Calibrate ADC' script folder)
    try:
        vrefmV=pycom.nvs_get('vref_mV')
    except Exception as e:
        vrefmV = None

    if vrefmV==None : # when no value is stored
        adc.vref(1100) # new functionality in ADC, works in release '1.10.2.b1Ã¢â‚¬â„¢ but not in older releases!
        print("ADC vref set to default value 1100 mV because no value was stored in NVRAM memory of board")
    elif vrefmV<900 or vrefmV>1300 : # when value is out of range
        adc.vref(1100) # same
        print("ADC vref set to default value 1100 mV")
        print("because vrefmV from NVRAM is equal to %6.0f" % vrefmV,"mV (that is outside [900,1300])")
    else :
        adc.vref(vrefmV) # same
        print("ADC vref set to %6.0f" % vrefmV,"mV (data that was stored in NVRAM of board)")

    apin = adc.channel(pin='P18',attn=attn)   # Create an analog pin on P18, that is the pin for reading VBatt
    nSamples=100

    ADCreading,Voltage=adcR.adcRead(apin,bits,attn,nSamples)   # read ADC and convert reading to voltage
    batteryVoltage=(Voltage-0.002)*3.060  # correct for the voltage divider, the 0.002V is the offset voltage on P20
    if printForDebugging is True:
        print("ADCreading = %6.4f" % ADCreading, "    Battery voltage = %8.3f" % batteryVoltage)


    # Initialize the ADC (ADS1015)
    addr = 72 # for address 72, the ADDR pin of the ADS1015 needs to be conneceted to GND
    gain = 1 # +/-4.096V range, 2mV resolution; See ads1x15.py lib

    i2c = I2C(baudrate=400000) # assumes defaults: P9=SDA, P10=SCL; baud rate 400kHz is max for pycom devices
    ads = ads1x15.ADS1115(i2c, addr, gain) # create instance of ADS1015 object
    print("i2c and adsx15 object created")

    #pin 13 connected to ALERT/RDY (defined as interrupt pin)
    irq_pin = Pin('P13', mode=Pin.IN, pull=Pin.PULL_UP)

    # Measurement of DS18B20 (temperature)
    # ************************************
    # DS18B20 data line connected to pin P21 and also to +3.3V via 4.7kohm resistor (pullup)
    #
    ow = OneWire(Pin('P21'))

    # Define function to measure the temperature with the DS18X20 sensor
    # on a one-wire bus (owBUS).  If several sensors are connected to this bus
    # you need to specify the ROM address of the sensor as well
    # If only one DS18x20 device is attached to the bus you may omit the rom parameter.
    def measureTemperature(owBus,rom=None):
        while True: # we loop until we get a valid measurement
            temp = DS18X20(owBus)
            temp.start_conversion(rom)
            time.sleep(1) # wait for one second
            TempCelsius=temp.read_temp_async(rom)
            if TempCelsius is not None:
                return TempCelsius # TempCelsius exit loop and return result

    # single temperature measurement omitting the ROM parameter
    while True:
        soilTempCelsius=measureTemperature(ow)
        if not soilTempCelsius==85:
            break # jump out of loop
        print('soilTempCelsius=85°C which means it is equal to the power-on reset value of the temperature register.  Repeat the measurement!')

    print("Soil temperature (degrees C) = %7.1f" % soilTempCelsius)

    """
    # Each DS18X20 has a unique 64-bit (=8 bytes) address in its ROM memory
    # (ROM = read only memory)
    # When one or several DS18XB20 are connected to the same onewire bus, we can
    # get their ROM addresses in the following way:
    roms=ow.scan() # returns a list of bytearrays
    for rom in roms: # we loop over the elements of the list
        print('ROM address of DS18XB20 = ',ubinascii.hexlify(rom))# hexlify to show
        # bytearray in hex format

    # The following loop measures temperature continuously, looping over all
    # sensors as well
    while True: # loop forever (stop with ctrl+C)
        for rom in roms: # we loop over the elements of the list, i.e. we loop over
            # the detected DS18XB20 sensors
            print("For DS18XB20 with ROM address =", ubinascii.hexlify(rom), "the temperature (degrees C) = %7.1f" % measureTemperature(ow,rom))
    """

    # # testing of ADC
    # adsDataRate=6 # for ADS reading
    # (ADCreading,voltage)=adsx15read(ads,irq_pin,adsDataRate,adsChannel=2)
    # print("Voltage= %6.3f" % voltage)


    # Read Watermark sensors
    # **********************
    # Set up watermark sensors (each sensor requires two analog and two digital pins)
    #
    # Het blijkt dat de meting heel stabiel is en je eigenlijk n=1 mag zetten in wm.readWM4(ads,irq_pin,n=5)
    # *********************************************************************************************************************************************
    wm=watermark.watermark(S0pin=Pin('P11'),S1pin=Pin('P12'),enableA2Bpin=Pin('P3'),enableB2Apin=Pin('P19'),powerWMpin=Pin('P22'),r1ohms=7870)
    # The rON resistance of the mux is about 8ohm when the watermark resistance varies between 4k and 94k (so in-out current is low).
    # This 80 ohm resistance is twice in series with the watermark resistance.  So we need to substract 160 ohm.
    wm1kohm=(wm.readWM1(ads,irq_pin,n=1)/1000
    print("WM1: rWatermark (kohm)= %7.3f" % wm1kohm)
    kPa1=watermark.ShockkPa(wm1kohm,soilTempCelsius) # calibration Shock et al. (1989)

    wm2kohm=(wm.readWM2(ads,irq_pin,n=1)-160)/1000
    print("WM2: rWatermark (kohm)= %7.3f" % wm2kohm)
    kPa2=watermark.ShockkPa(wm2kohm,soilTempCelsius) # calibration Shock et al. (1989)

    wm3kohm=(wm.readWM3(ads,irq_pin,n=1)-160)/1000
    print("WM3: rWatermark (kohm)= %7.3f" % wm3kohm)
    kPa3=watermark.ShockkPa(wm3kohm,soilTempCelsius) # calibration Shock et al. (1989)

    wm4kohm=(wm.readWM4(ads,irq_pin,n=1)-160)/1000
    print("WM4: rWatermark (kohm)= %7.3f" % wm4kohm)
    kPa4=watermark.ShockkPa(wm4kohm,soilTempCelsius) # calibration Shock et al. (1989)

    """ # For testing variability
    sum=0
    sq_sum=0
    nSamples=5
    start = time.ticks_us()
    for i in range(nSamples):
        # The rON resistance of the mux is about 8ohm when the watermark resistance varies between 4k and 94k (so in-out current is low).
        # This 80 ohm resistance is twice in series with the watermark resistance.  So we need to substract 160 ohm.
        # wm1kohm=(wm.readWM1(ads,irq_pin,n=5,uswait=100)-160)/1000 #substract 160 ohm
        # print("WM1: rWatermark (Kohm)= %6.2f" % wm1kohm)
        # wm2kohm=(wm.readWM2(ads,irq_pin,n=5,uswait=10)-160)/1000
        # print("WM2: rWatermark (Kohm)= %6.2f" % wm2kohm)
        # wm3kohm=(wm.readWM3(ads,irq_pin,n=5,uswait=10)-160)/1000
        # print("WM3: rWatermark (Kohm)= %6.2f" % wm3kohm)
        wm4kohm=(wm.readWM4(ads,irq_pin,n=5)-160)/1000
        print("WM4: rWatermark (Kohm)= %6.2f" % wm4kohm)
        dat=wm4kohm
        sum += dat
        sq_sum += (dat * dat)
    end = time.ticks_us()
    print("Measurement took ",(end-start)/1000000," seconds")
    meankohm = sum/nSamples    # calculate mean
    variance = sq_sum / nSamples - meankohm * meankohm
    if variance>=0:
        stdev=sqrt(variance)
    else:
        stdev=-999
    print("mean (kohm)= %8.4f stdev= %6.4f" % (meankohm,variance))
    """
    # Read the BME280 humidity/temperature/pressure sensor
    bme = bme280_float.BME280(i2c=i2c)
    print(bme.values) # to get T, P and RH printed with units
    (temperatureC,pressurePa,relHumidity)=bme.read_compensated_data() # to get T, P and RH as tuple of floats
    pressurehPa=pressurePa/100 # conversion from Pa to hPa

    # Write data to MicroSD memory
    # ****************************
    # Mount MicroSD memory
    print('Will now mount MicroSD memory:')

    try:
        sd = SD()
        os.mount(sd, '/sd')
    except Exception as error:
        print('Error when mounting MicroSD memory:')
        sys.print_exception(error) # this prints the error nicely without halting the script
        pycom.heartbeat(False) # stop the heartbeat
        for cycles in range(10): # stop after 10 cycles
            pycom.rgbled(0xffc300) # orange
            time.sleep_ms(50)
            pycom.rgbled(0) # switch led off
            time.sleep_ms(200)
        pycom.heartbeat(True) # restart the heartbeat


    # for testing
    # ***********
    # for debugging:
    # os.listdir('/sd')
    # f = open('/sd/test.csv', 'r')
    # f.read() # readall() is no longer available in micropython.  Read() without parameters does the job
    # f.close()


    # Write data to csv file
    print('Will now write to MicroSD memory:')
    try:
        f = open('/sd/test.csv', 'a') # 'w'=write; 'a'=append; 'r'=read
        f.write('{:11d},{:8.3f},{:7.1f},{:6.3f},{:6.3f},{:6.3f},{:7.1f},{:7.1f},{:7.1f},{:7.1f},{:7.1f},{:7.1f},{:10d})\n'.format(utime.time(),batteryVoltage,soilTempCelsius, wm1kohm,wm2kohm,wm3kohm,kPa1,kPa2,kPa3,temperatureC,pressurehPa,relHumidity, messageNumber))  # write data to file
        #f.write('{:11d},{:8.3f}\n'.format(utime.time(),voltage))  # write data to file
        f.close()
        os.umount('/sd')
    except Exception as error:
        print('Error when opening, closing or writing to csv file:')
        # blink red led to signal error
        sys.print_exception(error) # this prints the error nicely without halting the script
        pycom.heartbeat(False) # stop the heartbeat
        for cycles in range(10): # stop after 10 cycles
            pycom.rgbled(0x7f0000) # red
            time.sleep_ms(50)
            pycom.rgbled(0) # switch led off
            time.sleep_ms(200)
        pycom.heartbeat(True) # restart the heartbeat

    time.sleep(0.9)  # some waiting time (how long?) needed to ensure data is written to MicroSD and all is closed

    # Limit power consumption during deep sleep by pin settings
    # I2C and data pin DS18B20 to input mode to minimize power use during deepsleep
    # this is also their default at startup
    p=Pin("P21",mode=Pin.IN,pull=Pin.PULL_DOWN,alt=-1) # data pin DS18B20
    p9=Pin("P9",mode=Pin.IN,pull=Pin.PULL_DOWN,alt=-1) # SDA pin for I2C
    p10=Pin("P10",mode=Pin.IN,pull=Pin.PULL_DOWN,alt=-1) # SCL pin for I2C

    pinSD_SLCK=Pin("P23",mode=Pin.IN,pull=Pin.PULL_DOWN,alt=-1) # put pull-down resistor on P23
    # this is the SLCK pin for the microSD card. Default definition is no pullup or pulldown
    # That pin turned out to increase power consumption from 22µA to 80µA during deepsleep
    # when P23 is connected to microSD.
    pinSD_DAT0=Pin('P8',  mode=Pin.IN, pull=Pin.PULL_DOWN) # also needed to limit power consumption
    pinSD_CMD =Pin('P4',  mode=Pin.IN, pull=Pin.PULL_DOWN) # during deep sleep
    p20.value(1)  # set pin floating to disconnect sensors from ground during deep sleep
    p20.hold(1)   # hold pin in same status during deep sleep and wakeup

    # voorlopig niet nodig:
    # pinSD_DAT0.hold(1)
    # pinSD_CMD.hold(1)
    # pinSD_SLCK.hold(1) # en dan ook hold afzetten bij begin!

    return(batteryVoltage,kPa1,kPa2,kPa3,soilTempCelsius,temperatureC,pressurehPa,relHumidity)
