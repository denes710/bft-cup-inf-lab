from consensus import Consensus
from constants import *
from message import Message, MessageType

class ByzantineConsensus(Consensus):
    def __init__(self, node_id, available_node_ids, consensus_id, input_value, message_func, next_round_func,
    get_input_func, get_current_round_func, set_output_func, byzantine_info, nodes):
        Consensus.__init__(self, node_id, available_node_ids, consensus_id, input_value, message_func, \
            next_round_func, get_input_func, get_current_round_func, set_output_func)
        #FIXME it is not the best
        self.nodes = nodes
        self.echo_commands = byzantine_info[ECHOES_TAG] if ECHOES_TAG in byzantine_info else {}
        self.init_commands = byzantine_info[INITS_TAG] if INITS_TAG in byzantine_info else {}
        self.own_value = byzantine_info[OWN_VALUE_TAG] if OWN_VALUE_TAG in byzantine_info else None

    def CorrectNodesLeft(self):
        for node in self.nodes:
            if node.node_id in self.participants and self.consensus_id not in node.output_chain:
                return False
        return True

    def SendDifferentMessageValues(self, message_type, plus = 0):
        if self.own_value:
            self.message_func(Message(message_type, self.own_value, self.consensus_id))
        else:
            for i in range(0, len(self.participants)):
                self.message_func(Message(message_type, (i + plus) % 2, self.consensus_id, receiver=self.participants[i]))
 
    def InitByzantineConsensus(self):
        current_round = self.get_current_round_func()
        if current_round not in self.echo_commands and current_round not in self.init_commands:
            self.InitConsensus()
            return
        if current_round in self.init_commands:
            current_init_info = self.init_commands[current_round]
            for id in current_init_info:
                self.message_func(Message(MessageType.INIT, consensus_id=self.consensus_id, receiver=id))
        else:
            self.message_func(Message(MessageType.INIT, None, self.consensus_id))
        self.next_round_func()

        current_round = self.get_current_round_func()
        if current_round in self.echo_commands:
            for message in self.get_input_func(self.consensus_id, self.available_node_ids):
                if message.type == MessageType.INIT:
                    self.participants.append(message.sender)
            current_echoes_info = self.echo_commands[current_round]
            for id in current_echoes_info[RECEIVER_IDS_TAG]:
                self.message_func(Message(MessageType.ECHO, Message(MessageType.INIT, consensus_id=self.consensus_id, \
                    sender=current_echoes_info[NODE_ID_TAG]), receiver=id, consensus_id=self.consensus_id))
        else:
            for message in self.get_input_func(self.consensus_id, self.available_node_ids):
                if message.type == MessageType.INIT:
                    self.participants.append(message.sender)
                    self.message_func(Message(MessageType.ECHO, message, self.consensus_id))
        self.next_round_func()

    def Run(self):
        self.InitByzantineConsensus()
        participants_number = len(self.participants)
        if participants_number < 3:
            self.set_output_func(self.input_value, self.consensus_id)
            return
        # final if r − r′ > 5|S|/2 + 2.
        maximum_round_number = (5 * participants_number) / 2 + 2 + self.consensus_id
        while self.get_current_round_func() <= maximum_round_number and not self.CorrectNodesLeft():
            if self.input_value is not None:
                self.SendDifferentMessageValues(MessageType.INPUT)
                self.next_round_func()
            self.SendDifferentMessageValues(MessageType.PREFER, 1)
            self.next_round_func()
            self.SendDifferentMessageValues(MessageType.STRONGPREFER)
            self.SendDifferentMessageValues(MessageType.OPINION)
            self.next_round_func()