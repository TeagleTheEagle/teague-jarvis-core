# Required coverage correction

Scope: new TEST candidate only. Frozen checker, production and preserved evidence remain unchanged.

| Class | Kernel START / identity / STOP | Retained handle / creation / full image / exit | Native PE entry | Parent identity |
|---|---|---|---|---|
| Controlled probe | Mandatory | Mandatory | Mandatory | Mandatory |
| Qualification worker | Mandatory | Mandatory | Mandatory | Mandatory |
| OS-created console helper | Mandatory | Mandatory on successful acquisition; only the existing error-87, acquisition-began-after-kernel-STOP qualification is permitted | Not applicable: not an owned debugger launch | Mandatory |
| Application observer and its helper | Kernel completeness remains checked; separate infrastructure classification | Same recorded acquisition rules; observer launch/exit checked separately | Not applicable in this qualification | Mandatory |
| Kernel observer / outer launcher | Explicit infrastructure identities and clean exit; cannot self-observe a complete lifecycle | Existing launcher/host cleanup evidence | Not applicable | Root identity verified |

Optional evidence: supporting CIM may be ambiguous/unmatched, but collection and durable persistence are mandatory. Optional supplemental annotations cannot substitute for any mandatory channel.

Expected coverage is derived from declared worker/probe launch identities plus ALL authoritative kernel instances, never from the supplied verification lists. Unknown process classes fail. Empty required inventories or verification lists fail. Every field gets PRESENT_AND_VALID, PRESENT_BUT_CONTRADICTORY, MISSING_AND_REQUIRED, MISSING_BUT_OPTIONAL or NOT_APPLICABLE. A qualified post-exit exception is separately counted and requires its exact existing proof; omission alone never qualifies.

Full image means QueryFullProcessImageNameW on a creation-matched retained process handle, normalized with the current QueryDosDevice mapping. A basename or a copied kernel image string is insufficient.

Capture change: query full image immediately after GetProcessTimes matches the kernel creation identity; retain until exit reconciliation. Launch the controlled worker on a dedicated C# task through the existing own-child native debugger, preserving the worker command, original deadlines, release-handles sequence and per-run UAC. The native launcher records creation identity before debugger continuation. No arbitrary command interface is added.

Worker native PE evidence remains mandatory. OS console helper PE entry remains not applicable under the existing native-entry design. No classification is selected merely because evidence is missing.

Rollback: abandon the new candidate; preserved candidate a684e9f6f9ae4826af45c0a04c18d839 and its archived failure remain unchanged. Do not merge into the frozen acceptance checker. This pass ends at fresh kernel qualification, without combined validation.
