# bbc_scraper.py

from bs4 import BeautifulSoup
import pymongo
import os
import logging
import requests
from urllib.parse import urlparse
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# MongoDB setup
mongo_host = os.getenv('MONGO_HOST', 'localhost')
mongo_port = int(os.getenv('MONGO_PORT', 27017))
mongo_client = pymongo.MongoClient(f"mongodb://{mongo_host}:{mongo_port}/")
db_mongo = mongo_client["scraper_db"]
collection = db_mongo["bbc_articles"]


def is_allowed_by_robots_txt(url):
    # Implement based on BBC's actual robots.txt rules
    # For now, use a simple check
    return not any(url.startswith(path) for path in [
        '/bitesize/search', '/cbbc/search', '/cbeebies/search', '/chwilio',
        '/education/blocks', '/newsround', '/search', '/food/favourites',
        '/food/search', '/food/recipes/search', '/education/my', '/bitesize/my',
        '/food/recipes/*/shopping-list', '/food/menus/*/shopping-list', '/news/0',
        '/sport/alpha/', '/ugc', '/ugcsupport', '/userinfo/', '/u5llnop',
        '/sounds/search', '/ws/includes', '/radio/imda', '/storyworks/preview/',
        '/rd/search'
    ])


def fetch_bbc_articles():
    url = 'https://www.bbc.com/'

    if not is_allowed_by_robots_txt(url):
        logging.warning(f"Skipping {url} as it is disallowed by robots.txt")
        return None

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch BBC homepage: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    articles = []

    for link in soup.find_all('a', href=True):
        article_url = link['href']
        if is_article_url(article_url):
            article = fetch_article_details(article_url)
            if article:
                articles.append(article)

    return articles


def is_article_url(url):
    # Implement a more robust function to check if URL is an article URL
    return '/news/' in url and '/video/' not in url  # Example condition


def fetch_article_details(article_url):
    base_url = 'https://www.bbc.com'
    full_url = base_url + article_url

    try:
        response = requests.get(full_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch article '{article_url}': {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    title = soup.find('h1')
    description = soup.find('p')

    if title and description:
        article_content = scrape_article_content(full_url)  # Pass full URL for content scraping
        article_id = ObjectId()  # Generate unique ID for the article

        article = {
            '_id': article_id,
            'title': title.get_text(strip=True),
            'link': full_url,
            'description': description.get_text(strip=True),
            'content': article_content
        }
        return article
    else:
        logging.warning(f"Could not extract details from article '{article_url}'")
        return None


def scrape_article_content(full_url):
    try:
        response = requests.get(full_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch article content for URL: {full_url}: {e}")
        return ''

    soup = BeautifulSoup(response.content, 'html.parser')
    article_body = soup.find('article')
    if article_body:
        paragraphs = article_body.find_all('p')
        content = ' '.join([p.get_text(strip=True) for p in paragraphs])
        return content
    return ''


def scrape_and_store_articles():
    articles = fetch_bbc_articles()
    if articles:
        collection.delete_many({})
        result = collection.insert_many(articles)
        logging.info(f"Successfully scraped and inserted {len(result.inserted_ids)} articles into MongoDB")
    else:
        logging.warning("No articles scraped from BBC News homepage")
