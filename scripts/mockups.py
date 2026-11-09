import sys, numpy as np, onnxruntime as ort
from PIL import Image, ImageDraw
sys.path.insert(0, "/home/user/work/scripts")
from design import *

sess = ort.InferenceSession("/home/user/work/models/rvm_resnet50_fp32.onnx", providers=["CPUExecutionProvider"])


def matte(img, ratio):
    x = np.asarray(img).astype(np.float32).transpose(2, 0, 1)[None] / 255.0
    rec = [np.zeros((1, 1, 1, 1), np.float32)] * 4
    for _ in range(4):
        fgr, pha, *rec = sess.run(None, {"src": x, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3],
                                        "downsample_ratio": np.array([ratio], np.float32)})
    return pha[0, 0]


def comp(fg, alpha, bg):
    a = alpha[..., None]
    return Image.fromarray((np.asarray(fg).astype(np.float32) * a + np.asarray(bg).astype(np.float32) * (1 - a)).astype(np.uint8))


def subtitle(im, parts, y=H - 72):
    """parts: list of (text, color). Emulates the ASS style used in the final render."""
    d = ImageDraw.Draw(im)
    f = font(MB, 40)
    total = sum(d.textlength(t, font=f) for t, c in parts)
    x = (W - total) / 2
    for t, c in parts:
        d.text((x, y), t, font=f, fill=c, stroke_width=4, stroke_fill=(0, 0, 0), anchor="lm")
        x += d.textlength(t, font=f)


def replace_inset(frame, alpha_png=None):
    ins = frame.crop(INSET)
    a = np.asarray(Image.open(alpha_png)).astype(np.float32) / 255 if alpha_png else matte(ins, 0.6)
    bg = plate(ins.size, blur=2.5)
    new = comp(ins, a, bg)
    frame = frame.copy()
    frame.paste(new, INSET[:2])
    d = ImageDraw.Draw(frame)
    pixel_frame(d, (INSET[0] - 2, INSET[1] - 2, INSET[2] + 1, INSET[3] - 1), color=(0, 0, 0), inner=GREEN, t=5)
    return frame


out = "/home/user/claude-vid-tek2/storyboard/"
import os; os.makedirs(out, exist_ok=True)

# 1 title
title_frame(7.5).save(out + "mockup_1_tajuk.jpg", quality=90)

# 2 intro teacher, background replaced
src = Image.open("/home/user/work/test/raw_14.png").convert("RGB")
a = matte(src, 0.25)
a[860:, :640] = 0  # remove leftover bag from the original cut-out
canvas = plate((W, H), blur=5)
fg = Image.new("RGB", (W, H)); fg.paste(src, (192, 0))
al = np.zeros((H, W), np.float32); al[:, 192:192 + 1728] = a
im = comp(fg, al, canvas)
d = ImageDraw.Draw(im)
# lower third
d.rectangle((90, 760, 900, 880), fill=(16, 20, 14))
pixel_frame(d, (90, 760, 900, 880), color=(0, 0, 0), inner=GREEN, t=5)
d.text((120, 800), "MOHAMAD ALIFF BIN AHMAD SHAHABUDDIN", font=font(MXB, 30), fill=WHITE, anchor="lm")
d.text((120, 845), "Penyedia  |  IPG Kampus Tun Hussein Onn", font=font(MSB, 24), fill=YELLOW, anchor="lm")
subtitle(im, [("Pada hari ini, saya, ", WHITE), ("Mohamad Aliff bin Ahmad Shahabuddin", YELLOW), (", akan menunjukkan...", WHITE)])
im.save(out + "mockup_2_intro_guru.jpg", quality=90)

# 3 gameplay layout
fr = Image.open("/home/user/work/test/raw_g.png").convert("RGB")
fr.paste(Image.open("/home/user/work/test/m_src.png"), INSET[:2])
fr = replace_inset(fr, "/home/user/work/test/m_resne_0.4.png")
im = chrome_bg()
im.paste(fr.resize((GW, GH), Image.LANCZOS), (GX, GY))
side_label(im, "BAHAGIAN 1\nJENIS 1\nAYAT TANPA\nSUBJEK")
subtitle(im, [("Pada jenis yang pertama ini, pemain perlu memilih ", WHITE), ("blok warna", GREEN_L)], y=H - 92)
subtitle(im, [("untuk memilih ", WHITE), ("jawapan yang betul", YELLOW), (".", WHITE)], y=H - 42)
im.save(out + "mockup_3_gameplay.jpg", quality=90)

# 3b silent part sped up
fr = Image.open("/home/user/work/test/raw_s.png").convert("RGB")
fr = replace_inset(fr)
im = chrome_bg()
im.paste(fr.resize((GW, GH), Image.LANCZOS), (GX, GY))
side_label(im, "BAHAGIAN 1\nJENIS 3\nBAHASA\nROJAK")
speed_badge(im, 1.5)
im.save(out + "mockup_4_senyap_1.5x.jpg", quality=90)

# 4 credits
credits_frame(8).save(out + "mockup_5_penghargaan.jpg", quality=90)
print("done")
