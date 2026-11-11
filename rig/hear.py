#!/usr/bin/env python3
"""HEAR — transcribe the spoken files with a LOCAL speech recognizer.

Uses faster-whisper (CTranslate2 Whisper). Nothing leaves the machine.
The transcript is written exactly as recognized — mishearings included.
Correcting a transcript before driving the app would invalidate the test.
"""
import argparse, json, os, sys

def hear_all(cases_path, audio_dir, model_size, out_path, language="en"):
    from faster_whisper import WhisperModel  # lazy: keeps rig imports stdlib-light
    cfg = json.load(open(cases_path))
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    transcripts = {}
    for case in cfg["cases"]:
        path = os.path.join(audio_dir, case["id"] + ".mp3")
        if not os.path.exists(path):
            sys.exit(f"missing audio for case {case['id']}: {path} (run speak.py first)")
        segments, _info = model.transcribe(path, language=language or None, beam_size=1)
        text = " ".join(s.text.strip() for s in segments).strip()
        transcripts[case["id"]] = text
        print(f"[hear] {case['id']}: {text!r}")
    json.dump(transcripts, open(out_path, "w"), indent=2)
    print(f"[hear] wrote {out_path}")
    return transcripts

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default="cases.json")
    ap.add_argument("--audio-dir", default="audio")
    ap.add_argument("--model", default="tiny", help="whisper size: tiny|base|small (tiny is fine for clean TTS speech)")
    ap.add_argument("--language", default="en")
    ap.add_argument("--out", default="transcripts.json")
    a = ap.parse_args()
    hear_all(a.cases, a.audio_dir, a.model, a.out, a.language)
