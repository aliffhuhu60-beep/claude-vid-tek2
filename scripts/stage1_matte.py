"""Stage 1: background replacement for the teacher.

- intro (frames 0..724): full-body cut-out composited on a Minecraft plate (1920x1080) -> out/intro_comp.mp4
- inset (frames 725..end): bottom-left webcam inset (498x278 @ 13,802) composited on a Minecraft plate,
  written in 1800-frame chunks -> out/inset_XXX.mp4
The iPad facecam circle on the right is NOT touched.
"""
import subprocess, sys, os, time
import numpy as np, cv2, onnxruntime as ort
sys.path.insert(0, "/home/user/work/scripts")
from design import plate, W, H, INSET, GREEN
from PIL import Image, ImageDraw

SRC = "/home/user/work/src/original.mp4"
OUT = "/home/user/work/out/"
os.makedirs(OUT, exist_ok=True)
SW, SH = 1728, 1080
INTRO_END = 725            # first gameplay frame (24.1667 s)
LAST = int(1101.27 * 30)   # black tail starts
CHUNK = 1800
TEACHER_X = 192            # horizontal offset of the 1728-wide intro frame in the 1920 canvas

so = ort.SessionOptions(); so.intra_op_num_threads = 4
sess = ort.InferenceSession("/home/user/work/models/rvm_resnet50_fp32.onnx", so, providers=["CPUExecutionProvider"])


class Matter:
    def __init__(self, ratio):
        self.ratio = np.array([ratio], np.float32)
        self.rec = [np.zeros((1, 1, 1, 1), np.float32)] * 4

    def __call__(self, rgb):
        x = rgb.astype(np.float32).transpose(2, 0, 1)[None] / 255.0
        fgr, pha, *self.rec = sess.run(None, {"src": x, "r1i": self.rec[0], "r2i": self.rec[1], "r3i": self.rec[2],
                                              "r4i": self.rec[3], "downsample_ratio": self.ratio})
        return fgr[0].transpose(1, 2, 0), pha[0, 0]


def encoder(path, w, h, crf):
    return subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", "30",
                             "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", path],
                            stdin=subprocess.PIPE)


def reader(vf, w, h):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         stdout=subprocess.PIPE, bufsize=w * h * 3 * 4)
    n = w * h * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield np.frombuffer(b, np.uint8).reshape(h, w, 3)


def comp(fg, a, bg):
    a = a[..., None]
    return (fg * a + bg * (1 - a)).clip(0, 255).astype(np.uint8)


def do_intro():
    bg = np.asarray(plate((W, H), blur=5)).astype(np.float32)
    m = Matter(0.25)
    enc = encoder(OUT + "intro_comp.mp4", W, H, 14)
    t0 = time.time()
    for i, f in enumerate(reader(f"trim=end_frame={INTRO_END}", SW, SH)):
        fgr, a = m(f)
        a = a.copy()
        a[860:, :640] = 0                       # leftover bag from the original cut-out
        a[a < 0.02] = 0
        fg = np.where(a[..., None] > 0.97, f.astype(np.float32), fgr * 255.0)
        # the original cut-out ends ~55 px above the frame bottom: shift down so that edge is off-screen
        DY = 58
        full_fg = np.zeros((H, W, 3), np.float32); full_fg[DY:, TEACHER_X:TEACHER_X + SW] = fg[:H - DY]
        full_a = np.zeros((H, W), np.float32); full_a[DY:, TEACHER_X:TEACHER_X + SW] = a[:H - DY]
        enc.stdin.write(comp(full_fg, full_a, bg).tobytes())
        if i % 100 == 0:
            print(f"intro {i}/{INTRO_END} {time.time() - t0:.0f}s", flush=True)
    enc.stdin.close(); enc.wait()


def border(img):
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    w, h = im.size
    d.rectangle((0, 0, w - 1, h - 1), outline=(0, 0, 0), width=4)
    d.rectangle((4, 4, w - 5, h - 5), outline=GREEN, width=4)
    return np.asarray(im)


def do_inset(start_chunk=0):
    x0, y0, x1, y1 = INSET
    iw, ih = x1 - x0, y1 - y0
    bg = np.asarray(plate((iw, ih), blur=2.5)).astype(np.float32)
    m = Matter(0.4)
    first = INTRO_END + start_chunk * CHUNK
    warm = max(INTRO_END, first - 60)          # warm up recurrent state before a resumed chunk
    vf = f"trim=start_frame={warm}:end_frame={LAST},crop={iw}:{ih}:{x0}:{y0}"
    enc = None; t0 = time.time()
    for k, f in enumerate(reader(vf, iw, ih)):
        n = warm + k
        up = cv2.resize(f, (iw * 2, ih * 2), interpolation=cv2.INTER_CUBIC)
        fgr, a2 = m(up)
        if n < first:
            continue
        a = cv2.resize(a2, (iw, ih), interpolation=cv2.INTER_AREA)
        a[a < 0.03] = 0
        fg_d = cv2.resize(fgr, (iw, ih), interpolation=cv2.INTER_AREA) * 255.0
        fg = np.where(a[..., None] > 0.97, f.astype(np.float32), fg_d)
        out = border(comp(fg, a, bg))
        c = (n - INTRO_END) // CHUNK
        if (n - INTRO_END) % CHUNK == 0:
            if enc:
                enc.stdin.close(); enc.wait()
                os.rename(OUT + f"inset_{c - 1:03d}.part.mp4", OUT + f"inset_{c - 1:03d}.mp4")
            enc = encoder(OUT + f"inset_{c:03d}.part.mp4", iw, ih, 12)
        enc.stdin.write(out.tobytes())
        if k % 600 == 0:
            print(f"inset frame {n}/{LAST} chunk {c} {time.time() - t0:.0f}s", flush=True)
    enc.stdin.close(); enc.wait()
    c = (LAST - 1 - INTRO_END) // CHUNK
    os.rename(OUT + f"inset_{c:03d}.part.mp4", OUT + f"inset_{c:03d}.mp4")


if __name__ == "__main__":
    what = sys.argv[1]
    if what in ("intro", "all"):
        do_intro()
    if what in ("inset", "all"):
        do_inset(int(sys.argv[2]) if len(sys.argv) > 2 else 0)
    print("STAGE1 DONE", flush=True)
