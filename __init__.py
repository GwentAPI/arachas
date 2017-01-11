#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os.path
import json
import time
import queue
import threading
import requests
import codecs

import gwentifyHandler as siteHandler

HOST = 'http://gwentify.com/cards/?view=table'

test = ["http://gwentify.com/cards/page/4/?view=table"]
TIMEOUT = 5.0
THREADS_COUNT = 10

pageQueue = queue.Queue()
cardQueue = queue.Queue()
finalDataQueue = queue.Queue()

HEADERS = {
    'User-Agent': 'Mozilla/5.0'
}

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
                listCards = siteHandler.getCardsUrl(res.text)
                list(map(self.cardQueue.put, listCards))
            else:
                print("Error")
            self.pageQueue.task_done()


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
                cardData = siteHandler.getCardJson(res.text)
                self.finalDataQueue.put(cardData)
            else:
                print("bad")
            self.cardQueue.task_done()


def getPages(url):
    listPages = []

    res = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    res.encoding = 'UTF-8'

    if res.status_code == 200:
        listPages = siteHandler.getPages(res.text)
        listPages.append(url)
    else:
        print("bad")

    return listPages


def saveJson(filename, cardList):
    filepath = os.path.join('./' + filename)
    print("Saving %s cards to: %s" % (len(cardList), filepath))
    with open(filepath, "w", encoding="utf-8-sig", newline="\n") as f:
        json.dump(cardList, f, sort_keys=True, indent=2, separators=(',', ': '))


def main():
    for i in range(THREADS_COUNT):
        t = ThreadPage(pageQueue, cardQueue)
        t.setDaemon(True)
        t.start()

    pages = getPages(HOST)

    for page in pages:
        pageQueue.put(page)

    # for page in test:
    #    pageQueue.put(page)

    for i in range(THREADS_COUNT):
        c = CardThread(cardQueue, finalDataQueue)
        c.setDaemon(True)
        c.start()

    pageQueue.join()

    cardQueue.join()

    cardList = list(finalDataQueue.queue)

    cardList = sorted(cardList, key=lambda element: element['name'])

    saveJson("latest.json", cardList)


if __name__ == '__main__':
    print("Starting")
    start = time.time()
    main()
    print("Elapsed Time: %s" % (time.time() - start))