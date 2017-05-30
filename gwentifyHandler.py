#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re

from bs4 import BeautifulSoup

# Match against the following case: "200/800"
# Used to extract mill and craft cost from the website.
costRegex = re.compile("^([0-9]+)/([0-9]+)")

# Match against the URL pattern used for the paging of the cards.
# The pattern is used to extract the matching groups, then from the known maximum pages,
# generate the url for all the other pages without having to explore and send more than one web request.
pageRegex = re.compile("^(http://gwentify.com[a-z/=?&]+)([1-9]+)([a-z/=?&]+)$")


# Extract the url of every individual cards found in the html of a page
def getCardsUrl(html):
    listCards = []

    soup = BeautifulSoup(html, 'html.parser')
    tableRows = soup.find('table').find_all('tr')

    # The data is present inside a table. We iterate over every rows.
    for row in tableRows:
        # Get the URL for the card of that row.
        cardUrl = row.td.a.get('href')
        listCards.append(cardUrl)

    return listCards


# From the main website, extract data relative to the pagination (card are available in different pages).
# From that information we generate a list of URL pointing to every individual pages.
# That way we only have to send a single web request.
def getPages(html):
    listPages = []

    soup = BeautifulSoup(html, 'html.parser')
    # The website have a link that point to the last page.
    # We are interested in it because we will learn both
    # the pattern used by the link and also the number of pages in total.
    lastPage = soup.select("li > a.last")[0].get('href')

    # Run the regex against the href.
    match = pageRegex.findall(lastPage)

    # We expect all 3 groups to be matched.
    # Otherwise raise an exception because the website changed and we should change the code.
    if match and len(match[0]) == 3:
        # Extract the second matched group which contain the number of the last page.
        totalNumPage = int(match[0][1])
        # We already have the starting page, so we can skip it and start right to page 2.
        for i in range(2, totalNumPage + 1):
            # Generate the URL for every other pages.
            # We also generate the last page even if we already have it. Not really important.
            link = match[0][0] + str(i) + match[0][2]
            listPages.append(link)
    else:
        raise NotImplementedError("Page formatting unsupported. Unable to crawl the pages.")

    return listPages


# From the html of a page for a single card, extract all the information for the card
# and return it as a map.
def getCardJson(html):
    dataMap = {}

    soup = BeautifulSoup(html, 'html.parser')
    # All the information is found inside this element.
    cardArticle = soup.find('div', id='primary').main

    # The card name is found outside of cardArticle. Just the main header of the page.
    name = cardArticle.find('h1').get_text()
    # Retrieve the main href of the image of the card (the href when we click on the picture).
    # It's the full size picture of the card.
    imageUrl = cardArticle.find('div', class_="card-img").a.get('href')
    thumbnailUrl = cardArticle.find('div', class_="card-img").a.img.get('src')
    # We dive deeper. A lot of the information is inside that div.
    content = cardArticle.find('div', class_="entry-content")

    dataMap["name"] = name.strip()
    dataMap["variations"] = []

    # Only one variation in gwentify, but the game can have many variations of a card
    variation = {}
    variation["availability"] = "BaseSet" # Currently all cards are from the base set.

    # Certain cards created from effects (like tokens) are called "uncollectible" because we can't actually collect them
    # in the game. Those cards have a special element on their page to inform the reader. This is why this we're using
    # a try catch. Cards are collectible by default unless otherwise noted.
    # There is no way to differentiate a token from an unreleased/removed card of the game.
    try:
        #Invalid as of March 26 2017
        textCollectable = content.find('ul', class_="card-cats").find_next_sibling('strong').a.get_text().strip()
        if textCollectable == "Uncollectible":
            variation["availability"] = "NonOwnable"
        else:
            variation["availability"] = "BaseSet"
    except AttributeError:
        variation["availability"] = "BaseSet"



    art = {}
    art["fullsizeImage"] = imageUrl.strip()
    art["thumbnailImage"] = thumbnailUrl.strip()
    variation["art"] = art

    # The div contains an unordered list. We will get all the elements of that list
    # and iterate through them.
    for data in cardArticle.select('ul.card-cats > li'):
        # The name of the card field is inside a strong element.
        attribute = data.strong.get_text().strip()

        # We check the name and do the appropriate action to store it in the map.
        if attribute == "Group:":
            dataMap["type"] = data.a.get_text().strip()
        if attribute == "Rarity:":
            # Currently, we don't have any other variation so we only work with the single variation.
            variation["rarity"] = data.a.get_text().strip()
        if attribute == "Faction:":
            dataMap["faction"] = data.a.get_text().strip()
        if attribute == "Strength:":
            # The strength is in a sibling element.
            dataMap["strength"] = int(data.strong.next_sibling.strip())

        if attribute == "Loyalty:":
            # A card can have multiple loyalties.
            dataMap["loyalty"] = list()
            for loyalty in data.find_all('a'):
                dataMap["loyalty"].append(loyalty.get_text().strip())

        if attribute == "Type:":
            # A card can have multiple categories (called types on the website).
            dataMap["categories"] = list()
            for category in data.find_all('a'):
                dataMap["categories"].append(category.get_text().strip())

        if attribute == "Craft:":
            # Create a map for the crafting cost. To store both normal and premium cost.
            variation["craft"] = {}
            variation["craft"]["normal"] = -1
            variation["craft"]["premium"] = -1

            # Use the regex to extract both the normal and premium cost.
            match = costRegex.findall(data.strong.next_sibling.strip())
            # Both group should be matched.
            if match and len(match[0]) == 2:
                variation["craft"]["normal"] = int(match[0][0])
                variation["craft"]["premium"] = int(match[0][1])

        # Same as the crafting cost.
        if attribute == "Mill:":
            variation["mill"] = {}
            variation["mill"]["normal"] = -1
            variation["mill"]["premium"] = -1

            match = costRegex.findall(data.strong.next_sibling.strip())
            if match and len(match[0]) == 2:
                variation["mill"]["normal"] = int(match[0][0])
                variation["mill"]["premium"] = int(match[0][1])

        if attribute == "Position:":
            # A card can be played on multiple lanes (called position on the website).
            dataMap["positions"] = list()
            lane = data.a.get_text().strip()

            # If the text is "Multiple", then that mean all 3 lanes are valid.
            # We add the 3 different lanes to the list instead of giving it a special significance.
            if lane == "Multiple":
                # Danger, lane names might change on the website
                dataMap["positions"].append("Ranged")
                dataMap["positions"].append("Melee")
                dataMap["positions"].append("Siege")
            # If it's not "Multiple", then it's a single lane card and we can just add the name of the lane.
            else:
                dataMap["positions"].append(lane)

    dataMap["variations"].append(variation)

    # The card info (the text describing its ability) is stored in a particular element that is uniquely identifiable.
    # Some cards might not have their info data already either. We wrap it in a try catch it case the element doesn't
    # exists.
    try:
        infos = cardArticle.find('div', class_="card-text").find_all('p')
        infoString = ""
        for info in infos:
            # Check if empty. Add space if not
            if infoString:
                infoString += " "
            infoString += info.get_text().strip()
        dataMap["info"] = infoString
    except AttributeError:
        pass
        # dataMap["info"] = ""

    # Same as for info.
    try:
        flavor = cardArticle.find('p', class_="flavor").get_text().strip()
        dataMap["flavor"] = flavor
    except AttributeError:
        pass
        # dataMap["flavor"] = ""

    return dataMap
