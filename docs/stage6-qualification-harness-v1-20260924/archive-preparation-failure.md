# Preserved archive preparation failure

The first archive preparation stopped at `assert b'asInvoker' in binary` with AssertionError. This unsupported manifest assumption was in evidence packaging only. The archive destination had not been created; no qualification run was launched and no bound candidate changed.

The corrected evidence check uses the preserved successful ordinary subprocess.Popen/CreateProcess selftest and its exact launcher source. It makes no claim that an asInvoker manifest is embedded. Existing final-syntax.json and compiler-identity.json are preserved; the corrected archive script records a separate final-syntax-2.json.
