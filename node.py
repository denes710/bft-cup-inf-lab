import copy
import logging
import threading

from consensus import Consensus
from constants import *
from message import Message, MessageType

class Node:
    def __init__(self, node_id, network_event, is_byzantine = False):
        self.node_id = node_id
        self.network_event = network_event
        self.is_byzantine = is_byzantine
        self.input_value= None
        self.turnOff = False
        self.turn_offed = False
        self.is_running = False
        self.round_number = 0
        self.broadcast_messages = []
        self.sending_messages = []
        self.input_messages = []
        self.unprocessed_system_messages = []
        self.consensus_threads = []
        self.consensus_instances = []
        self.available_node_ids = [self.node_id]
        self.output_chain = {}
        self.state_lock = threading.RLock()
        self.sending_lock = threading.Lock()
        logging.info("Node{} creation is done!".format(str(self.node_id)))

    def IsByzantine(self):
        return False

    def HasConsensusInstance(self):
        with self.state_lock:
            return len(self.consensus_threads) > 0

    def DeleteFinishedConsensusInstances(self):
        with self.state_lock:
            self.consensus_threads = [thread for thread in self.consensus_threads if thread.is_alive()]
            self.consensus_instances = [consensus for consensus in self.consensus_instances if consensus.consensus_id not in self.output_chain]

    def IsRunning(self):
        with self.state_lock:
            self.DeleteFinishedConsensusInstances()
            return not self.turn_offed or self.HasConsensusInstance()

    def SetInputMessages(self, currentRoundinput_messages):
        self.input_messages.clear()
        self.input_messages = copy.copy(currentRoundinput_messages)
        for message in self.input_messages:
            if message.IsSystem():
                self.unprocessed_system_messages.append(message)

    def SetTurnOff(self):
        with self.state_lock:
            self.turnOff = True

    def GetTurnOff(self):
        with self.state_lock:
            return self.turnOff

    def GetNewInputMessage(self):
        for message in self.input_messages:
            if message.type == MessageType.NEWINPUT:
                return message
        return None

    def AddMessage(self, message):
        with self.sending_lock:
            message.sender = self.node_id
            if message.IsBroadcastMessage():
                self.broadcast_messages.append(message)
            else:
                self.sending_messages.append(message)

    def NextRound(self):
        self.network_event.clear()
        self.network_event.wait()

    def Init(self):
        round_numbers = {}
        for message in self.input_messages:
            if message.type == MessageType.ACK:
                self.available_node_ids.append(message.sender)
                if message.value in round_numbers:
                    round_numbers[message.value] = round_numbers[message.value] + 1
                else:
                    round_numbers[message.value] = 1
        if round_numbers:
            self.round_number = max(round_numbers, key = round_numbers.get) + 1
        else:
            self.round_number = 1
        return len(round_numbers) > 0

    def CheckNewNodes(self):
        result = False
        for message in self.unprocessed_system_messages:
            if message.type == MessageType.PRESENT and message.sender not in self.available_node_ids:
                result = True
                self.available_node_ids.append(message.sender)
                self.AddMessage(Message(MessageType.ACK, self.round_number, None, self.node_id, message.sender))
        self.unprocessed_system_messages = [x for x in self.unprocessed_system_messages if x.type != MessageType.PRESENT]
        return result

    def CheckLeavingNodes(self):
        for message in self.input_messages:
            if message.type == MessageType.ABSENT:
                self.available_node_ids.remove(message.sender)
        self.unprocessed_system_messages = [x for x in self.unprocessed_system_messages if x.type != MessageType.ABSENT]

    def GetInputForInstance(self, consensus_id, availableNodesInConsensus):
        result = []
        for message in self.input_messages:
            if message.sender in availableNodesInConsensus and message.consensus_id == consensus_id:
                result.append(message)
        return result

    def GetCurrentRoundNumber(self):
        return self.round_number
    
    def SetOutputValue(self, output_value, consensus_id):
        with self.state_lock:
            self.output_chain[consensus_id] = self.CreateOutputResult(output_value)

    def CreateOutputResult(self, output_value):
        return {VALUE_TAG : output_value, ROUND_TAG : self.round_number}

    def GetConsensus(self, consensus_id, input_value, add_message_func, nextround_func, get_input_func,
    get_current_round_number_func, set_output_value_func):
        return Consensus(self.node_id, self.available_node_ids, consensus_id, input_value, add_message_func, nextround_func, \
            get_input_func, get_current_round_number_func, set_output_value_func)

    def CreateNewConsensusInstances(self, new_input_message):
        input_value = new_input_message.value
        logging.info("New consensus is created in node{} with input:{} and consensus id:{}".format(str(self.node_id), str(input_value), str(self.round_number)))
        add_message_func = self.AddMessage
        nextround_func = self.NextRound
        get_input_func = self.GetInputForInstance
        get_current_round_number_func = self.GetCurrentRoundNumber
        set_output_value_func = self.SetOutputValue

        consensus = self.GetConsensus(self.round_number, input_value, add_message_func, nextround_func, get_input_func, \
            get_current_round_number_func, set_output_value_func)
        self.consensus_instances.append(consensus)
        thread = threading.Thread(name="{} node {} consensus".format(self.node_id, self.round_number), 
                        target=consensus.Run)
        self.consensus_threads.append(thread)
        thread.start()

    def Registration(self):
        self.AddMessage(Message(MessageType.PRESENT, self.node_id))
        self.NextRound()
        return self.Init()

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
            self.DeleteFinishedConsensusInstances()
            if self.input_value is not None:
                self.AddMessage(Message(MessageType.NEWINPUT, self.input_value))
                self.output_chain[self.round_number + 1] = self.CreateOutputResult(self.input_value)
                self.input_value = None
                self.NextRound()
            self.NextRound()
            new_input_message = self.GetNewInputMessage()
            if new_input_message:
                self.CreateNewConsensusInstances(new_input_message)
                self.NextRound()
        logging.info("{} node is turned off, no consensus instances are running!".format(self.node_id))