# Paxos Consensus Algorithm Simulator

This project simulates the **Paxos Consensus Algorithm**, enabling distributed processes to agree on a single value even in the presence of node failures and unreliable communication. The implementation follows Leslie Lamport's "Paxos Made Simple" paper and provides a configurable environment for testing and understanding the protocol.

---

## 📂 Project Structure

### Core Components
- **`main.py`**: Entry point for running the simulation.
- **`paxos/`**: Core implementation of the Paxos algorithm:
  - `proposer.py`: Implements the proposer role.
  - `acceptor.py`: Implements the acceptor role.
  - `learner.py`: Implements the learner role.
  - `message.py`: Defines message types and formats.
  - `node.py`: Base class for network communication.
  
### Network Simulation
- **`network/`**:
  - `network.py`: Simulates network delays and message losses.
  - `failures.py`: Simulates node failures and recoveries.

### Utilities
- **`utils/`**:
  - `logger.py`: Configures logging for the simulation.
  - `config_loader.py`: Handles configuration loading and validation.

### Configuration
- **`config.json`**: Default configuration file for nodes and their roles.

---

## 🛠️ Requirements

- **Python**: Version 3.7 or higher.
- **Dependencies**: No external libraries required (uses Python's standard library).

---

## 🚀 Getting Started

## 📖 Usage

### Running the Simulation
Run the simulation with default parameters:
```bash
python main.py
```

### Generating a New Configuration
Generate a default configuration file with custom node counts:
```bash
python main.py --generate-config --num-proposers 3 --num-acceptors 5 --num-learners 2
```

### Running with Custom Parameters
Customize the simulation with additional options:
```bash
python main.py --config custom_config.json --message-loss 0.1 --min-delay 0.05 --max-delay 0.2 --failure-prob 0.1
```

---

## ⚙️ Command-Line Arguments

| Argument               | Description                                                                 | Default Value       |
|------------------------|-----------------------------------------------------------------------------|---------------------|
| `--config`            | Path to the configuration file.                                             | `config.json`       |
| `--generate-config`   | Generate a default configuration file.                                      | `False`            |
| `--num-proposers`     | Number of proposers in the default config.                                  | `3`                |
| `--num-acceptors`     | Number of acceptors in the default config.                                  | `5`                |
| `--num-learners`      | Number of learners in the default config.                                   | `2`                |
| `--log-level`         | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).            | `INFO`             |
| `--message-loss`      | Probability of message loss (0.0-1.0).                                      | `0.0`              |
| `--min-delay`         | Minimum message delay in seconds.                                           | `0.01`             |
| `--max-delay`         | Maximum message delay in seconds.                                           | `0.1`              |
| `--failure-prob`      | Probability of node failure during a check.                                 | `0.05`             |
| `--recovery-prob`     | Probability of node recovery during a check.                                | `0.2`              |

---

## 📜 Paxos Protocol Implementation

The Paxos algorithm is implemented in the following phases:

1. **Phase 1a (Prepare)**: 
   - A proposer selects a proposal number and sends a `PREPARE` request to a majority of acceptors.

2. **Phase 1b (Promise)**:
   - Acceptors respond with a `PROMISE` if the proposal number is higher than any they have seen.
   - They include the highest-numbered proposal they have already accepted (if any).

3. **Phase 2a (Accept)**:
   - The proposer sends an `ACCEPT` request to the acceptors with the chosen value.

4. **Phase 2b (Learn)**:
   - Acceptors notify learners of the accepted value.
   - Learners determine the consensus value once a majority of acceptors agree.

---

## 🧪 Simulation Features

- **Multiple Roles**: Simulates proposers, acceptors, and learners.
- **Network Simulation**: Configurable message delays and losses.
- **Failure Handling**: Simulates node failures and recoveries.
- **Logging**: Comprehensive logs for debugging and analysis.
- **Consensus Verification**: Ensures Paxos safety properties:
  - **Agreement**: All learners agree on the same value.
  - **Validity**: The chosen value is proposed by a proposer.
  - **Integrity**: A value is chosen at most once.

---

## 📊 Example Output

### Logs
The simulation logs all protocol messages and events. Example:
```log
2025-04-21 14:42:17,798 - root - INFO - Proposed operation 'test_operation_1745217737' with timestamp 3000001
2025-04-21 14:42:17,815 - root - INFO - CONSENSUS REACHED: Operation 'test_operation_1745217737' has been chosen!
```

### Consensus Verification
- Learners log the chosen operation once consensus is reached.
- Example:
  ```log
  2025-04-21 14:42:17,815 - Learner_learner_1 - INFO - Operation test_operation_1745217737 has been chosen
  ```

---

## 🛡️ How to Verify Correctness

1. **Consensus**: Ensure all learners agree on the same value.
2. **Fault Tolerance**: Verify consensus is reached despite simulated failures.
3. **Safety Properties**: Check that agreement, validity, and integrity are maintained.

---

## 📚 References

- Leslie Lamport, *"Paxos Made Simple"*, November 2001.
- Laboratory Exercise 3 Guide: Paxos Consensus Algorithm Simulation.

---
