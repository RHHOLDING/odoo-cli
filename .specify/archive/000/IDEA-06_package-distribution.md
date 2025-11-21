# Idea: Package Distribution & Easy Installation

## Problem
Current installation requires manual git clone + pip install. No easy one-command installation for end users.

## Goal
Enable simple installation via package managers across all platforms:
```bash
# macOS/Linux
brew install odoo-cli

# Python (all platforms)
pip install odoo-cli

# Maybe: apt, yum, chocolatey, etc.
```

---

## 🔒 Security: Package Verification & Checksums

**Critical:** All distributed packages MUST include cryptographic checksums to prevent tampering and supply chain attacks.

### Why Checksums Matter

**Attack Scenario without checksums:**
1. Attacker compromises download server
2. Replaces legitimate package with malware
3. Users install infected version
4. **No way to detect tampering!**

**Protection with checksums:**
1. Official release has known SHA256 hash
2. User downloads package
3. Verifies hash matches official checksum
4. **Mismatch = compromised file, installation aborted**

### Checksum Types

| Algorithm | Bits | Security | Use Case |
|-----------|------|----------|----------|
| **SHA256** | 256 | High | Primary (Homebrew, PyPI) |
| SHA512 | 512 | Higher | Extra paranoid |
| MD5 | 128 | ⚠️ Broken | Legacy only, DO NOT USE |

**Recommendation:** Always use **SHA256 minimum**

---

### Implementation: Homebrew Formula

**Formula requires SHA256 checksum:**

```ruby
class OdooCli < Formula
  desc "LLM-friendly CLI tool for Odoo via JSON-RPC"
  homepage "https://github.com/RHHOLDING/odoo-cli"
  url "https://github.com/RHHOLDING/odoo-cli/archive/v1.2.0.tar.gz"
  sha256 "a3b5c6d7e8f9a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6"  # ← CRITICAL!
  license "MIT"
  # ...
end
```

**How to generate SHA256:**
```bash
# For release archive
curl -L https://github.com/RHHOLDING/odoo-cli/archive/v1.2.0.tar.gz | shasum -a 256

# Output: a3b5c6d7e8f9a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6
```

**Homebrew automatically verifies:**
```bash
brew install odoo-cli
# → Downloads .tar.gz
# → Computes SHA256 of downloaded file
# → Compares with Formula sha256 value
# → If mismatch: ERROR and aborts installation
# → If match: Proceeds with installation
```

---

### Implementation: PyPI Package Signing

**PyPI automatically generates hashes:**

When you upload to PyPI with `twine`:
```bash
twine upload dist/odoo-cli-1.2.0.tar.gz
```

**PyPI generates:**
- SHA256 hash of the package
- Displays on package page: https://pypi.org/project/odoo-cli/#files
- `pip` verifies hash automatically on installation

**User verification (manual):**
```bash
# Download package
pip download odoo-cli --no-deps

# Verify SHA256
shasum -a 256 odoo-cli-1.2.0.tar.gz

# Compare with PyPI website hash
# https://pypi.org/project/odoo-cli/#files
```

**Optional: GPG Signing (Advanced)**

Sign releases with GPG key for extra trust:

```bash
# Generate GPG key (one-time)
gpg --full-generate-key

# Sign package
gpg --detach-sign -a dist/odoo-cli-1.2.0.tar.gz
# Creates: dist/odoo-cli-1.2.0.tar.gz.asc

# Upload both to PyPI
twine upload dist/odoo-cli-1.2.0.tar.gz dist/odoo-cli-1.2.0.tar.gz.asc

# Users verify signature
gpg --verify odoo-cli-1.2.0.tar.gz.asc odoo-cli-1.2.0.tar.gz
```

---

### Implementation: Docker Image Digests

**Docker images have SHA256 digests:**

