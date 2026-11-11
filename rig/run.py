#!/usr/bin/env python3
"""RUN — speak -> hear -> drive, then write a report with the receipts.

Usage: python -m rig.run --cases cases.json [--report voice-rig-report.md]
Exit code is non-zero when any case fails any check.
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rig.speak import speak_all
from rig.hear import hear_all
from rig.drive import drive_all

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default="cases.json")
    ap.add_argument("--model", default="tiny")
    ap.add_argument("--audio-dir", default="audio")
    ap.add_argument("--report", default="voice-rig-report.md")
    a = ap.parse_args()
    os.makedirs(a.audio_dir, exist_ok=True)
    speak_all(a.cases, a.audio_dir)
    transcripts_path = os.path.join(a.audio_dir, "..", "transcripts.json")
    hear_all(a.cases, a.audio_dir, a.model, transcripts_path)
    results = drive_all(a.cases, transcripts_path)
    lines = ["# Voice Test Rig — run report", "",
             "Transcripts below are exactly as the recognizer produced them — never corrected.", ""]
    all_ok = True
    for r in results:
        ok = all(c["ok"] for c in r["checks"])
        all_ok = all_ok and ok
        lines += [f"## Case `{r['case']}` — {'PASS' if ok else 'FAIL'}", "",
                  f"- **Said:** {r['said']}", f"- **Heard:** {r['heard']}"]
        for c in r["checks"]:
            lines.append(f"- {'✅' if c['ok'] else '❌'} {c['check']} — {c['detail']}")
        lines.append("")
    lines += ["---", "Synthetic speech in a clean file is not the user's voice, mic, or room.",
              "The last mile — real hardware — still needs a run on the target machine."]
    open(a.report, "w").write("\n".join(lines) + "\n")
    json.dump(results, open(a.report.replace(".md", ".json"), "w"), indent=2)
    print(f"[run] report written to {a.report} — {'ALL PASS' if all_ok else 'FAILURES PRESENT'}")
    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()
