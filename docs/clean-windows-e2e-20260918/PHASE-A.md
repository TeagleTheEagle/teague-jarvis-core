# Phase A audit — complete; execution prerequisites explicit

Eight hardened file hashes match the prior review. Scripts inspected read-only.
Setup-Windows.ps1 -> check_windows_setup.py -> requirements.txt, optional requirements-local-voice.txt and requirements-test.txt -> post-install native imports.

Order: disposable full clone of CLEAN-WIN11-BASELINE; record guest state; official manual Python 3.12 x64 + py launcher, Node 24.x and VC++ x64 installers as documented; run documented CheckOnly, then setup, then explicit model provisioning; offline regressions; functional tests after secure external configuration; repeatability.

System prerequisites are detected, NOT installed by this automation. With no Python launcher the checker cannot itself start. Node is found through PATH; Python through py -3.12 or a compatible existing venv. Thus pre-existing Node/VC++ are required at script invocation, although the documented manual preparation allows a genuinely clean starting machine. No claim of zero-touch system provisioning is made.

No existing venv/cache/Codex runtime/old build/registry state required by setup. Pip/network package indexes and the py/Node command discovery are dependencies. Existing venv is reused only if version/bitness pass. Dependencies are not fully transitively locked; npm/model provisioning remain explicit separate steps. No deployment payload or credentials have been transferred. Setup neither reads nor copies .env. Existing launcher fallback behavior is outside hardening and must not be mistaken for a validated packaged deployment.

If guest execution policy blocks the documented PS invocation, STOP: no documented alternate invocation exists. Do not change policy or reinterpret the script to bypass it.

Original VM powered off; protected snapshot IDs recorded. Independent full clone only, not linked clone, restore, or execution of original. Host free space approximately 47 GiB, baseline disk allocated approximately 26 GiB. Existing snapshot content will not be written by guest validation.
