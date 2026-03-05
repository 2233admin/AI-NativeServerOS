"""Mesh Council — peer-to-peer discussion and consensus.

Nodes communicate via Redis Stream 'mesh:council'. Any node can propose
an action; peers vote. Quorum of 2/3 needed to approve risky operations.

Protocol:
  1. Node A publishes PROPOSAL to mesh:council
  2. Peers B,C read proposal and publish VOTE (approve/reject + reason)
  3. After quorum or timeout, proposer executes or aborts
  4. Result published as RESOLUTION

This enables three-node collective decision-making:
  "Should we reboot tokyo?" → central proposes, sv+tokyo vote
  "Upgrade nginx on all?" → any node proposes, 2/3 must agree
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum

from a2alaw.mesh.peer import whoami, peers, Node, MESH


COUNCIL_STREAM = "mesh:council"
QUORUM = 2  # 2 out of 3 nodes must agree
VOTE_TIMEOUT_S = 60


class MessageType(Enum):
    PROPOSAL = "proposal"
    VOTE = "vote"
    RESOLUTION = "resolution"
    CHAT = "chat"  # Free-form inter-node discussion


class VoteChoice(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


@dataclass
class Proposal:
    id: str
    proposer: str
    action: str  # NL description of what to do
    target_nodes: list[str]  # Which nodes are affected
    risk_level: str = "low"
    timestamp: float = 0.0
    votes: dict[str, VoteChoice] = field(default_factory=dict)
    resolved: bool = False

    def vote_count(self, choice: VoteChoice) -> int:
        return sum(1 for v in self.votes.values() if v == choice)

    @property
    def approved(self) -> bool:
        return self.vote_count(VoteChoice.APPROVE) >= QUORUM

    @property
    def rejected(self) -> bool:
        return self.vote_count(VoteChoice.REJECT) >= QUORUM


class Council:
    """Mesh council for peer deliberation."""

    def __init__(self, event_bus):
        self.me = whoami()
        self.bus = event_bus
        self.pending: dict[str, Proposal] = {}

    def propose(self, action: str, target_nodes: list[str] | None = None,
                risk_level: str = "medium") -> Proposal:
        """Publish a proposal for peer vote."""
        prop = Proposal(
            id=uuid.uuid4().hex[:12],
            proposer=self.me.name,
            action=action,
            target_nodes=target_nodes or [n.name for n in MESH],
            risk_level=risk_level,
            timestamp=time.time(),
        )
        # Self-vote: proposer approves their own proposal
        prop.votes[self.me.name] = VoteChoice.APPROVE

        self.bus.publish(COUNCIL_STREAM, {
            "type": MessageType.PROPOSAL.value,
            "proposal_id": prop.id,
            "proposer": prop.proposer,
            "action": prop.action,
            "target_nodes": json.dumps(prop.target_nodes),
            "risk_level": prop.risk_level,
        })

        self.pending[prop.id] = prop
        return prop

    def vote(self, proposal_id: str, choice: VoteChoice, reason: str = ""):
        """Cast a vote on a proposal."""
        self.bus.publish(COUNCIL_STREAM, {
            "type": MessageType.VOTE.value,
            "proposal_id": proposal_id,
            "voter": self.me.name,
            "choice": choice.value,
            "reason": reason,
        })

    def chat(self, message: str, to: str | None = None):
        """Send a free-form message to peers (or a specific node)."""
        self.bus.publish(COUNCIL_STREAM, {
            "type": MessageType.CHAT.value,
            "from": self.me.name,
            "to": to or "all",
            "message": message,
        })

    def resolve(self, proposal_id: str, outcome: str):
        """Publish final resolution."""
        self.bus.publish(COUNCIL_STREAM, {
            "type": MessageType.RESOLUTION.value,
            "proposal_id": proposal_id,
            "resolver": self.me.name,
            "outcome": outcome,
        })
        if proposal_id in self.pending:
            self.pending[proposal_id].resolved = True

    def wait_for_quorum(self, proposal_id: str, timeout_s: float = VOTE_TIMEOUT_S) -> Proposal:
        """Poll council stream for votes until quorum or timeout."""
        prop = self.pending.get(proposal_id)
        if not prop:
            raise ValueError(f"Unknown proposal: {proposal_id}")

        deadline = time.time() + timeout_s
        while time.time() < deadline:
            messages = self.bus.consume(
                COUNCIL_STREAM,
                group=f"council-{self.me.name}",
                consumer=self.me.name,
                count=10,
                block_ms=2000,
            )
            for _, msg in messages:
                if msg.get("type") == MessageType.VOTE.value:
                    if msg.get("proposal_id") == proposal_id:
                        voter = msg["voter"]
                        choice = VoteChoice(msg["choice"])
                        prop.votes[voter] = choice

            if prop.approved or prop.rejected:
                break

        return prop

    def auto_vote(self, proposal_id: str, action: str, risk_level: str) -> VoteChoice:
        """Automatic voting policy: approve low-risk, reject critical without detail."""
        if risk_level == "low":
            choice = VoteChoice.APPROVE
            reason = "Low risk, auto-approved"
        elif risk_level == "critical":
            choice = VoteChoice.REJECT
            reason = "Critical risk requires human review"
        else:
            # Medium/high: approve if it's a known safe pattern
            safe_patterns = ["check", "status", "install", "restart", "update"]
            if any(p in action.lower() for p in safe_patterns):
                choice = VoteChoice.APPROVE
                reason = "Known safe operation pattern"
            else:
                choice = VoteChoice.ABSTAIN
                reason = "Unknown operation, abstaining"

        self.vote(proposal_id, choice, reason)
        return choice
