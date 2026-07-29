---
name: export
track: core
kind: action
provider: none
requires_env: []
inputs: [content, filename, confirmed]
outputs: [status, path, chars_written]
side_effect: local_file_write
requires_confirmation: true
---
# export

Saves a finished markdown digest to a local file under `exports/`.

Use it only when the digest text already exists — it does not fetch or format
anything itself. The file is written only when `confirmed` is true; the first
call always returns `needs_confirmation` with a short preview so the user can
approve the exact content before anything touches disk.

Unlike `send`, the output stays on the local machine and never leaves the
conversation.
