import logging

from byzantine_consensus import ByzantineConsensus
from consensus import Consensus
from constants import *
from enum import Enum
from message import Message, MessageType
from node import Node

class ByzantineType(Enum):
    GENERAL = 0
    PARTICIPANT = 1
    BOTH = 2

    @staticmethod
    def FromNumber(number):
        if number is ByzantineType.GENERAL.value:
            return ByzantineType.GENERAL
        elif number is ByzantineType.PARTICIPANT.value:
            return ByzantineType.PARTICIPANT
        elif number is ByzantineType.BOTH.value:
            return ByzantineType.BOTH
        else:
            raise NotImplementedError

    @staticmethod
    def ToString(type):
        if type is ByzantineType.GENERAL:
            return "Byzantine General"
        elif type is ByzantineType.PARTICIPANT:
            return "Byzantine Participant"
        elif type is ByzantineType.BOTH:
            return "Byzantine Both"
        else:
            raise NotImplementedError

class ByzantineNode(Node):
    def __init__(self, node_id, network_event, byzantine_info, nodes):
        Node.__init__(self, node_id, network_event, True)
        self.nodes = nodes
        self.byzantine_type = ByzantineType.FromNumber(byzantine_info[TYPE_TAG])
        self.byzantine_info = byzantine_info
        logging.info("Node{} is {} byzantine!".format(str(self.node_id), self.byzantine_type.name))

    def IsByzantine(self):
        return True

    def IsByzantineGeneral(self):
        return self.byzantine_type == ByzantineType.GENERAL or self.byzantine_type == ByzantineType.BOTH

    def IsByzantineParticipate(self):
        return self.byzantine_type == ByzantineType.PARTICIPANT or self.byzantine_type == ByzantineType.BOTH

    def GetConsensus(self, consensus_id, input_value, add_message_func, nextround_func, get_input_func,
    get_current_round_number_func, set_output_value_func):
        if self.IsByzantineParticipate():
            return ByzantineConsensus(self.node_id, self.available_node_ids, consensus_id, input_value, add_message_func, \
                nextround_func, get_input_func, get_current_round_number_func, set_output_value_func, self.byzantine_info, self.nodes)
        return Consensus(self.node_id, self.available_node_ids, consensus_id, input_value, add_message_func, nextround_func, \
            get_input_func, get_current_round_number_func, set_output_value_func)

    def Run(self):
        if not self.Registration():
            self.Registration()
        self.is_running = True
        while True:
            if self.CheckNewNodes():
                self.NextRound()
            if self.GetTurnOff():
                self.AddMessage(Message(MessageType.ABSENT))
                self.NextRound()
                with self.state_lock:
                    self.turn_offed = True
                break
            self.CheckLeavingNodes()

            if self.input_value is not None:
                if self.IsByzantineGeneral():
                    for i in range(0, len(self.available_node_ids)):
                        if self.available_node_ids[i] != self.node_id:
                            self.AddMessage(Message(MessageType.NEWINPUT, 0 if i % 2 else 1, receiver=self.available_node_ids[i]))
                else:
                    self.AddMessage(Message(MessageType.NEWINPUT, self.input_value))
                self.output_chain[self.round_number + 1] = self.CreateOutputResult(self.input_value)
                self.input_value = None
                self.NextRound()
            self.NextRound()
            new_input_message = self.GetNewInputMessage()
            if new_input_message:
                self.CreateNewConsensusInstances(new_input_message)
                self.NextRound()