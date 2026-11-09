"""Build Malay ASS subtitles on the OUTPUT timeline from word timestamps.

- words come from the Whisper transcript (original timeline)
- token-level spelling corrections (Bahasa Melayu baku), never adding dialogue
- times mapped through the speed plan (map.json) + title offset
- keywords bold + yellow (concepts) / green (game objects)
"""
import json, re, sys

TITLE = float(sys.argv[1]) if len(sys.argv) > 1 else 9.0
T = json.load(open("/home/user/work/transcript.json"))
rows = json.load(open("/home/user/work/map.json"))

words = []
for s in T:
    for w in s["words"]:
        if w["s"] >= 1091.9:  # hallucinated tail
            continue
        if 608 < w["s"] < 610:  # misaligned "Pemain" -> belongs at 699.8
            w = dict(w, s=699.8, e=700.3)
        if 96.0 < w["s"] < 97.5 and w["w"].strip() == "Baiklah,":  # misaligned, re-checked at 117 s
            w = dict(w, s=116.7, e=117.3)
        words.append(dict(s=w["s"], e=w["e"], w=w["w"].strip()))
# speech missed by VAD (verified with a second pass)
for i, (tok, s, e) in enumerate([("Untuk", 445.74, 446.3), ("soalan", 446.3, 446.64), ("jenis", 446.64, 446.92),
                                  ("kedua", 446.92, 447.26), ("ini,", 447.26, 447.62)]):
    words.append(dict(s=s, e=e, w=tok))
words.sort(key=lambda w: w["s"])
# drop the duplicated "pemain boleh memilih ..." alignment overlap: the original segment at 447.64 continues correctly

# --- token sequence corrections (lowercased match on the token text without punctuation)
FIX = [
    (["bersyarah"], ["pensyarah"]),
    (["teknologi", "dalam", "pengajaran", "dan", "pembelajaran."], ["Teknologi", "dalam", "Pengajaran", "dan", "Pembelajaran."]),
    (["Puan", "Craft", "Education."], ["Minecraft", "Education."]),
    (["zamro"], ["zamrud"]),
    (["milih"], ["memilih"]),
    (["selamat", "datang", "ke", "misi", "penyelamat", "ayat."], ["Selamat", "Datang", "ke", "Misi", "Penyelamat", "Ayat."]),
    (["makah"], ["markah"]), (["makah."], ["markah."]), (["makah,"], ["markah,"]),
    (["Pemainan"], ["Permainan"]), (["pemainan"], ["permainan"]), (["pemainan,"], ["permainan,"]), (["pemainan."], ["permainan."]),
    (["gebang"], ["gerbang"]), (["umur,"], ["ungu,"]),
    (["5", "warna."], ["5", "warna:"]), (["Biru,"], ["biru,"]),
    (["diberapakan."], ["diberikan."]),
    (["markah", "100", "markah"], ["100", "markah"]),
    (["kelima", "soalan,"], ["kelima-lima", "soalan,"]),
    (["front"], ["frame"]),
    (["ke", "lima-lima"], ["kelima-lima"]),
    (["peparan", "kapan"], ["papan", "tanda"]),
    (["pakor"], ["parkour"]),
    (["Sebenarnya", "pemain", "terjatuh"], ["Sekiranya", "pemain", "terjatuh"]),
    (["riset", "semuanya."], ["di-reset", "semula,"]),
    (["tanya"], ["tahniah"]),
    (["pemain", "aku"], ["pemain"]),
    (["lobby"], ["lobi"]), (["lobby,"], ["lobi,"]),
    (["memulukan"], ["memulakan"]), (["dimulukan."], ["dimulakan."]),
    (["berpermain"], ["pemain"]),
    (["saya", "bersedia,"], ["\"Saya", "bersedia\","]),
    (["station"], ["stesen"]), (["station."], ["stesen."]), (["station,"], ["stesen,"]),
    (["cebaran"], ["cabaran"]), (["Cebaran"], ["Cabaran"]),
    (["menijak"], ["memijak"]),
    (["pingat", "apa", "yang"], ["pingat", "yang"]),
    (["code"], ["kod"]),
    (["penyelamat"], ["Penyelamat"]),
]


