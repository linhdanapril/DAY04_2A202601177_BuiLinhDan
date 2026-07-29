---
name: cite_check
track: core
kind: local_knowledge
provider: none
requires_env: []
inputs: [items, strict]
outputs: [verdict, checked, tier_counts, violation_count, violations]
side_effect: false
---
# cite_check

Validates a list of already-collected items against
`company_policy/source-citation-policy.md` before they are formatted or shared.

Rules enforced, taken from that policy:

- every item needs a source URL and a source name;
- Tier 3 evidence (social posts, forums) may be used as signal only, so its
  summary must carry a weak-evidence label such as "unverified" or
  "early signal";
- `strict=true` rejects Tier 3 items outright.

Tier is derived from the URL host: arXiv, official vendor blogs, `.gov` and
`.edu` count as Tier 1; known social hosts count as Tier 3; everything else is
Tier 2. The tool reads no network and calls no model — it only inspects the
items it is handed.

`verdict` is `pass` when there are no violations, `needs_review` otherwise.
