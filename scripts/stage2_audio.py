"""Build the final audio track on the output timeline.

title music (TITLE s) + original audio with speed plan (pitch-preserving atempo, exact segment lengths)
+ credits music (CRED s). Speech is never time-stretched (plan keeps speech at 1.0x).
"""
import json, subprocess, sys, numpy as np

SR = 48000
TITLE, CRED = 9.0, 12.0
SRC = "/home/user/work/src/original.mp4"
rows = json.load(open("/home/user/work/map.json"))
OUT = "/home/user/work/out/"


def load():
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", SRC, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2)


def atempo(x, s):
    p = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                        "-af", f"atempo={s}", "-f", "f32le", "-"], input=x.astype(np.float32).tobytes(), capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).reshape(-1, 2)


def main_track(a):
    out = []
    pos = 0
    for st, en, s, k, oa, ob in rows:
        seg = a[int(round(st * SR)):int(round(en * SR))]
        n_out = int(round(ob * SR)) - pos
        if abs(s - 1.0) > 1e-6:
            seg = atempo(seg, s)
        if len(seg) >= n_out:
            seg = seg[:n_out]
        else:
            seg = np.concatenate([seg, np.zeros((n_out - len(seg), 2), np.float32)])
        if abs(s - 1.0) > 1e-6 and n_out > 512:   # tiny fades at tempo joins (only in non-speech parts)
            r = np.linspace(0, 1, 128, dtype=np.float32)[:, None]
            seg = seg.copy(); seg[:128] *= r; seg[-128:] *= r[::-1]
        out.append(seg); pos += n_out
    return np.concatenate(out)


# ------------------------------------------------------------ chiptune (synthesised, royalty-free)
def note(f, dur, kind="pulse", vol=0.2, duty=0.25):
    t = np.arange(int(dur * SR)) / SR
    if kind == "pulse":
        w = np.where((t * f) % 1.0 < duty, 1.0, -1.0)
    elif kind == "tri":
        w = 2 * np.abs(2 * ((t * f) % 1.0) - 1) - 1
    else:
        w = np.sin(2 * np.pi * f * t)
    env = np.minimum(1, t / 0.01) * np.exp(-t * 3.2)
    return (w * env * vol).astype(np.float32)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tune(seconds, ending=False, seed=0):
    bpm = 112; beat = 60 / bpm; e = beat / 2
    prog = [(60, [60, 64, 67, 72]), (57, [57, 60, 64, 69]), (53, [53, 57, 60, 65]), (55, [55, 59, 62, 67])]
    buf = np.zeros(int((seconds + 2) * SR), np.float32)
    t = 0.0; bar = 0
    while t < seconds:
        root, ch = prog[bar % 4]
        for i in range(8):                            # arpeggio eighths
            m = ch[[0, 1, 2, 3, 2, 1, 2, 3][i]] + 12
            n = note(hz(m), e * 0.95, "pulse", 0.06, 0.25)
            k = int((t + i * e) * SR); buf[k:k + len(n)] += n[:len(buf) - k]
        for i in range(2):                            # bass half notes
            n = note(hz(root - 12), beat * 2, "tri", 0.16)
            k = int((t + i * 2 * beat) * SR); buf[k:k + len(n)] += n[:len(buf) - k]
        t += 8 * e; bar += 1
    if ending:
        k = int((seconds - 2.2) * SR)
        for m in (60, 64, 67, 72):
            n = note(hz(m), 2.2, "tri", 0.08); buf[k:k + len(n)] += n[:len(buf) - k]
    buf = buf[:int(seconds * SR)]
    # soften: one-pole lowpass + fades
    y = np.zeros_like(buf); acc = 0.0; alpha = 0.35
    for i in range(0, len(buf)):
        acc += alpha * (buf[i] - acc); y[i] = acc
    fi, fo = int(0.8 * SR), int(1.5 * SR)
    y[:fi] *= np.linspace(0, 1, fi); y[-fo:] *= np.linspace(1, 0, fo)
    return np.stack([y, y], 1)


def loudnorm(x, target):
    """two-pass EBU R128 normalisation via ffmpeg."""
    inp = x.astype(np.float32).tobytes()
    base = ["ffmpeg", "-v", "info", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-"]
    r = subprocess.run(base + ["-af", f"loudnorm=I={target}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       input=inp, capture_output=True)
    js = r.stderr.decode()
    js = json.loads(js[js.rfind("{"):js.rfind("}") + 1])
    af = (f"loudnorm=I={target}:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    p = subprocess.run(base + ["-af", af + f",aresample={SR}", "-f", "f32le", "-"], input=inp, capture_output=True, check=True)
    print("loudnorm in", js["input_i"], "LUFS ->", target, flush=True)
    return np.frombuffer(p.stdout, np.float32).reshape(-1, 2)


if __name__ == "__main__":
    a = load()
    m = main_track(a)
    # gentle clean-up: rumble high-pass + light broadband denoise (voice untouched otherwise)
    p = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                        "-af", "highpass=f=70,afftdn=nr=6:nf=-45", "-f", "f32le", "-"], input=m.tobytes(), capture_output=True, check=True)
    m = np.frombuffer(p.stdout, np.float32).reshape(-1, 2)[:len(m)]
    m = loudnorm(m, -16)
    # fade out the last 0.8 s of the main part into the credits
    fo = int(0.8 * SR); m = m.copy(); m[-fo:] *= np.linspace(1, 0, fo)[:, None]
    tmus = loudnorm(tune(TITLE), -23)
    cmus = loudnorm(tune(CRED, ending=True), -23)
    full = np.concatenate([tmus[:int(TITLE * SR)], m, cmus[:int(CRED * SR)]]).clip(-1, 1)
    full.astype(np.float32).tofile(OUT + "final_audio.f32")
    print("AUDIO DONE", len(full) / SR, "s", flush=True)
