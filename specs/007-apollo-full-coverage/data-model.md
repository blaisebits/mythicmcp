# Data Model: Apollo Full Command Coverage

**Date**: 2026-02-14
**Feature**: 007-apollo-full-coverage

## YAML Config Schema Extension

### Metadata Section (new)

Added as optional top-level field on `YamlConfigModel`:

```
metadata:
  agent_version: "2.4.8"        # Version of agent this config targets
  mythic_version: "3.4.6+"      # Minimum Mythic version required
  # Extensible — any additional key-value pairs allowed
```

- `metadata` is `dict[str, Any] | None`, default `None`
- Not validated beyond being a dict — informational only
- Does not trigger unrecognized-key warning

### Command Entries (62 total)

Each command follows the existing schema:

```
- name: <command_name>
  description: "<description>"
  mythic_command: <mythic_cmd>   # only if different from name
  timeout: <int>                 # 30-300, default 60
  parameters:                    # optional, omitted for no-param commands
    - name: <param_name>
      type: string|integer|boolean
      description: "<description>"
      required: true|false
      default: <value>           # optional
      choices:                   # optional, string type only
        - choice1
        - choice2
```

## Command Inventory (62 commands)

### Currently Defined (10) — update parameters as needed
shell, pwd, ls, cd, cat, ps, run, download, execute_assembly, screenshot

### New Commands (52)

**Shell/Command Execution** (4 new):
powershell, powerpick, powershell_import, wmiexecute

**File Operations** (4 new):
upload, cp, mv, rm, mkdir

**Process Management** (2 new):
kill, jobs, jobkill

**Agent Management** (3 new):
sleep, exit, load

**Assembly/Code Execution** (5 new):
inline_assembly, assembly_inject, register_assembly, register_file, register_coff, execute_pe, execute_coff

**Injection/Spawning** (5 new):
inject, shinject, psinject, spawn, screenshot_inject, keylog_inject

**Token/Identity** (6 new):
make_token, steal_token, rev2self, getprivs, whoami, getsystem

**Credential Operations** (4 new):
mimikatz, dcsync, pth, printspoofer

**Network Reconnaissance** (8 new):
ifconfig, netstat, listpipes, net_shares, net_dclist, net_localgroup, net_localgroup_member, ldap_query

**Registry** (2 new):
reg_query, reg_write_value

**Service Control** (1 new):
sc

**Kerberos Tickets** (7 new):
ticket_store_add, ticket_store_list, ticket_store_purge, ticket_cache_add, ticket_cache_list, ticket_cache_purge, ticket_cache_extract

**Process/Injection Config** (6 new):
spawnto_x64, spawnto_x86, ppid, blockdlls, get_injection_techniques, set_injection_technique

**P2P/Networking** (4 new):
link, unlink, socks, rpfwd

**Lateral Movement** (2 new):
jump_wmi, jump_psexec
