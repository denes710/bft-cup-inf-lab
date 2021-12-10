import copy
import json

from constants import *

class Node(object):
    def __init__(self, node_id, normal_node, is_byzantine_commander = False):
        self.node_id = node_id
        if normal_node:
            self.str_node_id = str(self.node_id)
        elif is_byzantine_commander:
            self.str_node_id = "{} (byz com)".format(str(self.node_id))
        else:
            self.str_node_id = "{} (byz)".format(str(self.node_id))
        self.states = {}
    
    def GetRowInfoList(self, round_number):
        st = self.states[round_number]
        current_value = str(st.current_value) if not st.output else "Out: {}".format(str(st.output))
        sent_messages = [json.dumps(message) for message in st.sent_messages]
        only_received = [json.dumps(message) for message in st.only_received_messages]
        str_participants = [str(item) for item in st.participants]
        str_candidates = [str(item) for item in st.candidates]
        str_selected_candidates = [str(item) for item in st.selected_candidates]
        return [self.str_node_id, current_value, ",".join(str_participants), ",".join(str_candidates), \
            ",".join(str_selected_candidates), "\n".join(sent_messages), "\n".join(only_received)]

class State(object):
    def __init__(self, participants = [], candidates = [], selected_candidates = [], current_value = None, output = None):
        self.participants = participants
        self.candidates = candidates
        self.selected_candidates = selected_candidates
        self.current_value = current_value
        self.sent_messages = []
        self.only_received_messages = []
        self.output = output

class DataHandler(object):
    def __init__(self, filename):
        file = open(filename)
        self.json_data = json.load(file)
        self.nodes = {}
        self.messages = {}
        self.consensus_id = self.json_data[CONSENSUS_ID_TAG]
        self.last_round = -1
        self.number_of_nodes = 0
        self.Init()

    def InitNodes(self, not_byzantines):
        for node in self.json_data[ROUNDS_TAG][1][ROUND_INFO_TAG]:
            self.nodes[node[NODE_ID_TAG]] = Node(node[NODE_ID_TAG], True if node[NODE_ID_TAG] in not_byzantines else False)
            self.number_of_nodes += 1
        for node_states in self.json_data[ROUNDS_TAG]:
            self.last_round = node_states[ROUND_TAG]
            for node_state in node_states[ROUND_INFO_TAG]:
                self.nodes[node_state[NODE_ID_TAG]].states[node_states[ROUND_TAG]] = \
                    State(node_state[PARTICIPANTS_TAG], node_state[CANDIDATES_TAG], node_state[SELECTED_CANDIDATES_TAG], node_state[CURRENT_VALUE_TAG])

    def SetOutputChains(self):
        for output in self.json_data[OUTPUT_CHAINS_TAG]:
            if output[NODE_ID_TAG] in self.nodes:
                if output[ROUND_TAG] in self.nodes[output[NODE_ID_TAG]].states:
                    self.nodes[output[NODE_ID_TAG]].states[output[ROUND_TAG]].output = output[VALUE_TAG]
                else:
                    self.nodes[output[NODE_ID_TAG]].states[output[ROUND_TAG]] = State(output = output[VALUE_TAG])

    def FillMissingNodeStates(self):
        for node in self.nodes.values():
            current_round = self.consensus_id
            if not current_round -1 in node.states:
                node.states[current_round - 1] = State()
            while current_round <= self.last_round:
                if current_round not in node.states:
                    node.states[current_round] = copy.deepcopy(node.states[current_round - 1])
                current_round += 1

    def Init(self):
        not_byzantines = [output[NODE_ID_TAG] for output in self.json_data[OUTPUT_CHAINS_TAG]]
        self.InitCommander(not_byzantines)
        self.InitNodes(not_byzantines)
        self.SetOutputChains()
        self.FillMissingNodeStates()
        self.InitMessages()

    def InitCommander(self, not_byzantines):
        self.number_of_nodes += 1
        if self.json_data[MESSAGES_TAG][0][BROADCASTED_MESSAGES_TAG]:
            message = self.json_data[MESSAGES_TAG][0][BROADCASTED_MESSAGES_TAG][0]
        else:
            message = self.json_data[MESSAGES_TAG][0][SENT_MESSAGES_TAG][0]
        node_id = message[SENDER_ID_TAG]
        self.nodes[node_id] = Node(node_id, True) if node_id in not_byzantines else Node(node_id, False, True)
        self.nodes[node_id].states[self.json_data[MESSAGES_TAG][0][ROUND_TAG] - 1] = State()

    def AddSentMessagesToNodes(self, tag):
        # current message were sent before one round earlier
        for round_messages in self.json_data[MESSAGES_TAG]:
            for message in round_messages[tag]:
                self.nodes[message[SENDER_ID_TAG]].states[round_messages[ROUND_TAG] - 1].sent_messages.append(message)

    def InitMessages(self):
        self.AddSentMessagesToNodes(BROADCASTED_MESSAGES_TAG)
        self.AddSentMessagesToNodes(SENT_MESSAGES_TAG)
        for round_messages in self.json_data[MESSAGES_TAG]:
            self.messages[round_messages[ROUND_TAG]] = []
            for message in round_messages[BROADCASTED_MESSAGES_TAG]:
                self.messages[round_messages[ROUND_TAG]].append(message)
            for message in round_messages[SENT_MESSAGES_TAG]:
                self.nodes[message[RECEIVER_ID_TAG]].states[round_messages[ROUND_TAG]].only_received_messages.append(message)

    def GetTableData(self, round_num):
        result = []
        for node in self.nodes.values():
            result.append(node.GetRowInfoList(round_num))
        return result

    def GetCurrentMessages(self, round_num):
        if round_num in self.messages:
            return [json.dumps(item) for item in self.messages[round_num]]
        return []
