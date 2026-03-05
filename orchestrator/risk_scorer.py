"""Risk assessment for execution plans."""

from __future__ import annotations

SYSCALL_BLACKLIST = {
    "mount", "umount", "reboot", "shutdown", "halt", "poweroff",
    "insmod", "rmmod", "modprobe", "swapon", "swapoff",
    "mkfs", "fdisk", "parted", "dd",
    "chroot", "pivot_root", "unshare",
    "ptrace", "process_vm_readv", "process_vm_writev",
    "init_module", "finit_module", "delete_module",
    "kexec_load", "kexec_file_load",
    "bpf", "perf_event_open", "lookup_dcookie",
    "keyctl", "request_key", "add_key",
    "nfsservctl", "quotactl", "acct",
    "settimeofday", "adjtimex", "clock_settime",
    "sethostname", "setdomainname",
    "iopl", "ioperm", "create_module",
    "query_module", "get_kernel_syms",
    "uselib", "personality",
    "syslog", "vhangup",
}

HIGH_RISK_PATTERNS = [
    "rm -rf /",
    "chmod 777",
    "curl | bash",
    "wget | sh",
    "> /dev/sda",
    "mkfs.",
    "dd if=",
    ":(){:|:&};:",
]


def score_command(command: str) -> tuple[float, list[str]]:
    """Score a command's risk from 0.0 (safe) to 1.0 (dangerous).

    Returns (score, list_of_reasons).
    """
    reasons = []
    score = 0.0

    for pattern in HIGH_RISK_PATTERNS:
        if pattern in command:
            reasons.append(f"High-risk pattern: {pattern}")
            score = max(score, 0.9)

    if "sudo" in command or command.strip().startswith("su "):
        reasons.append("Privilege escalation")
        score = max(score, 0.6)

    if any(sc in command for sc in ("systemctl stop", "systemctl disable", "kill -9")):
        reasons.append("Service disruption")
        score = max(score, 0.5)

    if not reasons:
        score = 0.1

    return min(score, 1.0), reasons


def requires_approval(risk_score: float, confidence: float) -> bool:
    """Determine if human approval is needed."""
    if risk_score >= 0.7:
        return True
    if risk_score >= 0.4 and confidence < 0.7:
        return True
    if confidence < 0.5:
        return True
    return False
