"""Explicit one-time model download. Never called during microphone use."""
from pathlib import Path
from huggingface_hub import snapshot_download

if __name__ == '__main__':
    directory = Path(__file__).resolve().parent / 'data' / 'speech-models' / 'base.en'
    snapshot_download('Systran/faster-whisper-base.en', local_dir=str(directory),
                      allow_patterns=['model.bin', 'config.json', 'tokenizer.json', 'vocabulary.*'])
    print('Local English speech model installed.')
