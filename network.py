import copy
import json
import logging
import time
import threading

from byzantine_node import ByzantineNode, ByzantineType
from constants import *
from node import Node

class Network(object):
    def __init__(self, input_filename):
        self.nodes = []
        file = open(input_filename)
        self.json_data = json.load(file)
        self.input_values = self.GetInputValues()
        self.starting_list = Network.TransformToDic(self.json_data[NODES_TAG], START_ROUND_TAG, NODE_ID_TAG)
        self.exit_list = Network.TransformToDic(self.json_data[NODES_TAG], EXIT_ROUND_TAG, NODE_ID_TAG)
        self.byzantine_nodes = Network.GetByzantineNodes(self.json_data)
        self.current_round = 0
        self.consensus_id_for_json = None
        self.json_output = None
        self.InitFrontendOutputData()

    def GetInputValues(self):
        result = {}
        for value in self.json_data[INPUT_VALUES_TAG]:
            result[value[ROUND_TAG]] = {VALUE_TAG : value[VALUE_TAG], NODE_ID_TAG : value[NODE_ID_TAG]}
        return result
    
    def CreateNewNode(self, node_id, byzantine_info = None):
        logging.debug("Creating node" + str(node_id))
        current_event = threading.Event()
        current_node = Node(node_id, current_event) if byzantine_info is None else ByzantineNode(node_id, current_event, byzantine_info, self.nodes)
        t1 = threading.Thread(name="{} node thread is created".format(node_id), 
                        target=current_node.Run)
        t1.start()
        self.nodes.append(current_node)
        time.sleep(0.3)

    def CreateNewNodes(self):
        if not self.current_round in self.starting_list:
            return    
        for node_id in self.starting_list[self.current_round]:
            if node_id in self.byzantine_nodes:
                self.CreateNewNode(node_id, self.byzantine_nodes[node_id])
            else:
                self.CreateNewNode(node_id)
        del self.starting_list[self.current_round]
  
    @staticmethod
    def GetNodeRole(node):
        if node.IsByzantine():
            return ByzantineType.ToString(node.byzantine_type)
        return "Correct"

    def HasRunningNode(self):
        for node in self.nodes:
            if node.IsRunning():
                return True
        return False

    def TurnOffNodes(self):
        if not self.current_round in self.exit_list:
            return  
        for node_id in self.exit_list[self.current_round]:
            node = next((node for node in self.nodes if node.node_id == node_id), None)
            if node:
                node.SetTurnOff()

    def GetOutputChains(self):
        result = {}
        for node_output_chain in self.json_data[OUTPUT_CHAINS_TAG]:
            result[node_output_chain[NODE_ID_TAG]] = {}
            for output_chain in node_output_chain[CHAIN_TAG]:
                result[node_output_chain[NODE_ID_TAG]][output_chain[CONSENSUS_ID_TAG]] = output_chain[VALUE_TAG]
        return result

    @staticmethod
    def LoggingMessages(broadcasted, sent):
        logging.debug("Broadcasted messages number: {}".format(str(len(broadcasted))))
        for message in broadcasted:
            logging.debug(message.GetJson())

        for receiver, messages in sent.items():
            logging.debug("Only node{} got specific {} messages:".format(str(receiver), str(len(messages))))
            for message in messages:
                logging.debug(message.GetJson())

    @staticmethod
    def GetByzantineNodes(json):
        if BYZANTINE_NODES_TAG not in json:
            return {}
        result = {}
        for byzantine in json[BYZANTINE_NODES_TAG]:
            if byzantine[TYPE_TAG] == 0:
                result[byzantine[NODE_ID_TAG]] = {TYPE_TAG : 0}
            elif byzantine[TYPE_TAG] == 1:
                result[byzantine[NODE_ID_TAG]] = {TYPE_TAG : 1, \
                    INITS_TAG : Network.TransformToDic(byzantine[INITS_TAG], ROUND_TAG, RECEIVER_IDS_TAG, True), \
                        ECHOES_TAG : Network.TransformToDic(byzantine[ECHOES_TAG], ROUND_TAG, None, True), \
                            OWN_VALUE_TAG : byzantine[OWN_VALUE_TAG]}
        return result        

    @staticmethod
    def TransformToDic(json, key_tag, value_tag, is_single_value = False):
        result = {}
        for value in json:
            if is_single_value:
                if value_tag is None:
                    result[value[key_tag]] = value
                else:    
                    result[value[key_tag]] = value[value_tag]
            else:
                if not value[key_tag] in result:
                    result[value[key_tag]] = [value[value_tag]]
                else:
                    result[value[key_tag]].append(value[value_tag])
        return result

    def InitFrontendOutputData(self):
        # dealing with frontend json creation
        if CONSENSUS_ID_JSON_TAG in self.json_data:
            self.json_output = {ROUNDS_TAG : [], MESSAGES_TAG : []}
            self.consensus_id_for_json = self.json_data[CONSENSUS_ID_JSON_TAG]         

    def AddJsonOutputChain(self):
        consensus_id = self.json_data[CONSENSUS_ID_JSON_TAG]
        output_chain = [] # {node_id, round, output}
        for node in self.nodes:
            if not node.IsByzantine() and consensus_id in node.output_chain:
                output_info = copy.deepcopy(node.output_chain[consensus_id])
                output_info[NODE_ID_TAG] = node.node_id
                output_chain.append(output_info)
        self.json_output[OUTPUT_CHAINS_TAG] = output_chain

    def CreateJsonOutput(self):
        if self.json_output is not None:
            self.AddJsonOutputChain()
            with open('output.json', 'w') as outfile:
                self.json_output[CONSENSUS_ID_TAG] = self.json_data[CONSENSUS_ID_JSON_TAG]
                json.dump(self.json_output, outfile, indent=4)

    def CheckExpectedOutputChains(self):
        if OUTPUT_CHAINS_TAG in self.json_data:       
            print("Checking output chains ...")
            passed = True
            expected_output_chains = self.GetOutputChains()
            for node in self.nodes:
                if not node.IsByzantine():
                    output_chain = expected_output_chains[node.node_id]
                    for round, value in node.output_chain.items():
                        if output_chain[round] != value[VALUE_TAG]:
                            passed = False
            print("Passed!") if passed else print("Failed!")
    
    def LogOutputChains(self):
        # writing output chain
        for node in self.nodes:
            logging.info("node{}({}) outputchain: ".format(str(node.node_id), Network.GetNodeRole(node)))
            for round, value in node.output_chain.items():
                logging.info("{} -> {}".format(round, value[VALUE_TAG]))

    def GetCurrentRoundInfo(self):
        current_round_info = []
        for node in self.nodes:
            for consensus in node.consensus_instances:
                if consensus.consensus_id == self.consensus_id_for_json:
                    candidates = []
                    selectedCandidates = []
                    if consensus.rotor_coordinator:
                        candidates = consensus.rotor_coordinator.candidate_coordinators
                        selectedCandidates = consensus.rotor_coordinator.selected_coordinators
                    current_round_info.append({NODE_ID_TAG : node.node_id, CURRENT_VALUE_TAG : copy.deepcopy(consensus.input_value), \
                        PARTICIPANTS_TAG : copy.deepcopy(consensus.participants), CANDIDATES_TAG : copy.deepcopy(candidates), \
                            SELECTED_CANDIDATES_TAG : copy.deepcopy(selectedCandidates)})
                    break
        return current_round_info

    def GetJsonMessagesList(self, messages, consensus_id, is_new_input):
        result = []
        for message in messages:
            if consensus_id and message.IsConsensusMessage(consensus_id):
                result.append(message.GetJson())
            elif is_new_input and message.IsNewInput():
                result.append(message.GetJson())
        return result

    def GetJsonMessagesDic(self, messages, consensus_id, is_new_input):
        result = []
        for list in messages:
            result += self.GetJsonMessagesList(list, consensus_id, is_new_input)
        return result

    def GetJsonConsensusMessages(self, broadcasted_messages, sent_messages, consensus_id = None, is_new_input = False):
        return {ROUND_TAG : self.current_round, \
                BROADCASTED_MESSAGES_TAG : self.GetJsonMessagesList(broadcasted_messages, consensus_id, is_new_input), \
                    SENT_MESSAGES_TAG : self.GetJsonMessagesDic(sent_messages.values(), consensus_id, is_new_input)}

    def CreateCurrentRoundJson(self, broadcasted_messages, sent_messages):
        if self.consensus_id_for_json is not None and self.current_round  == self.consensus_id_for_json:
            self.json_output[ROUNDS_TAG].append({ROUND_TAG : self.current_round - 1, ROUND_INFO_TAG : []})
            # messages are sent in the given round
            self.json_output[MESSAGES_TAG].append(self.GetJsonConsensusMessages(broadcasted_messages, sent_messages, is_new_input=True))

        if self.consensus_id_for_json is not None and self.current_round  > self.consensus_id_for_json:
            # the current state is the prev round state
            self.json_output[ROUNDS_TAG].append({ROUND_TAG : self.current_round - 1, ROUND_INFO_TAG : self.GetCurrentRoundInfo()})
            # messages are sent in the given round
            self.json_output[MESSAGES_TAG].append(self.GetJsonConsensusMessages(broadcasted_messages, sent_messages, self.consensus_id_for_json))
            still_running = False
            for node in self.nodes:
                if not node.IsByzantine() and self.consensus_id_for_json not in node.output_chain:
                    still_running = True            
            if not still_running:
                self.consensus_id_for_json = None

    def RunARound(self, current_broadcasted_messages, current_sent_messages):
        for node in self.nodes:
            node_messages = copy.copy(current_broadcasted_messages)
            if node.node_id in current_sent_messages:
                for message in current_sent_messages[node.node_id]:
                    node_messages.append(message)
            node.SetInputMessages(node_messages)
            node.round_number += 1
            node.network_event.set()
        time.sleep(0.3)

    def Run(self):
        self.CreateNewNodes()
        while self.HasRunningNode():
            print("round {}".format(str(self.current_round)))
            logging.info("Current round {}".format(str(self.current_round)))
            self.CreateNewNodes()
            self.TurnOffNodes()
            logging.debug("Current nodes array size: {}".format((len(self.nodes))))
            current_broadcasted_messages = []
            # {receiver : sent_messages_for_receiver}
            current_sent_messages = {}
            for node in self.nodes:
                # dealing with broadcast messages from a node
                for message in node.broadcast_messages:
                    current_broadcasted_messages.append(message)
                node.broadcast_messages.clear()
                # dealing with messages sent for only one node
                for message in node.sending_messages:
                    if message.receiver in current_sent_messages:
                        current_sent_messages[message.receiver].append(message)
                    else:
                        current_sent_messages[message.receiver] = [message]
                node.sending_messages.clear()
                # set input value if there is one for this round
                if self.current_round in self.input_values and node.is_running:
                    if node.node_id == self.input_values[self.current_round][NODE_ID_TAG]:
                        node.input_value = self.input_values[self.current_round][VALUE_TAG]
            self.LoggingMessages(current_broadcasted_messages, current_sent_messages)
            # create output for frontend
            self.CreateCurrentRoundJson(current_broadcasted_messages, current_sent_messages)
            self.current_round += 1
            self.RunARound(current_broadcasted_messages, current_sent_messages)
        self.LogOutputChains()
        self.CheckExpectedOutputChains()
        self.CreateJsonOutput()