from i2c import I2C, delayMilliseconds
from ctypes import c_short

class ADXL345:


   i2c = None
   def __init__(self, address):
       self.i2c = I2C(address) 

   def start_sampling(self):
       pass

if __name__ == "__main__":
    i2c = I2C(0x53)
    deviceid = i2c.read_reg8(0x00)
    print("device id:" + hex(deviceid))
    i2c.write_reg8(0x31, 0b00001001) 
    i2c.write_reg8(0x2d, 0b00001000)
    while True:
        x = i2c.read_reg16(0x32)
        y = i2c.read_reg16(0x34)
        z = i2c.read_reg16(0x36)

        x = c_short(x).value
        y = c_short(y).value
        z = c_short(z).value

        print("x:" + str(x) + " y:" + str(y) + " z:" + str(z))

