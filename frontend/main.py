import argparse
import sys

from consensus_visualizer import ConsensusVisualizer
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Program args")
    parser.add_argument("--input-file", dest="input_file", type=str, help="Json input file", required=True)
    args = parser.parse_args()
    app = QApplication(sys.argv)
    ex = ConsensusVisualizer(args.input_file)
    sys.exit(app.exec_())  