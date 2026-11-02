"""Paso 1 del reel: clona la voz y narra escena por escena, sin cargar Whisper (ahorra memoria en Macs de 8 GB).
Cada escena se guarda al terminar; si se interrumpe, retoma donde quedó.
Uso, desde la raíz: python reel/generar_voz.py reel/recursos/mi_voz.m4a [cpu|mps]"""
import json, sys, time
from pathlib import Path
import soundfile as sf, torch
from qwen_tts import Qwen3TTSModel
sys.path.insert(0, "reel")
import motor_sesion15 as m

REF = ("En el Perú, los datos nos ayudan a entender quiénes viven en pobreza. Hoy quiero mostrarles qué nos dice la Encuesta "
       "Nacional de Hogares sobre los niños, los adultos mayores y las regiones del país. Detrás de cada cifra hay una familia, "
       "y por eso vale la pena mirar los números con cuidado.")
S = Path("reel/recursos"); disp = sys.argv[2] if len(sys.argv) > 2 else "mps"
t0 = time.time()
tts = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-0.6B-Base", device_map=disp, dtype=torch.float32)
prompt = tts.create_voice_clone_prompt(ref_audio=(m.cargar_audio(sys.argv[1]), 16000), ref_text=REF)
print(f"cargado {time.time()-t0:.0f}s", flush=True)
for i, e in enumerate(json.load(open("reel/guion.json"))["escenas"]):
    f = S / f"narracion_{i}.wav"
    if f.exists(): continue
    t = time.time()
    w, sr = tts.generate_voice_clone(text=[e["frase"]], language=["Spanish"], voice_clone_prompt=prompt)
    sf.write(f, w[0], sr); print(f"escena {i}: {len(w[0])/sr:.1f}s de audio en {time.time()-t:.0f}s", flush=True)
print("VOZ LISTA", flush=True)
