# Uninstall

## Linux

```bash
# Remove binary
rm -f ~/.local/bin/brain

# Remove config (BACKUP FIRST if you want to keep it)
cp -r ~/.brain ~/.brain.backup  # backup
rm -rf ~/.brain                  # remove

# Remove PATH addition (edit ~/.bashrc or ~/.zshrc)
# Delete or comment out lines containing:
#   # Brain CLI
#   export PATH="$PATH:$HOME/.local/bin"

# Remove vault (BACKUP FIRST)
cp -r ~/my-brain ~/my-brain.backup
rm -rf ~/my-brain
```

## Windows

```powershell
# Remove binary
Remove-Item "$env:USERPROFILE\AppData\Local\Programs\brain\brain.exe"

# Remove from PATH
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
$newPath = ($currentPath.Split(';') | Where-Object { $_ -notlike "*brain*" }) -join ';'
[Environment]::SetEnvironmentVariable("PATH", $newPath, "User")

# Remove config (BACKUP FIRST)
Copy-Item "$env:USERPROFILE\.brain" "$env:USERPROFILE\.brain.backup" -Recurse
Remove-Item "$env:USERPROFILE\.brain" -Recurse -Force

# Remove vault
Copy-Item "$env:USERPROFILE\brain-vault" "$env:USERPROFILE\brain-vault.backup" -Recurse
Remove-Item "$env:USERPROFILE\brain-vault" -Recurse -Force
```

## Verify Removal

```bash
# Should return "command not found" or similar
brain --version
```

## Reinstall Later

Follow the Quickstart guide to install the latest version. Your old vault and config backups can be restored from the `.backup` directories.
