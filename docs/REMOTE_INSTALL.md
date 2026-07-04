# Remote Install

Install Brain CLI on a remote machine without interactive login.

## Linux (SSH)

```bash
# One-liner
ssh user@host "curl -fsSL https://github.com/MohamedHussien-zseeker/ai-dev-brain-kit/releases/latest/download/install.sh | bash"

# Or with version pinning
ssh user@host "curl -fsSL https://github.com/MohamedHussien-zseeker/ai-dev-brain-kit/releases/latest/download/install.sh | bash -s -- --version v0.1.0"

# Custom install directory
ssh user@host "curl -fsSL https://github.com/MohamedHussien-zseeker/ai-dev-brain-kit/releases/latest/download/install.sh | bash -s -- --dir /opt/brain"

# Ansible
- name: Install Brain CLI
  ansible.builtin.shell: |
    curl -fsSL https://github.com/MohamedHussien-zseeker/ai-dev-brain-kit/releases/latest/download/install.sh | bash
  args:
    creates: "{{ ansible_env.HOME }}/.local/bin/brain"
```

## Windows (WinRM)

```powershell
# PowerShell Remoting
Invoke-Command -ComputerName SERVER -ScriptBlock {
    Invoke-WebRequest -Uri https://github.com/MohamedHussien-zseeker/ai-dev-brain-kit/releases/latest/download/install.ps1 -OutFile install.ps1
    .\install.ps1
}
```

## Docker

```dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y curl
RUN curl -fsSL https://github.com/MohamedHussien-zseeker/ai-dev-brain-kit/releases/latest/download/install.sh | bash
```

## CI/CD

```yaml
# GitHub Actions
- name: Install Brain CLI
  run: |
    curl -fsSL https://github.com/MohamedHussien-zseeker/ai-dev-brain-kit/releases/latest/download/install.sh | bash
    brain --version
```

## Post-Install Verification

```bash
# Verify binary
brain --version

# Health check
brain doctor --offline

# Initialize vault
brain init --vault /path/to/vault
```
