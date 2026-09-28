"""
Draws the stadium background for Wave the Wheat as two 1280x720 PNGs:

  stadium_sky.png      the night sky on its own
  stadium_seating.png  light towers, a crimson ribbon board, then rows of blue and
                       crimson seats, with a transparent sky so TD can put the
                       fireworks between the two layers

Seats get bigger toward the bottom of the frame, split by aisles that lean toward a
vanishing point above the screen. Softened slightly so the user and fans in front
stay sharp.

Run with: td_mediapipe_env/bin/python3 stadium/make_stadium.py
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1280, 720
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "stadium_seating.png")
OUT_SKY = os.path.join(HERE, "stadium_sky.png")
FONT = os.path.expanduser("~/Library/Fonts/Gotham-Black.otf")

KU_BLUE = (0, 81, 186)
KU_CRIMSON = (232, 0, 13)
SEAT_BLUE_DARK = (0, 52, 125)
SEAT_CRIMSON_DARK = (150, 0, 10)
CONCRETE = (150, 150, 158)
CONCRETE_DARK = (95, 95, 104)

SKY_BOTTOM = 250
RIBBON_TOP, RIBBON_BOTTOM = 250, 296
SEATS_TOP = 304
TOWER_TOP = 110
VANISH = (W / 2, -700)          # aisles lean toward this point
AISLE_X_AT_BOTTOM = [-620, -340, -60, 220, 500, 780, 1060, 1340, 1620, 1900]
AISLE_HALF_AT_BOTTOM = 20


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_col(a, b, t):
    return tuple(int(lerp(x, y, t)) for x, y in zip(a, b))


def aisle_x(x_bottom, y):
    """x of an aisle line at height y, leaning toward the vanishing point."""
    t = (y - VANISH[1]) / (H - VANISH[1])
    return lerp(VANISH[0], x_bottom, t)


def draw_sky(img):
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = min(1.0, y / SKY_BOTTOM)
        d.line([(0, y), (W, y)], fill=lerp_col((6, 10, 32), (24, 40, 88), t))


def draw_towers(img):
    # light towers: a soft glow layer, then the rigs on top
    top = TOWER_TOP
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    towers = [150, 470, 810, 1130]
    for x in towers:
        gd.ellipse([x - 110, top - 64, x + 110, top + 116], fill=(255, 245, 210, 110))
    glow = glow.filter(ImageFilter.GaussianBlur(38))
    img.alpha_composite(glow)
    d = ImageDraw.Draw(img)
    for x in towers:
        d.rectangle([x - 4, top + 36, x + 4, SKY_BOTTOM], fill=(40, 44, 60))
        d.rectangle([x - 52, top, x + 52, top + 38], fill=(40, 44, 60))
        for r in range(3):
            for c in range(7):
                cx, cy = x - 42 + c * 14, top + 8 + r * 11
                d.ellipse([cx - 5, cy - 4, cx + 5, cy + 4], fill=(255, 250, 225))


def draw_ribbon(img):
    d = ImageDraw.Draw(img)
    d.rectangle([0, RIBBON_TOP - 4, W, RIBBON_BOTTOM + 4], fill=(20, 20, 26))
    d.rectangle([0, RIBBON_TOP, W, RIBBON_BOTTOM], fill=KU_CRIMSON)
    d.rectangle([0, RIBBON_TOP, W, RIBBON_TOP + 3], fill=(255, 90, 90))
    font = ImageFont.truetype(FONT, 26)
    text = "ROCK CHALK  •  JAYHAWK  •  KANSAS FOOTBALL  •  "
    x = -40
    while x < W:
        d.text((x, (RIBBON_TOP + RIBBON_BOTTOM) / 2), text, font=font, fill=(255, 255, 255), anchor="lm")
        x += d.textlength(text, font=font)


def row_edges():
    """Top y of each seating row. Rows grow toward the bottom (closer to the camera)."""
    edges, y, h = [], SEATS_TOP, 13.0
    while y < H:
        edges.append(y)
        y += h
        h *= 1.075
    edges.append(y)
    return edges


def draw_seats(img):
    d = ImageDraw.Draw(img)
    edges = row_edges()
    for i in range(len(edges) - 1):
        y0, y1 = edges[i], edges[i + 1]
        rh = y1 - y0
        riser = y0 + rh * 0.62
        # concrete step the row sits on
        d.rectangle([0, y0, W, y1], fill=CONCRETE)
        d.rectangle([0, riser, W, y1], fill=CONCRETE_DARK)
        seat_w = rh * 1.05
        gap = rh * 0.18
        # sections between aisles alternate blue / crimson
        for s in range(len(AISLE_X_AT_BOTTOM) - 1):
            ym = (y0 + y1) / 2
            left = aisle_x(AISLE_X_AT_BOTTOM[s], ym) + AISLE_HALF_AT_BOTTOM * (ym - VANISH[1]) / (H - VANISH[1])
            right = aisle_x(AISLE_X_AT_BOTTOM[s + 1], ym) - AISLE_HALF_AT_BOTTOM * (ym - VANISH[1]) / (H - VANISH[1])
            crimson = s % 2 == 1
            face = KU_CRIMSON if crimson else KU_BLUE
            shade = SEAT_CRIMSON_DARK if crimson else SEAT_BLUE_DARK
            x = left + gap
            while x + seat_w < right - gap:
                back_top = y0 + rh * 0.05
                d.rounded_rectangle([x, back_top, x + seat_w, riser], radius=max(2, rh * 0.18), fill=face)
                d.rectangle([x, riser - rh * 0.14, x + seat_w, riser + rh * 0.08], fill=shade)
                x += seat_w + gap
        # stairs in the aisles
        for xb in AISLE_X_AT_BOTTOM:
            ym = (y0 + y1) / 2
            half = AISLE_HALF_AT_BOTTOM * (ym - VANISH[1]) / (H - VANISH[1])
            cx = aisle_x(xb, ym)
            d.rectangle([cx - half, y0, cx + half, y1], fill=(120, 120, 128))
            d.rectangle([cx - half, y0, cx + half, y0 + max(1, rh * 0.1)], fill=(235, 190, 40))
    # front railing along the top of the seating
    d.rectangle([0, SEATS_TOP - 8, W, SEATS_TOP], fill=(60, 64, 76))


def main():
    sky = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    draw_sky(sky)
    sky.convert("RGB").save(OUT_SKY)
    print("wrote", OUT_SKY)

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_towers(img)
    draw_ribbon(img)
    draw_seats(img)
    # soften and dim a touch so the user and the fans read as the foreground
    img = img.filter(ImageFilter.GaussianBlur(1.6))
    dimmed = Image.alpha_composite(img, Image.new("RGBA", (W, H), (0, 0, 20, 45)))
    dimmed.putalpha(img.getchannel("A"))   # dim the stadium without filling in the sky
    dimmed.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
