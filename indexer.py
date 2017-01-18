#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os.path
import json
import ctypes
import pytz
from datetime import datetime
from DictDiffer import DictDiffer as differ
from termcolor import colored

FILE_ATTRIBUTE_HIDDEN = 0x02
FILE_ATTRIBUTE_NORMAL = 0x80
WINDOWS_FILE_NOT_FOUND_ERRNO = 2


class Indexer:
    FILE_NAME = ".card_index"

    def __init__(self, cardList):
        indexCards = {value['key']: True for value in cardList}
        currentIndexMap = {}
        currentIndexMap['cards'] = indexCards
        currentIndexMap['createdOn'] = str(datetime.now(pytz.utc))
        currentIndexMap['count'] = len(cardList)
        self.currentIndexMap = currentIndexMap
        try:
            print("Loading the index...")
            self.savedIndex = self.loadIndex()
            self.verifyIndex()
        except FileNotFoundError:
            print("Index not found.")
            print("Creating new index...")
            self.createIndex()
            self.savedIndex = self.currentIndexMap

    def createIndex(self):
        filepath = os.path.join('./' + self.FILE_NAME)
        Indexer.make_hidden_file(filepath, False)

        with open(filepath, "w", encoding="utf-8-sig", newline="\n") as f:
            f.write("")
            json.dump(self.currentIndexMap, f, ensure_ascii=False, sort_keys=True, indent=2, separators=(',', ': '))

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

    def loadIndex(self):
        filepath = os.path.join('./' + self.FILE_NAME)
        with open(filepath, 'r', encoding="utf-8-sig", newline="\n") as f:
            return json.load(f)

    def verifyIndex(self):
        diff = differ(self.currentIndexMap['cards'], self.savedIndex['cards'])
        added = diff.added()
        removed = diff.removed()

        if len(added) > 0:
            print(colored("The following cards were added: ", "yellow"))
            print(added)
        if len(removed) > 0:
            print(colored("The following cards were removed: ", "yellow"))
            print(removed)

        # Todo: prompt action if something changed.
        # Todo: Write a machine friendly log that could be used to automate.
