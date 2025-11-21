# .specify - Feature Specification System

This directory contains structured feature specifications for odoo-xml-cli using BMAD-inspired workflow.

## Structure

```
.specify/
├── config.yaml              # Configuration
├── templates/               # Templates for specs and plans
│   ├── spec-template.md
│   └── plan-template.md
└── features/                # Feature specifications
    ├── 001_environment_profiles/
    │   ├── spec.md
    │   ├── plan.md
    │   └── tasks.md
    └── 002_read_only_mode/
        ├── spec.md
        ├── plan.md
        └── tasks.md
```

## Workflow

1. **Idea Phase** - Create initial spec from template
2. **Specification** - Fill out requirements, design, testing
3. **Planning** - Break down into implementation tasks
4. **Implementation** - Execute tasks, update status
5. **Completion** - Mark as completed, document learnings

## Commands

### Using BMAD /specify commands:
```bash
/specify:specify              # Create/update feature spec
/specify:plan                 # Generate implementation plan
/specify:tasks                # Generate task breakdown
/specify:clarify              # Ask clarifying questions
/specify:implement            # Execute implementation
```

### Manual workflow:
```bash
# Create new feature
cp .specify/templates/spec-template.md .specify/features/00X_feature_name/spec.md

# Edit spec
# ... fill in requirements ...

# Generate plan
/specify:plan

# Implement
/specify:implement
```

## Integration with Legacy Specs

Existing specs in `specs/000/IDEA-*.md` remain as high-level ideas.  
`.specify/features/` contains detailed, actionable specifications.

## Naming Convention

Features: `{id}_{name}`
- `001_environment_profiles`
- `002_read_only_mode`

IDs are sequential, names are snake_case.
