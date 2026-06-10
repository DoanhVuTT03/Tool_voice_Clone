# -*- coding: utf-8 -*-
"""Tao logo + app.ico thuong hieu: Doanhbadboiz (Vu Duc Doanh).
Chu de: mic + song am (voice cloning). Mau gradient tim -> xanh."""
import numpy as np
from PIL import Image, ImageDraw

S = 1024
CX = S // 2


def gradient_bg():
    ys = np.linspace(0, 1, S)[:, None]
    top = np.array([124, 58, 237], dtype=float)   # violet
    bot = np.array([37, 99, 235], dtype=float)     # blue
    rgb = top[None, :] * (1 - ys) + bot[None, :] * ys      # (S,3)
    arr = np.repeat(rgb[:, None, :], S, axis=1).astype(np.uint8)  # (S,S,3)
    return Image.fromarray(arr, "RGB").convert("RGBA")


def make_master():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    grad = gradient_bg()
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1],
                                           radius=int(S * 0.23), fill=255)
    img.paste(grad, (0, 0), mask)

    d = ImageDraw.Draw(img)
    white = (255, 255, 255, 255)
    soft = (255, 255, 255, 90)

    # song am hai ben (equalizer)
    bar_w = 26
    heights = [120, 210, 300, 210, 120]
    for side in (-1, 1):
        base_x = CX + side * 250
        for i, h in enumerate(heights):
            x = base_x + side * i * (bar_w + 16) - bar_w // 2
            y0, y1 = CX - h // 2, CX + h // 2
            d.rounded_rectangle([x, y0, x + bar_w, y1], radius=bar_w // 2, fill=soft)

    # than mic (capsule)
    mw = 150
    d.rounded_rectangle([CX - mw, 250, CX + mw, 560], radius=mw, fill=white)
    # khe grille
    for gy in range(300, 521, 55):
        d.line([CX - mw + 30, gy, CX + mw - 30, gy], fill=(124, 58, 237, 130), width=10)

    # vong giu mic (arc)
    d.arc([CX - 215, 300, CX + 215, 640], start=25, end=155, fill=white, width=34)
    # chan + de
    d.rounded_rectangle([CX - 20, 640, CX + 20, 760], radius=20, fill=white)
    d.rounded_rectangle([CX - 130, 770, CX + 130, 812], radius=21, fill=white)
    return img


def main():
    img = make_master()
    img.save("logo.png")
    # icon nhieu kich co (Windows tu chon size phu hop)
    img.save("app.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                               (64, 64), (128, 128), (256, 256)])
    print("Da tao: logo.png + app.ico")


if __name__ == "__main__":
    main()
