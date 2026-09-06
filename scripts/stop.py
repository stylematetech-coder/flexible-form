#!/usr/bin/env python3
import os, signal, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
PIDS = ROOT / "scripts" / ".pids"
for name in ("backend", "designer", "runtime"):
    pf = PIDS / (name + ".pid")
    if pf.exists():
        try:
            pid = int(pf.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            print("stopped", name, pid)
        except Exception as e:
            print(name, e)
        pf.unlink(missing_ok=True)
for port in (8000, 5173, 5175):
    subprocess.run(["fuser", "-k", f"{port}/tcp"], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("done")
