"""Stage 2: final composition on the output timeline + encode with burned-in subtitles and the final audio.

usage: stage2_video.py OUT.mp4 [max_output_seconds]
"""
import json, subprocess, sys, os, glob, time
import numpy as np, cv2
from PIL import Image, ImageDraw
sys.path.insert(0, "/home/user/work/scripts")
import design as D

OUTF = sys.argv[1]
LIMIT = float(sys.argv[2]) if len(sys.argv) > 2 else None
SRC = "/home/user/work/src/original.mp4"
WD = "/home/user/work/"
FPS = 30
TITLE, CRED = D.TITLE_DUR, D.CRED_DUR
SW, SH = 1728, 1080
INTRO_END = 725
LAST = int(1101.27 * 30)
rows = json.load(open(WD + "map.json"))
MAIN = rows[-1][5]
TOTAL = TITLE + MAIN + CRED
if LIMIT:
    TOTAL = min(TOTAL, LIMIT)
NFR = int(round(TOTAL * FPS))

CHAPTERS = [  # source seconds -> side label
    (24.17, "PERMULAAN\n&\nLOBI UTAMA"),
    (146.9, "BAHAGIAN 1\n\nJENIS 1\nAYAT TANPA\nSUBJEK"),
    (321.2, "BAHAGIAN 1\n\nJENIS 2\nAYAT TIDAK\nLENGKAP"),
    (698.4, "BAHAGIAN 1\n\nJENIS 3\nBAHASA\nROJAK"),
    (816.0, "BAHAGIAN 1\n\nKAWASAN\nPEMENANG"),
    (851.0, "BAHAGIAN 2\n\nEKSPEDISI\nAYAT"),
    (1004.0, "CABARAN\nAKHIR"),
    (1066.0, "KEPUTUSAN\n&\nPINGAT"),
]


def chapter(t):
    c = CHAPTERS[0][1]
    for s, name in CHAPTERS:
        if t >= s:
            c = name
    return c


def src_time(tau):
    """output main-timeline seconds -> (source seconds, speed)"""
    for a, b, s, k, oa, ob in rows:
        if tau < ob:
            return a + (tau - oa) * s, s
    a, b, s, k, oa, ob = rows[-1]
    return b, s


_chrome = D.chrome_bg()
_cache = {}


def chrome(label, speed):
    key = (label, speed)
    if key not in _cache:
        im = _chrome.copy()
        D.side_label(im, label)
        if speed:
            D.speed_badge(im, speed)
        _cache[key] = np.asarray(im).copy()
    return _cache[key]


def lower_third(alpha):
    im = Image.new("RGBA", (D.W, D.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    a = int(255 * alpha)
    d.rectangle((90, 760, 900, 880), fill=(16, 20, 14, int(235 * alpha)))
    D.pixel_frame(d, (90, 760, 900, 880), color=(0, 0, 0, a), inner=D.GREEN + (a,), t=5)
    d.text((120, 800), "MOHAMAD ALIFF BIN AHMAD SHAHABUDDIN", font=D.font(D.MXB, 30), fill=D.WHITE + (a,), anchor="lm")
    d.text((120, 845), "Penyedia  |  IPG Kampus Tun Hussein Onn", font=D.font(D.MSB, 24), fill=D.YELLOW + (a,), anchor="lm")
    return np.asarray(im).astype(np.float32)


LT_FULL = lower_third(1.0)


def overlay_rgba(base, rgba, alpha_mul=1.0):
    a = rgba[..., 3:4] / 255.0 * alpha_mul
    return (base.astype(np.float32) * (1 - a) + rgba[..., :3] * a).astype(np.uint8)


def frames(path, w, h, vf=None):
    cmd = ["ffmpeg", "-v", "error", "-i", path]
    if vf:
        cmd += ["-vf", vf]
    cmd += ["-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=w * h * 3 * 2)
    n = w * h * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            return
        yield np.frombuffer(b, np.uint8).reshape(h, w, 3)


class Seq:
    """sequential frame reader with forward seeking by index"""
    def __init__(self, gen, first=0):
        self.gen, self.idx, self.cur = gen, first - 1, None

    def get(self, i):
        while self.idx < i:
            nxt = next(self.gen, None)
            if nxt is None:
                break
            self.cur = nxt; self.idx += 1
        return self.cur


def inset_gen():
    x0, y0, x1, y1 = D.INSET
    for f in sorted(glob.glob(WD + "out/inset_[0-9][0-9][0-9].mp4")):
        yield from frames(f, x1 - x0, y1 - y0)


src = Seq(frames(SRC, SW, SH, f"trim=end_frame={LAST}"))
intro = Seq(frames(WD + "out/intro_comp.mp4", D.W, D.H))
inset = Seq(inset_gen(), 0)  # inset stream index == source frame index (first 725 are padding)

title_bg = D.plate((D.W, D.H), blur=7, darken=0.35)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{D.W}x{D.H}", "-r", str(FPS), "-i", "-",
                        "-f", "f32le", "-ar", "48000", "-ac", "2", "-i", WD + "out/final_audio.f32",
                        "-vf", f"ass={WD}subs.ass:fontsdir={WD}assfonts",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-level", "4.1",
                        "-pix_fmt", "yuv420p", "-g", "60", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                        "-t", f"{TOTAL:.3f}", "-movflags", "+faststart",
                        "-metadata", "title=Video Penerangan: Cara Bermain Dunia Minecraft Education - Misi Penyelamat Ayat",
                        "-metadata", "artist=Mohamad Aliff bin Ahmad Shahabuddin", OUTF], stdin=subprocess.PIPE)

x0, y0, x1, y1 = D.INSET
t0 = time.time()
for n in range(NFR):
    T = n / FPS
    if T < TITLE:
        out = np.asarray(D.title_frame(T, title_bg))
    elif T < TITLE + MAIN:
        tau = T - TITLE
        ts, sp = src_time(tau)
        si = min(int(round(ts * FPS)), LAST - 1)
        if si < INTRO_END:
            out = intro.get(si)
            src.get(si)  # keep the source reader in step
            lt = min(1, max(0, (ts - 12.2) / 0.5)) * min(1, max(0, (21.5 - ts) / 0.5))
            if lt > 0:
                out = overlay_rgba(out, LT_FULL, lt)
            fin = min(1, tau / 0.5)  # fade in from the title's black
            if fin < 1:
                out = (out * fin).astype(np.uint8)
        else:
            f = src.get(si).copy()
            f[y0:y1, x0:x1] = inset.get(si)
            g = cv2.resize(f, (D.GW, D.GH), interpolation=cv2.INTER_AREA)
            badge = round(sp, 1) if sp >= 1.35 else None
            out = chrome(chapter(ts), badge).copy()
            out[D.GY:D.GY + D.GH, D.GX:D.GX + D.GW] = g
            fo = (MAIN - tau) / 0.8
            if fo < 1:
                out = (out * max(fo, 0)).astype(np.uint8)
    else:
        tc = T - TITLE - MAIN
        out = np.asarray(D.credits_frame(tc, title_bg))
        fin = min(1, tc / 0.6)
        if fin < 1:
            out = (out * fin).astype(np.uint8)
    enc.stdin.write(np.ascontiguousarray(out).tobytes())
    if n % 900 == 0:
        el = time.time() - t0
        print(f"frame {n}/{NFR} ({T:.0f}s) {el:.0f}s elapsed, eta {el / max(n, 1) * (NFR - n) / 60:.1f} min", flush=True)
enc.stdin.close(); enc.wait()
print("STAGE2 DONE", OUTF, flush=True)
