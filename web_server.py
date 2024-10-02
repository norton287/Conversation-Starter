import network
import socket
import utime
import machine
import rp2
from WIFI_CONFIG import SSID, SSID2, PSK
from pimoroni import Button, Pin, RGBLED
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY, PEN_P4
from machine import Pin
import uasyncio as asyncio

# Set to current hardware time
rtc = machine.RTC()

client_ip = "None"
net = False
net2 = "Empty"
EST_CONNECTION = False
CCONNECTED = 0

sys_status = "STATUS"

# Webpage
html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Web Test</title>
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css">
<style>
.container {
display: flex;
flex-direction: column;
justify-content: center;
align-items: center;
height: 100vh;
}
.box {
box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
padding: 20px;
margin: 10px;
max-width: 600px;
background-color: #f9fafb; /* Soft blue-gray */
border-radius: 10px;
}
.text-bright {
color: #ff6600; /* Bright orange */
}
.bg-bright {
background-color: #ff6600; /* Bright orange */
}
</style>
</head>
<body class="bg-blue-100">
<div class="container">
<div class="box bg-white rounded text-center">
<h1 class="text-3xl font-bold mb-6 animate__animated animate__rubberBand text-bright">Click The Button To Revel The Hidden Text</h1>
<button id="showText" class="bg-bright hover:bg-yellow-300 text-white font-bold py-2 px-4 rounded mb-6">
Click Me
</button>
<div id="hiddenText" class="hidden my-4 text-l font-bold animate__animated animate__bounce text-bright">Some Hidden Text!!!</div>
</div>
</div>
<script>
document.getElementById('showText').addEventListener('click', function() {
document.getElementById('hiddenText').classList.toggle('hidden');
});
</script>
</body>
</html>
"""

# We're only using a few colours so we can use a 4 bit/16 colour palette and save RAM!
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, pen_type=PEN_P4, rotate=0)

WIDTH, HEIGHT = display.get_bounds()
display.set_backlight(1)
display.set_font("bitmap8")

text_size = 2

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

CCONNECTED = 0

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
    global net, net2
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
        net2 = wlan.ifconfig()
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

# Draw the output to the screen
TEXT_SIZE = 1
LINE_HEIGHT = 22

def draw_header():
    global EST_CONNECTION, client_ip, net2
    # Page Header
    display.set_pen(ORANGE_2)
    display.clear()
    display.set_pen(BLACK)

    display.set_pen(PINK)
    display.rectangle(0, 0, WIDTH, 35)
    display.set_pen(WHITE)
    display.text("Pico Web Server", 10, 10, -1, text_size)
    display.set_pen(BLACK)

    y = 35 + int(LINE_HEIGHT / 2)

    if net2:
        display.text(f'> LOCAL IP: {net2[0]}', 5, y, WIDTH)
        y += LINE_HEIGHT
    else:
        display.text("No network connection!", 5, y, WIDTH)
        y += LINE_HEIGHT
        display.text("Check configuration.", 5, y, WIDTH)
        
    if client_ip and client_ip != "None":
        display.text("> Client IP: ", 5, y, WIDTH)
        y += LINE_HEIGHT
        display.text("> " + client_ip, 5, y, WIDTH)
        y += LINE_HEIGHT
    
    if EST_CONNECTION == True:
        display.text("> Client Connected!", 5, y, WIDTH)
        EST_CONNECTION = False
    else:
        display.text("> No Clients Connected!", 5, y, WIDTH)
        EST_CONNECTION = False
        
    # Draw the complete display output
    display.update()

async def serve_client(reader, writer):
    global EST_CONNECTION, client_ip
    
    pressed = False
    
    if button_x.is_pressed:
        pressed = True
        # Perform a soft reset
        machine.soft_reset()
    else:
        pressed = False
          
    request_line = await reader.readline()
    
    # Check if the request is an HTTPS request
    if request_line.startswith(b'GET https://'):
        await writer.aclose()  # Close connection if HTTPS request is detected
        return
    
    # Retrieve and store client's IP address
    client_ip = writer.get_extra_info('peername')[0]
    
    # We are not interested in HTTP request headers, skip them
    while await reader.readline() != b"\r\n":
        pressed = False
        
        if button_x.is_pressed:
            pressed = True
            # Perform a soft reset
            machine.soft_reset()
        else:
            pressed = False
        pass
    response = html
    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    EST_CONNECTION = True
    writer.write(response)
    await writer.drain()
    await writer.wait_closed()
    
    draw_header()
async def main():
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))
    
    pressed = False
    
    while True:
        if button_x.is_pressed:
            pressed = True
            # Perform a soft reset
            machine.soft_reset()
        else:
            pressed = False
            await asyncio.sleep(5)
    
draw_header()

try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()