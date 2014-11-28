from wiringpi2 import *

class I2C:
    fd = 0
    def __init__(self, address):
        wiringPiSetup()
        self.fd = wiringPiI2CSetup(address) 

    def read_reg8(self, reg):
        r = wiringPiI2CReadReg8(self.fd, reg)
        if r < 0:
            raise Exception("failed to read data")
        return r

    def write_reg8(self, reg, data):
        r = wiringPiI2CWriteReg8(self.fd, reg, data)
        if r < 0:
            raise Exception("failed to write data")

def delayMilliseconds(milliseconds):
    delay(milliseconds)
