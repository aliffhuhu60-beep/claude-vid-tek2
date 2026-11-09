import sys, json, subprocess, numpy as np, cv2
sys.path.insert(0, "/home/user/work/scripts")
import design as D
from PIL import Image
rows = json.load(open("/home/user/work/map.json"))
T = float(sys.argv[1]); tau = T - 9.0
for a, b, s, k, oa, ob in rows:
    if tau < ob: ts = a + (tau - oa) * s; sp = s; break
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{ts:.3f}", "-i", "/home/user/work/src/original.mp4", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
f = np.frombuffer(raw, np.uint8).reshape(1080, 1728, 3).copy()
im = D.chrome_bg(); D.side_label(im, "BAHAGIAN 1\n\nJENIS 1\nAYAT TANPA\nSUBJEK")
if sp >= 1.35: D.speed_badge(im, sp)
out = np.asarray(im).copy()
out[D.GY:D.GY + D.GH, D.GX:D.GX + D.GW] = cv2.resize(f, (D.GW, D.GH), interpolation=cv2.INTER_AREA)
Image.fromarray(out).save("/home/user/work/test/lay.png")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", "/home/user/work/test/lay.png", "-vf",
  f"setpts=PTS+{T}/TB,ass=/home/user/work/subs.ass:fontsdir=/home/user/work/assfonts", "-frames:v", "1", sys.argv[2]], check=True)
print("src", ts, "speed", sp)
