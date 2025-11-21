# Feature: Environment Profiles

**ID:** 001
**Status:** specified
**Version:** v1.5.0
**Priority:** High
**Effort:** 4-6 hours

---

## Problem Statement

**What problem does this solve?**

Users need to switch between different Odoo environments (production, staging, development, local) frequently. Currently they must:
- Manually edit `~/.odoo-cli.yaml` config each time
- Remember different URLs, databases, and credentials for each environment
- Risk accidentally running commands against production when intending staging

This is error-prone, time-consuming, and dangerous (especially with write operations on production).

**Who is affected?**
- LLM users (Claude, GPT) working with multiple Odoo instances
- Developers testing features across environments
- Admins performing safe production queries vs staging experiments

**Current pain points:**
- No quick way to switch between environments
- Easy to forget which environment is active
- Credentials scattered across different config files
- No environment-specific context (different company IDs, warehouse IDs per env)

---

## Goals

### Primary Goals
1. Enable one-command switching between Odoo environments
2. Support environment-specific configurations (URLs, credentials, context)
3. Prevent accidental cross-environment operations
4. Provide clear indication of current active environment

### Success Criteria
- [ ] Can switch between environments in <1 second
- [ ] Current environment clearly visible in all outputs
- [ ] Environment-specific configs isolated (no cross-contamination)
- [ ] Works seamlessly with existing `~/.odoo-cli.yaml`
- [ ] LLMs can understand which environment is active

---

## Solution Overview

**High-level approach:**

Introduce **environment profiles** - named configurations for different Odoo instances. Users define profiles once, then switch between them using `--profile` flag or environment variable.

**Key components:**
1. **Profile Configuration** - YAML structure defining multiple environments
2. **Profile Switching** - CLI flag and environment variable support
3. **Active Profile Indicator** - Show current profile in JSON output and errors
4. **Profile Management Commands** - List, show, validate profiles

---

## Requirements

### Functional Requirements

#### FR-1: Profile Definition
**Description:** Users can define multiple named profiles in config file
**Priority:** Must Have
**Acceptance Criteria:**
- [ ] Config file supports `profiles` section
- [ ] Each profile has: name, url, db, username, password
- [ ] Optional: timeout, verify_ssl, default_context
- [ ] One profile marked as `default`

#### FR-2: Profile Switching via CLI Flag
**Description:** `--profile NAME` flag switches active environment
**Priority:** Must Have
**Acceptance Criteria:**
- [ ] `odoo --profile prod search ...` uses prod config
- [ ] `odoo --profile dev search ...` uses dev config
- [ ] Flag works with all commands
- [ ] Clear error if profile doesn't exist

#### FR-3: Profile Switching via Environment Variable
**Description:** `ODOO_PROFILE=name` sets default profile
**Priority:** Must Have
**Acceptance Criteria:**
- [ ] `export ODOO_PROFILE=staging` sets default
- [ ] CLI flag overrides environment variable
- [ ] Empty/unset uses `default` profile

#### FR-4: Active Profile Indicator
**Description:** Show current profile in outputs
**Priority:** Must Have
**Acceptance Criteria:**
- [ ] JSON output includes `"profile": "prod"`
- [ ] Error messages show active profile
- [ ] `--llm-help` shows current profile

#### FR-5: Profile Management Commands
**Description:** Commands to inspect and validate profiles
**Priority:** Should Have
**Acceptance Criteria:**
- [ ] `odoo profiles list` shows all profiles
- [ ] `odoo profiles show NAME` shows profile details (mask password)
- [ ] `odoo profiles test NAME` validates connectivity

### Non-Functional Requirements

#### NFR-1: Performance
**Description:** Profile switching must be instant
**Metric:** <100ms overhead for profile loading

#### NFR-2: Security
**Description:** Credentials must be protected
**Metric:** Passwords never logged, masked in outputs

#### NFR-3: Backward Compatibility
**Description:** Existing configs must still work
**Metric:** 100% compatibility with current `~/.odoo-cli.yaml` format

---

## User Stories

### Story 1: Quick Environment Switching
**As a** developer
**I want** to switch between prod and staging with one command
**So that** I can test queries safely before running on production

**Acceptance Criteria:**
- [ ] `odoo --profile staging search ...` uses staging instantly
- [ ] No need to edit config files
- [ ] Clear indication of which environment is active

