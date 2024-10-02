import urequests
from WIFI_CONFIG import SSID, SSID2, PSK
import utime
import network
import time
import rp2
import uasyncio
from pimoroni import Button, Pin, RGBLED
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY, PEN_P4


# Setup Variables
global last, set_clock, cursor, year, month, day, hour, minute, second

net = False
cset = False

# Store the title of the latest story
response = None
latest_title = None
new_description = None

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
        while not cset:
            try:
                ntptime.settime()
                print("Time set")
                cset = True
            except OSError as e:
                print(f'Exception setting time {e}')
                cset = False
                utime.sleep(2) # Set a backoff time as to not spam the NTP server
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
    text = f'{month}-{day}-{year}, {hour}:{minute}:{second}'
    output_display(text)
    utime.sleep(4)
    print(f'Month: {mnth}, Day: {d}, WkDay: {wkd}, Hour: {hour}, Minute: {m}, Second: {s}')
    print(f'Year = {year}, Month = {month}, Day = {day}, Hour = {hour}, Minute = {minute}, Second = {second}')
    print("Time set in sync_time function!")
    
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
        print('ip = ' + status[0])
        text = f'IP = {status[0]}'
        output_display(text)
        utime.sleep(4)
        return

    for ssid, password in zip(ssids, passwords):
        if net or wlan.isconnected():
            net = True
            net2 = wlan.ifconfig()
            print('WiFi Link Up!')
            print('ip = ' + net2[0])
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
                utime.sleep(8)
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
                connect_net()
                max_tries -= 1
except Exception as e:
    # Write to Display
    if not net:
        text = "No WiFi, Try Rebooting!"
        output_display(text)
    print(f'Error connecting or setting time {e}')

# Fetch the RSS feed
response = urequests.get('https://www.npr.org/rss/rss.php?id=1019')

# Create a list to store all the items
items = []

# Find the start of the first <item> tag
start = response.text.find('<item>')

while start != -1:
    # Find the end of the <item> tag
    end = response.text.find('</item>', start)

    # Extract the item
    item = response.text[start:end]

    # Add the item to the list
    items.append(item)

    # Find the start of the next <item> tag, starting from 'start'
    start = response.text.find('<item>', start + len('<item>'))

# Create a variable to keep track of the current item index
current_item_index = 0

def draw_page1(index):
    global response, latest_title, new_description, net
    # Clear the display
    display.set_pen(ORANGE_2)
    display.clear()
    display.set_pen(BLACK)

    # Draw the page header
    display.set_font("bitmap8")
    display.set_pen(PINK)
    display.rectangle(0, 0, WIDTH, 30)
    display.set_pen(WHITE)
    display.text("NPR News", 12, 6)
    display.set_pen(BLACK)
    display.set_font("bitmap8")
    display.set_pen(BLACK)
    
    if net:
        # Get the item at the specified index
        item = items[index]

        # Find the start and end of the <title> tag within the item
        title_start = item.find('<title>') + len('<title>')
        title_end = item.find('</title>', title_start)

        # Extract the title
        new_title = item[title_start:title_end]

        display.text(new_title, 10, 35, WIDTH - 10, 2)

        # Find the start and end of the <description> tag within the item
        desc_start = item.find('<description>') + len('<description>')
        desc_end = item.find('</description>', desc_start)
        new_description = item[desc_start:desc_end]

def draw_page2():
    global response, latest_title, new_description, net
    # Clear the display
    display.set_pen(ORANGE_2)
    display.clear()
    display.set_pen(BLACK)

    # Draw the page header
    display.set_font("bitmap8")
    display.set_pen(PINK)
    display.rectangle(0, 0, WIDTH, 30)
    display.set_pen(WHITE)
    display.text("NPR News", 12, 6)
    display.set_pen(BLACK)
    display.set_font("bitmap4")
    display.set_pen(BLACK)
    
    # Print the description
    display.text(new_description, 10, 35, WIDTH - 10, 2)
    
draw_page1(current_item_index)
display.update()

while True:
    pressed = False
    a_pressed = False
    b_pressed = False
    x_pressed = False
    y_pressed = False

    # Set up button handlers
    if button_x.is_pressed:
        x_pressed = True
        print("Button X Pressed")
        # Increment the current item index and wrap around if necessary
        current_item_index = (current_item_index + 1) % len(items)
        # Draw the new item
        draw_page1(current_item_index)
        display.update()
        time.sleep(1)
    else:
        x_pressed = False
            
    if button_y.is_pressed:
        y_pressed = True
        print("Button Y Pressed")
        # Decrement the current item index and wrap around if necessary
        current_item_index = (current_item_index - 1) % len(items)
        # Draw the new item
        draw_page1(current_item_index)
        display.update()
        time.sleep(1)            
    else:
        y_pressed = False
    
    # Break out of app and back to main.py (menu)
    if button_x.is_pressed and button_y.is_pressed:
        pressed = True
        # Perform a soft reset
        machine.soft_reset()
    else:
        pressed = False
        
    if net and button_a.is_pressed:
        a_pressed = True
        print("Button A Pressed")
        draw_page1(current_item_index)
        display.update()
        time.sleep(1)
    else:
        a_pressed = False
    
    if net and button_b.is_pressed:
        b_pressed = True
        print("Button B Pressed")
        draw_page2()
        display.update()
        time.sleep(1)
    else:
        b_pressed = False