```bash
# Build image
docker build -t actec/odoo-cli:1.2.0 .

# Push to Docker Hub
docker push actec/odoo-cli:1.2.0

# Docker Hub generates digest (SHA256)
# Example: sha256:a3b5c6d7e8f9a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6
```

**Users can verify:**
```bash
# Pull by digest instead of tag (immutable!)
docker pull actec/odoo-cli@sha256:a3b5c6d7e8f9a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6

# Tags can be overwritten (1.2.0 → malware)
# Digests CANNOT be changed (cryptographically bound)
```

**Docker Content Trust (DCT):**

Enable automatic signature verification:
```bash
export DOCKER_CONTENT_TRUST=1

# Now all pulls verify signatures
docker pull actec/odoo-cli:1.2.0
# → Verifies image signature
# → If tampered: ERROR and aborts
```

---

### Implementation: Binary Checksums

**For PyInstaller binaries, provide checksums:**

**Create checksums file:**
```bash
# After building binaries
cd dist/

# Generate SHA256 for all binaries
shasum -a 256 odoo-macos odoo-linux odoo-windows.exe > SHA256SUMS.txt

# Sign checksums file with GPG (optional)
gpg --clearsign SHA256SUMS.txt
# Creates: SHA256SUMS.txt.asc
```

**SHA256SUMS.txt example:**
```
a3b5c6d7e8f9a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6  odoo-macos
b4c5d6e7f8a9b0c1d2e3f4a5b6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5  odoo-linux
c5d6e7f8a9b0c1d2e3f4a5b6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6  odoo-windows.exe
```

**User verification:**
```bash
# Download binary
curl -L https://github.com/.../odoo-macos -o odoo

# Download checksums
curl -L https://github.com/.../SHA256SUMS.txt -o SHA256SUMS.txt

# Verify (macOS/Linux)
shasum -a 256 -c SHA256SUMS.txt
# Output: odoo-macos: OK

# Or manually compare
shasum -a 256 odoo
# Compare output with SHA256SUMS.txt
```

**Windows verification (PowerShell):**
```powershell
# Compute hash
Get-FileHash odoo-windows.exe -Algorithm SHA256

# Compare with SHA256SUMS.txt manually
```

---

### GitHub Release Automation

**Automated checksum generation in CI:**

```yaml
# .github/workflows/release.yml
name: Release

on:
  release:
    types: [published]

jobs:
  checksums:
    runs-on: ubuntu-latest
    steps:
      - name: Download release assets
        uses: actions/download-artifact@v3
        with:
          name: binaries
          path: dist/

      - name: Generate SHA256 checksums
        run: |
          cd dist/
          sha256sum * > SHA256SUMS.txt

          # Optional: Sign with GPG
          # gpg --import ${{ secrets.GPG_PRIVATE_KEY }}
          # gpg --clearsign SHA256SUMS.txt

      - name: Upload checksums to release
        uses: actions/upload-release-asset@v1
        with:
          asset_path: dist/SHA256SUMS.txt
          asset_name: SHA256SUMS.txt
          asset_content_type: text/plain
```

---

### Documentation: Installation with Verification

**Update README.md with verification steps:**

````markdown
## Installation with Verification

### Homebrew (automatic verification)
```bash
brew install odoo-cli
# ✓ Homebrew automatically verifies SHA256 checksum
```

### PyPI (automatic verification)
```bash
pip install odoo-cli
# ✓ pip automatically verifies package hash
```

### Binary Download (manual verification recommended)

**macOS:**
```bash
# Download binary
curl -L https://github.com/RHHOLDING/odoo-cli/releases/download/v1.2.0/odoo-macos -o odoo

# Download checksums
curl -L https://github.com/RHHOLDING/odoo-cli/releases/download/v1.2.0/SHA256SUMS.txt -o SHA256SUMS.txt

# Verify checksum
grep odoo-macos SHA256SUMS.txt | shasum -a 256 -c
# Expected output: odoo-macos: OK

# If OK, make executable
chmod +x odoo
./odoo --help
```