def norm(t):
    return t


def apply_fixes(ws):
    out = []
    i = 0
    while i < len(ws):
        done = False
        for src, dst in FIX:
            n = len(src)
            if [w["w"] for w in ws[i:i + n]] == src:
                s, e = ws[i]["s"], ws[i + n - 1]["e"]
                step = (e - s) / len(dst)
                for k, d in enumerate(dst):
                    out.append(dict(s=s + k * step, e=s + (k + 1) * step, w=d))
                i += n
                done = True
                break
        if not done:
            out.append(ws[i]); i += 1
    return out


words = apply_fixes(words)
# remove immediate repetition "setelah pemain memilih, setelah pemain memilih," ? -> keep (spoken), but it is a false start;
# subtitles must not invent nor drop explanation, repetition kept.


def o(t):
    for a, b, s, k, oa, ob in rows:
        if a - 1e-6 <= t <= b + 1e-6:
            return TITLE + oa + (t - a) / s
    return TITLE + rows[-1][5]


PROTECT_PHRASES = ["papan tanda", "minecraft education", "join code", "enter code", "blok warna", "blok berwarna", "berwarna hijau",
    "berwarna ungu", "berwarna hitam", "berwarna emas", "puan julina", "julina binti", "binti tarikat", "mohamad aliff", "aliff bin",
    "bin ahmad", "ahmad shahabuddin", "ayat aktif", "ayat pasif", "100 markah", "50 markah", "30 saat", "plat besi", "lobi utama",
    "peti yang", "yang pertama", "yang kedua", "yang ketiga", "jenis yang", "misi penyelamat", "penyelamat ayat", "lobi jenis"]
PROT = set(PROTECT_PHRASES)


def clean(t):
    return re.sub(r"[^\w-]", "", t.lower())


# --- group into cues
cues = []
cur = []
MAXC = 84
for w in words:
    if cur:
        gap = w["s"] - cur[-1]["e"]
        text = " ".join(x["w"] for x in cur)
        end_punct = cur[-1]["w"][-1] in ".?!"
        soft_punct = cur[-1]["w"][-1] in ",;:"
        protected = (clean(cur[-1]["w"]) + " " + clean(w["w"])) in PROT and gap < 0.9 and len(text) < 100
        if protected:
            pass
        elif gap > 0.9 or len(text) + len(w["w"]) + 1 > MAXC or (end_punct and len(text) > 25) or (soft_punct and len(text) > 55) \
                or (w["s"] - cur[0]["s"] > 6.5):
            cues.append(cur); cur = []
    cur.append(w)
if cur:
    cues.append(cur)
# merge orphan single-word cues into the next cue
merged = []
i = 0
while i < len(cues):
    c = cues[i]
    if len(c) == 1 and i + 1 < len(cues) and cues[i + 1][0]["s"] - c[-1]["e"] < 3.5:
        cues[i + 1] = c + cues[i + 1]
    else:
        merged.append(c)
    i += 1
cues = merged

# --- highlighting
YEL = r"{\fnMontserrat\b1\c&H40D6FF&}"
GRN = r"{\fnMontserrat\b1\c&H48CC7E&}"
RST = r"{\fnMontserrat SemiBold\b0\c&HFFFFFF&}"
KEY_Y = ["Puan Julina binti Tarikat", "Mohamad Aliff bin Ahmad Shahabuddin", "Misi Penyelamat Ayat", "Minecraft Education",
         "Teknologi dalam Pengajaran dan Pembelajaran", "100 markah", "50 markah", "markah", "ayat tanpa subjek", "subjek", "predikat",
         "ayat aktif-ayat pasif", "ayat aktif", "ayat pasif", "pingat", "individu", "berkumpulan", "kumpulan",
         "ekspedisi ayat", "cabaran yang terakhir", "Cabaran terakhir", "kawasan pemenang", "keputusan", "tiga hakim",
         "lobi utama", "jenis yang pertama", "jenis yang kedua", "jenis yang ketiga", "30 saat", "jawapan yang betul",
         "bahagian yang kedua", "bahagian kedua", "Selamat Datang", "kelima-lima soalan", "Penyelamat"]
