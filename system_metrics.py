"""Real readings of this PC for the Command dashboard: processor, memory and disk use, measured by the Core.
Windows APIs through ctypes (no extra packages). Nothing is estimated: a value that cannot be read is None."""
import ctypes
import shutil
import sys
import threading
import time

_lock = threading.Lock()
_previous = None  # (idle, kernel, user) from the last reading, for the processor share between two readings


class _FileTime(ctypes.Structure):
    _fields_ = [('low', ctypes.c_uint32), ('high', ctypes.c_uint32)]


class _MemoryStatus(ctypes.Structure):
    _fields_ = [('length', ctypes.c_uint32), ('load', ctypes.c_uint32), ('total_phys', ctypes.c_uint64),
                ('avail_phys', ctypes.c_uint64), ('total_page', ctypes.c_uint64), ('avail_page', ctypes.c_uint64),
                ('total_virtual', ctypes.c_uint64), ('avail_virtual', ctypes.c_uint64), ('avail_extended', ctypes.c_uint64)]


def _system_times():
    """(idle, kernel, user) in 100-nanosecond units since boot; kernel time includes idle time."""
    if sys.platform != 'win32':
        return None
    idle, kernel, user = _FileTime(), _FileTime(), _FileTime()
    if not ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
        return None
    return tuple(t.high << 32 | t.low for t in (idle, kernel, user))


def cpu_percent():
    """Share of processor time spent busy since the previous call; None on the first call or when unreadable."""
    global _previous
    current = _system_times()
    with _lock:
        previous, _previous = _previous, current
    if not current or not previous:
        return None
    idle, kernel, user = (now - before for now, before in zip(current, previous))
    total = kernel + user
    if total <= 0:
        return None
    return round(max(0.0, min(100.0, (total - idle) * 100 / total)), 1)


def memory():
    if sys.platform != 'win32':
        return None
    status = _MemoryStatus()
    status.length = ctypes.sizeof(_MemoryStatus)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return None
    return {'used_percent': int(status.load), 'total_bytes': int(status.total_phys), 'available_bytes': int(status.avail_phys)}


def disk(path):
    try:
        usage = shutil.disk_usage(path)
    except OSError:
        return None
    return {'used_percent': round(usage.used * 100 / usage.total, 1) if usage.total else None,
            'free_bytes': usage.free, 'total_bytes': usage.total}


def snapshot(data_root, started, timings):
    """One reading for /api/metrics. `timings` are the Core's recent response timings (server.App.timings)."""
    answered = [t for t in timings if not t.get('cancelled') and t.get('elapsed_ms') is not None]
    return {'sampled_at': time.time(), 'cpu_percent': cpu_percent(), 'memory': memory(), 'disk': disk(data_root),
            'core_uptime_seconds': int(time.time() - started),
            'last_response_ms': answered[-1]['elapsed_ms'] if answered else None,
            'responses_measured': len(answered),
            'scope': 'This PC, read by the JARVIS Core at sampled_at. Processor use is the busy share since the previous '
                     'reading; disk is the drive holding JARVIS data; response time is the last completed request in this '
                     'Core session. Graphics, temperature and network traffic are not measured.'}
