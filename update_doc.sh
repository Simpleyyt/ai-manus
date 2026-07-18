#!/bin/bash
# Compatibility wrapper — real script lives in the update-docs skill.
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.cursor/skills/update-docs/update_doc.sh" "$@"
