import socket
import threading
import json
import logging
from typing import Dict, Any

from paxos.message import Message


class Node:
    def __init__(self, node_id: str, ip: str, port: int, config: Dict[str, Any]):
        self.id = node_id
        self.ip = ip
        self.port = port
        self.config = config
        self.running = False
        self.socket = None
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{node_id}")
        
        # Set up connections to other nodes based on config
        self.proposers = config.get("proposers", {})
        self.acceptors = config.get("acceptors", {})
        self.learners = config.get("learners", {})
    
    def start(self):
        """Start listening for incoming messages."""
        self.running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.ip, self.port))
        
        # Start the receiving thread
        self.receive_thread = threading.Thread(target=self._listen)
        self.receive_thread.daemon = True
        self.receive_thread.start()
        
        self.logger.info(f"Node {self.id} started at {self.ip}:{self.port}")
    
    def stop(self):
        """Stop the node."""
        self.running = False
        if self.socket:
            self.socket.close()
        self.logger.info(f"Node {self.id} stopped")
    
    def _listen(self):
        """Listen for incoming messages."""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(4096)
                message_dict = json.loads(data.decode())
                
                # Process the message in a new thread
                process_thread = threading.Thread(
                    target=self._process_message,
                    args=(message_dict,)
                )
                process_thread.daemon = True
                process_thread.start()
            
            except Exception as e:
                if self.running:  # Only log errors if we're still supposed to be running
                    self.logger.error(f"Error receiving message: {e}")
    
    def _process_message(self, message_dict):
        """Process an incoming message. To be implemented by subclasses."""
        pass
    
    def send_message(self, message: Message):
        """Send a message to another node."""
        # Determine the IP and port of the receiver
        receiver_id = message.receiver_id
        receiver_info = None
        
        if receiver_id in self.proposers:
            receiver_info = self.proposers[receiver_id]
        elif receiver_id in self.acceptors:
            receiver_info = self.acceptors[receiver_id]
        elif receiver_id in self.learners:
            receiver_info = self.learners[receiver_id]
        
        if not receiver_info:
            self.logger.error(f"Receiver {receiver_id} not found in config")
            return False
        
        try:
            # Convert the message to a dictionary and then to JSON
            message_dict = {
                "msg_type": message.msg_type.value,
                "timestamp": message.timestamp,
                "sender_id": message.sender_id,
                "receiver_id": message.receiver_id,
                "operation": message.operation,
                "accepted_timestamp": message.accepted_timestamp,
                "accepted_operation": message.accepted_operation,
            }
            message_json = json.dumps(message_dict)
            
            # Send the message
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(message_json.encode(), (receiver_info["ip"], receiver_info["port"]))
            sock.close()
            
            self.logger.debug(f"Sent {message.msg_type.value} to {receiver_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending message to {receiver_id}: {e}")
            return False