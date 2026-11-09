"""Shared visual design: Minecraft-Education-themed plates, frames, title & credit cards."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
FONTS = "/home/user/work/fonts/"
PIX = FONTS + "PressStart2P.ttf"
SILK = FONTS + "Silkscreen-Bold.ttf"
MB = FONTS + "Montserrat-700.ttf"
MXB = FONTS + "Montserrat-800.ttf"
MSB = FONTS + "Montserrat-600.ttf"

GREEN = (94, 168, 52)
GREEN_L = (126, 204, 72)
DIRT = (134, 96, 67)
DIRT_D = (89, 61, 41)
SKY = (120, 180, 240)
YELLOW = (255, 214, 64)
WHITE = (255, 255, 255)
DARK = (22, 26, 20)

# gameplay window in the 1920x1080 canvas (source 1728x1080 scaled to 1472x920)
GX, GY, GW, GH = 224, 14, 1472, 920
SCALE = GW / 1728.0
# teacher inset & facecam circle in SOURCE pixels
INSET = (13, 802, 511, 1080)
PLATE_SRC = "/home/user/work/test/raw_990.png"
PLATE_CROP = (470, 120, 1350, 615)


def font(path, size):
    return ImageFont.truetype(path, size)


def plate(size, blur=2.0, darken=0.0):
    """Clean Minecraft scenery from the author's own world (Misi Penyelamat Ayat)."""
    im = Image.open(PLATE_SRC).convert("RGB").crop(PLATE_CROP)
    tw, th = size
    r = max(tw / im.width, th / im.height)
    im = im.resize((int(im.width * r + 1), int(im.height * r + 1)), Image.LANCZOS)
    l, t = (im.width - tw) // 2, (im.height - th) // 2
    im = im.crop((l, t, l + tw, t + th))
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    if darken:
        im = Image.blend(im, Image.new("RGB", size, (0, 0, 0)), darken)
    return im


def _tile(kind, seed):
    rng = np.random.default_rng(seed)
    t = np.zeros((16, 16, 3), np.float32)
    if kind == "grass":
        base = np.array(DIRT, np.float32)
        t[:] = base
        n = rng.integers(-18, 18, (16, 16, 1))
        t += n
        g = np.array(GREEN, np.float32)
        depth = 4 + rng.integers(0, 3, 16)
        for x in range(16):
            t[: depth[x], x] = g + rng.integers(-16, 16, (depth[x], 1))
    elif kind == "dirt":
        t[:] = np.array(DIRT, np.float32) + rng.integers(-20, 20, (16, 16, 1))
        for _ in range(10):
            x, y = rng.integers(0, 16, 2)
            t[y, x] = DIRT_D
    elif kind == "stone":
        t[:] = 125 + rng.integers(-18, 18, (16, 16, 1))
    return Image.fromarray(np.clip(t, 0, 255).astype(np.uint8))


def block(kind, px, seed=0):
    return _tile(kind, seed).resize((px, px), Image.NEAREST)


