import json,wave,numpy as np
T=json.load(open("transcript.json"))
words=[w for s in T for w in s["words"] if not (w["s"]>=1091.9) and not (608<w["s"]<610)]  # drop end hallucinations + misaligned word
words.append(dict(s=699.8,e=700.3,w="Pemain",p=1))
# add missed words (no-VAD pass) 445.7-451.2
words.append(dict(s=445.74,e=451.2,w="[Untuk soalan jenis kedua ini...]",p=1))
words.sort(key=lambda w:w["s"])
iv=[]
for w in words:
    s,e=w["s"],min(w["e"],w["s"]+2.5)
    if iv and s-iv[-1][1]<2.0: iv[-1][1]=max(iv[-1][1],e)
    else: iv.append([s,e])
END=1101.27  # black tail starts
PRE,POST,RAMP=0.8,0.5,0.6
segs=[]; t=0.0
def add(a,b,sp,kind):
    if b-a>1e-3: segs.append([a,b,sp,kind])
for i,(a,b) in enumerate(iv):
    gs,ge=t,a
    g=ge-gs
    if i==0 or g<6.0: add(gs,ge,1.0,"jeda pendek")
    else:
        sp=1.5 if g>=20 else 1.4
        add(gs,gs+POST,1.0,"jeda pendek")
        add(gs+POST,gs+POST+RAMP,(1+sp)/2,"ramp-naik")
        add(gs+POST+RAMP,ge-PRE-RAMP,sp,"senyap")
        add(ge-PRE-RAMP,ge-PRE,(1+sp)/2,"ramp-turun")
        add(ge-PRE,ge,1.0,"jeda pendek")
    add(a,b,1.0,"penerangan"); t=b
g=END-t; sp=1.5
add(t,t+POST,1.0,"jeda pendek"); add(t+POST,t+POST+RAMP,1.25,"ramp-naik"); add(t+POST+RAMP,END,sp,"senyap")
out=sum((b-a)/s for a,b,s,k in segs)
print("speech iv",len(iv),"orig",END,"new",round(out,1))
json.dump(dict(speech=iv,segments=segs),open("plan.json","w"),indent=1)
for a,b,s,k in segs:
    if k in("senyap",): print(f"  {a:7.2f}-{b:7.2f} {b-a:5.1f}s @{s}x")
