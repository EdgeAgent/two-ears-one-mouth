#!/usr/bin/env python3
"""DRIVE — feed the recognized transcripts into the app under test and
score the responses against each case's expectations.

The reference adapter targets Robot Orchestra's local voice API
(POST /api/voice/enable|wake|command, GET /api/voice/status). Any app with
an equivalent transcript-in endpoint can be adapted by changing the
'endpoints' map in the cases file and the payload keys below.

RULE: transcripts go in exactly as the recognizer produced them.
"""
import json, urllib.request, urllib.error

def call(base, path, payload=None):
    req = urllib.request.Request(base + path, method="POST" if payload is not None else "GET")
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data=data, timeout=20) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}

def pending_of(*responses):
    for r in responses:
        if not isinstance(r, dict):
            continue
        if r.get("pendingApproval"):
            return r["pendingApproval"]
        state = r.get("state")
        if isinstance(state, dict) and state.get("pendingApproval"):
            return state["pendingApproval"]
    return None

def evaluate(case, wake_resp, cmd_status, cmd_resp, status_resp):
    """Pure scoring: returns a list of {check, ok, detail}. Unit-tested."""
    expect = case.get("expect", {})
    checks = []
    if "woke" in expect:
        got = bool(wake_resp.get("woke"))
        checks.append({"check": "wake word recognized and accepted",
                       "ok": got == bool(expect["woke"]), "detail": f"woke={got}"})
    if "routed_agent_contains" in expect:
        routed = cmd_resp.get("routed") or {}
        hay = f"{routed.get('agentName', '')} {routed.get('agentId', '')}".lower()
        ok = expect["routed_agent_contains"].lower() in hay and cmd_resp.get("ok") is True
        checks.append({"check": f"command routed to an agent matching '{expect['routed_agent_contains']}'",
                       "ok": ok, "detail": f"routed={routed} http={cmd_status}"})
    if expect.get("gate") == "pending_approval":
        pending = pending_of(cmd_resp, status_resp)
        executed = cmd_resp.get("ok") is True and not pending
        checks.append({"check": "risky command stopped at the approval gate (nothing executed)",
                       "ok": bool(pending) and not executed,
                       "detail": f"pendingApproval={pending} http={cmd_status}"})
    return checks

def drive_all(cases_path, transcripts_path):
    cfg = json.load(open(cases_path))
    transcripts = json.load(open(transcripts_path))
    app = cfg.get("app", {})
    base = app.get("base_url", "http://127.0.0.1:4178")
    ep = app.get("endpoints", {"enable": "/api/voice/enable", "wake": "/api/voice/wake",
                               "command": "/api/voice/command", "status": "/api/voice/status"})
    call(base, ep["enable"], {"enabled": True})
    results = []
    for case in cfg["cases"]:
        heard = transcripts[case["id"]]
        _s, wake = call(base, ep["wake"], {"transcript": heard})
        cmd_status, cmd = call(base, ep["command"], {"command": heard})
        _s, status = call(base, ep["status"])
        checks = evaluate(case, wake, cmd_status, cmd, status)
        if case.get("cleanup_say"):  # e.g. answer "no" to clear a pending approval
            call(base, ep["command"], {"command": case["cleanup_say"]})
        results.append({"case": case["id"], "said": case["say"], "heard": heard, "checks": checks})
        for c in checks:
            print(f"[drive] {case['id']}: {'PASS' if c['ok'] else 'FAIL'} — {c['check']} ({c['detail']})")
    return results

if __name__ == "__main__":
    import argparse, sys
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default="cases.json")
    ap.add_argument("--transcripts", default="transcripts.json")
    a = ap.parse_args()
    results = drive_all(a.cases, a.transcripts)
    failed = [r for r in results if not all(c["ok"] for c in r["checks"])]
    print(f"[drive] {len(results) - len(failed)}/{len(results)} cases passed")
    sys.exit(1 if failed else 0)
