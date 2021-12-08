from data_handler import DataHandler
from PyQt5.QtWidgets import *

class ConsensusVisualizer(QMainWindow):
    def __init__(self, filename):
        super().__init__()
        self.data_handler = DataHandler(filename)
        self.title = "Consensus {}".format(self.data_handler.consensus_id)
        self.headers = ["Id", "Value", "Participants", "Candidates", "Selected candidates", "Sent messages", "Only received messages"]
        self.left = 0
        self.top = 0
        self.current_num = self.data_handler.consensus_id - 1
        self.table_data = self.data_handler.GetTableData(self.current_num)
        self.InitUI()
        self.show()

    def SetCurrentMessages(self):
        current_messages = self.data_handler.GetCurrentMessages(self.current_num)
        self.messages_box.setRowCount(len(current_messages))
        for i in range(len(current_messages)):
            self.messages_box.setItem(i, 0, QTableWidgetItem(current_messages[i]))
        self.messages_box.resizeColumnsToContents()
        self.messages_box.resizeRowsToContents()

    def InitUI(self):
        self.setWindowTitle(self.title)
        self.resize(2000, 1500)
        # divide window into two parts
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.w1 = QWidget()
        self.w2 = QWidget()
        lay = QGridLayout(central_widget)
        for w, (r, c) in zip((self.w1, self.w2), ((0, 0), (1, 0))):
            lay.addWidget(w, r, c)
        for r in range(2):
            lay.setRowStretch(r, 1)
        # upper part
        lay = QVBoxLayout(self.w1)
        self.CreateTable()
        lay.addWidget(self.table_widget)
        # lower part
        lay = QVBoxLayout(self.w2)
        self.CreateMessageBox(lay)
        self.counter_label = QLabel()
        self.counter_label.setText("Current round: {}".format(self.current_num))
        lay.addWidget(self.counter_label)
        self.CreateButton(lay, "Prev", self.PrevClicked)
        self.CreateButton(lay, "Next", self.NextClicked)

    def CreateMessageBox(self, lay):
        self.messages_box = QTableWidget()
        self.messages_box.setColumnCount(1)
        self.messages_box.setHorizontalHeaderLabels(["Current broadcasted messages:"])
        self.messages_box.verticalHeader().setVisible(False)
        self.messages_box.resize(800, 1500)
        self.SetCurrentMessages()
        lay.addWidget(self.messages_box)

    def CreateButton(self, lay, label, event):
        button = QPushButton()
        button.setText(label)
        button.clicked.connect(event)
        lay.addWidget(button)        

    def SetTable(self):
        self.table_data = self.data_handler.GetTableData(self.current_num)
        self.UpdateTable()
        self.counter_label.setText("Current round: {}".format(self.current_num))
        self.SetCurrentMessages()

    def PrevClicked(self):
        if self.current_num - 1 < self.data_handler.consensus_id - 1:
            return
        self.current_num -= 1
        self.SetTable()

    def NextClicked(self):
        if self.current_num + 1 > self.data_handler.last_round:
            return
        self.current_num += 1
        self.SetTable()

    def UpdateTable(self):
        for i in range(0, len(self.table_data)):
            for j in range(0, len(self.headers)):
                self.table_widget.setItem(i, j, QTableWidgetItem(self.table_data[i][j]))
        self.table_widget.resizeColumnsToContents()
        self.table_widget.resizeRowsToContents()

    def CreateTable(self):
        self.table_widget = QTableWidget()
        self.table_widget.setRowCount(self.data_handler.number_of_nodes)
        self.table_widget.setColumnCount(len(self.headers))
        self.table_widget.setHorizontalHeaderLabels(self.headers)
        self.table_widget.verticalHeader().setVisible(False)
        self.UpdateTable()
