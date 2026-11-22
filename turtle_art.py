"""Turtle graphics for MedTimer.

Draws the reward artwork the app shows when adherence is high:
a smiley (weekly score >= 80%) and a trophy (a perfect 100% week).

Each drawing is rendered to a PostScript file and converted to PNG
so Streamlit can display it. Run this file directly to regenerate
the PNGs in assets/.
"""
import os
import subprocess
import turtle

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def _new_screen(width=480, height=480, bg="white"):
    screen = turtle.Screen()
    screen.setup(width, height)
    screen.bgcolor(bg)
    screen.tracer(0, 0)  # no animation; draw instantly
    t = turtle.Turtle(visible=False)
    t.speed(0)
    return screen, t


def _fill_circle(t, x, y, radius, color):
    t.penup()
    t.goto(x, y - radius)
    t.pendown()
    t.color(color)
    t.begin_fill()
    t.circle(radius)
    t.end_fill()


def _save(screen, name):
    """Export the canvas to a PNG inside assets/."""
    os.makedirs(ASSETS, exist_ok=True)
    ps_path = os.path.join(ASSETS, name + ".ps")
    png_path = os.path.join(ASSETS, name + ".png")
    screen.getcanvas().postscript(file=ps_path, colormode="color")
    subprocess.run(
        ["gs", "-dQUIET", "-dBATCH", "-dNOPAUSE",
         "-sDEVICE=pngalpha", "-r150", "-o", png_path, ps_path],
        check=True,
    )
    os.remove(ps_path)
    return png_path


def draw_smiley(screen):
    """A big friendly smiley for a good week (score >= 80%)."""
    t = turtle.Turtle(visible=False)
    t.speed(0)
    _fill_circle(t, 0, 0, 110, "#FFD93D")          # face
    _fill_circle(t, -40, 45, 14, "#3B3B3B")        # left eye
    _fill_circle(t, 40, 45, 14, "#3B3B3B")         # right eye
    _fill_circle(t, -70, 10, 13, "#FFB3A7")        # left cheek
    _fill_circle(t, 70, 10, 13, "#FFB3A7")         # right cheek
    # smile: a thick arc along the lower half of the face
    t.penup()
    t.goto(-50, -10)
    t.setheading(-60)
    t.pensize(8)
    t.pencolor("#3B3B3B")
    t.pendown()
    t.circle(58, 120)
    screen.update()
    return _save(screen, "smiley")


def draw_trophy(screen):
    """A trophy for a perfect week (score == 100%)."""
    t = turtle.Turtle(visible=False)
    t.speed(0)

    def poly(points, color):
        t.penup()
        t.goto(points[0])
        t.setheading(0)
        t.color(color)
        t.pendown()
        t.begin_fill()
        for p in points[1:]:
            t.goto(p)
        t.goto(points[0])
        t.end_fill()

    # handles: rings on both sides, inner half hidden behind the cup
    for side in (-1, 1):
        t.penup()
        t.goto(88 * side, 10)
        t.setheading(90)
        t.pensize(14)
        t.pencolor("#D99900")
        t.pendown()
        t.circle(40)

    # cup body: trapezoid, wide at the top
    t.pensize(1)
    poly([(-72, 80), (72, 80), (42, -15), (-42, -15)], "#F4B400")
    # stem and base
    poly([(-16, -15), (16, -15), (16, -58), (-16, -58)], "#D99900")
    poly([(-52, -58), (52, -58), (52, -78), (-52, -78)], "#D99900")
    # star on the cup
    t.penup()
    t.goto(0, 48)
    t.setheading(-18)
    t.color("white")
    t.pendown()
    t.begin_fill()
    for _ in range(5):
        t.forward(42)
        t.right(144)
    t.end_fill()
    screen.update()
    return _save(screen, "trophy")


if __name__ == "__main__":
    screen, _ = _new_screen()
    print("smiley ->", draw_smiley(screen))
    screen.clear()
    print("trophy ->", draw_trophy(screen))
    os._exit(0)  # skip turtle's atexit mainloop
