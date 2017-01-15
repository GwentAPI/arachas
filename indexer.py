#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os.path
import json
import ctypes
import time

FILE_ATTRIBUTE_HIDDEN = 0x02

class Indexer:
    def __init__(self, cardList):
        indexMap = {value['key']: key for (key, value) in enumerate(cardList)}
        self.indexMap = indexMap

    def createIndex(self):
        filepath = os.path.join('./' + ".card_index")
        with open(filepath, "w", encoding="utf-8-sig", newline="\n") as f:
            json.dump(self.indexMap, f, sort_keys=True, indent=2, separators=(',', ': '))

        # Indexer.make_hidden_file(filepath) #  Unresolved Permission error on overwriting hidden file.

    # https://stackoverflow.com/questions/25432139/python-cross-platform-hidden-file
    @staticmethod
    def make_hidden_file(file_name):
        # For windows set file attribute.
        if os.name == 'nt':
            ret = ctypes.windll.kernel32.SetFileAttributesW(file_name, FILE_ATTRIBUTE_HIDDEN)
            if not ret:  # There was an error
                raise ctypes.WinError()  # ¯\_(ツ)_/¯
