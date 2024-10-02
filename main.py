import gc
from WIFI_CONFIG import SSID, SSID2, PSK
import utime
import time
import machine
import binascii
import ntptime
import network
import rp2
import urequests
from os import listdir
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY, PEN_P4, PEN_RGB332
from pimoroni import Button, RGBLED

# We're only using a few colours so we can use a 4 bit/16 colour palette and save RAM!
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, pen_type=PEN_P4, rotate=0)

WIDTH, HEIGHT = display.get_bounds()
display.set_backlight(1)
display.set_font("bitmap8")

WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)

led = RGBLED(6, 7, 8)
led.set_rgb(0, 0, 0)

# Set to current hardware time
rtc = machine.RTC()

# Set Country Code Time Zone
rp2.country('US')

global last, set_clock, cursor, year, month, day, hour, minute, second, net

net = False
cset = False

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
    
dtext = "MattOS"
output_display(dtext)
utime.sleep(5)

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
        sync_time()
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
                connect_net()
                max_tries -= 1
except Exception as e:
    # Write to Display
    if not net:
        text = "No WiFi, Try Rebooting!"
        output_display(text)
    print(f'Error configuring WiFi or setting time {e}')

def hsv_to_rgb(h: float, s: float, v: float) -> tuple[float, float, float]:
    if s == 0.0:
        return v, v, v
    i = int(h * 6.0)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    v = int(v * 255)
    t = int(t * 255)
    p = int(p * 255)
    q = int(q * 255)
    i = i % 6
    if i == 0:
        return v, t, p
    if i == 1:
        return q, v, p
    if i == 2:
        return p, v, t
    if i == 3:
        return p, q, v
    if i == 4:
        return t, p, v
    if i == 5:
        return v, p, q


def get_applications() -> list[dict[str, str]]:
    # fetch a list of the applications that are stored in the filesystem
    applications = []
    for file in listdir():
        if file.endswith(".py") and file != "main.py" and file != "network_manager.py" and file != "WIFI_CONFIG.py":
            # convert the filename from "something_or_other.py" to "Something Or Other"
            # via weird incantations and a sprinkling of voodoo
            title = " ".join([v[:1].upper() + v[1:] for v in file[:-3].split("_")])

            applications.append(
                {
                    "file": file,
                    "title": title
                }
            )

    # sort the application list alphabetically by title and return the list
    return sorted(applications, key=lambda x: x["title"])


def prepare_for_launch() -> None:
    for k in locals().keys():
        if k not in ("__name__",
                     "application_file_to_launch",
                     "gc"):
            del locals()[k]
    gc.collect()


def menu() -> str:
    applications = get_applications()

    button_a = Button(12)
    button_b = Button(13)
    button_x = Button(14)
    button_y = Button(15)

    display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, pen_type=PEN_RGB332, rotate=1)
    display.set_backlight(1.0)

    selected_item = 2
    scroll_position = 2
    target_scroll_position = 2

    selected_pen = display.create_pen(255, 255, 255)
    unselected_pen = display.create_pen(80, 80, 100)
    background_pen = display.create_pen(50, 50, 70)
    shadow_pen = display.create_pen(0, 0, 0)
    
    while True:
        t = utime.ticks_ms() / 1000.0
           
        if button_x.read():
            target_scroll_position -= 1
            target_scroll_position = target_scroll_position if target_scroll_position >= 0 else len(applications) - 1

        if button_y.read():
            target_scroll_position += 1
            target_scroll_position = target_scroll_position if target_scroll_position < len(applications) else 0

        if button_a.read():
            # Wait for the button to be released.
            while button_a.is_pressed:
                utime.sleep(0.01)

            return applications[selected_item]["file"]

        display.set_pen(background_pen)
        display.clear()

        scroll_position += (target_scroll_position - scroll_position) / 5

        grid_size = 25
        for y in range(0, 165 // grid_size):
            for x in range(0, 250 // grid_size):
                h = x + y + int(t * 5)
                h = h / 50.0
                r, g, b = hsv_to_rgb(h, 0.5, 1)

                display.set_pen(display.create_pen(r, g, b))
                display.rectangle(x * grid_size, y * grid_size, grid_size, grid_size)

        # work out which item is selected (closest to the current scroll position)
        selected_item = round(target_scroll_position)

        for list_index, application in enumerate(applications):
            distance = list_index - scroll_position

            text_size = 4 if selected_item == list_index else 3

            # center text horixontally
            title_width = display.measure_text(application["title"], text_size)
            text_x = int(120 - title_width / 2)

            row_height = text_size * 5 + 20

            # center list items vertically
            text_y = int(120 + distance * row_height - (row_height / 2))

            # draw the text, selected item brightest and with shadow
            if selected_item == list_index:
                display.set_pen(shadow_pen)
                display.text(application["title"], text_x + 1, text_y + 1, -1, text_size)

            text_pen = selected_pen if selected_item == list_index else unselected_pen
            display.set_pen(text_pen)
            display.text(application["title"], text_x, text_y, -1, text_size)

        display.update()


# The application we will be launching. This should be ouronly global, so we can
# drop everything else.
application_file_to_launch = menu()

# Run whatever we've set up to.
# If this fails, we'll exit the script and drop to the REPL, which is
# fairly reasonable.
prepare_for_launch()
__import__(application_file_to_launch)