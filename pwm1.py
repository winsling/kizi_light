import time
import pigpio
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import sonar_scan

# Hardware SPI configuration:
SPI_PORT   = 0
SPI_DEVICE = 0
mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))

FREQ = 150
DC = 20
PWM1 = 17

REFRESH=1000

CHARSET={
' ': 0b00000000,
'0': 0b11111100,
'1': 0b01100000,
'2': 0b11011010,
'3': 0b11110010,
'4': 0b01100110,
'5': 0b10110110,
'6': 0b00111110,
'7': 0b11100000,
'8': 0b11111110,
'9': 0b11100110,
'A': 0b11101110,
'b': 0b00111110,
'C': 0b10011100,
'c': 0b00011010,
'd': 0b01111010,
'E': 0b10011110,
'F': 0b10001110,
'H': 0b01101110,
'h': 0b00101110,
'L': 0b00011100,
'l': 0b01100000,
'O': 0b11111100,
'o': 0b00111010,
'P': 0b11001110,
'S': 0b10110110,
}

# This defines which gpios are connected to which segments
#          a   b   c   d   e   f   g  dp

SEG2GPIO=[ 4, 27, 18, 22, 23, 13, 24,  19]

# This defines the gpio used to switch on a LCD
#          1   2   3   4   5

LCD2GPIO=[ 5,  6,  16,  25]

wid = None

showing = [0]*len(LCD2GPIO)

CHARS=len(CHARSET)

def display(lcd, char):
   if char in CHARSET:
      showing[lcd] = CHARSET[char]
   else:
      showing[lcd] = 0

def update_display():
   global wid
   wf = []
   for lcd in range(len(LCD2GPIO)):

      segments = showing[lcd] # segments on for current LCD

      on = 0 # gpios to switch on
      off = 0 # gpios to switch off

      # set this LCD on, others off
      for L in range(len(LCD2GPIO)):
         if L == lcd:
            off |= 1<<LCD2GPIO[L] # switch LCD on
         else:
            on |= 1<<LCD2GPIO[L] # switch LCD off

      # set used segments on, unused segments off
      for b in range(8):
         if segments & 1<<(7-b):
            on |= 1<<SEG2GPIO[b] # switch segment on
         else:
            off |= 1<<SEG2GPIO[b] # switch segment off

      wf.append(pigpio.pulse(on, off, REFRESH))

      #print(lcd, on, off, REFRESH) # debugging only

   p.wave_add_generic(wf) # add pulses to waveform
   new_wid = p.wave_create() # commit waveform
   p.wave_send_repeat(new_wid) # transmit waveform repeatedly

   if wid is not None:
      p.wave_delete(wid) # delete no longer used waveform

      #print("wid", wid, "new_wid", new_wid)
      
   wid = new_wid


p = pigpio.pi()

p.set_mode(PWM1,pigpio.OUTPUT)

p.set_PWM_frequency(PWM1,FREQ)

p.set_PWM_dutycycle(PWM1,DC)


for segment in SEG2GPIO:
   p.set_mode(segment, pigpio.OUTPUT)

for lcd in LCD2GPIO:
   p.set_mode(lcd, pigpio.OUTPUT)

char=0

ck = CHARSET.keys()

sonar = sonar_scan.ranger(p, 21, 20, 2600)

try:
    while True:

        sonar.trig()
        time.sleep(0.1)
        distanz = (sonar.read()*34300)/(2*1000000)

        values = [0]*8
        for i in range(8):
            values[i] = mcp.read_adc(i)

        poti = (255*values[0])/1024
        temp = (500*values[1])/1024

        poti_proz = (poti * 100) / 255
        poti_strg = str(poti_proz)

        temp_strg = str(temp)

        dist_strg = str(distanz)
        
        if len(poti_strg) > 1:
           display(0,str(poti_strg[0]))
           display(1,str(poti_strg[1]))
        else:
           display(0,' ')
           display(1,str(poti_strg[0]))

        if len(temp_strg) > 1:
           display(2,str(temp_strg[0]))
           display(3,str(temp_strg[1]))
        else:
           display(2,' ')
           display(3,str(temp_strg[0]))

        if distanz <10:
           display(0,' ')
           display(1,' ')
           display(2,' ')
           display(3,str(dist_strg[0]))
           
        p.set_PWM_dutycycle(PWM1,poti)

        update_display()



except KeyboardInterrupt:
    pass

sonar.cancel()
p.wave_delete(wid)
p.stop()



