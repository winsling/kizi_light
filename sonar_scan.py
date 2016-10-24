#!/usr/bin/env python

import time

import pigpio

class ranger:
   """
   This class encapsulates a type of acoustic ranger.  In particular
   the type of ranger with separate trigger and echo pins.

   A pulse on the trigger initiates the sonar ping and shortly
   afterwards a sonar pulse is transmitted and the echo pin
   goes high.  The echo pins stays high until a sonar echo is
   received (or the response times-out).  The time between
   the high and low edges indicates the sonar round trip time.
   """

   def __init__(self, pi, trigger, echo, toolong=10000):
      """
      The class is instantiated with the Pi to use and the
      gpios connected to the trigger and echo pins.  If the
      echo is longer than toolong it is assumed to be an
      outlier and is ignored.
      """
      self.pi = pi
      self.trigger = trigger
      self.echo = echo
      self.toolong = toolong

      self.high_tick = None
      self.echo_time = toolong
      self.echo_tick = pi.get_current_tick()

      self.trigger_mode = pi.get_mode(trigger)
      self.echo_mode = pi.get_mode(echo)

      pi.set_mode(trigger, pigpio.OUTPUT)
      pi.set_mode(echo, pigpio.INPUT)

      self.cb = pi.callback(echo, pigpio.EITHER_EDGE, self._cbf)

      self.inited = True

   def _cbf(self, gpio, level, tick):
      if level == 1:
         self.high_tick = tick
      else:
         if self.high_tick is not None:
            echo_time = tick - self.high_tick
            if echo_time < self.toolong:
               self.echo_time = echo_time
               self.echo_tick = tick
            else:
               self.echo_time = self.toolong
            self.high_tick = None

   def read(self):
      """
      The returned reading is the number
      of microseconds for the sonar round-trip.

      round trip cms = round trip time / 1000000.0 * 34030
      """
      if self.inited:
         return self.echo_time
      else:
         return None

   def trig(self):
      """
      Triggers a reading.
      """
      if self.inited:
         self.pi.gpio_trigger(self.trigger)

   def cancel(self):
      """
      Cancels the ranger and returns the gpios to their
      original mode.
      """
      if self.inited:
         self.inited = False
         self.cb.cancel()
         self.pi.set_mode(self.trigger, self.trigger_mode)
         self.pi.set_mode(self.echo, self.echo_mode)

if __name__ == "__main__":

   import time

   import pigpio

   import sonar_scan

   VSERVO=14
   HSERVO=15

   pi = pigpio.pi()

   # point sonar ranger slightly up
   pi.set_servo_pulsewidth(VSERVO, 1350)

   sonar = sonar_scan.ranger(pi, 23, 18, 2600)

   end = time.time() + 600.0

   r = 1

   angles = [-45, -40, -35, -30, -25, -20, -15, -10, -5,   0,
               5,  10,  15,  20,  25,  30,  35,  40, 45,  40,
              35,  30,  25,  20,  15,  10,   5,   0, -5, -10,
             -15, -20, -25, -30, -35, -40, -45]

   for x in range(5):

      for ang in angles:
         # move servo to angle
         pi.set_servo_pulsewidth(HSERVO, 1500+(ang*1000/90))

         time.sleep(0.5)

         for i in range(50):
            sonar.trig()
            time.sleep(0.1)
            print("{} {} {}".format(r, sonar.read(), ang))
            r += 1

   sonar.cancel()

   pi.stop()

