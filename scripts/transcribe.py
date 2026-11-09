import json, sys, time
from faster_whisper import WhisperModel
t=time.time()
m = WhisperModel(sys.argv[2], device="cpu", compute_type="int8", cpu_threads=4)
import wave, numpy as np
wf=wave.open(sys.argv[1]); audio=np.frombuffer(wf.readframes(wf.getnframes()),dtype=np.int16).astype(np.float32)/32768.0
segs, info = m.transcribe(audio, language="ms", word_timestamps=True, vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=700), beam_size=5,
    initial_prompt="Minecraft Education, Misi Penyelamat Ayat, Mohamad Aliff bin Ahmad Shahabuddin, Puan Julina binti Tarikat, EDUP3133, Institut Pendidikan Guru Kampus Tun Hussein Onn.")
out=[]
for s in segs:
    d=dict(start=s.start,end=s.end,text=s.text.strip(),words=[dict(s=w.start,e=w.end,w=w.word,p=w.probability) for w in (s.words or [])])
    out.append(d); print(f"[{s.start:7.2f}-{s.end:7.2f}] {s.text.strip()}", flush=True)
json.dump(out, open(sys.argv[3],"w"), ensure_ascii=False, indent=1)
print("DONE", time.time()-t, flush=True)
