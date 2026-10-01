# Stage 4 TEST native peer bridge — implementation in progress

Trusted Electron main-process callers only. No renderer export, process launch,
Store, credentials, voice, ACL changes or arbitrary PID/path lookup is provided.

`connectTestPipe(name, pin)` accepts only a local TEAGUE-TEST hexadecimal namespace.
The caller supplies independently pinned PID, creation-time decimal string and
executable SHA256. The actual connected pipe supplies the inspected PID. No bytes
are sent before all three values match. The connection owns non-inheritable
handles and uses identification-only SQOS. It supports bounded 8192-byte framed
messages on that same handle, with a five-second connection deadline. Identity
evidence does not itself authorize attachment: Stage 2 transcript authentication
and client/session scope checks remain required in the JS adapter.

`currentProcessIdentity()` observes only this process, never a supplied PID.
Creation time is a decimal string to avoid JavaScript Number precision loss.

Approved isolated extension: `connectTestPipe(name, peerPin, corePin)` captures
one independently pinned Core identity from trusted main-process state. The
connection's `verifyCore()` accepts no arguments and returns true on a live
PID/creation-time/executable-digest match; otherwise it throws. It checks the
original pipe peer before and after the observation. It returns no process
information and cannot change the captured pin. No renderer interface is added.
The main adapter calls it after verifying the signed transcript and before
sending the client proof. This preserves the separate bootstrap/Core process
case from Stage 2; it does not grant lifecycle or tool authority.

Validation: 15 native cases, 6 authenticated-transcript interoperability cases,
and 6 JavaScript tests passed. Separate-process probes use idle disposable
processes, not another JARVIS App/Core. Actual PID reuse is not forced; mismatched
creation times and terminated processes are tested. A live observation does
not promise the process cannot exit afterward. Full Stage 4 acceptance is pending.

Build in a local development cache with CMake, setting ELECTRON_HEADERS to the
verified matching headers/include/node directory and ELECTRON_NODE_LIB to the
verified matching win-x64/node.lib. No installation/download logic is included.
The target includes Electron's required Windows delay-load hook.

No production use is authorized. Tests and complete Stage 4 acceptance remain
outstanding. Like the accepted Stage 2 transport, timeout cancellation waits for
the OS to retire OVERLAPPED storage; a pathological driver cancellation stall is
not proven bounded. This must be reviewed before calling the bridge's total
wall-clock shutdown behavior bounded or integrating it with lifecycle draining.
