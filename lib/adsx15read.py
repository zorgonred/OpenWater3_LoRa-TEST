from machine import Pin
import time # REMOVE THIS LATER

def adsx15read(ads,irq_pin,adsDataRate,adsChannel):

    # One cannot reference a variable in the global space directly from an interrupt callback
    #  so one needs to create a class
    class Conversion:
        pass

    conversion = Conversion() # Create an instance of that class
    conversion.value = -99999 # and just put an integer variable in the class
    # it will be used to send the ADC reading from the interrupt callback to the 
    # main programme  

    #
    # Interrupt service routine for data acquisition
    # activated by a pin level interrupt
    #
    def sample_auto(x, adc = ads.alert_read):
        # This function is called when the alert pin has fallen at end of the conversion
        global alert_received
        alert_received=True
        conversion.value =adc() # read the register with the ADC reading
    
    ads.conversion_start2(adsDataRate, adsChannel) # Start a single conversion

    irq_pin.callback(Pin.IRQ_FALLING, handler=sample_auto) # when alert pin falls, call function sample_auto

    global alert_received
    alert_received = False
    # while alert_received == False:
    #     pass  # This loop is just to wait until alert is received
    time.sleep(0.01) # wait for n seconds (REMOVE THIS LATER)
    voltage = ads.raw_to_v(ads.alert_read()) # REMOVE THIS LATER

    irq_pin.callback(handler=None) # when loop is finished the callback is canceled
    # voltage = ads.raw_to_v(conversion.value) # to put back into action LATER
    return(conversion.value,voltage)