**Linux:**
```bash
# Same as macOS
curl -L https://.../odoo-linux -o odoo
curl -L https://.../SHA256SUMS.txt -o SHA256SUMS.txt
grep odoo-linux SHA256SUMS.txt | sha256sum -c
chmod +x odoo
```

**Windows (PowerShell):**
```powershell
# Download binary
Invoke-WebRequest -Uri https://.../odoo-windows.exe -OutFile odoo.exe

# Download checksums
Invoke-WebRequest -Uri https://.../SHA256SUMS.txt -OutFile SHA256SUMS.txt

# Compute hash
$hash = (Get-FileHash odoo.exe -Algorithm SHA256).Hash.ToLower()

# Compare with checksums file
$expected = (Get-Content SHA256SUMS.txt | Select-String "odoo-windows.exe").Line.Split()[0]

if ($hash -eq $expected) {
    Write-Host "✓ Checksum verified successfully!" -ForegroundColor Green
    .\odoo.exe --help
} else {
    Write-Host "✗ Checksum verification FAILED! Do not run this file!" -ForegroundColor Red
}
```
````

---

### Security Best Practices Summary

| Distribution | Verification | Who Checks | Automatic |
|--------------|--------------|------------|-----------|
| **Homebrew** | SHA256 | Homebrew | ✅ Yes |
| **PyPI** | SHA256 + MD5 | pip | ✅ Yes |
| **Docker** | SHA256 Digest | Docker | ✅ Yes (with DCT) |
| **Binary Downloads** | SHA256 | User (manual) | ❌ No |
| **GPG Signing** | GPG Signature | User (manual) | ❌ No |

**Recommendations:**
1. ✅ **Always provide SHA256 checksums** for all distributions
2. ✅ **Automate checksum generation** in CI/CD (GitHub Actions)
3. ✅ **Document verification steps** for manual downloads
4. ✅ **Use SHA256 minimum** (never MD5)
5. ⚡ **Optional: GPG signing** for paranoid users
6. ⚡ **Optional: Docker Content Trust** for container security

---

### Supply Chain Security Checklist

**Before releasing:**
- [ ] Generate SHA256 checksums for all artifacts
- [ ] Upload checksums to GitHub Release
- [ ] Update Homebrew Formula with correct SHA256
- [ ] Verify PyPI generates hashes automatically
- [ ] Sign checksums file with GPG (optional but recommended)
- [ ] Document verification steps in README
- [ ] Test verification on all platforms

**Example Release Artifacts:**
```
v1.2.0/
├── odoo-cli-1.2.0.tar.gz           # Source
├── odoo-macos                       # Binary (macOS)
├── odoo-linux                       # Binary (Linux)
├── odoo-windows.exe                 # Binary (Windows)
├── SHA256SUMS.txt                   # Checksums file
└── SHA256SUMS.txt.asc              # GPG signature (optional)
```

---

## 1. Homebrew Formula (macOS & Linux)

**Current Installation:**
```bash
git clone https://github.com/RHHOLDING/odoo-cli.git
cd odoo-xml-cli
pip install -e .
```

**Proposed Installation:**
```bash
brew tap actec-andre/odoo-cli
brew install odoo-cli
```

**Or via Core Homebrew (if accepted):**
```bash
brew install odoo-cli
```

### Implementation Steps

#### A. Create Homebrew Formula
**File:** `homebrew-odoo-cli/Formula/odoo-cli.rb`