def ground_strip(width, px=64, rows=2, seed=1):
    im = Image.new("RGB", (width, px * rows))
    for r in range(rows):
        for i in range(width // px + 1):
            im.paste(block("grass" if r == 0 else "dirt", px, seed + i * 7 + r * 131), (i * px, r * px))
    return im


def pixel_frame(draw, box, color=DARK, inner=GREEN, t=6):
    """Blocky double border like Minecraft UI panels."""
    x0, y0, x1, y1 = box
    draw.rectangle(box, outline=color, width=t)
    draw.rectangle((x0 + t, y0 + t, x1 - t, y1 - t), outline=inner, width=t)


def shadow_text(draw, xy, text, fnt, fill=WHITE, shadow=(40, 30, 20), off=6, anchor="mm"):
    x, y = xy
    draw.text((x + off, y + off), text, font=fnt, fill=shadow, anchor=anchor)
    draw.text((x, y), text, font=fnt, fill=fill, anchor=anchor)


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


# ---------------------------------------------------------------- title card
TITLE_DUR = 9.0


def title_frame(t, bg=None):
    """Opening title, t in seconds (0..TITLE_DUR)."""
    if bg is None:
        bg = plate((W, H), blur=7, darken=0.35)
    # slow push-in
    z = 1.0 + 0.04 * (t / TITLE_DUR)
    bw, bh = int(W * z), int(H * z)
    im = bg.resize((bw, bh), Image.BILINEAR).crop(((bw - W) // 2, (bh - H) // 2, (bw - W) // 2 + W, (bh - H) // 2 + H))
    im = im.convert("RGBA")
    d = ImageDraw.Draw(im)

    # blocks rising from the bottom
    gs = ground_strip(W, 72, 2)
    rise = ease(t / 1.0)
    im.paste(gs, (0, H - int(144 * rise)))

    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    a = ease((t - 0.5) / 0.8)
    if a > 0:
        pw, ph = 1500, 560
        px, py = (W - pw) // 2, 150 + int((1 - a) * 40)
        od.rectangle((px, py, px + pw, py + ph), fill=(16, 20, 14, int(200 * a)))
        pixel_frame(od, (px, py, px + pw, py + ph), color=(0, 0, 0, int(255 * a)), inner=GREEN + (int(255 * a),), t=8)
    im = Image.alpha_composite(im, ov)
    d = ImageDraw.Draw(im)

    def fade(start, dur=0.6):
        return ease((t - start) / dur)

    cx = W // 2
    if fade(0.9) > 0:
        al = fade(0.9)
        f = font(SILK, 44)
        d.text((cx, 235), "VIDEO PENERANGAN", font=f, fill=YELLOW + (int(255 * al),), anchor="mm")
    if fade(1.3) > 0:
        al = fade(1.3)
        f = font(MXB, 50)
        d.text((cx + 3, 318 + 3), "CARA BERMAIN DUNIA MINECRAFT EDUCATION", font=f, fill=(0, 0, 0, int(200 * al)), anchor="mm")
        d.text((cx, 318), "CARA BERMAIN DUNIA MINECRAFT EDUCATION", font=f, fill=WHITE + (int(255 * al),), anchor="mm")
    # main title: letters drop in like blocks
    title = "MISI PENYELAMAT AYAT"
    f = font(PIX, 64)
    total = d.textlength(title, font=f)
    x = cx - total / 2
    for i, ch in enumerate(title):
        lt = (t - 1.8 - i * 0.05) / 0.35
        cw = d.textlength(ch, font=f)
        if lt > 0 and ch != " ":
            e = ease(lt)
            y = 445 - int((1 - e) * 120)
            al = int(255 * min(1, lt * 2))
            d.text((x + 7, y + 7), ch, font=f, fill=(60, 40, 20, al), anchor="lm")
            d.text((x, y), ch, font=f, fill=GREEN_L + (al,), anchor="lm")
        x += cw
    if fade(3.4) > 0:
        al = int(255 * fade(3.4))
        d.line((cx - 420, 525, cx + 420, 525), fill=YELLOW + (al,), width=4)
        d.text((cx, 572), "MOHAMAD ALIFF BIN AHMAD SHAHABUDDIN", font=font(MXB, 38), fill=WHITE + (al,), anchor="mm")
    if fade(3.9) > 0:
        al = int(255 * fade(3.9))
        d.text((cx, 630), "INSTITUT PENDIDIKAN GURU KAMPUS TUN HUSSEIN ONN", font=font(MSB, 30), fill=(230, 230, 230, al), anchor="mm")
        d.text((cx, 674), "EDUP3133: TEKNOLOGI UNTUK PENGAJARAN DAN PEMBELAJARAN", font=font(MSB, 28), fill=YELLOW + (al,), anchor="mm")
    # fade out to intro
    out = ease((t - (TITLE_DUR - 0.7)) / 0.7)
    if out > 0:
        im = Image.blend(im, Image.new("RGBA", (W, H), (0, 0, 0, 255)), out)
    return im.convert("RGB")


# ---------------------------------------------------------------- credits card
CRED_DUR = 12.0


def credits_frame(t, bg=None):
    if bg is None:
        bg = plate((W, H), blur=7, darken=0.35)
    im = bg.copy().convert("RGBA")
    im.paste(ground_strip(W, 72, 2, seed=5), (0, H - 144))
    a0 = ease(t / 0.8)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    pw, ph = 1440, 600
    px, py = (W - pw) // 2, 150
    od.rectangle((px, py, px + pw, py + ph), fill=(16, 20, 14, int(205 * a0)))
    pixel_frame(od, (px, py, px + pw, py + ph), color=(0, 0, 0, int(255 * a0)), inner=YELLOW + (int(255 * a0),), t=8)
    im = Image.alpha_composite(im, ov)
    d = ImageDraw.Draw(im)
    cx = W // 2

    def al(s):
        return int(255 * ease((t - s) / 0.7))

    d.text((cx + 6, 262 + 6), "SETINGGI-TINGGI PENGHARGAAN", font=font(PIX, 46), fill=(60, 40, 20, al(0.5)), anchor="mm")
    d.text((cx, 262), "SETINGGI-TINGGI PENGHARGAAN", font=font(PIX, 46), fill=YELLOW + (al(0.5),), anchor="mm")
    d.text((cx, 352), "kepada pensyarah yang dihormati", font=font(MSB, 36), fill=(235, 235, 235, al(1.2)), anchor="mm")
    d.text((cx + 3, 440 + 3), "PUAN JULINA BINTI TARIKAT", font=font(MXB, 62), fill=(0, 0, 0, al(1.8)), anchor="mm")
    d.text((cx, 440), "PUAN JULINA BINTI TARIKAT", font=font(MXB, 62), fill=GREEN_L + (al(1.8),), anchor="mm")
    d.line((cx - 380, 505, cx + 380, 505), fill=YELLOW + (al(2.3),), width=4)
    d.text((cx, 562), "Pensyarah EDUP3133: Teknologi untuk Pengajaran dan Pembelajaran", font=font(MSB, 32), fill=WHITE + (al(2.6),), anchor="mm")
    d.text((cx, 618), "Institut Pendidikan Guru Kampus Tun Hussein Onn", font=font(MSB, 32), fill=WHITE + (al(3.0),), anchor="mm")
    d.text((cx, 690), "Disediakan oleh: MOHAMAD ALIFF BIN AHMAD SHAHABUDDIN", font=font(MB, 26), fill=YELLOW + (al(3.6),), anchor="mm")
    out = ease((t - (CRED_DUR - 1.2)) / 1.2)
    if out > 0:
        im = Image.blend(im, Image.new("RGBA", (W, H), (0, 0, 0, 255)), out)
    return im.convert("RGB")


# ---------------------------------------------------------------- main layout chrome
def chrome_bg():
    """Static canvas behind the gameplay window: blurred scenery + grass blocks + frame."""
    im = plate((W, H), blur=14, darken=0.55).convert("RGBA")
    im.paste(ground_strip(W, 48, 3, seed=9), (0, H - 144))
    dk = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dk)
    dd.rectangle((0, H - 144, W, H), fill=(0, 0, 0, 150))  # keep subtitle band readable
    im = Image.alpha_composite(im, dk)
    d = ImageDraw.Draw(im)
    pixel_frame(d, (GX - 12, GY - 6, GX + GW + 11, GY + GH + 11), color=(0, 0, 0), inner=GREEN, t=6)
    return im.convert("RGB")


def side_label(im, text_top, text_bottom=None):
    d = ImageDraw.Draw(im)
    f = font(SILK, 22)
    x = GX // 2
    d.text((x, 60), "MISI", font=f, fill=YELLOW, anchor="mm")
    d.text((x, 88), "PENYELAMAT", font=f, fill=YELLOW, anchor="mm")
    d.text((x, 116), "AYAT", font=f, fill=YELLOW, anchor="mm")
    y = 190
    for line in text_top.split("\n"):
        d.text((x, y), line, font=font(SILK, 20), fill=WHITE, anchor="mm")
        y += 28


def speed_badge(im, speed):
    d = ImageDraw.Draw(im)
    x = GX + GW + (W - GX - GW) // 2
    d.rectangle((x - 70, 40, x + 70, 96), fill=(16, 20, 14), outline=YELLOW, width=4)
    d.text((x, 68), f">> {speed:.1f}x", font=font(SILK, 24), fill=YELLOW, anchor="mm")
