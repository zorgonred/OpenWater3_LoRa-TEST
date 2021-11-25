from machine import Pin
from adsx15read import adsx15read # module for reading ADC and converting it to voltage

class watermark:

   # set class attributes (=valid for all instances of class watermark)
   # attn=3 # attenuation for adc
   # bits=12 # resolution set at 12 bits

   def __init__(self,S0pin,S1pin,enableA2Bpin,enableB2Apin,powerWMpin,r1ohms):
      # pins S0 and S1 for selecting channels on CD74HC52 mux
      self.S0pin=S0pin
      self.S0pin.init(S0pin.OUT) # define as output pin
      self.S0pin(0) # set it low
      self.S1pin=S1pin
      self.S1pin.init(S1pin.OUT) # define as output pin
      self.S1pin(0) # set it low
      # pins S0 to enable either the CD74HC52 mux that lets current go through the watermark
      # sensor from A > B contacts or the other mux that lets current go from B > A
      self.enableA2Bpin=enableA2Bpin
      self.enableA2Bpin.init(enableA2Bpin.OUT) # define as output pin
      self.enableA2Bpin(0) # set it low
      self.enableB2Apin=enableB2Apin
      self.enableB2Apin.init(enableB2Apin.OUT) # define as output pin
      self.enableB2Apin(0) # set it low
      # pin for powering the voltage divider by which the Watermark resistor is measured
      self.powerWMpin=powerWMpin
      self.powerWMpin.init(powerWMpin.OUT) # define as output pin
      self.powerWMpin(0) # set it low
      # value of the resistor used in the voltage divider
      self.r1ohms=r1ohms

   def readWM1(self,ads,irq_pin,n=1): # Read watermark 1
      self.S0pin(0) # set mux
      self.S1pin(0)
      wmResistance=self.read(ads,irq_pin)
      return wmResistance

   def readWM2(self,ads,irq_pin,n=1,uswait=10): # Read watermark 2
      self.S0pin(1) # set mux
      self.S1pin(0)
      wmResistance=self.read(ads,irq_pin)
      return wmResistance

   def readWM3(self,ads,irq_pin,n=1): # Read watermark 3
      self.S0pin(0) # set mux
      self.S1pin(1)
      wmResistance=self.read(ads,irq_pin)
      return wmResistance

   def readWM4(self,ads,irq_pin,n=1): # Read watermark 4
      self.S0pin(1) # set mux
      self.S1pin(1)
      wmResistance=self.read(ads,irq_pin)
      return wmResistance

   def read(self,ads,irq_pin,n=1): # Read the Watermark sensor
      # n= number of times to repeat measurement;
      # uswait = waiting time in µs to stabilize voltage
      adsDataRate=6 # for ADS reading
      wmResistance=0.0
      # Power the voltage divider by which the Watermark resistor is measured
      self.powerWMpin(1)
      for i in range(n):
         # Let current go from A > B in the Watermark sensor, read voltages again and calculate resistance
         self.enableA2Bpin(1)
         (ADCreading1,voltage1)=adsx15read(ads,irq_pin,adsDataRate,adsChannel=0)
         (ADCreading2,voltage2)=adsx15read(ads,irq_pin,adsDataRate,adsChannel=1)
         if(voltage2>0.0001):
            rWatermark=self.r1ohms*(voltage1-voltage2)/voltage2
         else: # if no watermark connected, voltage2 will be zero
            rWatermark=-98840 # result set to missing value
         # print("A>B: Voltage1=%6.3f Voltage2=%6.3f rWatermark (ohm)= %6.0f" % (voltage1,voltage2,rWatermark))
         wmResistance+=rWatermark
         self.enableA2Bpin(0)
         # Now reverse polarity over the watermark sensor (B > A), read voltages again and calculate resistance
         self.enableB2Apin(1)
         (ADCreading1,voltage1)=adsx15read(ads,irq_pin,adsDataRate,adsChannel=0)
         (ADCreading2,voltage2)=adsx15read(ads,irq_pin,adsDataRate,adsChannel=1)
         if(voltage2>0.0001):
            rWatermark=self.r1ohms*(voltage1-voltage2)/voltage2
         else: # if no watermark connected, voltage2 will be zero
            rWatermark=-98840 # result set to missing value
         # print("B>A: Voltage1=%6.3f Voltage2=%6.3f rWatermark (ohm)= %6.0f" % (voltage1,voltage2,rWatermark))
         wmResistance+=rWatermark
         self.enableB2Apin(0)
      self.powerWMpin(0) # set it low
      return wmResistance/(2*n)

def ShockkPa(Rkohm,tempDegC=20):
   # Calibration equation Shock, C.C., Barnum, J.M., Seddigh, M., 1998.
   # Calibration of Watermark Soil Moisture Sensors for Irrigation Management,
   # Proceedings of the International Irrigation Show, San Diego, California, USA. pp. 139-146.
   if(Rkohm<0):
      wPotentialkPa=-9999.
   elif(Rkohm>30):
      wPotentialkPa=9999.
   else:
      wPotentialkPa=(4.093 + 3.213 * Rkohm)/(1 - 0.009733 * Rkohm - 0.01205 * tempDegC)
   return wPotentialkPa
