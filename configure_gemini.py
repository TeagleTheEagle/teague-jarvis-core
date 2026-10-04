"""Local, masked credential setup. Never sends conversation history or prints keys."""
import json
import datetime
import os
from pathlib import Path
import queue
import re
import threading
import tkinter as tk
from tkinter import ttk
import providers

ROOT = Path(__file__).resolve().parent


def save_config(key):
    path = ROOT / '.env'
    text = path.read_text(encoding='utf-8-sig') if path.exists() else ''
    updates = {'GEMINI_API_KEY': key, 'GEMINI_MODEL': providers.GEMINI_DEFAULT_MODEL, 'JARVIS_PROVIDER': 'gemini'}
    lines = [line for line in text.splitlines()
             if line.partition('=')[0].strip() not in updates]
    lines.extend(f'{name}={value}' for name, value in updates.items())
    # Same-directory atomic replacement; no extra backup containing credentials.
    temp = ROOT / '.env.gemini-setup.tmp'
    try:
        temp.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def main():
    window = tk.Tk()
    window.title('JARVIS — Connect Gemini locally')
    window.geometry('640x340')
    window.minsize(640, 340)
    window.attributes('-topmost', True)
    window.after(500, window.lift)
    window.after(3000, lambda: window.attributes('-topmost', False))
    frame = ttk.Frame(window, padding=24)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text='Connect Gemini to JARVIS', font=('Segoe UI', 16)).pack(anchor='w')
    ttk.Label(frame, wraplength=585, text='Paste your key below. It stays in the local .env file. The test sends only “Reply with only READY.” to Google. Your existing voice settings are preserved.').pack(anchor='w', pady=12)
    ttk.Label(frame, wraplength=585, text=f'Model: {providers.GEMINI_DEFAULT_MODEL}. Confirm your project shows Free tier in AI Studio. Free-tier content may be used to improve Google products; normal JARVIS chats include relevant memory/context.').pack(anchor='w')
    entry = ttk.Entry(frame, show='*', width=70)
    entry.pack(fill='x', pady=14)
    status = tk.StringVar(value='Not tested. No configuration changed.')
    mailbox = queue.Queue()

    def connect():
        key = entry.get().strip()
        if not re.fullmatch(r'[A-Za-z0-9_-]{20,200}', key):
            status.set('Enter the API key without spaces or quotation marks.')
            return
        button.config(state='disabled')
        status.set('Testing Google connection…')

        def work():
            try:
                result = providers.request(
                    'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions',
                    {'model': providers.GEMINI_DEFAULT_MODEL, 'messages': [{'role': 'user', 'content': 'Reply with only READY.'}], 'max_completion_tokens': 8192},
                    {'Authorization': 'Bearer ' + key}, timeout=45)
                choice = (result.get('choices') or [{}])[0]
                if choice.get('finish_reason') != 'stop' or (choice.get('message') or {}).get('content', '').strip().rstrip('.') != 'READY':
                    raise providers.ProviderError('The expected test reply was not returned. Configuration unchanged.')
                save_config(key)
                (ROOT / 'review').mkdir(exist_ok=True)
                (ROOT / 'review' / 'gemini-connection.json').write_text(json.dumps({'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'generation': 'passed', 'model': providers.GEMINI_DEFAULT_MODEL, 'tools': 'not tested', 'voice': 'not tested'}), encoding='utf-8')
                mailbox.put('Connection passed. Gemini saved. Restart JARVIS to load it. Tool use and voice still need testing.')
            except providers.ProviderError as exc:
                mailbox.put(str(exc))
            except Exception:
                mailbox.put('Local setup failed. Check folder permissions; no success assumed.')
        threading.Thread(target=work, daemon=True).start()

    button = ttk.Button(frame, text='Test connection and save', command=connect)
    button.pack(anchor='w')
    ttk.Label(frame, textvariable=status, wraplength=585).pack(anchor='w', pady=12)

    def poll():
        try:
            status.set(mailbox.get_nowait())
            entry.delete(0, 'end')
            button.config(state='normal')
        except queue.Empty:
            pass
        window.after(150, poll)
    poll()
    entry.focus_set()
    window.mainloop()


if __name__ == '__main__':
    main()
