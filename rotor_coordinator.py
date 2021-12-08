from message import Message, MessageType

class RotorCoordinator:
    def __init__(self, node_id, consensus_id, participants, message_func):
        self.selected_coordinators = []
        self.candidate_coordinators = []
        self.previous_round_p = None
        self.node_id = node_id
        self.consensus_id = consensus_id
        self.participants = participants
        self.number_of_paritipants = len(participants)
        self.message_func = message_func
        self.echoes_map = {}

    def SetEchoesMap(self, input_messages):
        self.echoes_map = {}
        for message in input_messages:
            if message.type == MessageType.ECHO:
                if message.value.sender in self.echoes_map:
                    self.echoes_map[message.value.sender] = self.echoes_map[message.value.sender] + 1
                else:
                    self.echoes_map[message.value.sender] = 1

    def RunOneRound(self, nodeInputValue, currentRound):
        for node_id, number_of_echo in self.echoes_map.items(): 
            if number_of_echo >= self.number_of_paritipants / 3 and node_id not in self.candidate_coordinators:
                self.message_func(Message(MessageType.ECHO, Message(MessageType.INIT, sender=node_id, consensus_id=self.consensus_id), self.consensus_id))
            if number_of_echo >= self.number_of_paritipants * 2 / 3 and node_id not in self.candidate_coordinators:
                self.candidate_coordinators.append(node_id)
        self.candidate_coordinators.sort()
        if not self.candidate_coordinators:
            return
        p = self.candidate_coordinators[currentRound % len(self.candidate_coordinators)]
        if p in self.selected_coordinators:
            return
        self.selected_coordinators.append(p)
        if self.node_id == p:
            self.message_func(Message(MessageType.OPINION, nodeInputValue, self.consensus_id))
        self.previous_round_p = p