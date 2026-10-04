"""Put the current UTC clock time into an evidence record in place of the marker @@NOW@@.

Records written by hand carry the marker where a timestamp belongs, so that no time is ever typed by estimate.
The file must be valid JSON after stamping; it is written back unchanged otherwise.

  python tools\\host\\stamp_record.py <file> [<file> ...]
"""
import datetime
import json
import sys
from pathlib import Path

MARKER = '@@NOW@@'


def main():
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    for name in sys.argv[1:]:
        path = Path(name)
        text = path.read_text(encoding='utf-8')
        if MARKER not in text:
            sys.exit(f'STOP: no {MARKER} marker in {path}')
        stamped = text.replace(MARKER, now)
        json.loads(stamped)
        path.write_text(stamped, encoding='utf-8', newline='\n')
        print(f'{now}  {path}')


if __name__ == '__main__':
    main()
