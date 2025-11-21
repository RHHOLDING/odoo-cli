#!/bin/bash
# Create new feature specification
# Usage: ./create-new-feature.sh [--json] "Feature description"

set -e

# Parse arguments
JSON_OUTPUT=false
FEATURE_DESC=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --json)
      JSON_OUTPUT=true
      shift
      ;;
    *)
      FEATURE_DESC="$1"
      shift
      ;;
  esac
done

# Validate feature description
if [ -z "$FEATURE_DESC" ]; then
  echo "Error: Feature description required"
  exit 1
fi

# Get repository root
REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

# Generate feature ID (find next available number)
FEATURES_DIR=".specify/features"
mkdir -p "$FEATURES_DIR"

# Find next ID
LAST_ID=$(find "$FEATURES_DIR" -maxdepth 1 -type d -name "[0-9]*_*" | sed 's/.*\/\([0-9]*\)_.*/\1/' | sort -n | tail -1)
if [ -z "$LAST_ID" ]; then
  NEXT_ID="001"
else
  NEXT_ID=$(printf "%03d" $((10#$LAST_ID + 1)))
fi

# Generate feature name (slug from description)
FEATURE_NAME=$(echo "$FEATURE_DESC" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/_/g' | sed 's/__*/_/g' | sed 's/^_//;s/_$//')

# Limit feature name length
FEATURE_NAME=$(echo "$FEATURE_NAME" | cut -c1-50)

FEATURE_ID="${NEXT_ID}_${FEATURE_NAME}"
FEATURE_DIR="$FEATURES_DIR/$FEATURE_ID"
SPEC_FILE="$REPO_ROOT/$FEATURE_DIR/spec.md"

# Create feature directory
mkdir -p "$FEATURE_DIR"

# Create branch name
BRANCH_NAME="feature/${NEXT_ID}-${FEATURE_NAME}"

# Create and checkout branch
if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
  git checkout "$BRANCH_NAME"
else
  git checkout -b "$BRANCH_NAME"
fi

# Initialize spec file with header
cat > "$SPEC_FILE" << EOF
# Feature: $FEATURE_DESC

**ID:** $NEXT_ID
**Status:** idea
**Version:** TBD
**Priority:** TBD
**Effort:** TBD

---

[Template content will be filled by specify command]
EOF

# Output result
if [ "$JSON_OUTPUT" = true ]; then
  cat << EOF
{
  "feature_id": "$FEATURE_ID",
  "branch_name": "$BRANCH_NAME",
  "spec_file": "$SPEC_FILE",
  "feature_dir": "$REPO_ROOT/$FEATURE_DIR",
  "next_id": "$NEXT_ID"
}
EOF
else
  echo "Created feature: $FEATURE_ID"
  echo "Branch: $BRANCH_NAME"
  echo "Spec file: $SPEC_FILE"
fi