### Story 2: LLM Environment Awareness
**As an** LLM assistant (Claude)
**I want** to know which Odoo environment the user is querying
**So that** I can provide environment-appropriate suggestions

**Acceptance Criteria:**
- [ ] `--llm-help` includes active profile name
- [ ] JSON responses include `"profile": "name"`
- [ ] Can recommend correct commands per environment

### Story 3: Safe Production Access
**As an** admin
**I want** to clearly see when I'm querying production
**So that** I don't accidentally run dangerous commands

**Acceptance Criteria:**
- [ ] Production profile clearly labeled in all outputs
- [ ] Error messages show environment context
- [ ] Can set environment-specific safety flags (for future read-only mode)

---

## Design

### CLI Interface

```bash
# Using profile flag
odoo --profile prod search res.partner '[]'
odoo --profile staging create res.partner name="Test"
odoo --profile dev get-models

# Using environment variable
export ODOO_PROFILE=staging
odoo search res.partner '[]'  # Uses staging

# Override environment variable with flag
export ODOO_PROFILE=staging
odoo --profile prod search ...  # Uses prod (flag wins)

# Profile management commands
odoo profiles list                    # Show all profiles
odoo profiles show prod               # Show prod details (mask password)
odoo profiles test staging            # Test staging connectivity
odoo profiles current                 # Show active profile
```

### Configuration

```yaml
# ~/.odoo-cli.yaml

# Legacy format (still supported)
url: "https://default-instance.odoo.com"
db: "default-db"
username: "admin"
password: "secret"

# New profile format
profiles:
  prod:
    url: "https://rhholding.odoo.com"
    db: "rhholding-production-10209498"
    username: "admin@actec.de"
    password: "prod-password"
    timeout: 60
    verify_ssl: true
    default: true  # Used when no profile specified

  staging:
    url: "https://rhholding-staging.odoo.com"
    db: "rhholding-staging"
    username: "admin@actec.de"
    password: "staging-password"
    timeout: 30

  dev:
    url: "https://rhholding-ac-mail2-25724858.dev.odoo.com"
    db: "rhholding-ac-mail2-25724858"
    username: "mcp@ananda.gmbh"
    password: "dev-password"

  local:
    url: "http://localhost:8069"
    db: "odoo_production"
    username: "admin"
    password: "admin"
    verify_ssl: false

# Backward compatibility: If no profiles defined, uses top-level config
```

### Data Structures

```python
# odoo_cli/models/profile.py

@dataclass
class Profile:
    name: str
    url: str
    db: str
    username: str
    password: str
    timeout: int = 30
    verify_ssl: bool = True
    default: bool = False
    context: Optional[dict] = None

class ProfileManager:
    """Manages environment profiles"""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.profiles: Dict[str, Profile] = {}
        self._load_profiles()

    def _load_profiles(self) -> None:
        """Load profiles from config file"""

    def get_profile(self, name: Optional[str] = None) -> Profile:
        """Get profile by name, or default, or from env var"""

    def list_profiles(self) -> List[str]:
        """List all profile names"""

    def test_connection(self, profile_name: str) -> bool:
        """Test if profile can connect to Odoo"""
```

---

## Implementation Notes

### Files to Modify
- `odoo_cli/cli.py` - Add `--profile` global option, load ProfileManager
- `odoo_cli/models/context.py` - Add `profile_name: Optional[str]` field
- `odoo_cli/config.py` - Update config loading to support profiles
- `odoo_cli/utils/output.py` - Include profile name in JSON output
- `odoo_cli/help.py` - Show active profile in `--llm-help`

### New Files
- `odoo_cli/models/profile.py` - Profile and ProfileManager classes
- `odoo_cli/commands/profiles.py` - Profile management commands (list, show, test)

### Dependencies
- PyYAML (already in use for config)
- No new external dependencies needed

---

## Testing Strategy

### Unit Tests
- [ ] Test profile loading from YAML
- [ ] Test default profile selection
- [ ] Test profile override priority (flag > env var > default)
- [ ] Test backward compatibility with legacy config
- [ ] Test profile validation (required fields)

### Integration Tests
- [ ] Test actual connection with each profile type
- [ ] Test profile switching mid-session
- [ ] Test error handling for missing profiles
- [ ] Test credential masking in outputs

