import random
import time
import threading
from typing import List, Dict, Any

from network.network import Network


class FailureSimulator:
    def __init__(self, network: Network, config: Dict[str, Any], failure_probability=0.05, recovery_probability=0.2):
        """
        Simulate random node failures and recoveries.
        
        Args:
            network: The network to simulate failures on
            config: The configuration containing node information
            failure_probability: Probability of a node failing during a check
            recovery_probability: Probability of a failed node recovering during a check
        """
        self.network = network
        self.config = config
        self.failure_probability = failure_probability
        self.recovery_probability = recovery_probability
        self.running = False
        self.failure_thread = None
        self.failed_nodes = set()
        self.logger = logging.getLogger("FailureSimulator")
    
    def start(self, check_interval=5.0):
        """
        Start the failure simulator with a specified check interval.
        
        Args:
            check_interval: Time between failure/recovery checks in seconds
        """
        self.running = True
        self.failure_thread = threading.Thread(target=self._failure_loop, args=[check_interval])
        self.failure_thread.daemon = True
        self.failure_thread.start()
        self.logger.info("Failure simulator started")
    
    def stop(self):
        """Stop the failure simulator."""
        self.running = False
        if self.failure_thread:
            self.failure_thread.join(timeout=1.0)
        self.logger.info("Failure simulator stopped")
    
    def _failure_loop(self, check_interval):
        """Periodically check for node failures and recoveries."""
        while self.running:
            self._check_failures()
            self._check_recoveries()
            time.sleep(check_interval)
    
    def _check_failures(self):
        """Check each active node for potential failure."""
        nodes = {**self.config.get("proposers", {}), **self.config.get("acceptors", {}), **self.config.get("learners", {})}
        
        for node_id in nodes:
            if node_id not in self.failed_nodes and random.random() < self.failure_probability:
                self._simulate_node_failure(node_id)
    
    def _check_recoveries(self):
        """Check each failed node for potential recovery."""
        for node_id in list(self.failed_nodes):
            if random.random() < self.recovery_probability:
                self._simulate_node_recovery(node_id)
    
    def _simulate_node_failure(self, node_id):
        """Simulate the failure of a specific node."""
        self.failed_nodes.add(node_id)
        self.network.simulate_node_failure(node_id)
        self.logger.info(f"Simulated failure of node {node_id}")
    
    def _simulate_node_recovery(self, node_id):
        """Simulate the recovery of a specific node."""
        self.failed_nodes.remove(node_id)
        self.network.simulate_node_recovery(node_id)
        self.logger.info(f"Simulated recovery of node {node_id}")
    
    def manually_fail_node(self, node_id):
        """Manually trigger a node failure."""
        if node_id not in self.failed_nodes:
            self._simulate_node_failure(node_id)
            return True
        return False
    
    def manually_recover_node(self, node_id):
        """Manually trigger a node recovery."""
        if node_id in self.failed_nodes:
            self._simulate_node_recovery(node_id)
            return True
        return False


import logging  # Add this import at the top of the file