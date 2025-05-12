import random
import time
import threading
from typing import Dict, List, Any, Set, Callable

class Network:
    def __init__(self, message_delay_range=(0.01, 0.1), message_loss_probability=0.0):
        """
        Simulate a network with message delays and potential message loss.
        
        Args:
            message_delay_range: Tuple of (min_delay, max_delay) in seconds
            message_loss_probability: Probability of dropping a message (0.0-1.0)
        """
        self.message_delay_range = message_delay_range
        self.message_loss_probability = message_loss_probability
        self.failed_nodes: Set[str] = set()
        self.message_handlers: Dict[str, Callable] = {}
        self.logger = logging.getLogger("Network")
    
    def register_node(self, node_id: str, message_handler: Callable):
        """Register a node with the network."""
        self.message_handlers[node_id] = message_handler
        
    def unregister_node(self, node_id: str):
        """Unregister a node from the network."""
        if node_id in self.message_handlers:
            del self.message_handlers[node_id]
    
    def simulate_node_failure(self, node_id: str):
        """Simulate a node failure."""
        self.failed_nodes.add(node_id)
        self.logger.info(f"Node {node_id} has failed")
    
    def simulate_node_recovery(self, node_id: str):
        """Simulate a node recovery."""
        if node_id in self.failed_nodes:
            self.failed_nodes.remove(node_id)
            self.logger.info(f"Node {node_id} has recovered")
    
    def send_message(self, sender_id: str, receiver_id: str, message: Any):
        """
        Send a message from one node to another with simulated delay and potential loss.
        """
        if sender_id in self.failed_nodes:
            self.logger.debug(f"Message from failed node {sender_id} dropped")
            return
        
        if receiver_id in self.failed_nodes:
            self.logger.debug(f"Message to failed node {receiver_id} dropped")
            return
        
        # Simulate message loss
        if random.random() < self.message_loss_probability:
            self.logger.debug(f"Message from {sender_id} to {receiver_id} dropped due to simulated network loss")
            return
        
        # Simulate message delay
        delay = random.uniform(*self.message_delay_range)
        
        # Schedule delivery of the message after the delay
        threading.Timer(delay, self._deliver_message, args=[sender_id, receiver_id, message]).start()
    
    def _deliver_message(self, sender_id: str, receiver_id: str, message: Any):
        """Deliver a message to its destination after the delay."""
        if receiver_id in self.failed_nodes:
            self.logger.debug(f"Message to failed node {receiver_id} dropped during delivery")
            return
        
        if receiver_id in self.message_handlers:
            try:
                self.message_handlers[receiver_id](sender_id, message)
            except Exception as e:
                self.logger.error(f"Error delivering message to {receiver_id}: {e}")
        else:
            self.logger.warning(f"No handler registered for node {receiver_id}")


import logging  # Add this import at the top of the file