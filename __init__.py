#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os.path
import json
import time
import queue
import threading
import requests
import mimetypes
import argparse
import re

import unicodedata

import gwentifyHandler as siteHandler
import indexer

args = {}

NAME_REPLACE = {" ": "_", ":": "", "'": "", "`": "", "’": "", "(": "", ")": ""}

# URL where we can begin the crawl.
HOST = 'http://gwentify.com/cards/?view=table'

IMAGE_FOLDER = 'media'

FILE_NAME = 'latest.json'

DOWNLOAD_ARTWORK = False

# Timeout for the requests module.
TIMEOUT = 5.0
# Number of threads that the program uses.
THREADS_COUNT = 10

# Queue containing the URL of every pages.
pageQueue = queue.Queue()
# Queue containing the URL of every cards.
cardQueue = queue.Queue()

# Queue containing every cards already processed and ready to be saved.
finalDataQueue = queue.Queue()

imageQueue = queue.Queue()

# Request headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0'
}


def setParser():
    parser = argparse.ArgumentParser(description='This script allows you to crawl different Gwent community website '
                                                 'to parse and save data about the cards.')
    parser.add_argument('-o', '--output', help='Name of the json file that will be saved.', required=False)
    parser.add_argument('-i', '--image', help='Use this argument to download all cards artworks.',
                        action='store_true', required=False)

    global args
    args = parser.parse_args()


# Class responsible for processing the URL of a page and obtaining the URL of every cards on the page.
class ThreadPage(threading.Thread):
    def __init__(self, pageQueue, cardQueue):
        threading.Thread.__init__(self)
        self.pageQueue = pageQueue
        self.cardQueue = cardQueue

    def run(self):
        while True:
            url = self.pageQueue.get()
            res = requests.get(url, headers=HEADERS, timeout=TIMEOUT)

            if res.status_code == 200:
                # Send the html to the siteHandler module for processing.
                # Return a list of URL where every URL is the URL for a card.
                listCards = siteHandler.getCardsUrl(res.content)
                # Add all entry of listCards in the cardQueue.
                list(map(self.cardQueue.put, listCards))
            else:
                print("Error")
            # Notify that we have finished one task.
            self.pageQueue.task_done()


# Class responsible for processing the URL of a card and obtaining all information related to the card.
class CardThread(threading.Thread):
    def __init__(self, cardQueue, finalDataQueue, imageQueue):
        threading.Thread.__init__(self)
        self.cardQueue = cardQueue
        self.finalDataQueue = finalDataQueue
        self.imageQueue = imageQueue

    def run(self):
        while True:
            url = self.cardQueue.get()
            res = requests.get(url, headers=HEADERS, timeout=TIMEOUT)

            if res.status_code == 200:
                # Send the html to the siteHandler module for processing.
                # Return a card.
                cardData = siteHandler.getCardJson(res.content)
                key = getNameKey(cardData['name'])
                cardData['key'] = key
                self.finalDataQueue.put(cardData)
                self.imageQueue.put((cardData['key'], cardData['variations'][0]['art']['fullsizeImageUrl']))

            else:
                print("bad")
            # Notify that we have finished one task.
            self.cardQueue.task_done()


def getNameKey(name):
    # test = unicodedata.normalize('NFD', name).encode('ascii', 'ignore')
    # https://stackoverflow.com/questions/6116978/python-replace-multiple-strings
    name = name.lower()

    rep = dict((re.escape(k), v) for k, v in NAME_REPLACE.items())
    pattern = re.compile("|".join(rep.keys()))
    name = pattern.sub(lambda m: rep[re.escape(m.group(0))], name)

    return name


class ImageThread(threading.Thread):
    def __init__(self, imageQueue):
        threading.Thread.__init__(self)
        self.imageQueue = imageQueue

    def run(self):
        while True:
            name, url = self.imageQueue.get()
            res = requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True)

            if res.status_code == 200:
                content_type = res.headers['content-type']
                extension = mimetypes.guess_extension(content_type)

                filepath = os.path.join('./' + IMAGE_FOLDER + '/' + name + extension)

                with open(filepath, 'wb') as f:
                    for chunk in res:
                        f.write(chunk)
            self.imageQueue.task_done()

# Function to retrieve a list of URL for every pages of cards.
# The url parameter is the entry point of the website where we might extract the information.
def getPages(url):
    listPages = []

    res = requests.get(url, headers=HEADERS, timeout=TIMEOUT)

    if res.status_code == 200:
        # Process the html and return a list of URL for every available pages.
        listPages = siteHandler.getPages(res.content)
        listPages.append(url)
    else:
        print("bad")

    return listPages


# Save a list of cards in a file in the json format.
# filename is the name under which the file will be saved.
# cardList is the list of cards.
# The file is saved in the same path as where the script is ran from.
def saveJson(filename, cardList):
    filepath = os.path.join('./' + filename)
    print("Saving %s cards to: %s" % (len(cardList), filepath))
    with open(filepath, "w", encoding="utf-8-sig", newline="\n") as f:
        json.dump(cardList, f, ensure_ascii=False, sort_keys=True, indent=2, separators=(',', ': '))


def main():

    global DOWNLOAD_ARTWORK

    if args.image:
        DOWNLOAD_ARTWORK = args.image

    imageFilePath = os.path.join('./' + IMAGE_FOLDER)

    if not os.path.exists(imageFilePath):
        os.makedirs(imageFilePath)

    # Start THREADS_COUNT number of thread working on retrieving cards URL from a page URL.
    for i in range(THREADS_COUNT):
        t = ThreadPage(pageQueue, cardQueue)
        t.setDaemon(True)
        t.start()

    # Retrieve the URL of all pages.
    pages = getPages(HOST)

    # Populate the page queue.
    for page in pages:
        pageQueue.put(page)

    # for page in test:
    #    pageQueue.put(page)

    # Start THREADS_COUNT number of thread working on retrieving card data from card URL.
    for i in range(THREADS_COUNT):
        c = CardThread(cardQueue, finalDataQueue, imageQueue)
        c.setDaemon(True)
        c.start()

    if DOWNLOAD_ARTWORK:
        for i in range(THREADS_COUNT):
            it = ImageThread(imageQueue)
            it.setDaemon(True)
            it.start()

    # Blocks until the queue is finished processing.
    pageQueue.join()

    # Blocks until the queue is finished processing.
    cardQueue.join()

    if DOWNLOAD_ARTWORK:
        imageQueue.join()

    cardList = list(finalDataQueue.queue)

    # Sort the cards in the list by the name of the cards in order to get a predictable output.
    # Makes it easier to see difference when using a diff tool.
    cardList = sorted(cardList, key=lambda element: element['name'])

    global FILE_NAME

    if args.output:
        FILE_NAME = args.output

    saveJson(FILE_NAME, cardList)

    indexer.Indexer(cardList)

if __name__ == '__main__':
    setParser()
    print("Starting")
    start = time.time()
    main()
    print("Elapsed Time: %s" % (time.time() - start))