KEY_G = ["Enter Join Code", "Enter Code", "Join Code", "blok berwarna hijau", "blok warna", "blok yang berwarna hitam", "blok glowstone",
         "glowstone", "plat besi", "peti 1", "peti 2", "peti yang pertama", "peti yang kedua", "peti pertama", "peti kedua",
         "NPC", "papan tanda", "frame gambar", "gerbang berwarna ungu", "pintu berwarna hijau", "peta yang berwarna emas",
         "parkour", "air", "stesen", "menu utama", "zamrud", "bulu", "\"Saya bersedia\""]


def highlight(text):
    spans = []
    low = text.lower()
    for col, keys in ((YEL, KEY_Y), (GRN, KEY_G)):
        for k in sorted(keys, key=len, reverse=True):
            pat = re.escape(k.lower()).replace("\\ ", "[ ¦]")
            for m in re.finditer(r"(?<![\w-])" + pat + r"(?![\w-])", low):
                if all(m.end() <= a or m.start() >= b for a, b, _ in spans):
                    spans.append((m.start(), m.end(), col))
    spans.sort()
    out, p = "", 0
    for a, b, col in spans:
        out += text[p:a] + col + text[a:b] + RST
        p = b
    return out + text[p:]


def wrap(text):
    if len(text) <= 52:
        return text
    best = None
    for m in re.finditer(" ", text):
        i = m.start()
        score = abs(len(text[:i]) - len(text[i + 1:]))
        a = clean(text[:i].split(" ")[-1]); b = clean(text[i + 1:].split(" ")[0])
        if (a + " " + b) in PROT:
            score += 25
        if text[i - 1] in ",.":
            score -= 6
        if best is None or score < best[0]:
            best = (score, i)
    i = best[1]
    return text[:i] + "¦" + text[i + 1:]


def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def srt_ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = int(t % 60); ms = int(round((t - int(t)) * 1000))
    if ms == 1000:
        s += 1; ms = 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def join(ws):
    t = ""
    for x in ws:
        t += x["w"] if (not t or x["w"].startswith("-")) else " " + x["w"]
    return t


events = []
prev_end_sentence = True
for c in cues:
    st, en = o(c[0]["s"]), o(c[-1]["e"])
    en = max(en + 0.25, st + 1.0)
    text = join(c)
    if prev_end_sentence:
        text = text[0].upper() + text[1:]
    prev_end_sentence = text.rstrip()[-1] in ".?!"
    events.append([st, en, text])
# no overlaps
for i in range(len(events) - 1):
    if events[i][1] > events[i + 1][0] - 0.04:
        events[i][1] = events[i + 1][0] - 0.04

head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Montserrat SemiBold,36,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,3.5,1.2,2,180,180,8,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
with open("/home/user/work/subs.ass", "w") as f:
    f.write(head)
    for st, en, text in events:
        f.write(f"Dialogue: 0,{ts(st)},{ts(en)},Sub,,0,0,0,,{highlight(wrap(text)).replace("¦", chr(92) + "N")}\n")
with open("/home/user/work/subs.srt", "w") as f:
    for i, (st, en, text) in enumerate(events, 1):
        f.write(f"{i}\n{srt_ts(st)} --> {srt_ts(en)}\n{wrap(text).replace("¦", chr(10))}\n\n")
print(len(events), "cues")
