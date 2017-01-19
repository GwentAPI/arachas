#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os.path
import json
import ctypes
import pytz
from datetime import datetime
from DictDiffer import DictDiffer as differ
from termcolor import colored

# Windows attribute for a hidden and normal file.
FILE_ATTRIBUTE_HIDDEN = 0x02
FILE_ATTRIBUTE_NORMAL = 0x80
WINDOWS_FILE_NOT_FOUND_ERRNO = 2


# s
class Indexer:
    # Default name for the index. Start with dot for making it hidden on linux.
    FILE_NAME = ".card_index"

    # Takes as a parameter a list of cards.
    def __init__(self, cardList):

        # The data format of the index is just the key value of the card.
        # We put True as a value but we only care if the key exist or not.
        indexCards = {value['key']: True for value in cardList}

        # The new index made up from the fresh data.
        currentIndexMap = {}
        currentIndexMap['cards'] = indexCards
        # We use pytz to make our datetime in UTC time.
        currentIndexMap['createdOn'] = str(datetime.now(pytz.utc))
        currentIndexMap['count'] = len(cardList)
        self.currentIndexMap = currentIndexMap

        # We try to load a previously saved index file.
        try:
            print("Loading the index...")
            self.savedIndex = self.loadIndex()
            # We verify the index. The method will print a summary and return true if there is any change.
            needReIndex = self.verifyIndex()

            if needReIndex:
                # Recreate a new index file.
                self.createIndex()
        except FileNotFoundError:
            print("Index not found.")
            print("Creating new index...")

            # Create a new index file.
            self.createIndex()
            self.savedIndex = self.currentIndexMap

    # Use the currentIndexMap and save it as a json encoded file.
    # The file is hidden.
    def createIndex(self):
        filepath = os.path.join('./' + self.FILE_NAME)
        # If the file already exist, this will remove the hidden attribute on Windows.
        # There was a permission related bug where an hidden file couldn't be overwritten.
        # No clue why the problem was happening or how to fix it, but
        # removing the hidden attribute is a good workaround.
        Indexer.make_hidden_file(filepath, False)

        with open(filepath, "w", encoding="utf-8-sig", newline="\n") as f:
            json.dump(self.currentIndexMap, f, ensure_ascii=False, sort_keys=True, indent=2, separators=(',', ': '))

        # Set the hidden attribute on the file on Windows.
        Indexer.make_hidden_file(filepath)

    # https://stackoverflow.com/questions/25432139/python-cross-platform-hidden-file
    # The static method takes the path for a file and set the hidden attribute.
    # By default the file will be made hidden. Set hidden=False to make it visible again.
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

    # Load a previously saved index file.
    def loadIndex(self):
        filepath = os.path.join('./' + self.FILE_NAME)
        with open(filepath, 'r', encoding="utf-8-sig", newline="\n") as f:
            return json.load(f)

    # Verify the saved index against the fresh data.
    # Return true if the saved index needs to be refreshed, otherwise false.
    # Will print a summary of deleted/added cards.
    def verifyIndex(self):
        needReIndex = False
        message = "SUMMARY OF CHANGES"

        # Object used to calculate the difference between the two dict.
        # We only pass the "cards" key because it contain all the cards and we are not interested in the card
        # counts or the createdOn key.
        diff = differ(self.currentIndexMap['cards'], self.savedIndex['cards'])
        # Set of keys that were added.
        added = diff.added()
        # Set of keys that were removed.
        removed = diff.removed()

        # Print an header.
        print("=".center(80, "="))
        print('\n'.join('{:^80}'.format(s) for s in message.split('\n')))
        print("=".center(80, "="))

        if len(added) > 0:
            needReIndex = True

            print()
            print("The following cards were added: \n")
            for card in added:
                print(colored(card, "green"))
            print()

        if len(removed) > 0:
            needReIndex = True

            print()
            print("The following cards were removed: \n")
            for card in removed:
                print(colored(card, "red"))
            print()

        if len(removed) > 0 and len(added) > 0:
            print(colored("WARNING: ", "yellow"))
            print("It's possible one of the card(s) was renamed.\n")

        print("=".center(80, "="))
        print()

        return needReIndex
        # Todo: prompt action if something changed.
        # Todo: Write a machine friendly log that could be used to automate.
