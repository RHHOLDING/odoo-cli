# Installation Guides
**Choose your platform and follow the setup steps**

---

## Platform-Specific Guides

### 🍎 macOS
→ **[INSTALL-MAC.md](INSTALL-MAC.md)**
- Homebrew, Python, Virtual Environment setup
- Troubleshooting for macOS-specific issues
- Credential configuration options

### 🐧 Linux (Coming Soon)
→ **INSTALL-LINUX.md** - Ubuntu/Debian/CentOS setup

### 🪟 Windows (Coming Soon)
→ **INSTALL-WINDOWS.md** - PowerShell/Windows Terminal setup

---

## Quick Start (All Platforms)

```bash
# 1. Clone repository
git clone https://github.com/RHHOLDING/odoo-cli.git
cd odoo-cli

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install
pip install -e .

# 4. Configure (create .env)
cat > .env << 'EOF'
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database
ODOO_USERNAME=your-email@example.com
ODOO_PASSWORD=your-password
EOF

# 5. Test
odoo get-models
```

---

## System Requirements

| Item | Minimum | Recommended |
|------|---------|-------------|
| **Python** | 3.10 | 3.11+ |
| **pip** | Latest | Latest |
| **Virtual Env** | venv | venv or conda |
| **Git** | Latest | Latest |
| **Internet** | Required | Required |
| **Disk Space** | 500 MB | 1 GB |

---

## Installation Methods

### Method 1: From GitHub (Development)
```bash
git clone https://github.com/RHHOLDING/odoo-cli.git
cd odoo-cli
pip install -e .
```

### Method 2: From PyPI (When Released)
```bash
pip install odoo-xml-cli
```

### Method 3: Local Development
```bash
# Copy entire odoo-xml-cli folder
cd /path/to/odoo-xml-cli
pip install -e .
```

---

## Verification

After installation, verify with these commands:

```bash
# Check Python version
python3 --version  # Must be 3.10+

# Check pip
pip --version

# Check odoo command
which odoo

# Test connection
odoo get-models

# Show all available models
odoo get-models --json | head -20
```

---

## Configuration

### Credentials Priority Order
1. Command-line arguments (`--url`, `--db`, `--username`, `--password`)
2. Environment variables (`ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`, `ODOO_PASSWORD`)
3. `.env` file in current directory
4. `~/.odoo-cli/config` (system-wide)

### Configuration Files

**Local .env (Development)**
```bash
# .env (in project root, never commit!)
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database
ODOO_USERNAME=your-email@example.com
ODOO_PASSWORD=your-password
ODOO_TIMEOUT=30
```

**System Config (~/.odoo-cli/config)**
```bash
# For system-wide installation
~/.odoo-cli/config:
[odoo]
url = https://your-instance.odoo.com
database = your-database
username = your-email@example.com
password = your-password
timeout = 30
```

---

## Troubleshooting

### Issue: "command not found: odoo"
- ✅ Check virtual environment is activated
- ✅ Try: `python3 -m odoo_cli.cli get-models`
- ✅ Reinstall: `pip install -e .`

### Issue: "Connection refused"
- ✅ Verify ODOO_URL is correct
- ✅ Check internet connection
- ✅ Test: `curl https://your-url.odoo.com`

### Issue: "Authentication failed"
- ✅ Verify credentials in `.env`
- ✅ Test with: `odoo --url X --db Y --username Z get-models`
- ✅ Check password doesn't have special chars (escape if needed)

### Issue: "Python 3.10+ required"
- ✅ Check: `python3 --version`
- ✅ Upgrade Python using Homebrew/apt/choco
- ✅ Create virtual environment with correct version

---

## Using pipx (Recommended for System-Wide)

```bash
# Install pipx (if not already installed)
pip install pipx

# Install odoo-xml-cli
pipx install git+https://github.com/RHHOLDING/odoo-cli.git

# Verify
odoo get-models

# Update
pipx upgrade odoo-xml-cli
```

---

## Docker Installation (Alternative)

If you prefer containerization:

```bash
# Clone repo
git clone https://github.com/RHHOLDING/odoo-cli.git
cd odoo-cli

# Build image
docker build -t odoo-cli .

# Run container
docker run -e ODOO_URL=... -e ODOO_DB=... odoo-cli get-models
```

---

## Next Steps After Installation

1. **Basic Usage:** `odoo get-models`
2. **Read Docs:** [docs/README.md](../README.md)
3. **Learn CLI:** See [docs/](../) directory
4. **View Examples:** [docs/examples/](../examples/)

---

## Getting Help

- 📖 **Documentation:** See [docs/README.md](../README.md)
- 🐛 **Errors:** Check [docs/ERROR-HANDLING.md](../ERROR-HANDLING.md)
- 🔧 **Troubleshooting:** See platform-specific guide (INSTALL-*.md)
- 💬 **Issues:** GitHub Issues tab

---

**Last Updated:** 2025-11-20
**Version:** 1.0.0
**Status:** Production Ready ✅
