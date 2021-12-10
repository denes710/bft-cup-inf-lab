from enum import Enum
from constants import *

class MessageType(Enum):
    PRESENT = 0
    ACK = 1
    ABSENT = 2
    INIT = 3
    ECHO = 4
    OPINION = 5
    INPUT = 6
    PREFER = 7
    STRONGPREFER = 8
    NOPREFERENCE = 9
    NOSTRONGPREFERENCE = 10
    NEWINPUT = 11

class Message:
    def __init__(self, type, value = None, consensus_id = None, sender = None, receiver = None):
        self.type = type
        self.sender = sender
        self.consensus_id = consensus_id
        self.value = value
        self.receiver = receiver

    def IsBroadcastMessage(self):
        return self.receiver is None

    def IsConsensusMessage(self, consensus_id):
        return self.consensus_id is not None and self.consensus_id == consensus_id

    def IsNewInput(self):
        return self.type == MessageType.NEWINPUT

    def IsEcho(self):
        return self.type == MessageType.ECHO

    def IsSystem(self):
        return self.type == MessageType.PRESENT or self.type == MessageType.ABSENT
    
    def CreateJson(self, value, consensus_id, receiver):
        return {SENDER_ID_TAG : self.sender, MESSAGE_TYPE_TAG : self.type.name, \
            CONSENSUS_ID_TAG : consensus_id, VALUE_TAG : value, RECEIVER_ID_TAG : None}

    def GetJson(self):
        current_value = self.value.GetJson() if self.IsEcho() else self.value
        return {SENDER_ID_TAG : self.sender, MESSAGE_TYPE_TAG : self.type.name, \
            CONSENSUS_ID_TAG : self.consensus_id, VALUE_TAG : current_value, RECEIVER_ID_TAG : self.receiver}