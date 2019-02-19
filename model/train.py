import os
import sys
import argparse

sys.path.append('model/robosat-pink/')

from robosat_pink.tools.train import main

def add_parser(subparser):
    parser = subparser.add_parser(
        "train", help="trains a model on a dataset", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--config", type=str, required=True, help="path to configuration file")
    parser.add_argument("--checkpoint", type=str, required=False, help="path to a model checkpoint (to retrain)")
    parser.add_argument("--resume", action="store_true", help="resume training (imply to provide a checkpoint)")
    parser.add_argument("--workers", type=int, default=0, help="number of workers pre-processing images")
    parser.add_argument("--dataset", type=str, help="if set, override dataset path value from config file")
    parser.add_argument("--epochs", type=int, help="if set, override epochs value from config file")
    parser.add_argument("--batch_size", type=int, help="if set, override batch_size value from config file")
    parser.add_argument("--lr", type=float, help="if set, override learning rate value from config file")
    parser.add_argument("out", type=str, help="directory to save checkpoint .pth files and log")

    # calls to robosat_pink.tools.train.main
    parser.set_defaults(func=main)
