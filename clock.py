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

global last, set_clock, cursor, year, month, day, hour, minute, second

net = False
cset = False

# Set the time zone offset in seconds for CST (UTC-6)
time_zone_offset = -5 * 3600

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

rtc = machine.RTC()

# Output to Display the passed text
def output_display(tmptext):
    global doutput

    # Write to Display
    display.set_pen(WHITE)
    display.clear()
    display.set_pen(BLACK)

    text = tmptext
    
    text_size = 2

    # center text horizontally
    title_width = display.measure_text(text, text_size)
    text_x = int((WIDTH - title_width) / 2)

    row_height = text_size * 5 + 20

    # calculate the top-left corner of the text based on the height of the display and the size of the text
    top_left_y = (int(HEIGHT) - row_height) // 2

    text_y = (int(HEIGHT - row_height)) // 2

    display.text(text, text_x, text_y, -1, text_size)
    display.update()
    
# Connect to wifi and synchronize the RTC time from NTP
def sync_time():
    global cset, year, month, day, wd, hour, minute, second

    text = "Setting Time"
    output_display(text)
    utime.sleep(1)

    # Check if RTC has valid time, reset if not
    try:
        rtc.datetime((2023, 1, 1, 0, 0, 0, 0, 0))  # Reset to a known good time
        year, month, day, wd, hour, minute, second, _ = rtc.datetime()
        if not all(isinstance(x, int) for x in [year, month, day, wd, hour, minute, second]):
            raise ValueError("Invalid time values in RTC")
        print(f'Year = {year}, Month = {month}, Day = {day}, Hour = {hour}, Minute = {minute}, Second = {second}')
    except (ValueError, OSError) as e:
        print(f"RTC reset required: {e}")
        rtc.datetime((2023, 1, 1, 0, 0, 0, 0, 0))  # Reset to a known good time
        year, month, day, wd, hour, minute, second, _ = rtc.datetime()
        print(f'Year = {year}, Month = {month}, Day = {day}, Hour = {hour}, Minute = {minute}, Second = {second}')
    
    if not net:
        return

    if net:
        max_tries = 100
        while not cset:
            max_tries -= 1
            try:
                ntptime.settime()
                print("Time set")
                cset = True
            except OSError as e:
                print(f'Exception setting time {e}')
                cset = False
                pass
    
        # Get the current time in UTC
    y, mnth, d, h, m, s, wkd, yearday = time.localtime()

    # Create a time tuple for January 1st of the current year (standard time)
    jan_1st = (year, 1, 1, 0, 0, 0, 0, 0)

    # Create a time tuple for July 1st of the current year (daylight saving time, if applicable)
    jul_1st = (year, 7, 1, 0, 0, 0, 0, 0)

    # Determine if daylight saving time (CDT) is in effect
    is_dst = time.localtime(time.mktime(jul_1st))[3] != time.localtime(time.mktime(jan_1st))[3]

    # Set the appropriate UTC offset
    utc_offset = -5  # CST

    if is_dst:
        utc_offset = -6  # CDT

    hour = (h + utc_offset) % 24

    # If hour became 0 after modulo, it means we crossed into the previous day
    if hour == 0 and h + utc_offset < 0:
        # Decrement the day, handling month/year transitions if necessary
        d -= 1
        if d == 0:
            mnth -= 1
            if mnth == 0:
                y -= 1
                mnth = 12
            # Adjust for the number of days in the previous month
            d = 31  # Start with the assumption of 31 days
            if mnth in [4, 6, 9, 11]:
                d = 30
            elif mnth == 2:
                d = 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 28

    # Check all values before setting RTC
    if not (1 <= mnth <= 12 and 1 <= d <= 31 and 0 <= wkd <= 6 and 0 <= hour <= 23 and 0 <= m <= 59 and 0 <= s <= 59):
        print(f'Month: {mnth}, Day: {d}, WkDay: {wkd}, Hour: {hour}, Minute: {m}, Second: {s}')
        print("Invalid time values detected, skipping RTC update")
    else:
        try:
            rtc.datetime((y, mnth, d, wkd, hour, m, s, 0))
        except Exception as e:
            print(f'Exception setting time: {e}')
            
    year, month, day, wd, hour, minute, second, _ = rtc.datetime()
    print(f'Month: {mnth}, Day: {d}, WkDay: {wkd}, Hour: {hour}, Minute: {m}, Second: {s}')
    print(f'Year = {year}, Month = {month}, Day = {day}, Hour = {hour}, Minute = {minute}, Second = {second}')
    print("Time set in sync_time function!")
    text = f'{month}-{day}-{year}, {hour}:{minute}:{second}'
    output_display(text)
    utime.sleep(4)
    
