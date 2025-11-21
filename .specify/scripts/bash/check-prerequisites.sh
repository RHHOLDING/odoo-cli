#!/bin/bash
# Check prerequisites and return feature paths for specify workflows

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Parse arguments
JSON_MODE=false
PATHS_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --json) JSON_MODE=true; shift ;;
        --paths-only) PATHS_ONLY=true; shift ;;
        -Json) JSON_MODE=true; shift ;;
        -PathsOnly) PATHS_ONLY=true; shift ;;
        *) shift ;;
    esac
done

# Get current branch
BRANCH=$(git -C "$REPO_ROOT" branch --show-current)

# Find active feature directory (match feature/* branch pattern)
if [[ $BRANCH =~ ^feature/([0-9]+)- ]]; then
    FEATURE_NUM="${BASH_REMATCH[1]}"
    FEATURE_DIR=$(find "$REPO_ROOT/.specify/features" -maxdepth 1 -type d -name "${FEATURE_NUM}_*" | head -1)

    if [ -z "$FEATURE_DIR" ]; then
        echo "Error: No feature directory found for feature $FEATURE_NUM" >&2
        exit 1
    fi
else
    # Not on a feature branch, find most recent feature
    FEATURE_DIR=$(find "$REPO_ROOT/.specify/features" -maxdepth 1 -type d -name "*_*" | sort -r | head -1)

    if [ -z "$FEATURE_DIR" ]; then
        echo "Error: No feature directories found" >&2
        exit 1
    fi
fi

FEATURE_SPEC="$FEATURE_DIR/spec.md"
IMPL_PLAN="$FEATURE_DIR/plan.md"
TASKS_FILE="$FEATURE_DIR/tasks.md"
SPECS_DIR="$FEATURE_DIR"

# Verify spec file exists
if [ ! -f "$FEATURE_SPEC" ]; then
    echo "Error: Feature spec not found at $FEATURE_SPEC" >&2
    exit 1
fi

# Output
if [ "$JSON_MODE" = true ]; then
    cat <<EOF
{
  "branch": "$BRANCH",
  "feature_dir": "$FEATURE_DIR",
  "feature_spec": "$FEATURE_SPEC",
  "impl_plan": "$IMPL_PLAN",
  "tasks": "$TASKS_FILE",
  "specs_dir": "$SPECS_DIR",
  "repo_root": "$REPO_ROOT"
}
EOF
else
    echo "BRANCH=$BRANCH"
    echo "FEATURE_DIR=$FEATURE_DIR"
    echo "FEATURE_SPEC=$FEATURE_SPEC"
    echo "IMPL_PLAN=$IMPL_PLAN"
    echo "TASKS=$TASKS_FILE"
    echo "SPECS_DIR=$SPECS_DIR"
fi

exit 0
