#!/usr/bin/env python3
"""SPEAK — turn each case's line into an audio file with any CLI TTS.

The TTS engine is a command template from the cases file, e.g.
  "tts_command": "edge-tts --voice en-US-GuyNeural --text {text} --write-media {output}"
  "tts_command": "piper --model en_US-lessac-medium --output_file {output} --stdin"
Placeholders: {text} (the line to say), {output} (target audio path).
Piper-style engines that read stdin get the text on stdin as well.
"""
import argparse, json, os, shlex, subprocess, sys

def speak_all(cases_path, audio_dir):
    cfg = json.load(open(cases_path))
    template = cfg.get("tts_command")
    if not template:
        sys.exit("cases file has no 'tts_command' — set one (see cases.example.json)")
    os.makedirs(audio_dir, exist_ok=True)
    written = []
    for case in cfg["cases"]:
        out = os.path.join(audio_dir, case["id"] + ".mp3")
        cmd = [part.replace("{text}", case["say"]).replace("{output}", out)
               for part in shlex.split(template)]
        print(f"[speak] {case['id']}: {case['say']!r}")
        subprocess.run(cmd, input=case["say"], text=True, check=True)
        if not os.path.exists(out):
            sys.exit(f"TTS did not produce {out}")
        written.append(out)
    return written

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default="cases.json")
    ap.add_argument("--audio-dir", default="audio")
    a = ap.parse_args()
    speak_all(a.cases, a.audio_dir)
    print("[speak] done")