```ruby
class OdooCli < Formula
  include Language::Python::Virtualenv

  desc "LLM-friendly CLI tool for Odoo via JSON-RPC"
  homepage "https://github.com/RHHOLDING/odoo-cli"
  url "https://github.com/RHHOLDING/odoo-cli/archive/v1.2.0.tar.gz"
  sha256 "CHECKSUM_HERE"
  license "MIT"

  depends_on "python@3.10"

  resource "click" do
    url "https://files.pythonhosted.org/packages/.../click-8.1.7.tar.gz"
    sha256 "..."
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/.../rich-13.7.0.tar.gz"
    sha256 "..."
  end

  resource "requests" do
    url "https://files.pythonhosted.org/packages/.../requests-2.31.0.tar.gz"
    sha256 "..."
  end

  resource "python-dotenv" do
    url "https://files.pythonhosted.org/packages/.../python-dotenv-1.0.0.tar.gz"
    sha256 "..."
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    system bin/"odoo", "--version"
  end
end
```

#### B. Create Tap Repository
**Repository:** `actec-andre/homebrew-odoo-cli`

```bash
# User installation
brew tap actec-andre/odoo-cli
brew install odoo-cli

# Uninstall
brew uninstall odoo-cli
brew untap actec-andre/odoo-cli
```

#### C. Submit to Homebrew Core (Optional)
For wider distribution, submit to official Homebrew:
- Requires 75+ stars on GitHub
- Requires 30+ forks
- Project must be stable (v1.0+)
- Active maintenance

**Effort:** High, but worth it for visibility

---

## 2. PyPI Distribution (Python Package Index)

**Current:** Not published
**Proposed:** Publish to PyPI as `odoo-cli`

### Implementation Steps

#### A. Update pyproject.toml
```toml
[project]
name = "odoo-cli"  # Check availability on PyPI!
version = "1.2.0"
description = "LLM-friendly CLI tool for Odoo via JSON-RPC"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
    {name = "Andre", email = "andre@example.com"}
]
keywords = ["odoo", "cli", "json-rpc", "llm", "erp"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

[project.urls]
Homepage = "https://github.com/RHHOLDING/odoo-cli"
Repository = "https://github.com/RHHOLDING/odoo-cli"
Issues = "https://github.com/RHHOLDING/odoo-cli/issues"
Changelog = "https://github.com/RHHOLDING/odoo-cli/blob/main/CHANGELOG.md"

[project.scripts]
odoo = "odoo_cli.cli:cli"

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"
```

#### B. Build & Publish Workflow

**Manual:**
```bash
# Build distribution
python -m build

# Upload to PyPI (requires API token)
python -m twine upload dist/*
```

**GitHub Action (Automated):**
```yaml
# .github/workflows/publish-pypi.yml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install build tools
        run: |
          python -m pip install --upgrade pip
          pip install build twine

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

#### C. User Installation
```bash
# Simple pip install
pip install odoo-cli

# With extras (if we add optional features)
pip install odoo-cli[async]

# Upgrade
pip install --upgrade odoo-cli
```

**Effort:** Low (1-2 hours setup, then automated)

---

## 3. Platform-Specific Package Managers

### Linux: apt (Debian/Ubuntu)
**Challenge:** Need to maintain .deb packages

```bash
# Create PPA (Personal Package Archive)
sudo add-apt-repository ppa:actec-andre/odoo-cli
sudo apt update
sudo apt install odoo-cli
```

**Effort:** High (packaging, maintenance)
**Priority:** Low (pip works fine on Linux)

### Linux: Snap
**Easier than apt, cross-distro:**

```bash
snap install odoo-cli
```

**snapcraft.yaml:**
```yaml
name: odoo-cli
version: '1.2.0'
summary: LLM-friendly CLI for Odoo
description: |
  High-performance JSON-RPC CLI tool for Odoo with LLM-friendly output.

grade: stable
confinement: strict
base: core22

apps:
  odoo:
    command: bin/odoo
    plugs:
      - network
      - home

parts:
  odoo-cli:
    plugin: python
    source: .
    python-packages:
      - click
      - rich
      - requests
      - python-dotenv
