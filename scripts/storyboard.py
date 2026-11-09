import json
rows=json.load(open("/home/user/work/map.json"))
TITLE=9.0; CRED=12.0
def o(t):  # original -> output (incl. title offset)
    for a,b,s,k,oa,ob in rows:
        if a-1e-6<=t<=b+1e-6: return TITLE+oa+(t-a)/s
    return TITLE+rows[-1][5]
def f(t):
    m,s=divmod(t,60); return f"{int(m):02d}:{s:04.1f}"
SP="1.0x"; FAST="1.5x (ramp 1.0→1.5→1.0)"; FAST4="1.4x (ramp 1.0→1.4→1.0)"
G="Gameplay + inset guru"
BG_IN="Inset kiri bawah: bilik → latar Minecraft"
S=[ # start,end,content,edit,speed,subs
(0.0,24.17,"Pengenalan guru (badan penuh): salam, penghargaan kepada **Puan Julina binti Tarikat**, memperkenalkan diri **Mohamad Aliff bin Ahmad Shahabuddin**, tujuan video.","Guru dipotong daripada latar, diletak di hadapan landskap Minecraft (kabur lembut). Lower-third nama penyedia.",SP,"Ya – nama ditebalkan/kuning","**Latar hitam asal (dengan sisa beg di kiri bawah) → landskap Minecraft**"),
(24.17,41.68,"Skrin utama Minecraft Education → Join Code → kod disahkan.",G+" ; label bab 'MULA'",SP,"Ya","Inset: bilik → Minecraft"),
(41.68,59.64,"Skrin 'Connecting / Generating World' (tiada suara).",G,FAST,"Tiada (lencana ⏩ 1.5x)","Inset: bilik → Minecraft"),
(59.64,98.48,"Paparan Selamat Datang, papan 'Selamat datang ke Misi Penyelamat Ayat', markah **+100 / −50**, mod individu & kumpulan, lobi contoh kesalahan ayat.",G,SP,"Ya","Inset: bilik → Minecraft"),
(98.48,115.94,"Pemain berjalan di lobi (tiada suara).",G,FAST4,"Tiada","Inset: bilik → Minecraft"),
(115.94,154.24,"Gerbang **ungu** (berkumpulan), warna kumpulan, pintu **hijau** (individu), pijak blok hijau → Lobi Jenis 1 (30 saat membaca papan tanda).",G,SP,"Ya","Inset: bilik → Minecraft"),
(154.24,181.85,"Lobi Jenis 1 – pemain membaca papan tanda, kiraan 30 saat (tiada suara).",G,FAST,"Tiada","Inset: bilik → Minecraft"),
(181.85,244.02,"**Jenis 1: Ayat Tanpa Subjek** – Soalan 1 & 2: baca soalan, 3 pilihan, pijak **blok warna**, BETUL +100 + penerangan; perlu betul 5 soalan untuk ke Jenis 2.",G+" ; label bab 'BAHAGIAN 1 · JENIS 1'",SP,"Ya","Inset: bilik → Minecraft"),
(244.02,321.17,"Jenis 1 – Soalan 3, 4, 5 dijawab (tiada suara).",G,FAST,"Tiada","Inset: bilik → Minecraft"),
(321.17,407.4,"Lobi Jenis 2 (30 saat). Plat besi → lobi utama. **Jenis 2: Ayat Tidak Lengkap** – Soalan 1: **Peti 1 = subjek**, **Peti 2 = predikat**; rehat di lobi & blok **glowstone** untuk sambung. (Jeda 5–7 s di 5:41 & 6:40 dipercepat 1.4x)",G+" ; label 'JENIS 2'",SP+" (jeda: 1.4x)","Ya","Inset: bilik → Minecraft"),
(408.5,444.34,"Pemain membuka peti dan memilih kepingan ayat (tiada suara).",G,FAST,"Tiada","Inset: bilik → Minecraft"),
(444.34,477.3,"Penerangan Peti 1 & Peti 2, letak ayat pada **bingkai** (item frame) yang disediakan.",G,SP,"Ya","Inset: bilik → Minecraft"),
(477.3,523.92,"Jenis 2 – Soalan 2 & 3 (tiada suara).",G,FAST,"Tiada","Inset: bilik → Minecraft"),
(523.92,554.9,"Jawapan salah → bilik pilihan (kembali ke lobi utama / teruskan). Perlu betul 5 soalan untuk ke Jenis 3.",G,SP,"Ya","Inset: bilik → Minecraft"),
(554.9,698.4,"Jenis 2 – Soalan 4, 5 & 6 (termasuk SALAH −50), masuk ke Lobi Jenis 3 (tiada suara, 2 min 24 s).",G,FAST,"Tiada","Inset: bilik → Minecraft"),
(698.4,762.49,"**Jenis 3: Bahasa Rojak** – Lobi 30 saat, aktiviti **parkour** (lompat blok ke blok) memilih jawapan; jatuh ke air → reset ke permulaan.",G+" ; label 'JENIS 3'",SP+" (jeda 29 s: 1.5x)","Ya","Inset: bilik → Minecraft"),
(762.49,804.64,"Jenis 3 – parkour soalan seterusnya (tiada suara).",G,FAST,"Tiada","Inset: bilik → Minecraft"),
(804.64,845.31,"Perlu betul 5 soalan → **kawasan pemenang**, ucapan tahniah, pijak blok untuk papar markah & kedudukan.",G,SP+" (jeda 8 s: 1.4x)","Ya","Inset: bilik → Minecraft"),
(845.31,945.26,"Kembali ke lobi utama → pijak blok **hitam** → **Bahagian 2: Ekspedisi Ayat**; berinteraksi dengan **NPC**, papan tanda arahan, pusat permainan, 'Saya bersedia!', misi bina **ayat aktif & ayat pasif**. (Jeda 20 s di 14:35 dipercepat)",G+" ; label 'BAHAGIAN 2'",SP+" (jeda: 1.5x)","Ya","Inset: bilik → Minecraft"),
(946.36,986.39,"Pemain menaip ayat di stesen (Ladang Pertanian), BETUL +100 (tiada suara).",G,FAST,"Tiada","Inset: bilik → Minecraft"),
(986.39,1020.69,"Selepas bina ayat aktif–pasif → hujung stesen → blok hitam → **cabaran terakhir** (3 hakim), pilih satu jenis.",G+" ; label 'CABARAN AKHIR'",SP,"Ya","Inset: bilik → Minecraft"),
(1020.69,1056.78,"Pemain menjawab soalan Hakim C1 (tiada suara).",G,FAST,"Tiada","Inset: bilik → Minecraft"),
(1056.78,1093.1,"Bahagian **keputusan**, pijak blok **emas** → **pingat** ikut markah; kembali ke menu utama untuk tamat.",G,SP,"Ya","Inset: bilik → Minecraft"),
(1093.1,1101.27,"Gameplay penutup (tiada suara) → fade ke penutup. Skrin hitam asal 5.1 s di hujung dibuang.",G+" ; fade-out",FAST,"Tiada","Inset: bilik → Minecraft"),
]
out=[]
out.append("| # | Mula (output) | Tamat (output) | Asal (rakaman) | Kandungan babak | Jenis penyuntingan | Kelajuan | Sari kata | Perubahan latar belakang |")
out.append("|---|---|---|---|---|---|---|---|---|")
out.append(f"| 0 | 00:00.0 | {f(TITLE)} | — (baharu) | Animasi pembukaan: VIDEO PENERANGAN / CARA BERMAIN DUNIA MINECRAFT EDUCATION / **MISI PENYELAMAT AYAT** + nama, institusi, kursus | Grafik tajuk animasi (blok jatuh, panel piksel), muzik latar lembut | — | Tiada (teks tajuk) | Landskap Minecraft dari dunia anda |")
for i,(a,b,c,e,s,sub,bg) in enumerate(S,1):
    out.append(f"| {i} | {f(o(a))} | {f(o(b))} | {f(a)}–{f(b)} | {c} | {e} | {s} | {sub} | {bg} |")
end=TITLE+rows[-1][5]
out.append(f"| {len(S)+1} | {f(end)} | {f(end+CRED)} | — (baharu) | **SETINGGI-TINGGI PENGHARGAAN** kepada pensyarah yang dihormati **PUAN JULINA BINTI TARIKAT**, Pensyarah EDUP3133: Teknologi untuk Pengajaran dan Pembelajaran, Institut Pendidikan Guru Kampus Tun Hussein Onn | Kad penutup bertema Minecraft (sepadan pembukaan), muzik lembut, fade ke hitam | — | Tiada (teks kad) | Landskap Minecraft |")
open("/home/user/work/table.md","w").write("\n".join(out))
print(f"TOTAL {f(end+CRED)}")
