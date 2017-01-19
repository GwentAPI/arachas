# arachas

Arachas is a web crawler that is capable of extracting card data related to the GWENT®: The Witcher Card Game from community websites.
Currently it only crawl the popular [gwentify](http://gwentify.com/) website.

The extracted data is then saved in a json file. It's also capable of downloading the card images but it will not do it by default.

Arachas have rudimentary diff capabilities which allow a user to keep track of what changed between consecutive runs.
It will print a message if a card was added/removed or modified (it can't make the distinction by itself). 

## Dependencies

You will need Python 3.6.

Install the dependencies:

```
pip install beautifulsoup4
pip install requests
pip install pytz
pip install termcolor
pip install unidecode
```

## How to use

```
python arachas.py
```

If you want to download the full sized card images:

```
python arachas.py --image
```

If you want to save the output data under a different name:

```
python arachas.py --output <name>
```
