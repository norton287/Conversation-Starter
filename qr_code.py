# Press X to reboot the pico back to menu (main.py)
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY
from pimoroni import Button, RGBLED
import machine
import time
import qrcode

# Turn of the RGB LED
led = RGBLED(6, 7, 8)
led.set_rgb(0, 0, 0)

display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, rotate=0)
display.set_backlight(1.0)

button_a = Button(12)
button_b = Button(13)
button_x = Button(14)
button_y = Button(15)

WIDTH, HEIGHT = display.get_bounds()

BG = display.create_pen(0, 0, 0)
FG = display.create_pen(255, 255, 255)


def measure_qr_code(size, code):
    w, h = code.get_size()
    module_size = int(size / w)
    return module_size * w, module_size


def draw_qr_code(ox, oy, size, code):
    size, module_size = measure_qr_code(size, code)
    display.set_pen(FG)
    display.rectangle(ox, oy, size, size)
    display.set_pen(BG)
    for x in range(size):
        for y in range(size):
            if code.get_module(x, y):
                display.rectangle(ox + x * module_size, oy + y * module_size, module_size, module_size)


code = qrcode.QRCode()
code.set_text("Hey I'm Matt!")

display.set_pen(FG)
display.clear()
display.set_pen(BG)

max_size = min(WIDTH, HEIGHT)

size, module_size = measure_qr_code(max_size, code)
left = int((WIDTH // 2) - (size // 2))
top = int((HEIGHT // 2) - (size // 2))
draw_qr_code(left, top, max_size, code)

display.update()

while True:
    # Reset the app
    pressed = False  
    
    if button_x.is_pressed:
      if not pressed:
          pressed = True
          # Perform a soft reset
          machine.soft_reset()
      else:
          pressed = False
        
        
    time.sleep(1)