import argparse
import logging

from datetime import datetime, date
from network import Network

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Program args")
    parser.add_argument("--input-file", dest="input_filename", type=str, help="Json input file")
    parser.add_argument("--no-logging", dest="no_logging", action="store_true", help="Turn off loggin")
    args = parser.parse_args()
    if not args.no_logging:
        log_name = "{}-{}".format(date.today().strftime("%Y-%m-%d"),datetime.now().strftime("%H.%M.%S"))
        logging.basicConfig(format='Date-Time : %(asctime)s : Line No. : %(lineno)d : %(message)s', \
            level = logging.DEBUG, filename = '{}.log'.format(log_name))

    network = Network(args.input_filename)
    network.Run()
    print("All nodes are turned off!")