# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in odoo-cli, please help us address it responsibly.

### How to Report

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, use one of these methods:

1. **GitHub Security Advisory** (Recommended)
   - Go to the [Security tab](https://github.com/RHHOLDING/odoo-cli/security/advisories)
   - Click "Report a vulnerability"
   - Provide details in the private advisory

2. **Email**
   - Send to: andre@solarcraft.gmbh
   - Subject: "Security Vulnerability in odoo-cli"
   - Include: Description, steps to reproduce, impact assessment

### What to Include

When reporting a vulnerability, please provide:

- **Description** - Clear explanation of the issue
- **Steps to Reproduce** - Detailed instructions
- **Impact** - What can an attacker do?
- **Affected Versions** - Which versions are vulnerable?
- **Proof of Concept** - Code or commands (if applicable)
- **Suggested Fix** - If you have ideas (optional)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - Critical: 1-7 days
  - High: 7-14 days
  - Medium: 14-30 days
  - Low: 30-60 days

### Security Update Process

1. We acknowledge receipt of your report
2. We investigate and confirm the vulnerability
3. We develop and test a fix
4. We release a security patch
5. We credit you in the release notes (unless you prefer anonymity)

### Scope

**In Scope:**
- Authentication bypass
- SQL injection via domain filters
- Command injection
- Credential exposure
- Privilege escalation
- Code execution vulnerabilities

**Out of Scope:**
- Odoo server vulnerabilities (report to Odoo S.A.)
- Third-party dependencies (report to respective maintainers)
- Social engineering attacks
- Denial of service via rate limiting

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.4.x   | ✅ Yes             |
| 1.3.x   | ✅ Yes (until 2025-06) |
| 1.2.x   | ⚠️ Limited         |
| < 1.2   | ❌ No              |

## Security Best Practices for Users

When using odoo-cli:

1. **Credentials Management**
   - Never commit `.env` files to version control
   - Use environment variables or `~/.odoo-cli.yaml`
   - Rotate passwords regularly
   - Use read-only Odoo users when possible

2. **Network Security**
   - Always use HTTPS for Odoo connections
   - Verify SSL certificates (avoid `--no-verify-ssl` in production)
   - Use VPN for accessing internal Odoo instances

3. **Access Control**
   - Create dedicated API users with minimal permissions
   - Avoid using admin accounts for automation
   - Monitor Odoo access logs for unusual activity

4. **Data Safety**
   - Test commands in development environments first
   - Create backups before bulk operations
   - Review domain filters before destructive operations (delete, update-bulk)

## Disclosure Policy

We follow **coordinated disclosure**:

1. You report the vulnerability privately
2. We work with you to understand and fix the issue
3. We release a security patch
4. We publicly disclose the vulnerability (with your consent)
5. We credit you in the security advisory (unless anonymous)

We aim to disclose vulnerabilities within **90 days** of the initial report.

## Contact

- **Security Email**: andre@solarcraft.gmbh
- **Maintainer**: Andre Kremer ([@actec-andre](https://github.com/actec-andre))
- **GitHub Security**: [Report Vulnerability](https://github.com/RHHOLDING/odoo-cli/security/advisories/new)

---

Thank you for helping keep odoo-cli and its users safe!
