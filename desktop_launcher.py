"""JARVIS desktop entry point for PyInstaller/portable builds."""
import os, subprocess, sys, time, urllib.request, threading
from pathlib import Path

def main():
    root = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
    port = int(os.getenv('JARVIS_PORT', '8765'))
    if getattr(sys, 'frozen', False):
        import server
        server_thread = threading.Thread(target=server.main, daemon=True)
        server_thread.start()
        process = None
    else:
        process = subprocess.Popen([sys.executable, str(root / 'server.py'), '--port', str(port)], cwd=root)
    url = f'http://127.0.0.1:{port}'
    try:
        for _ in range(40):
            try: urllib.request.urlopen(url, timeout=1).close(); break
            except Exception: time.sleep(.25)
        edge = Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / 'Microsoft/Edge/Application/msedge.exe'
        subprocess.Popen([str(edge), '--app=' + url]) if edge.exists() else os.startfile(url)
        if process is not None: process.wait()
    except KeyboardInterrupt: pass
    finally:
        if process is not None and process.poll() is None: process.terminate()

if __name__ == '__main__': main()
