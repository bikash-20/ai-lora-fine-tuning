# Security boundaries

- The system prompt marks retrieved documents as untrusted data and prohibits following their embedded instructions.
- Document context is encoded as JSON data by `app/security/tool_boundary.py`; it does not become executable tool arguments.
- File access defaults to denied and must be resolved under an application-approved root.
- The model is not authorized to execute arbitrary shell commands. Tool execution remains an application responsibility and is not implemented by this data-preparation phase.
- Tests cover an injected document instruction, file access outside approved roots, and approved path resolution.
