from enum import Enum
from dataclasses import dataclass
from typing import Optional, Any


class MessageType(Enum):
    PREPARE = "PREPARE"
    PROMISE = "PROMISE"
    ACCEPT = "ACCEPT"
    LEARN = "LEARN"
    NACK = "NACK"  # For rejections


@dataclass
class Message:
    msg_type: MessageType
    timestamp: int  # Also referred to as proposal number
    sender_id: str
    receiver_id: str
    operation: Optional[Any] = None  # The value being proposed
    accepted_timestamp: Optional[int] = None  # Used in PROMISE responses
    accepted_operation: Optional[Any] = None  # Used in PROMISE responses
    
    def __str__(self):
        if self.msg_type == MessageType.PREPARE:
            return f"PREPARE <{self.timestamp}>"
        elif self.msg_type == MessageType.PROMISE:
            if self.accepted_operation is not None:
                return f"<{self.accepted_timestamp}, {self.accepted_operation}>"
            else:
                return f"PROMISE <{self.timestamp}>"
        elif self.msg_type == MessageType.ACCEPT:
            return f"ACCEPT <{self.timestamp}, {self.operation}>"
        elif self.msg_type == MessageType.LEARN:
            return f"LEARN <{self.operation}>"
        elif self.msg_type == MessageType.NACK:
            return f"NACK <{self.timestamp}>"
        else:
            return f"Unknown message type: {self.msg_type}"