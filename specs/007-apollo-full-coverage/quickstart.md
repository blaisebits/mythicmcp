# Quickstart: Apollo Full Command Coverage

**Date**: 2026-02-14
**Feature**: 007-apollo-full-coverage

## What Changed

1. **apollo.yaml** expanded from 10 to 62 commands (100% of Apollo agent)
2. **YamlConfigModel** gains optional `metadata` field
3. **Tests** updated to assert new tool count

## Files Modified

| File | Change |
|------|--------|
| `src/mythicmcp/plugins/builtin/apollo.yaml` | Add 52 new command entries + metadata section |
| `src/mythicmcp/plugins/yaml_loader.py` | Add `metadata` field to `YamlConfigModel` |
| `tests/unit/test_yaml_loader.py` | Update Apollo tool count assertion (10 → 62), add metadata test |

## Verification

```bash
# Run all tests
uv run pytest tests/ -v

# Verify Apollo tool count
uv run python -c "
from mythicmcp.plugins.yaml_loader import load_yaml_plugin
from pathlib import Path
p = load_yaml_plugin(Path('src/mythicmcp/plugins/builtin/apollo.yaml'))
print(f'Apollo tools: {len(p.get_tools())}')
"
```

## Command Categories

| Category | Count | Examples |
|----------|-------|---------|
| Shell/Command Execution | 6 | shell, powershell, powerpick |
| File Operations | 10 | ls, cat, upload, cp, mv, rm |
| Process Management | 4 | ps, kill, jobs, jobkill |
| Agent Management | 3 | sleep, exit, load |
| Assembly/Code Execution | 8 | execute_assembly, execute_pe, execute_coff |
| Injection/Spawning | 7 | inject, shinject, spawn, keylog_inject |
| Token/Identity | 6 | make_token, steal_token, whoami, getsystem |
| Credential Operations | 4 | mimikatz, dcsync, pth, printspoofer |
| Network Reconnaissance | 8 | ifconfig, netstat, ldap_query, net_shares |
| Registry | 2 | reg_query, reg_write_value |
| Service Control | 1 | sc |
| Kerberos Tickets | 7 | ticket_store_*, ticket_cache_* |
| Process/Injection Config | 6 | spawnto_x64, ppid, blockdlls |
| P2P/Networking | 4 | link, unlink, socks, rpfwd |
| Lateral Movement | 2 | jump_wmi, jump_psexec |
