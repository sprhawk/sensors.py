#! /bin/env python
# -*- coding: utf-8 -*-

from i2c import I2C, delayMilliseconds
from ctypes import c_ulong , c_ushort , c_short ,c_long
import math

class BMP180:
    i2c = None
    AC1 = 0
    AC2 = 0
    AC3 = 0
    AC4 = 0
    AC5 = 0
    AC6 = 0
    B1 = 0
    B2 = 0
    B5 = 0 # calculated by temperature
    MB = 0
    MC = 0
    MD = 0
    def __init__(self, address): # 0x77
        self.i2c = I2C(address)
        self.read_calibration_data()
        

    def get_device_id(self):
        r = self.i2c.read_reg(self.fd, 0xd0)
        return r

    def _write_control_reg(self, data):
        self.i2c.write_reg8( 0xf4, data)

    def _read_reg(self, reg):
        r = self.i2c.read_reg8(reg)
        return r

    def soft_reset(self):
        self.write_reg8(0xe0, 0xb6)

    def start_sampling_temperature(self):
        self._write_control_reg(0x2e)

    def wait_for_sampling_temperature(self):
        delayMilliseconds(5)

    def start_sampling_presure(self, level):
        if level >= 0 and level <= 3:
            self._write_control_reg(0x34 + level * 2 ** 6)
        else:
            raise Exception("invalid parameter")

    def wait_for_sampling_presure(self, level):
        m = 0
        if 0 == level:
            m = 5
        elif 1 == level:
            m = 8
        elif 2 == level:
            m = 14
        elif 3 == level:
            m = 26
        else:
            raise Exception("invalid parameter")

        delayMilliseconds(m)
        
    def read_calibration_slot(self, start_address):
        a = self._read_reg(start_address)
        b = self._read_reg(start_address + 1)
        c = a * 2 ** 8 + b
        if c == 0 or c == 0xffff:
            raise Exception("Failed to communication")
        return c

    def read_calibration_data(self):
        self.AC1 = c_short(self.read_calibration_slot(0xaa)).value
        self.AC2 = c_short(self.read_calibration_slot(0xac)).value
        self.AC3 = c_short(self.read_calibration_slot(0xae)).value
        self.AC4 = c_ushort(self.read_calibration_slot(0xb0)).value
        self.AC5 = c_ushort(self.read_calibration_slot(0xb2)).value
        self.AC6 = c_ushort(self.read_calibration_slot(0xb4)).value
        self.B1 = c_short(self.read_calibration_slot(0xb6)).value
        self.B2 = c_short(self.read_calibration_slot(0xb8)).value
        self.MB = c_short(self.read_calibration_slot(0xba)).value
        self.MC = c_short(self.read_calibration_slot(0xbc)).value
        self.MD = c_short(self.read_calibration_slot(0xbe)).value

    def read_temperature_data(self):
        a = self._read_reg(0xf6)
        b = self._read_reg(0xf7)
        return a * 2 ** 8 + b

    def read_presure_data(self, level):
        if level >= 0 and level <= 3:
            a = self._read_reg(0xf6)
            b = self._read_reg(0xf7)
            c = self._read_reg(0xf8)
            return (a * 2 ** 16 + b * 2 ** 8 + c) / (2 ** (8 - level))
        else:
            raise Exception("invaild level parameter")

    def calculate_temperature(self, data):
        X1 = ((data - self.AC6) * self.AC5) / ( 2 ** 15 )
        X2 = (self.MC * (2 ** 11)) / (X1 + self.MD)
        self.B5 = X1 + X2
        T = (self.B5 + 8) / (2 ** 4)
        return T

    def calculate_presure(self, data, level):
        B6 = self.B5 - 4000
        X1 = (self.B2 * (B6 * B6 / 2 ** 12)) / (2 ** 11)
        X2 = self.AC2 * B6 / (2 ** 11)
        X3 = X1 + X2
        B3 = (((self.AC1 * 4 + X3) * 2 ** level) + 2 ) / 4
        X1 = self.AC3 * B6 / (2 ** 13)
        X2 = (self.B1 * (B6 * B6 / (2 ** 12))) / (2 ** 16)
        X3 = ((X1 + X2) + 2) / ( 2 ** 2 )
        B4 = self.AC4 * c_ulong(X3 + 32768).value / (2 ** 15)
        B7 = (c_ulong(data).value - B3) * (50000 / 2 ** level)
        if B7 < 0x80000000:
            p = (B7 * 2) / B4
        else:
            p = (B7 / B4) * 2
        X1 = (p / (2 ** 8)) ** 2
        X1 = (X1 * 3038) / (2 ** 16)
        X2 = (-7357 * p) / (2 ** 16)
        p = p + (X1 + X2 + 3791) / (2 ** 4)
        return p
    
    def calculate_altitude(self, p, p0):
        alt = 44330 * ( 1- math.pow( float(p) / float(p0), float(1) / 5.255) )
        return alt

    def calculate_sealevel_presure(self, p, alt):
        sealevel = float(p) / math.pow( 1 - float(alt) / 44330, 5.255)
        return sealevel

def load_test_data():
    b = BMP180(0x77)
    b.AC1 = 408
    b.AC2 = -72
    b.AC3 = -14383
    b.AC4 = 32741
    b.AC5 = 32757
    b.AC6 = 23153
    b.B1 = 6190
    b.B2 = 4
    b.MB = -32768
    b.MC = -8711
    b.MD = 2868
    t = b.calculate_temperature(27898)
    print(str(t) + " (should be 150)")
    p = b.calculate_pressure(23843, 0)
    print(str(p) + " (should be 69964)")
    return b

if __name__ == "__main__":
    b = BMP180(0x77)
    while True:
        b.start_sampling_temperature()
        b.wait_for_sampling_temperature()
        t = b.read_temperature_data()
        t = b.calculate_temperature(t)
        l = 3
        b.start_sampling_presure(l)
        b.wait_for_sampling_presure(l)
        p = b.read_presure_data(l)
        p = b.calculate_presure(p, l)
        print("t:" + str(t / 10.0) + " p:" + str(p / 100.0))
        delayMilliseconds(1000)

