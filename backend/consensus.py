from message import Message, MessageType
from rotor_coordinator import RotorCoordinator

class Consensus:
    def __init__(self, node_id, available_node_ids, consensus_id, input_value, message_func, next_round_func, get_input_func, get_current_round_func, set_output_func):
        self.node_id = node_id
        self.available_node_ids = available_node_ids
        self.consensus_id = consensus_id
        self.message_func = message_func
        self.next_round_func = next_round_func
        self.get_input_func = get_input_func
        self.input_value = input_value
        self.participants = []
        self.get_current_round_func = get_current_round_func
        self.set_output_func = set_output_func
        self.rotor_coordinator = None

    def ReceivedValueRateChecking(self, input_messages, type, value):
        counter = 0
        for message in input_messages:
            if message.type == type and message.value == value:
                counter += 1
        return counter

    def GetDictionary(self, input_messages, type):
        result = {}
        for message in input_messages:
            if message.type == type:
                if message.value in result:
                    result[message.value] = result[message.value] + 1
                else:
                    result[message.value] = 1
        return result

    def GetOpinion(self, input_messages):
        for message in input_messages:
            if message.type == MessageType.OPINION and message.sender == self.rotor_coordinator.previous_round_p:
                return message.value
        return -1

    def InitConsensus(self):
        self.message_func(Message(MessageType.INIT, None, self.consensus_id))
        self.next_round_func()
        for message in self.get_input_func(self.consensus_id, self.available_node_ids):
            if message.type == MessageType.INIT:
                self.participants.append(message.sender)
                self.message_func(Message(MessageType.ECHO, message, self.consensus_id))
        self.next_round_func()

    def Run(self):
        self.InitConsensus()
        participants_number = len(self.participants)
        if participants_number < 3:
            self.set_output_func(self.input_value, self.consensus_id)
            return
        self.rotor_coordinator = RotorCoordinator(self.node_id, self.consensus_id, self.participants, self.message_func)
        self.rotor_coordinator.SetEchoesMap(self.get_input_func(self.consensus_id, self.available_node_ids))

        # final if r − r′ > 5|S|/2 + 2.
        maximum_round_number = (5 * participants_number) / 2 + 2 + self.consensus_id
        while self.get_current_round_func() <= maximum_round_number:
            if self.input_value is not None:
                self.message_func(Message(MessageType.INPUT, self.input_value, self.consensus_id))
                self.next_round_func()
            
            if self.ReceivedValueRateChecking(self.get_input_func(self.consensus_id, self.participants), MessageType.INPUT, self.input_value) >= participants_number * 2 / 3:
                self.message_func(Message(MessageType.PREFER, self.input_value, self.consensus_id))
            else:
                self.message_func(Message(MessageType.NOPREFERENCE, None, self.consensus_id))
            self.next_round_func()

            current_dic = self.GetDictionary(self.get_input_func(self.consensus_id, self.participants), MessageType.PREFER)
            most_prefered_value = -1
            most_prefered_count = -1
            if len(current_dic) > 0:
                most_prefered_value = max(current_dic, key = current_dic.get)
                most_prefered_count = current_dic[most_prefered_value]
            if most_prefered_count >= participants_number / 3:
                self.input_value = most_prefered_value
            if most_prefered_count >= participants_number * 2 / 3:
                self.message_func(Message(MessageType.STRONGPREFER, self.input_value, self.consensus_id))
            else:
                self.message_func(Message(MessageType.NOSTRONGPREFERENCE, None, self.consensus_id))
            self.rotor_coordinator.RunOneRound(self.input_value, self.get_current_round_func())
            self.next_round_func()
            
            current_input = self.get_input_func(self.consensus_id, self.participants)
            if self.ReceivedValueRateChecking(current_input, MessageType.STRONGPREFER, self.input_value) < participants_number / 3:
                self.input_value = self.GetOpinion(current_input)

            current_dic = self.GetDictionary(current_input, MessageType.STRONGPREFER)
            if len(current_dic) > 0:
                most_prefered_value = max(current_dic, key = current_dic.get)
                most_prefered_count = current_dic[most_prefered_value]
            if most_prefered_count >= participants_number * 2 / 3:
                self.set_output_func(most_prefered_value, self.consensus_id)
                return