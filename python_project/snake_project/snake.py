import turtle
import time
import random

# Setup screen
wn = turtle.Screen()
wn.title("Snake Game with Wrap-Around")
wn.bgcolor("black")
wn.setup(width=600, height=600)
wn.tracer(0)

# Snake head
head = turtle.Turtle()
head.speed(0)
head.shape("square")
head.color("green")
head.penup()
head.goto(0, 0)
head.direction = "stop"

# Food
food = turtle.Turtle()
food.speed(0)
food.shape("circle")
food.color("red")
food.penup()
food.goto(0, 100)

# Snake body segments
segments = []

# Movement functions
def go_up():
    if head.direction != "down":
        head.direction = "up"
def go_down():
    if head.direction != "up":
        head.direction = "down"
def go_left():
    if head.direction != "right":
        head.direction = "left"
def go_right():
    if head.direction != "left":
        head.direction = "right"

def move():
    x = head.xcor()
    y = head.ycor()

    if head.direction == "up":
        y += 20
    if head.direction == "down":
        y -= 20
    if head.direction == "left":
        x -= 20
    if head.direction == "right":
        x += 20

    # Wrap-around logic
    if x > 290:
        x = -290
    if x < -290:
        x = 290
    if y > 290:
        y = -290
    if y < -290:
        y = 290

    head.goto(x, y)

# Keyboard bindings
wn.listen()
wn.onkey(go_up, "w")
wn.onkey(go_down, "s")
wn.onkey(go_left, "a")
wn.onkey(go_right, "d")

# Main game loop
while True:
    wn.update()

    # Check collision with food
    if head.distance(food) < 20:
        # Move food to random spot
        x = random.randint(-290, 290)//20*20
        y = random.randint(-290, 290)//20*20
        food.goto(x, y)

        # Add segment
        new_segment = turtle.Turtle()
        new_segment.speed(0)
        new_segment.shape("square")
        new_segment.color("green")
        new_segment.penup()
        segments.append(new_segment)

    # Move the end segments first
    for i in range(len(segments)-1, 0, -1):
        segments[i].goto(segments[i-1].xcor(), segments[i-1].ycor())
    if segments:
        segments[0].goto(head.xcor(), head.ycor())

    move()

    # Check collision with self
    for segment in segments:
        if head.distance(segment) < 20:
            print("Game Over!")
            time.sleep(2)
            exit()

    time.sleep(0.1)

wn.mainloop()
