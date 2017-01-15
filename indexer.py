#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os.path
import json
import ctypes
import time

FILE_ATTRIBUTE_HIDDEN = 0x02
FILE_ATTRIBUTE_NORMAL = 0x80
WINDOWS_FILE_NOT_FOUND_ERRNO = 2


class Indexer:
    def __init__(self, cardList):
        indexMap = {value['key']: key for (key, value) in enumerate(cardList)}
        self.indexMap = indexMap

    def createIndex(self):
        filepath = os.path.join('./' + ".card_index")
        Indexer.make_hidden_file(filepath, False)

        with open(filepath, "w", encoding="utf-8-sig", newline="\n") as f:
            json.dump(self.indexMap, f, sort_keys=True, indent=2, separators=(',', ': '))

        Indexer.make_hidden_file(filepath)

    # https://stackoverflow.com/questions/25432139/python-cross-platform-hidden-file
    @staticmethod
    def make_hidden_file(file_name, hidden=True):
        # For windows set file attribute.
        if os.name == 'nt':
            fileAttribute = FILE_ATTRIBUTE_HIDDEN
            if not hidden:
                fileAttribute = FILE_ATTRIBUTE_NORMAL

            ret = ctypes.windll.kernel32.SetFileAttributesW(file_name, fileAttribute)
            if not ret:  # There was an error
                if ctypes.WinError().errno == WINDOWS_FILE_NOT_FOUND_ERRNO:
                    pass
                else:
                    raise ctypes.WinError()  # ¯\_(ツ)_/¯
