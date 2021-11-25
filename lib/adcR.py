# adcR.py -- revised adc library with conversion to voltage
def adcRead(apin,bits,attn,nSamples=100):
    """
    Take ADC reading and convert to voltage.

    Keyword arguments:
    apin -- pin object as created with adc.channel() call
    bits -- integer value between 9 and 12 = the resolution set for the ADC with machine.ADC() call ()
    attn -- integer value (0, 1, 2, or 3) that sets the attenuation for the pin object
    nsamples -- (optional) number of times the ADC reading is repeated to calculate an average (default=100)
    """
    meanADC=0.0
    for i in range(nSamples):
        meanADC+=apin()    # read ADC
    meanADC /= nSamples    # calculate mean
    voltage=apin.value_to_voltage(int(meanADC+0.5))/1000 # convert using new built-in calibration
    return(meanADC,voltage)
