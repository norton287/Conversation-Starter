# PicoPong
import time
import random
import machine
from pimoroni import Button, RGBLED
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY, PEN_P8

global SCREEN_WIDTH,SCREEN_HEIGHT

# Turn of the RGB LED
led = RGBLED(6, 7, 8)
led.set_rgb(0, 0, 0)

display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, pen_type=PEN_P8)
display.set_backlight(1.0)

WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)

right = Button(12)
left = Button(13)
right2 = Button(14)
left2 = Button(15)

SCREEN_WIDTH, SCREEN_HEIGHT = display.get_bounds()

# Game parameters
BALL_SIZE = int(SCREEN_WIDTH/28)         # size of the ball size in pixels
PADDLE_WIDTH = int(SCREEN_WIDTH/4)       # size of the paddle in pixels
PADDLE_HEIGHT = int(SCREEN_HEIGHT/36)
PADDLE_Y = SCREEN_HEIGHT-2*PADDLE_HEIGHT # Vertical position of the paddle

# variables
ballX = 64     # ball position in pixels
ballY = 0
ballVX = 1.0    # ball velocity along x in pixels per frame
ballVY = 1.0    # ball velocity along y in pixels per frame

paddleX = int(SCREEN_WIDTH/2) # paddle  position in pixels
paddleVX = 6                  # paddle velocity in pixels per frame

score = 0

def game_reset():
    global paddleX, ballX, ballY, ballVX, ballVY, score
    paddleX = (SCREEN_WIDTH - PADDLE_WIDTH) // 2
    ballX = SCREEN_WIDTH // 2
    ballY = SCREEN_HEIGHT // 2
    ballVX = random.choice([-2, 2])
    ballVY = -2
    score = 0

game_reset()

prev_paddleX = paddleX
prev_ballX = ballX
prev_ballY = ballY

while True:
    # move the paddle when a button is pressed
    if right.read() or right2.read():
        # right button pressed
        paddleX += paddleVX
        if paddleX + PADDLE_WIDTH > SCREEN_HEIGHT:
            paddleX = SCREEN_HEIGHT - PADDLE_WIDTH
    elif left.read() or left2.read():
        # left button pressed
        paddleX -= paddleVX
        if paddleX < 0:
            paddleX = 0
    
    # move the ball
    if abs(ballVX) < 1:
        # do not allow an infinite vertical trajectory for the ball
        ballVX = 1

    ballX = int(ballX + ballVX)
    ballY = int(ballY + ballVY)
    
    # collision detection
    collision=False
    if ballX < 0:
        # collision with the left edge of the screen 
        ballX = 0
        ballVX = -ballVX
        collision = True
    
    if ballX + BALL_SIZE > SCREEN_WIDTH:
        # collision with the right edge of the screen
        ballX = SCREEN_WIDTH-BALL_SIZE
        ballVX = -ballVX
        collision = True

    if ballY+BALL_SIZE>PADDLE_Y and ballX > paddleX-BALL_SIZE and ballX<paddleX+PADDLE_WIDTH+BALL_SIZE:
        # collision with the paddle
        # => change ball direction
        ballVY = -ballVY
        ballY = PADDLE_Y-BALL_SIZE
        # increase speed!
        ballVY -= 0.2
        ballVX += (ballX - (paddleX + PADDLE_WIDTH/2))/10
        collision = True
        score += 10
        
    if ballY < 0:
        # collision with the top of the screen
        ballY = 0
        ballVY = -ballVY
        collision = True
        
    if ballY + BALL_SIZE > SCREEN_HEIGHT:
        # collision with the bottom of the screen
        # => Display Game Over
        display.set_pen(WHITE)
        display.clear()
        display.update()
        display.set_pen(BLACK)
        display.text("GAME OVER", int(SCREEN_WIDTH/2)-int(len("Game Over!")/2 * 10), int(SCREEN_HEIGHT/2) - 8)
        display.text(str(score), int(SCREEN_HEIGHT/2) - 5, 0)
        display.update()
        # wait for a button
        while True:
            if right.read():
                game_reset()
                break
            elif left.read():
                game_reset()
                break
            elif right2.read():
                game_reset()
                break
            elif left2.read():
                game_reset()
                break
            time.sleep(0.001)
        
    # clear the screen
    display.set_pen(WHITE)
    display.clear()
    
    # display the paddle
    display.set_pen(BLACK)
    display.rectangle(paddleX, PADDLE_Y, PADDLE_WIDTH, PADDLE_HEIGHT)
        
    # display the ball
    display.rectangle(ballX, ballY, BALL_SIZE, BALL_SIZE)
    
    # display the score
    display.text(str(score), int(SCREEN_HEIGHT/2) - 5, 0)
    
    display.update()
    
    time.sleep(0.001)
