import json,re,sys
T=json.load(open(sys.argv[1]))
words=[w for s in T for w in s["words"]]
# speech intervals from words; merge gaps < 2.0s
iv=[]
for w in words:
    s,e=w["s"],w["e"]
    if e-s>3.0: e=s+1.0   # long word = likely stretched over silence
    if iv and s-iv[-1][1]<2.0: iv[-1][1]=max(iv[-1][1],e)
    else: iv.append([s,e])
sil=[]
for line in open(sys.argv[2]):
    m=re.search(r"silence_start: ([\d.]+)",line)
    if m: st=float(m.group(1))
    m=re.search(r"silence_end: ([\d.]+)",line)
    if m: sil.append((st,float(m.group(1))))
print("speech intervals:",len(iv))
prev=0
for a,b in iv:
    gap=a-prev
    if gap>=4: print(f"  GAP {prev:7.2f}-{a:7.2f}  ({gap:5.1f}s)")
    prev=b
print(f"  GAP {prev:7.2f}-1106.43 ({1106.43-prev:.1f}s)")
for w in words:
    if w["e"]-w["s"]>3: print("long word",w)
