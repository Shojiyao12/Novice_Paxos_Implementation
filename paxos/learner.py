import logging
from typing import Dict, Any, Set

from paxos.node import Node
from paxos.message import Message, MessageType


class Learner(Node):
    def __init__(self, node_id: str, ip: str, port: int, config: Dict[str, Any]):
        super().__init__(node_id, ip, port, config)
        # Track accepted operations for each proposal
        self.accepted_operations = {}
        # Set of operations that have been chosen (majority of acceptors agreed)
        self.chosen_operations = set()
        # List of operations in the order they were chosen
        self.chosen_operation_sequence = []
        # Callback to execute when a new operation is chosen
        self.on_chosen_operation = None
        
        self.logger = logging.getLogger(f"Learner_{node_id}")
    
    def _process_message(self, message_dict):
        """Process LEARN messages from acceptors."""
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
            operation=operation
        )
        
        self.logger.info(f"Received {message}")
        
        if message.msg_type == MessageType.LEARN:
            # Track which acceptors have accepted which operations
            operation_key = (timestamp, operation)
            
            if operation_key not in self.accepted_operations:
                self.accepted_operations[operation_key] = set()
            
            # Add this acceptor to the set that has accepted this operation
            self.accepted_operations[operation_key].add(sender_id)
            
            # Check if a majority of acceptors have accepted this operation
            if len(self.accepted_operations[operation_key]) > len(self.acceptors) // 2:
                # If this operation wasn't already chosen, add it
                if operation_key not in self.chosen_operations:
                    self.chosen_operations.add(operation_key)
                    self.chosen_operation_sequence.append(operation)
                    self.logger.info(f"Operation {operation} has been chosen")
                    
                    # If there's a callback function, call it
                    if self.on_chosen_operation:
                        self.on_chosen_operation(operation)
        else:
            self.logger.warning(f"Unexpected message type: {message.msg_type}")
    
    def set_on_chosen_operation(self, callback):
        """Set a callback function to be called when a new operation is chosen."""
        self.on_chosen_operation = callback
    
    def get_chosen_operations(self):
        """Return the list of operations that have been chosen, in order."""
        return self.chosen_operation_sequence.copy()