def connect_net():
    global net
    # Write to Display
    
    text = "Configuring WiFi"
    output_display(text)
    
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
        text = f'IP = {status[0]}'
        output_display(text)
        utime.sleep(4)
        sync_time()
        return

    for ssid, password in zip(ssids, passwords):
        if net or wlan.isconnected():
            net = True
            net2 = wlan.ifconfig()
            print('WiFi Link Up!')
            print('ip = ' + status[0])
            text = f'IP = {status[0]}'
            output_display(text)
            utime.sleep(4)
            break
        
        qtext = "Connecting To WiFi"
        output_display(qtext)
        wlan.connect(ssid, password)
        utime.sleep(4)

        # Wait for connect or fail
        max_wait = 20
        while max_wait > 0:
            if wlan.isconnected():
                net = True
                status = wlan.ifconfig()
                print('ip = ' + status[0])
                text = f'IP = {status[0]}'
                output_display(text)
                utime.sleep(4)
                sync_time()
                break
            else:
                text = "Retrying WiFi"
                output_display(text)
                if wlan.status() is -2:
                    print('No Net!')
                if wlan.status() is 0:
                    print('Link Down!')
                if wlan.status() is 1:
                    print('Link Join!')
                if wlan.status() is 2:
                    print('No IP Address!')
                if wlan.status() is -3:
                    print('Failed Auth!')
            max_wait -= 1
            utime.sleep(1)
            output_display(qtext)
            wlan.connect(ssid,password)
            utime.sleep(3)
                
try:
    if not net:
        while not net:
            if net:
                print("Breaking net connect loop!")
                break
            max_tries = 10
            while max_tries > 0:
                if net:
                    print("Breaking net connect loop!")
                    break
                else:
                    connect_net()
                    max_tries -= 1
except Exception as e:
    # Write to Display
    if not net:
        text = "No WiFi, Try Rebooting!"
        output_display(text)
    print(f'Error configuring WiFi or setting time {e}')
    
def draw_clock():

    display.set_pen(WHITE)
    display.clear()

    hr = "{:02}".format(hour)
    min = "{:02}".format(minute)
    sec = "{:02}".format(second)

    hr_width = display.measure_text(hr, 1)
    hr_offset = 15

    minute_width = display.measure_text(min, 1)
    minute_offset = 25

    second_width = display.measure_text(sec, 1)
    second_offset = 65

    display.set_pen(PINK)
    display.rectangle(10, 10, (hour * 8 + 50), 35)
    display.set_pen(ORANGE_1)
    display.rectangle(10, 53, (minute * 3 + 50), 35)
    display.set_pen(ORANGE_2)
    display.rectangle(10, 96, (second * 3 + 50), 35)

    display.set_pen(WHITE)
    display.text(hr, 20, 15, 25, 3)
    display.text(min, 20, 60, 25, 3)
    display.text(sec, 20, 105, 25, 3)

    display.set_pen(BLACK)

    display.update()

last_second = second

while True:
    pressed = False
    
    if button_x.is_pressed:
        pressed = True
        # Perform a soft reset
        machine.soft_reset()
    else:
        pressed = False
          
    year, month, day, wd, hour, minute, second, _ = rtc.datetime()
    if second != last_second:
       draw_clock()
       last_second = second
        
    draw_clock()        
    time.sleep(0.01)