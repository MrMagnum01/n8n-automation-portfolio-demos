#!/bin/sh
# Export the workflow from the live n8n and strip owner/project metadata (contains the owner account name).
set -e
docker exec n8n n8n export:workflow --id=invPdfToCsv01 --pretty --output=/tmp/out_inv2.json
docker cp n8n:/tmp/out_inv2.json "$(dirname "$0")/../workflow.json"
python3 - "$(dirname "$0")/../workflow.json" <<'PY'
import json, sys
p = sys.argv[1]
w = json.load(open(p))
w = w[0] if isinstance(w, list) else w
for k in ("shared", "versionMetadata", "activeVersionId", "versionId", "sourceWorkflowId", "triggerCount", "versionCounter"):
    w.pop(k, None)
json.dump(w, open(p, "w"), indent=2)
PY
