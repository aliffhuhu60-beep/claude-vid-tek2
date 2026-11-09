import json,re
T=json.load(open("/home/user/work/transcript.json"))
FIX=[("bersyarah","pensyarah"),("subjek teknologi dalam pengajaran dan pembelajaran","subjek Teknologi dalam Pengajaran dan Pembelajaran"),
("Puan Craft Education","Minecraft Education"),("Pilih zamro untuk","Pilih zamrud untuk"),("untuk milih","untuk memilih"),
("selamat datang ke misi penyelamat ayat","Selamat Datang ke Misi Penyelamat Ayat"),("makah","markah"),("Pemainan","Permainan"),("pemainan","permainan"),
("gebang berwarna umur","gerbang berwarna ungu"),("Biru, merah","biru, merah"),("telah diberapakan","telah diberikan"),("markah 100 markah","100 markah"),
("betul kelima soalan","betul kelima-lima soalan"),("front gambar","frame gambar"),("ke lima-lima","kelima-lima"),
("peparan kapan","papan tanda"),("aktiviti pakor","aktiviti parkour"),("Sebenarnya pemain terjatuh","Sekiranya pemain terjatuh"),
("terus riset semuanya.","terus di-reset semula,"),("ucapan tanya","ucapan tahniah"),("pemain aku boleh","pemain boleh"),("lobby","lobi"),
("memulukan","memulakan"),("dimulukan","dimulakan"),("Setelah berpermain memilih,","Setelah pemain memilih,"),("saya bersedia","\"Saya bersedia\""),
("station","stesen"),("cebaran","cabaran"),("Cebaran","Cabaran"),("menijak","memijak"),("pingat apa yang sesuai","pingat yang sesuai"),
("dunia penyelamat","dunia Penyelamat"),("Enter Join Code","Enter Join Code"),("code telah","kod telah"),("glowstone","glowstone"),("riset","reset")]
out=[]
for s in T:
    if s["start"]>=1091.9: continue
    t=s["text"]
    for a,b in FIX: t=t.replace(a,b)
    st=s["start"]
    if 608<st<609: st=699.8
    if 96<st<97: st=117.0
    if 240<st<241: st=240.1
    out.append((st,s["end"],t))
# insert missed line
out.append((445.74,451.2,"[ulangan] Untuk soalan jenis kedua ini, pemain perlu memilih peti yang pertama dan peti yang kedua."))
out.sort()
json.dump(out,open("/home/user/work/subs_draft.json","w"),ensure_ascii=False,indent=0)
def f(t): m,s=divmod(t,60); return f"{int(m):02d}:{s:04.1f}"
for st,en,t in out: print(f"{f(st)} | {t}")
