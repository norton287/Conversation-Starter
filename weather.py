# press X to reboot the pico back to the main menu (main.py)
import utime
from WIFI_CONFIG import SSID, SSID2, PSK
import machine
import network
import rp2
import urequests
from pimoroni import Button, Pin, RGBLED
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY, PEN_P4

# Set your latitude/longitude here (find yours by right clicking in Google Maps!)
LAT = 33.9306
LNG = -98.4902
TIMEZONE = "auto"  # determines time zone from lat/long

current_condition = "None"

net = False

# Meteo URL API
URL = "http://api.open-meteo.com/v1/forecast?latitude=" + str(LAT) + "&longitude=" + str(LNG) + "&current_weather=true&timezone=" + TIMEZONE

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

def get_data():
    global weathercode, temperature, windspeed, winddirection, date, time
    print(f"Requesting URL: {URL}")
    r = urequests.get(URL)
    # open the json data
    j = r.json()
    print("Data obtained!")
    print(j)

    # parse relevant data from JSON
    current = j["current_weather"]
    temperature = current["temperature"]
    windspeed = current["windspeed"] * 0.621371 # Convert km/h to mph
    winddirection = calculate_bearing(current["winddirection"])
    weathercode = current["weathercode"]
    date, time = current["time"].split("T")

    r.close()


def calculate_bearing(d):
    # calculates a compass direction from the wind direction in degrees
    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    ix = round(d / (360. / len(dirs)))
    return dirs[ix % len(dirs)]

def draw_page():
    global current_condition
    # Clear the display
    display.set_pen(ORANGE_2)
    display.clear()
    display.set_pen(BLACK)

    # Draw the page header
    display.set_font("bitmap8")
    display.set_pen(ORANGE_1)
    display.rectangle(0, 0, WIDTH, 30)
    display.set_pen(WHITE)
    display.text("Weather", 10, 6)
    display.set_pen(BLACK)

    display.set_font("bitmap8")

    if temperature is not None:
        if weathercode in [71, 73, 75, 77, 85, 86]:  # codes for snow
            current_condition = "Snow"
        elif weathercode in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:  # codes for rain
            current_condition = "Raining"
        elif weathercode in [1, 2, 3, 45, 48]:  # codes for cloud
            current_condition = "Cloudy"
        elif weathercode in [0]:  # codes for sun
            current_condition = "Sunny"
        elif weathercode in [95, 96, 99]:  # codes for storm
            current_condition = "Stormy"
        display.set_pen(BLACK)
        temperature_f = (temperature * 9/5) + 32  # Convert °C to °F
        display.text(f"Temperature: {temperature_f: .2f} °F", 10, 35, -1, 2)
        display.text(f"Wind: ({winddirection}){windspeed: .2f} mph", 10, 55, -1, 2)
        display.text(f"Conditions: {current_condition}", 10, 75, -1, 2)
        display.text(f"Last update: {date}, {time}", 10, 95, WIDTH - 10, 2)

    else:
        display.set_pen(BLACK)
        display.rectangle(0, 60, WIDTH, 25)
        display.set_pen(WHITE)
        display.text("Unable to display weather! Check your network settings", 5, 65, WIDTH, 1)

    display.update()

get_data()
draw_page()
    
while True:
    count = 600
    pressed = False  
    
    if button_x.is_pressed:
        pressed = True
        # Perform a soft reset
        machine.soft_reset()
    else:
        pressed = False
          
    utime.sleep(1)
    count -= 1
    
    if count <= 2:
        get_data()
        draw_page()
        count = 600