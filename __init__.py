#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os.path
import json
import time
import queue
import threading
import requests

import gwentifyHandler as siteHandler

# URL where we can begin the crawl.
HOST = 'http://gwentify.com/cards/?view=table'

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

# Request headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0'
}


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
            res.encoding = 'UTF-8'

            if res.status_code == 200:
                # Send the html to the siteHandler module for processing.
                # Return a list of URL where every URL is the URL for a card.
                listCards = siteHandler.getCardsUrl(res.text)
                # Add all entry of listCards in the cardQueue.
                list(map(self.cardQueue.put, listCards))
            else:
                print("Error")
            # Notify that we have finished one task.
            self.pageQueue.task_done()


# Class responsible for processing the URL of a card and obtaining all information related to the card.
class CardThread(threading.Thread):
    def __init__(self, cardQueue, finalDataQueue):
        threading.Thread.__init__(self)
        self.cardQueue = cardQueue
        self.finalDataQueue = finalDataQueue

    def run(self):
        while True:
            url = self.cardQueue.get()
            res = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            res.encoding = 'UTF-8'

            if res.status_code == 200:
                # Send the html to the siteHandler module for processing.
                # Return a card.
                cardData = siteHandler.getCardJson(res.text)
                self.finalDataQueue.put(cardData)
            else:
                print("bad")
            # Notify that we have finished one task.
            self.cardQueue.task_done()


# Function to retrieve a list of URL for every pages of cards.
# The url parameter is the entry point of the website where we might extract the information.
def getPages(url):
    listPages = []

    res = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    res.encoding = 'UTF-8'

    if res.status_code == 200:
        # Process the html and return a list of URL for every available pages.
        listPages = siteHandler.getPages(res.text)
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
        json.dump(cardList, f, sort_keys=True, indent=2, separators=(',', ': '))


def main():
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
        c = CardThread(cardQueue, finalDataQueue)
        c.setDaemon(True)
        c.start()

    # Blocks until the queue is finished processing.
    pageQueue.join()

    # Blocks until the queue is finished processing.
    cardQueue.join()

    cardList = list(finalDataQueue.queue)

    # Sort the cards in the list by the name of the cards in order to get a predictable output.
    # Makes it easier to see difference when using a diff tool.
    cardList = sorted(cardList, key=lambda element: element['name'])

    saveJson("latest.json", cardList)


if __name__ == '__main__':
    print("Starting")
    start = time.time()
    main()
    print("Elapsed Time: %s" % (time.time() - start))