import logging
import time
import random
from typing import Dict, Any, List, Set, Optional

from paxos.node import Node
from paxos.message import Message, MessageType


class Proposer(Node):
    def __init__(self, node_id: str, ip: str, port: int, config: Dict[str, Any]):
        super().__init__(node_id, ip, port, config)
        # The highest proposal number used by this proposer
        self.next_timestamp = 1
        # Node ID to ensure uniqueness of proposal numbers
        self.node_number = int(node_id.split('_')[1])
        # Base timestamp unique to this proposer
        self.timestamp_base = self.node_number * 1000000
        
        # Active proposals being tracked
        self.active_proposals = {}
        # Lock to protect access to active_proposals
        self.proposal_lock = threading.Lock()
        
        self.logger = logging.getLogger(f"Proposer_{node_id}")
    
    def propose(self, operation: Any):
        """Start a new proposal."""
        timestamp = self._get_next_timestamp()
        
        # Initialize data for tracking this proposal
        proposal_data = {
            "operation": operation,
            "timestamp": timestamp,
            "phase": 1,  # Phase 1 (prepare)
            "promises": 0,
            "nacks": 0,
            "acceptances": 0,
            "highest_accepted_timestamp": 0,
            "highest_accepted_operation": None,
            "responded_acceptors": set(),
            "acceptor_count": len(self.acceptors)
        }
        
        with self.proposal_lock:
            self.active_proposals[timestamp] = proposal_data
        
        # Start phase 1 (prepare)
        self._send_prepare(timestamp)
        
        # Return the timestamp so the caller can track this proposal
        return timestamp
    
    def _get_next_timestamp(self) -> int:
        """Generate a unique timestamp for this proposer."""
        # Each proposer uses a unique range of timestamps
        timestamp = self.timestamp_base + self.next_timestamp
        self.next_timestamp += 1
        return timestamp
    
    def _send_prepare(self, timestamp: int):
        """Send PREPARE messages to all acceptors (Phase 1a)."""
        for acceptor_id in self.acceptors:
            prepare_message = Message(
                msg_type=MessageType.PREPARE,
                timestamp=timestamp,
                sender_id=self.id,
                receiver_id=acceptor_id
            )
            self.logger.info(f"Sending PREPARE to {acceptor_id} with timestamp {timestamp}")
            self.send_message(prepare_message)
    
    def _process_message(self, message_dict):
        """Process incoming messages according to the Paxos protocol."""
        msg_type = message_dict["msg_type"]
        timestamp = message_dict["timestamp"]
        sender_id = message_dict["sender_id"]
        
        # Convert to a Message object
        message = Message(
            msg_type=MessageType(msg_type),
            timestamp=timestamp,
            sender_id=sender_id,
            receiver_id=self.id,
            operation=message_dict.get("operation"),
            accepted_timestamp=message_dict.get("accepted_timestamp"),
            accepted_operation=message_dict.get("accepted_operation")
        )
        
        self.logger.info(f"Received {message}")
        
        # Check if this is a response to one of our active proposals
        with self.proposal_lock:
            if timestamp not in self.active_proposals:
                self.logger.warning(f"Received response for unknown proposal {timestamp}")
                return
            
            proposal_data = self.active_proposals[timestamp]
            
            # Avoid counting responses from the same acceptor multiple times
            if sender_id in proposal_data["responded_acceptors"]:
                self.logger.warning(f"Duplicate response from {sender_id} for proposal {timestamp}")
                return
            proposal_data["responded_acceptors"].add(sender_id)
            
            if message.msg_type == MessageType.PROMISE:
                self._handle_promise(message, proposal_data)
            elif message.msg_type == MessageType.NACK:
                self._handle_nack(message, proposal_data)
            else:
                self.logger.warning(f"Unexpected message type: {message.msg_type}")
    
    def _handle_promise(self, message: Message, proposal_data: Dict):
        """Handle PROMISE message from acceptor."""
        proposal_data["promises"] += 1
        
        # If the acceptor has already accepted a proposal, update our tracking
        if message.accepted_timestamp is not None:
            if message.accepted_timestamp > proposal_data["highest_accepted_timestamp"]:
                proposal_data["highest_accepted_timestamp"] = message.accepted_timestamp
                proposal_data["highest_accepted_operation"] = message.accepted_operation
        
        # Check if we have a majority of promises
        if proposal_data["promises"] > proposal_data["acceptor_count"] // 2:
            # If we haven't started phase 2 yet, do so now
            if proposal_data["phase"] == 1:
                proposal_data["phase"] = 2  # Phase 2 (accept)
                
                # Determine what operation to propose
                if proposal_data["highest_accepted_operation"] is not None:
                    # Use the operation from the highest accepted proposal
                    operation = proposal_data["highest_accepted_operation"]
                else:
                    # Use our original operation
                    operation = proposal_data["operation"]
                
                # Send ACCEPT messages to all acceptors
                self._send_accept(proposal_data["timestamp"], operation)
    
    def _handle_nack(self, message: Message, proposal_data: Dict):
        """Handle NACK message from acceptor."""
        proposal_data["nacks"] += 1
        
        # If a majority of acceptors have rejected our proposal, abandon it
        if proposal_data["nacks"] > proposal_data["acceptor_count"] // 2:
            self.logger.info(f"Abandoning proposal {proposal_data['timestamp']} due to NACKs")
            # Remove this proposal from active proposals
            with self.proposal_lock:
                self.active_proposals.pop(proposal_data["timestamp"], None)
    
    def _send_accept(self, timestamp: int, operation: Any):
        """Send ACCEPT messages to all acceptors (Phase 2a)."""
        for acceptor_id in self.acceptors:
            accept_message = Message(
                msg_type=MessageType.ACCEPT,
                timestamp=timestamp,
                sender_id=self.id,
                receiver_id=acceptor_id,
                operation=operation
            )
            self.logger.info(f"Sending ACCEPT to {acceptor_id} with timestamp {timestamp} and operation {operation}")
            self.send_message(accept_message)


import threading  # Add this import at the top of the file