```

**Effort:** Medium (1 day setup)
**Priority:** Medium (good for Linux users)

### Windows: Chocolatey
**Windows package manager:**

```powershell
choco install odoo-cli
```

**Effort:** High (need .nupkg, testing)
**Priority:** Low (pip works on Windows too)

### Windows: Scoop
**Simpler alternative:**

```powershell
scoop bucket add actec-andre https://github.com/actec-andre/scoop-bucket
scoop install odoo-cli
```

**Effort:** Medium
**Priority:** Low

---

## 4. Docker Image (Containerized Installation)

**For users who don't want to install Python:**

```bash
# Run directly
docker run --rm -it actec/odoo-cli:latest odoo --help

# With config from host
docker run --rm -it \
  -v ~/.odoo_cli.env:/root/.odoo_cli.env \
  actec/odoo-cli:latest odoo read res.partner 1

# Alias for convenience
alias odoo='docker run --rm -it -v ~/.odoo_cli.env:/root/.odoo_cli.env actec/odoo-cli:latest odoo'
```

**Dockerfile:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY odoo_cli/ ./odoo_cli/
COPY pyproject.toml .

# Install CLI
RUN pip install -e .

ENTRYPOINT ["odoo"]
```

**GitHub Action for Auto-build:**
```yaml
# .github/workflows/docker-publish.yml
name: Publish Docker Image

on:
  release:
    types: [published]

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: |
            actec/odoo-cli:latest
            actec/odoo-cli:${{ github.ref_name }}
```

**Effort:** Low (2-3 hours)
**Priority:** Medium (good for isolated environments)

---

## 5. Binary Distribution (PyInstaller)

**For users without Python installed:**

```bash
# Download pre-built binary
curl -L https://github.com/RHHOLDING/odoo-cli/releases/download/v1.2.0/odoo-macos -o odoo
chmod +x odoo
./odoo --help
```

**Build with PyInstaller:**
```bash
pip install pyinstaller

# Build single-file executable
pyinstaller --onefile \
  --name odoo \
  --add-data "odoo_cli:odoo_cli" \
  odoo_cli/cli.py

# Output: dist/odoo (macOS/Linux) or dist/odoo.exe (Windows)
```

**GitHub Action:**
```yaml
name: Build Binaries

on:
  release:
    types: [published]

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install PyInstaller
        run: pip install pyinstaller

      - name: Build binary
        run: |
          pyinstaller --onefile --name odoo odoo_cli/cli.py

      - name: Upload to release
        uses: actions/upload-release-asset@v1
        with:
          asset_path: dist/odoo${{ matrix.os == 'windows-latest' && '.exe' || '' }}
          asset_name: odoo-${{ matrix.os }}${{ matrix.os == 'windows-latest' && '.exe' || '' }}
```

**Effort:** Medium (testing across platforms)
**Priority:** Medium-High (good UX)

---

## Priority Ranking

| Distribution Method | Effort | Maintenance | Reach | Priority |
|---------------------|--------|-------------|-------|----------|
| **PyPI (pip)** | Low | Low | High | 🔥 **P0 - Critical** |
| **Homebrew Tap** | Low | Low | High (macOS) | 🔥 **P1 - High** |
| **Docker Image** | Low | Low | Medium | ⚡ **P2 - Medium** |
| **Binary (PyInstaller)** | Medium | Medium | High | ⚡ **P2 - Medium** |
| **Snap** | Medium | Medium | Medium (Linux) | 💡 **P3 - Low** |
| **Homebrew Core** | High | Low | Very High | 💡 **P4 - Future** |
| **apt/PPA** | High | High | Medium | 💡 **P5 - Very Low** |
| **Chocolatey** | High | Medium | Low | 💡 **P5 - Very Low** |
| **Scoop** | Medium | Low | Low | 💡 **P5 - Very Low** |

---

## Recommended Implementation Order

### Phase 1: Python Ecosystem (Week 1)
1. ✅ **Publish to PyPI** (2-3 hours)
   - Update pyproject.toml
   - Create PyPI account
   - Upload package
   - Test installation

