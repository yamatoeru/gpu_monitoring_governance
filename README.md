# gpu_monitoring_governance

You are a senior infrastructure engineer.

Generate production-ready code for a GPU monitoring governance system based on the following constraints and architecture.

---

SYSTEM CONTEXT

The system operates in an air-gapped environment with:

- No central root access
- No Ansible/Puppet
- User-driven installation
- Centralized monitoring required

---

TARGET ENVIRONMENTS

1. Windows VM
2. Linux VM / Baremetal
3. Kubernetes

---

ARCHITECTURE

Components

- gpu-agent (Python CLI)
- Telegraf (data collection)
- dcgm-exporter (Linux/K8s GPU metrics)
- ClickHouse (central storage)

---

DESIGN RULES

1. Do NOT assume SSH or root access
2. Do NOT use external internet
3. Do NOT rely on Ansible/Puppet
4. Separate:
   - Validation logic (gpu-agent)
   - Transport (Telegraf)
   - Storage (ClickHouse)
5. Keep user interface minimal

---

REQUIRED FEATURES

gpu-agent CLI

Commands:

- install
- validate
- repair
- upgrade
- version

---

VALIDATION LOGIC

Implement checks:

Common

- agent version
- latest version (via HTTP JSON)

Linux

- nvidia-smi
- systemd service (telegraf, dcgm-exporter)
- dcgm metrics endpoint

Windows

- nvidia-smi
- Windows service (telegraf)

Kubernetes

- DaemonSet status
- Pod health
- metrics endpoint

---

OUTPUT FORMAT

The agent must produce a JSON file:

Path:

- Linux: /var/log/gpu-agent/last_result.json
- Windows: C:\gpu-agent\status\last_result.json

Format:

{
"event_time": "...",
"host": "...",
"env_type": "...",
"os_type": "...",
"event_type": "...",
"severity": "...",
"error_code": "...",
"message": "...",
"root_cause": "...",
"recommended_action": "...",
"agent_version": "...",
"config_version": "...",
"checks": [...]
}

---

REPAIR LOGIC

Implement safe actions only:

- restart services
- recreate missing config
- re-run validation

---

VERSION CHECK

Fetch from:

http://repo.internal/gpu-agent/latest_version.json

Compare with current version.

---

TELEGRAF INTEGRATION

Assume Telegraf reads JSON file and sends to central system.

Do NOT implement ingestion in gpu-agent.

---

KUBERNETES

Generate:

- DaemonSet YAML for dcgm-exporter
- DaemonSet YAML for Telegraf
- CronJob YAML for validator

---

OUTPUT REQUIREMENTS

Generate:

1. Python CLI code (modular, production-ready)
2. Linux systemd service files
3. Windows PowerShell scripts
4. Kubernetes YAML manifests
5. Example Telegraf config

---

CODE QUALITY

- Use clean modular structure
- Add comments explaining logic
- Include error handling
- Avoid unnecessary dependencies

---

Now generate the full implementation.