---
name: select_items
track: core
kind: control
provider: none
requires_env: []
inputs: [items, question, allow_multiple]
outputs: [question, options, item_count, allow_multiple, awaiting_user]
side_effect: false
---
# select_items

Human-in-the-loop curation step. Given items already collected by a research
tool, it renders them as a numbered list and pauses the agent so a person can
choose which ones survive into the digest.

It returns `awaiting_user: true`, which is the flag `chat.py` and `app.py` use to
stop the tool loop and hand control back to the user. The agent must wait for the
next user turn and then continue with only the chosen items.

Different from `clarify`: `clarify` asks for information the agent is missing,
while `select_items` presents information the agent already has and asks a human
to make an editorial decision about it.

Typical pipeline: `lookup` → `select_items` → `cite_check` → `format` → `export`.