### Manual Testing
- [ ] Create profiles for prod/staging/dev/local
- [ ] Switch between profiles and verify correct instances used
- [ ] Test with LLMs (Claude) to ensure profile visibility
- [ ] Test backward compatibility with existing configs

---

## Edge Cases

1. **No profiles defined**
   Handling: Fall back to legacy top-level config (backward compatible)

2. **Profile specified but doesn't exist**
   Handling: Error with suggestion: "Available profiles: prod, staging, dev"

3. **Multiple profiles marked as default**
   Handling: Use first default found, warn about ambiguity

4. **Missing required fields in profile**
   Handling: Validation error listing missing fields

5. **Environment variable set to non-existent profile**
   Handling: Error with clear message, suggest valid profiles

6. **No default profile and no profile specified**
   Handling: Use first profile found, or error if no profiles at all

---

## Security Considerations

- **Password Masking:** Always mask passwords in `profiles show` output and logs
- **Config File Permissions:** Warn if `~/.odoo-cli.yaml` has world-readable permissions
- **Credential Exposure:** Never include passwords in error messages or JSON output
- **Profile Validation:** Validate profile names to prevent path traversal attacks
- **Environment Variable Security:** Document that ODOO_PROFILE is not sensitive (only name)

---

## Documentation Updates

- [ ] Update README.md with profile configuration examples
- [ ] Update SPEC.md with environment profile section
- [ ] Update CLAUDE.md with profile usage for LLMs
- [ ] Update `--llm-help` to include active profile and available profiles
- [ ] Add migration guide for users with existing configs

---

## Related Work

**Related Features:**
- IDEA-02 (Read-Only Mode) - Future integration: per-profile read-only flag
- IDEA-07 (Project Context Layer) - Future: per-profile context files (`.odoo-context.{profile}.yaml`)

**Dependencies:**
- None (standalone feature)

**Conflicts:**
- None (backward compatible with existing config)

---

## Open Questions

1. **Profile-specific context files?**
   - Should each profile auto-load `.odoo-context.{profile}.yaml`?
   - Decision: Yes, but defer to context layer implementation

2. **Global vs per-profile defaults?**
   - Should timeout/verify_ssl have global defaults?
   - Decision: Yes, inherit from top-level, override per-profile

3. **Profile aliases/shortcuts?**
   - Should we support `odoo -p prod` as shorthand?
   - Decision: Not in v1, can add if requested

4. **Shell completion?**
   - Auto-complete profile names in bash/zsh?
   - Decision: Nice-to-have, not MVP

---

## Timeline

**Estimated Effort:** 4-6 hours
**Complexity:** Medium

**Breakdown:**
- Design: 30 min (this spec)
- Implementation: 3-4 hours
  - Profile model & manager: 1 hour
  - CLI integration: 1 hour
  - Profile commands: 1 hour
  - Output integration: 30 min
  - Help integration: 30 min
- Testing: 1 hour
- Documentation: 1 hour

---

## Appendix

### References
- IDEA-07: Project Context Layer (lines 746-749 on multi-environment)
- Current config format: `odoo_cli/config.py`
- Click multi-command patterns: https://click.palletsprojects.com/

### Previous Discussions
- 2025-11-21: User requested environment switching + read-only mode
- Decision: Split into two features, implement profiles first
- Read-only mode deferred to separate feature (30-60 min effort)

### Example Migration

**Before (legacy):**
```yaml
url: "https://rhholding.odoo.com"
db: "rhholding-production"
username: "admin"
password: "secret"
```

**After (with profiles):**
```yaml
# Legacy still works (becomes implicit default profile)
url: "https://rhholding.odoo.com"
db: "rhholding-production"
username: "admin"
password: "secret"

# Or migrate to explicit profiles
profiles:
  prod:
    url: "https://rhholding.odoo.com"
    db: "rhholding-production"
    username: "admin"
    password: "secret"
    default: true
```

### Profile Selection Priority

```
1. CLI flag:           odoo --profile staging ...
2. Environment var:    export ODOO_PROFILE=staging
3. Default profile:    profile with default: true
4. First profile:      first profile in list
5. Legacy config:      top-level url/db/username/password
6. Error:              No config found
```
