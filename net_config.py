# Press X to reboot the pico back to the main menu (main.py)
import time
from WIFI_CONFIG import SSID, SSID2, PSK
import utime
import machine
import network
import ntptime
import rp2
from pimoroni import Button, Pin, RGBLED
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY, PEN_P4

# Set to current hardware time
rtc = machine.RTC()

# Set Country Code Time Zone
rp2.country('US')

global last, set_clock, cursor, year, month, day, hour, minute, second

net = False
cset = False

# We're only using a few colours so we can use a 4 bit/16 colour palette and save RAM!
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, pen_type=PEN_P4, rotate=0)

WIDTH, HEIGHT = display.get_bounds()
display.set_backlight(1)
display.set_font("bitmap8")

# Turn of the RGB LED
led = RGBLED(6, 7, 8)
led.set_rgb(0, 0, 0)

button_a = Button(12)
button_b = Button(13)
button_x = Button(14)
button_y = Button(15)

WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)

PINK = display.create_pen(214, 28, 78)
ORANGE_1 = display.create_pen(247, 126, 33)
ORANGE_2 = display.create_pen(250, 194, 19)
   
def connect_net():
    global net
    # Write to Display
    display.set_pen(WHITE)
    display.clear()
    display.set_pen(BLACK)

    text = "Configuring WiFi"
    x, y = 20, 15
    text_size = 2
    line_height = 2

    # center text horixontally
    title_width = display.measure_text(text, text_size)
    text_x = 10

    row_height = text_size * 5 + 20

    # center list items vertically
    text_y = int(3 * row_height - (row_height / 2))
    
    display.text(text, text_x, text_y + 1, -1, text_size)
    display.update()
    
    # Wifi Network Info
    ssids = [SSID, SSID2]
    passwords = [PSK, PSK]

    # Activate Thrusters
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    # If already connected, return
    if wlan.isconnected():
        print("WiFi is already connected.")
        net = True
        status = wlan.ifconfig()
        print('ip = ' + status[0])
        return

    for ssid, password in zip(ssids, passwords):
        if net or wlan.status() == 3:
            net = True
            net2 = wlan.ifconfig()
            print('WiFi Link Up!')
            print('ip = ' + net2[0])
            break

        wlan.connect(ssid, password)

        # Wait for connect or fail
        max_wait = 20
        while max_wait > 0:
            if wlan.status() == 3:
                net = True
                status = wlan.ifconfig()
                print('ip = ' + status[0])
                break
            if wlan.status() == 3:
                status = wlan.ifconfig()
                print('ip = ' + status[0])
                net = True
                break
            max_wait -= 1
            if wlan.status() is -2:
                print('No Net!')
            if wlan.status() is 0:
                print('Link Down!')
                wlan.active(False)
                wlan.active(True)
            if wlan.status() is 1:
                print('Link Join!')
            if wlan.status() is 2:
                print('No IP Address!')
            if wlan.status() is -3:
                print('Failed Auth!')
                net = True
                break
            utime.sleep(1)
            
                
try:
    if not net:
        while not net:
            max_tries = 10
            while max_tries > 0:
                if net:
                    break
                connect_net()
                max_tries -= 1
except Exception as e:
    if not net:
        while not net:
            max_tries = 10
            while max_tries > 0:
                if net:
                    break
                connect_net()
                max_tries -= 1

    # Write to Display
    display.set_pen(WHITE)
    display.clear()
    display.set_pen(BLACK)

    text = "No WiFi"
    text2 = "Try Rebooting"
    x, y = 20, 15
    text_size = 2
    line_height = 2

    # center text horixontally
    title_width = display.measure_text(text, text_size)
    text_x = 10
    row_height = text_size * 5 + 20

    # center list items vertically
    text_y = 20
    text_y2 = 50

    display.text(text, text_x, text_y, -1, text_size)
    display.text(text2, text_x, text_y2, -1, text_size)
    display.update()

# Get the network configuration from the adapter
net = network.WLAN(network.STA_IF).ifconfig()

# Draw the output to the screen
TEXT_SIZE = 2.5
LINE_HEIGHT = 22

# Page Header
display.set_pen(ORANGE_2)
display.clear()
display.set_pen(BLACK)

display.set_pen(ORANGE_1)
display.rectangle(0, 0, WIDTH, 35)
display.set_pen(WHITE)
display.text("Network Configuration", 10, 10, -1, TEXT_SIZE)
display.set_pen(BLACK)

y = 35 + int(LINE_HEIGHT / 2)

if net:
    display.text("> LOCAL IP: {}".format(net[0]), 5, y, WIDTH)
    y += LINE_HEIGHT
    display.text("> Subnet: {}".format(net[1]), 5, y, WIDTH)
    y += LINE_HEIGHT
    display.text("> Gateway: {}".format(net[2]), 5, y, WIDTH)
    y += LINE_HEIGHT
    display.text("> DNS: {}".format(net[3]), 5, y, WIDTH)
else:
    display.text("> No network connection!", 5, y, WIDTH)
    y += LINE_HEIGHT
    display.text("> Check configuration.", 5, y, WIDTH)

# Draw the complete display output
display.update()

# Loop to keep alive the app to register button presses
while True:
    pressed = False  
    
    if button_x.is_pressed:
      if not pressed:
          pressed = True
          # Perform a soft reset
          machine.soft_reset()
      else:
          pressed = False
    
    time.sleep(1)