"""Fasa E: automated final checks."""
import json, subprocess, re, numpy as np

F = "/home/user/work/out/VIDEO_PENERANGAN_MISI_PENYELAMAT_AYAT_FINAL.mp4"
rows = json.load(open("/home/user/work/map.json"))
plan = json.load(open("/home/user/work/plan.json"))
ok = lambda c: "LULUS" if c else "GAGAL"

# 1 specs
pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", F], capture_output=True).stdout)
v = [s for s in pr["streams"] if s["codec_type"] == "video"][0]
a = [s for s in pr["streams"] if s["codec_type"] == "audio"][0]
print(f"[{ok(v['codec_name']=='h264' and v['width']==1920 and v['height']==1080)}] Video: {v['codec_name']} {v['profile']} {v['width']}x{v['height']} {v['r_frame_rate']} fps, {v['pix_fmt']}")
print(f"[{ok(a['codec_name']=='aac')}] Audio: {a['codec_name']} {a['sample_rate']} Hz {a['channels']} ch")
dur = float(pr["format"]["duration"])
print(f"[INFO] Durasi: {int(dur // 60)}:{dur % 60:04.1f}  saiz {int(pr['format']['size']) / 1e9:.2f} GB")

# 2 speech never sped up
bad = []
for s0, e0 in plan["speech"]:
    for st, en, sp, k, oa, ob in rows:
        if en > s0 and st < e0 and abs(sp - 1) > 1e-6:
            bad.append((s0, e0, st, en, sp))
print(f"[{ok(not bad)}] Semua {len(plan['speech'])} blok penerangan pada 1.0x (pertindihan dengan bahagian dipercepat: {len(bad)})")
# padding around speech
print(f"[INFO] Kelajuan maksimum digunakan: {max(r[2] for r in rows)}x (had 1.5x)")

# 3 order preserved, nothing cut
mono = all(rows[i][1] <= rows[i + 1][0] + 1e-6 for i in range(len(rows) - 1))
gaps = sum(rows[i + 1][0] - rows[i][1] for i in range(len(rows) - 1))
print(f"[{ok(mono and abs(gaps) < 1e-3 and rows[0][0] == 0)}] Susunan rakaman asal dikekalkan, tiada bahagian dipotong (0.0 s → {rows[-1][1]:.2f} s berterusan; hanya 5.1 s skrin hitam di hujung dibuang)")

# 4 names and titles in subtitles / graphics source
ass = open("/home/user/work/subs.ass").read()
txt = re.sub(r"\{[^}]*\}", "", ass).replace("\\N", " ")
for name in ["Puan Julina binti Tarikat", "Mohamad Aliff bin Ahmad Shahabuddin", "Misi Penyelamat Ayat", "Minecraft Education"]:
    print(f"[{ok(name in txt)}] Sari kata mengandungi ejaan tepat: {name}")
for wrong in ["makah", "Puan Craft", "bersyarah", "pemainan", "cebaran", "memulukan", "gebang", "SIMULASI PENGAJARAN MIKRO"]:
    if wrong.lower() in txt.lower():
        print(f"[GAGAL] Ejaan salah masih ada: {wrong}")
design = open("/home/user/work/scripts/design.py").read()
for s in ["VIDEO PENERANGAN", "CARA BERMAIN DUNIA MINECRAFT EDUCATION", "MISI PENYELAMAT AYAT", "MOHAMAD ALIFF BIN AHMAD SHAHABUDDIN",
          "INSTITUT PENDIDIKAN GURU KAMPUS TUN HUSSEIN ONN", "EDUP3133: TEKNOLOGI UNTUK PENGAJARAN DAN PEMBELAJARAN",
          "SETINGGI-TINGGI PENGHARGAAN", "kepada pensyarah yang dihormati", "PUAN JULINA BINTI TARIKAT",
          "Pensyarah EDUP3133: Teknologi untuk Pengajaran dan Pembelajaran", "Institut Pendidikan Guru Kampus Tun Hussein Onn"]:
    print(f"[{ok(s in design)}] Grafik: {s}")
print(f"[{ok('SIMULASI' not in design)}] Tiada tajuk 'SIMULASI PENGAJARAN MIKRO'")

# 5 audio/video sync: final audio speech envelope vs original mapped through the plan
def env(path, start, dur):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(start), "-t", str(dur), "-i", path, "-vn", "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32)
    return np.sqrt(np.convolve(x ** 2, np.ones(80) / 80, "same"))[::80]
def out_t(t):
    for st, en, sp, k, oa, ob in rows:
        if st <= t <= en:
            return 9.0 + oa + (t - st) / sp
lags = []
for t in [5.0, 190.0, 460.0, 720.0, 1000.0, 1070.0]:
    o = env("/home/user/work/src/original.mp4", t, 6); f = env(F, out_t(t), 6)
    n = min(len(o), len(f)); o, f = o[:n] - o[:n].mean(), f[:n] - f[:n].mean()
    c = [np.dot(o[max(0, -L):n - max(0, L)], f[max(0, L):n - max(0, -L)]) for L in range(-20, 21)]
    lags.append((np.argmax(c) - 20) * 10)
print(f"[{ok(all(abs(l) <= 40 for l in lags))}] Penyelarasan audio (lag ms pada 6 titik): {lags}")
