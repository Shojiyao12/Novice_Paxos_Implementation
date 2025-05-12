import logging
from typing import Dict, Any, Optional

from paxos.node import Node
from paxos.message import Message, MessageType


class Acceptor(Node):
    def __init__(self, node_id: str, ip: str, port: int, config: Dict[str, Any]):
        super().__init__(node_id, ip, port, config)
        # The highest proposal number this acceptor has promised to
        self.highest_promised_timestamp = 0
        # The highest proposal number and value that this acceptor has accepted
        self.accepted_timestamp: Optional[int] = None
        self.accepted_operation: Optional[Any] = None
        
        self.logger = logging.getLogger(f"Acceptor_{node_id}")
    
    def _process_message(self, message_dict):
        """Process incoming messages according to the Paxos protocol."""
        msg_type = message_dict["msg_type"]
        timestamp = message_dict["timestamp"]
        sender_id = message_dict["sender_id"]
        operation = message_dict.get("operation")
        
        # Convert to a Message object
        message = Message(
            msg_type=MessageType(msg_type),
            timestamp=timestamp,
            sender_id=sender_id,
            receiver_id=self.id,
            operation=operation,
            accepted_timestamp=message_dict.get("accepted_timestamp"),
            accepted_operation=message_dict.get("accepted_operation")
        )
        
        self.logger.info(f"Received {message}")
        
        if message.msg_type == MessageType.PREPARE:
            self._handle_prepare(message)
        elif message.msg_type == MessageType.ACCEPT:
            self._handle_accept(message)
        else:
            self.logger.warning(f"Unexpected message type: {message.msg_type}")
    
    def _handle_prepare(self, message: Message):
        """
        Handle PREPARE message from proposer.
        Phase 1b of the Paxos algorithm.
        """
        # If this prepare request has a higher timestamp than any we've seen
        if message.timestamp > self.highest_promised_timestamp:
            # Promise not to accept proposals with lower timestamps
            self.highest_promised_timestamp = message.timestamp
            
            # If we have already accepted a proposal, include it in the response
            if self.accepted_timestamp is not None:
                response = Message(
                    msg_type=MessageType.PROMISE,
                    timestamp=message.timestamp,
                    sender_id=self.id,
                    receiver_id=message.sender_id,
                    accepted_timestamp=self.accepted_timestamp,
                    accepted_operation=self.accepted_operation
                )
            else:
                # We haven't accepted any proposals yet
                response = Message(
                    msg_type=MessageType.PROMISE,
                    timestamp=message.timestamp,
                    sender_id=self.id,
                    receiver_id=message.sender_id
                )
            
            self.logger.info(f"Sending PROMISE to {message.sender_id} with timestamp {message.timestamp}")
            self.send_message(response)
        else:
            # We've already promised to a higher proposal number, send a NACK
            response = Message(
                msg_type=MessageType.NACK,
                timestamp=message.timestamp,
                sender_id=self.id,
                receiver_id=message.sender_id
            )
            self.logger.info(f"Rejecting PREPARE from {message.sender_id} with timestamp {message.timestamp}")
            self.send_message(response)
    
    def _handle_accept(self, message: Message):
        """
        Handle ACCEPT message from proposer.
        Phase 2b of the Paxos algorithm.
        """
        # If we haven't promised to a higher proposal number, accept this proposal
        if message.timestamp >= self.highest_promised_timestamp:
            self.accepted_timestamp = message.timestamp
            self.accepted_operation = message.operation
            
            # Notify all learners of the accepted value
            for learner_id in self.learners:
                learn_message = Message(
                    msg_type=MessageType.LEARN,
                    timestamp=message.timestamp,
                    sender_id=self.id,
                    receiver_id=learner_id,
                    operation=message.operation
                )
                self.logger.info(f"Sending LEARN to {learner_id} with operation {message.operation}")
                self.send_message(learn_message)
        else:
            # We've already promised to a higher proposal number, send a NACK
            response = Message(
                msg_type=MessageType.NACK,
                timestamp=message.timestamp,
                sender_id=self.id,
                receiver_id=message.sender_id
            )
            self.logger.info(f"Rejecting ACCEPT from {message.sender_id} with timestamp {message.timestamp}")
            self.send_message(response)