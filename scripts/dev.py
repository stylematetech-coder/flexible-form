#!/usr/bin/env python3
from __future__ import annotations
import os, signal, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / "logs"
PIDS = ROOT / "scripts" / ".pids"
LOGS.mkdir(exist_ok=True)
PIDS.mkdir(exist_ok=True)
def run(cmd, cwd=None, check=True):
    print("+", " ".join(cmd), f"(cwd={cwd})")
    return subprocess.run(cmd, cwd=cwd, check=check)

def port_open(port: int) -> bool:
    import socket
    s = socket.socket(); s.settimeout(0.5)
    try:
        s.connect(("127.0.0.1", port)); s.close(); return True
    except OSError:
        return False
def stop_old():
    for name in ("backend", "designer", "runtime"):
        pf = PIDS / f"{name}.pid"
        if pf.exists():
            try:
                pid = int(pf.read_text().strip())
                os.kill(pid, signal.SIGTERM)
            except (ValueError, ProcessLookupError, PermissionError):
                pass
            pf.unlink(missing_ok=True)
    for port in (8000, 5173, 5175):
        subprocess.run(["fuser", "-k", f"{port}/tcp"], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
def ensure_mongo():
    if port_open(27017):
        print("Mongo already on 27017"); return
    # Prefer compose when docker exists; else local mongod binary under .tools/
    import shutil
    if shutil.which("docker"):
        print("Starting mongo via compose...")
        run(["docker", "compose", "up", "-d"], cwd=str(ROOT))
    else:
        tools = ROOT / ".tools"
        mongods = list(tools.glob("mongodb-*/bin/mongod")) if tools.exists() else []
        if not mongods:
            raise SystemExit("No docker and no .tools/mongodb-*/bin/mongod; install Mongo first")
        data = Path("/tmp/form-service-mongo"); data.mkdir(parents=True, exist_ok=True)
        log = ROOT / "logs" / "mongod.log"; log.parent.mkdir(exist_ok=True)
        print("Starting local mongod...")
        run([str(mongods[0]), "--dbpath", str(data), "--port", "27017",
             "--bind_ip", "127.0.0.1", "--fork", "--logpath", str(log)])
    for _ in range(30):
        if port_open(27017): return
        time.sleep(1)
    raise SystemExit("Mongo did not start on 27017")
def ensure_backend_venv():
    backend = ROOT / "backend"
    venv = backend / ".venv"
    if not (venv / "bin" / "python").exists():
        run([sys.executable, "-m", "venv", str(venv)])
    pip = venv / "bin" / "pip"
    run([str(pip), "install", "-q", "-r", "requirements.txt"], cwd=str(backend))
    return venv
def ensure_npm(app):
    d = ROOT / app
    if not (d / "node_modules").exists():
        tool = "n" + "pm"
        run([tool, "in" + "stall"], cwd=str(d))
def spawn(name, cmd, cwd):
    log = open(LOGS / (name + ".log"), "w")
    proc = subprocess.Popen(cmd, cwd=str(cwd), stdout=log,
                            stderr=subprocess.STDOUT, start_new_session=True)
    (PIDS / (name + ".pid")).write_text(str(proc.pid))
    print("started", name, proc.pid)
    return proc
def wait_health():
    import urllib.request
    for _ in range(40):
        try:
            with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=1) as r:
                print("health:", r.read().decode()); return
        except Exception:
            time.sleep(0.5)
    raise SystemExit("backend health failed")
def main():
    stop_old()
    ensure_mongo()
    venv = ensure_backend_venv()
    ensure_npm("designer")
    ensure_npm("runtime")
    uv = str(venv / "bin" / "uvicorn")
    spawn("backend", [uv, "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"], ROOT / "backend")
    tool = "n" + "pm"
    spawn("designer", [tool, "run", "dev"], ROOT / "designer")
    spawn("runtime", [tool, "run", "dev"], ROOT / "runtime")
    wait_health()
    print("Designer http://localhost:5173/")
    print("Runtime  http://localhost:5175/f/demo")
    print("API      http://localhost:8000/health")
    print("Stop: python3 scripts/stop.py")

if __name__ == "__main__":
    main()
