#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re

from bs4 import BeautifulSoup

# 200/800
costRegex = re.compile("^([0-9]+)/([0-9]+)")

pageRegex = re.compile("^(http://gwentify.com[a-z/=?&]+)([1-9]+)([a-z/=?&]+)$")

def getCardsUrl(html):
    listCards = []

    soup = BeautifulSoup(html, 'html.parser')
    tableRows = soup.find('table').find_all('tr')

    for row in tableRows:
        cardUrl = row.td.a.get('href')
        listCards.append(cardUrl)

    return listCards


def getPages(html):
    listPages = []

    soup = BeautifulSoup(html, 'html.parser')
    lastPage = soup.select("li > a.last")[0].get('href')

    match = pageRegex.findall(lastPage)

    if match and len(match[0]) == 3:
        totalNumPage = int(match[0][1])
        for i in range(2, totalNumPage + 1):
            link = match[0][0] + str(i) + match[0][2]
            listPages.append(link)
    else:
        raise NotImplementedError("Page formatting unsupported. Unable to crawl the pages.")

    return listPages


def getCardJson(html):
    dataMap = {}

    soup = BeautifulSoup(html, 'html.parser')
    cardArticle = soup.find('div', id='primary').article

    name = cardArticle.find('h1').get_text()
    imageUrl = cardArticle.find('div', class_="card-img").a.get('href')
    content = cardArticle.find('div', class_="entry-content")

    dataMap["name"] = name.strip()
    dataMap["imageUrl"] = imageUrl.strip()

    for data in content.select('ul.card-cats > li'):
        attribute = data.strong.get_text().strip()

        if attribute == "Group:":
            dataMap["type:"] = data.a.get_text().strip()
        if attribute == "Rarity:":
            dataMap["rarity:"] = data.a.get_text().strip()
        if attribute == "Faction:":
            dataMap["faction:"] = data.a.get_text().strip()
        if attribute == "Strength:":
            dataMap["strength:"] = data.strong.next_sibling.strip()

        if attribute == "Loyalty:":
            dataMap["loyalty"] = list()
            for loyalty in data.find_all('a'):
                dataMap["loyalty"].append(loyalty.get_text().strip())

        if attribute == "Type:":
            dataMap["category"] = list()
            for category in data.find_all('a'):
                dataMap["category"].append(category.get_text().strip())

        if attribute == "Craft:":
            dataMap["craft"] = {}
            dataMap["craft"]["normal"] = -1
            dataMap["craft"]["premium"] = -1

            match = costRegex.findall(data.strong.next_sibling.strip())
            if match and len(match[0]) == 2:
                dataMap["craft"]["normal"] = match[0][0]
                dataMap["craft"]["premium"] = match[0][1]

        if attribute == "Mill:":
            dataMap["mill"] = {}
            dataMap["mill"]["normal"] = -1
            dataMap["mill"]["premium"] = -1

            match = costRegex.findall(data.strong.next_sibling.strip())
            if match and len(match[0]) == 2:
                dataMap["mill"]["normal"] = match[0][0]
                dataMap["mill"]["premium"] = match[0][1]

        if attribute == "Position:":
            dataMap["lane"] = list()
            lane = data.a.get_text().strip()

            if lane == "Multiple":
                # Danger, lane names might change on the website
                dataMap["lane"].append("Ranged")
                dataMap["lane"].append("Melee")
                dataMap["lane"].append("Siege")
            else:
                dataMap["lane"].append(lane)
    try:
        info = cardArticle.find('div', class_="card-text").find('p').get_text().strip()
        dataMap["info"] = info
    except AttributeError:
        dataMap["info"] = ""

    try:
        flavor = cardArticle.find('p', class_="flavor").get_text().strip()
        dataMap["flavour"] = flavor
    except AttributeError:
        dataMap["flavour"] = ""

    # For Uncollectible
    dataMap["collectible"] = True
    try:
        textCollectable = content.find('ul', class_="card-cats").find_next_sibling('strong').a.get_text().strip()
        if textCollectable == "Uncollectible":
            dataMap["collectible"] = False
    except AttributeError:
        dataMap["collectible"] = True

    # print(dataMap)
    return dataMap