2. ✅ **Setup auto-publish GitHub Action** (1 hour)
   - Trigger on release
   - Upload to PyPI automatically

**Deliverable:** `pip install odoo-cli` works

---

### Phase 2: macOS/Linux (Week 2)
3. ✅ **Create Homebrew Tap** (3-4 hours)
   - Create homebrew-odoo-cli repository
   - Write Formula
   - Test on macOS
   - Test on Linux

4. ✅ **Documentation** (1 hour)
   - Update README with installation methods
   - Add troubleshooting section

**Deliverable:** `brew install odoo-cli` works

---

### Phase 3: Containerization (Week 3)
5. ✅ **Docker Image** (2-3 hours)
   - Write Dockerfile
   - Test locally
   - Setup auto-build on Docker Hub
   - Add to README

**Deliverable:** `docker run actec/odoo-cli` works

---

### Phase 4: Binaries (Week 4)
6. ✅ **PyInstaller Binaries** (1 day)
   - Setup build workflow
   - Test on all platforms
   - Upload to GitHub Releases
   - Add download links to README

**Deliverable:** Download & run without Python

---

### Future (If Demand)
7. ❓ **Snap Package** - If Linux users request
8. ❓ **Homebrew Core** - When project is mature
9. ❓ **Windows Package Managers** - If Windows adoption is high

---

## Installation Documentation (README Update)

```markdown
## Installation

### Quick Start (Python)
```bash
pip install odoo-cli
```

### macOS/Linux (Homebrew)
```bash
brew tap actec-andre/odoo-cli
brew install odoo-cli
```

### Docker
```bash
docker pull actec/odoo-cli:latest
docker run --rm -it actec/odoo-cli odoo --help
```

### Binary Download (No Python Required)
Download pre-built binaries from [Releases](https://github.com/RHHOLDING/odoo-cli/releases):

**macOS:**
```bash
curl -L https://github.com/RHHOLDING/odoo-cli/releases/latest/download/odoo-macos -o odoo
chmod +x odoo
./odoo --help
```

**Linux:**
```bash
curl -L https://github.com/RHHOLDING/odoo-cli/releases/latest/download/odoo-linux -o odoo
chmod +x odoo
./odoo --help
```

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri https://github.com/RHHOLDING/odoo-cli/releases/latest/download/odoo-windows.exe -OutFile odoo.exe
.\odoo.exe --help
```

### From Source
```bash
git clone https://github.com/RHHOLDING/odoo-cli.git
cd odoo-xml-cli
pip install -e .
```
```

---

## Open Questions

1. **Package Name on PyPI:**
   - `odoo-cli` - Simple, but might be taken?
   - `odoo-rpc-cli` - More specific
   - `odoorpc-cli` - Clear what it is
   - Check availability: https://pypi.org/search/?q=odoo-cli

2. **License:**
   - Current: Not specified
   - Recommendation: MIT (permissive, good for tools)
   - Need to add LICENSE file

3. **Binary Size:**
   - PyInstaller creates 20-50MB binaries (includes Python)
   - Acceptable for CLI tool?

4. **Auto-update mechanism:**
   - Should tool check for updates?
   - `odoo --update` command?
   - Or rely on package managers?

---

## Quick Win: PyPI Publication (2-3 hours)

**Immediate steps:**
1. Check name availability on PyPI
2. Add MIT license (create LICENSE file)
3. Update pyproject.toml with metadata
4. Create PyPI account
5. Generate API token
6. Build package: `python -m build`
7. Upload: `twine upload dist/*`
8. Test: `pip install odoo-cli`
9. Update README

**Result:** Anyone can install with `pip install odoo-cli`

---

**Status:** Distribution strategy defined - PyPI publication is quick win
**Related:** None (independent improvement)
**Next Action:** Check PyPI name availability, add LICENSE, publish
