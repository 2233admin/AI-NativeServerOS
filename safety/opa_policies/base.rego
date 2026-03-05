package a2alaw.safety

default allow := false

# Allow low-risk actions unconditionally
allow if {
    input.risk_level == "low"
    input.confidence >= 0.7
}

# Medium risk requires higher confidence
allow if {
    input.risk_level == "medium"
    input.confidence >= 0.85
}

# High/critical always requires human approval
deny[msg] if {
    input.risk_level == "critical"
    msg := sprintf("Critical risk action '%s' on '%s' requires human approval", [input.action, input.target])
}

deny[msg] if {
    input.risk_level == "high"
    not input.human_approved
    msg := sprintf("High risk action '%s' requires approval", [input.action])
}

# Block blacklisted patterns
deny[msg] if {
    contains(input.command, "rm -rf /")
    msg := "Blocked: recursive delete on root"
}

deny[msg] if {
    contains(input.command, "chmod 777")
    msg := "Blocked: world-writable permissions"
}

deny[msg] if {
    contains(input.command, "> /dev/sd")
    msg := "Blocked: direct disk write"
}
