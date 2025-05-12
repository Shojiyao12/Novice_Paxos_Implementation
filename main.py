import argparse
import logging
import sys
import time
import json
import threading
from typing import Dict, Any, List

from paxos.proposer import Proposer
from paxos.acceptor import Acceptor
from paxos.learner import Learner
from network.network import Network
from network.failures import FailureSimulator
from utils.logger import setup_logger
from utils.config_loader import load_config, generate_default_config, save_config


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Paxos Consensus Algorithm Simulator")
    
    parser.add_argument('--config', type=str, default='config.json',
                        help='Path to the configuration file')
    parser.add_argument('--generate-config', action='store_true',
                        help='Generate a default configuration file')
    parser.add_argument('--num-proposers', type=int, default=3,
                        help='Number of proposers to generate in the default config')
    parser.add_argument('--num-acceptors', type=int, default=5,
                        help='Number of acceptors to generate in the default config')
    parser.add_argument('--num-learners', type=int, default=2,
                        help='Number of learners to generate in the default config')
    parser.add_argument('--log-level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging level')
    parser.add_argument('--message-loss', type=float, default=0.0,
                        help='Probability of message loss (0.0-1.0)')
    parser.add_argument('--min-delay', type=float, default=0.01,
                        help='Minimum message delay in seconds')
    parser.add_argument('--max-delay', type=float, default=0.1,
                        help='Maximum message delay in seconds')
    parser.add_argument('--failure-prob', type=float, default=0.05,
                        help='Probability of node failure during a check')
    parser.add_argument('--recovery-prob', type=float, default=0.2,
                        help='Probability of node recovery during a check')
    
    return parser.parse_args()


def load_or_generate_config(args):
    """Load the configuration or generate a default one if requested."""
    if args.generate_config:
        config = generate_default_config(
            num_proposers=args.num_proposers,
            num_acceptors=args.num_acceptors,
            num_learners=args.num_learners
        )
        save_config(config, args.config)
        logging.info(f"Generated default configuration and saved to {args.config}")
    
    try:
        return load_config(args.config)
    except (FileNotFoundError, ValueError) as e:
        logging.error(f"Error loading configuration: {e}")
        sys.exit(1)


def create_nodes(config, network):
    """Create all the nodes specified in the configuration."""
    proposers = {}
    acceptors = {}
    learners = {}
    
    # Create proposers
    for prop_id, prop_info in config["proposers"].items():
        proposer = Proposer(
            node_id=prop_id,
            ip=prop_info["ip"],
            port=prop_info["port"],
            config=config
        )
        proposers[prop_id] = proposer
        network.register_node(prop_id, proposer._process_message)
    
    # Create acceptors
    for acc_id, acc_info in config["acceptors"].items():
        acceptor = Acceptor(
            node_id=acc_id,
            ip=acc_info["ip"],
            port=acc_info["port"],
            config=config
        )
        acceptors[acc_id] = acceptor
        network.register_node(acc_id, acceptor._process_message)
    
    # Create learners
    for learn_id, learn_info in config["learners"].items():
        learner = Learner(
            node_id=learn_id,
            ip=learn_info["ip"],
            port=learn_info["port"],
            config=config
        )
        learners[learn_id] = learner
        network.register_node(learn_id, learner._process_message)
    
    return proposers, acceptors, learners


def on_operation_chosen(operation):
    """Callback for when an operation is chosen."""
    logging.info(f"CONSENSUS REACHED: Operation '{operation}' has been chosen!")


def run_simulation(args):
    """Run the Paxos consensus simulation."""
    # Set up logging
    log_level = getattr(logging, args.log_level)
    setup_logger(log_level=log_level)
    
    # Load configuration
    config = load_or_generate_config(args)
    
    # Create network with specified parameters
    network = Network(
        message_delay_range=(args.min_delay, args.max_delay),
        message_loss_probability=args.message_loss
    )
    
    # Create nodes
    proposers, acceptors, learners = create_nodes(config, network)
    
    # Set up failure simulator
    failure_simulator = FailureSimulator(
        network=network,
        config=config,
        failure_probability=args.failure_prob,
        recovery_probability=args.recovery_prob
    )
    
    # Start all nodes
    logging.info("Starting all nodes...")
    for node_list in [proposers.values(), acceptors.values(), learners.values()]:
        for node in node_list:
            node.start()
    
    # Set callbacks for learners
    for learner in learners.values():
        learner.set_on_chosen_operation(on_operation_chosen)
    
    # Start failure simulator if enabled
    if args.failure_prob > 0:
        failure_simulator.start()
        logging.info("Failure simulator started")
    
    # Run some test proposals
    try:
        # Wait a moment for all nodes to initialize
        time.sleep(1)
        
        # Choose a proposer randomly
        import random
        proposer_ids = list(proposers.keys())
        chosen_proposer_id = random.choice(proposer_ids)
        chosen_proposer = proposers[chosen_proposer_id]
        
        logging.info(f"Selected proposer {chosen_proposer_id} to propose a value")
        
        # Propose a value
        operation = f"test_operation_{int(time.time())}"
        proposal_timestamp = chosen_proposer.propose(operation)
        
        logging.info(f"Proposed operation '{operation}' with timestamp {proposal_timestamp}")
        
        # Wait for consensus to be reached
        wait_time = 0
        max_wait = 10  # seconds
        consensus_reached = False
        
        while wait_time < max_wait and not consensus_reached:
            time.sleep(0.5)
            wait_time += 0.5
            
            # Check if any learner has learned the value
            for learner_id, learner in learners.items():
                chosen_ops = learner.get_chosen_operations()
                if operation in chosen_ops:
                    consensus_reached = True
                    logging.info(f"Learner {learner_id} has learned the chosen operation: {operation}")
                    break
        
        if consensus_reached:
            logging.info("Paxos consensus algorithm successfully demonstrated!")
        else:
            logging.warning("Consensus not reached within the time limit. This could be due to simulated failures or message losses.")
        
        # Keep the simulation running for manual inspection
        logging.info("Simulation running. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        logging.info("Simulation interrupted by user")
    
    finally:
        # Clean up resources
        if args.failure_prob > 0:
            failure_simulator.stop()
        
        for node_list in [proposers.values(), acceptors.values(), learners.values()]:
            for node in node_list:
                node.stop()
        
        logging.info("Simulation finished")


if __name__ == "__main__":
    args = parse_arguments()
    run_simulation(args)