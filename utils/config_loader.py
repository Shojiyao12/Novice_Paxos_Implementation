import json
import os
from typing import Dict, Any


def load_config(config_file: str) -> Dict[str, Any]:
    """Load node configuration from a JSON file."""
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Config file not found: {config_file}")
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Validate the configuration
    if not _validate_config(config):
        raise ValueError("Invalid configuration format")
    
    return config


def _validate_config(config: Dict[str, Any]) -> bool:
    """Validate the configuration format."""
    required_node_types = ["proposers", "acceptors", "learners"]
    
    # Check if all required node types exist
    for node_type in required_node_types:
        if node_type not in config:
            return False
    
    # Check if each node has the required fields
    for node_type in required_node_types:
        nodes = config[node_type]
        for node_id, node_info in nodes.items():
            if "ip" not in node_info or "port" not in node_info:
                return False
    
    return True


def generate_default_config(num_proposers=3, num_acceptors=5, num_learners=2) -> Dict[str, Any]:
    """Generate a default configuration with specified numbers of nodes."""
    config = {
        "proposers": {},
        "acceptors": {},
        "learners": {}
    }
    
    # Generate proposers
    for i in range(num_proposers):
        node_id = f"proposer_{i+1}"
        config["proposers"][node_id] = {
            "ip": "127.0.0.1",
            "port": 8000 + i
        }
    
    # Generate acceptors
    for i in range(num_acceptors):
        node_id = f"acceptor_{i+1}"
        config["acceptors"][node_id] = {
            "ip": "127.0.0.1",
            "port": 9000 + i
        }
    
    # Generate learners
    for i in range(num_learners):
        node_id = f"learner_{i+1}"
        config["learners"][node_id] = {
            "ip": "127.0.0.1",
            "port": 10000 + i
        }
    
    return config


def save_config(config: Dict[str, Any], config_file: str) -> None:
    """Save a configuration to a JSON file."""
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)