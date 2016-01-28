#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
import json
import os
import sys, argparse
import sqlite3
import time

re_read = re.compile('阅读\s*(\d+)')
re_comment = re.compile('评论\s*(\d+)')
re_like = re.compile('喜欢\s*(\d+)')
re_paid = re.compile('打赏\s*(\d+)')

meta = [('read', re_read), ('comment', re_comment), ('like', re_like), ('paid', re_paid)]

main_url = 'http://www.jianshu.com'

bot = requests.session()


def get_articles(soup):
    """Return a list of article informations

    :soup: TODO
    :returns: [{'title': .., 'url':.. , 'read': .., 'comment':.., 'liked':.., 'paid':..}]

    """
    def format_article(sp):
        article = {}
        try:
            tmp = sp.select('.title a')[0]
            article['title'] = tmp.text
            article['url'] = tmp['href']

            author = sp.select('a.author-name')[0]
            article['author'] = author.text
            article['author_url'] = author['href']

            text = sp.select('.list-footer')[0].text
            for (idx, regex) in meta:
                tmp = regex.search(text)
                if tmp:
                    article[idx] = tmp.group(1)
                else:
                    article[idx] = 0
            return article
        except:
            return {}

    sp_articles = soup.select('.article-list li div')
    articles = [format_article(article) for article in sp_articles]
    articles = [x for x in articles if x]
    return articles

def get_next_url(soup):
    """Get the url for retrieve next articles."""
    try:
        return soup.select('.load-more button')[0]['data-url']
    except:
        return None

def extract_content(url):
    main_page = bot.get(main_url + url)
    sp_main = BeautifulSoup(main_page.content, 'html.parser')
    articles = get_articles(sp_main)
    next_url = get_next_url(sp_main)
    return (articles, next_url)

def get_article_content(soup):
    try:
        return soup.select('.article')[0]
    except:
        return None

def extract_article(url):
    """Fetch the main content of an article"""
    try:
        article = bot.get(main_url + url)
        soup = BeautifulSoup(article.content, 'html.parser')
        return get_article_content(soup)
    except:
        return None

class Crawler():
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        c = self.conn.cursor()
        # create table if needed
        c.execute('''CREATE TABLE IF NOT EXISTS articles
        (url text, title text, author text, author_url text, read num, comment num, like num, paid num)''')
        self.conn.commit()
        c.execute('''CREATE TABLE IF NOT EXISTS content
        (url text, html_content text, text_content text)''')
        self.conn.commit()
        self.cursor = self.conn.cursor()

    def update_meta(self, info):
        self.cursor.execute('UPDATE articles SET read = ?, comment = ?, like = ?, paid = ? where url = ?',
                (info['read'], info['comment'], info['like'], info['paid'], info['url']))
        self.conn.commit()

    def save_article(self, info, content):
        self.cursor.execute('INSERT into articles VALUES(?, ?, ?, ?, ?, ?, ?, ?)',
                (info['url'], info['title'], info['author'], info['author_url'], info['read'],
                    info['comment'], info['like'], info['paid']))
        self.conn.commit()

        html_content = content if content else ''
        text_content = content.text if content else ''
        self.cursor.execute('INSERT into content VALUES(?, ?, ?)',
                (info['url'], str(html_content), text_content))
        self.conn.commit()

    def fetch_article(self, info):
        print('fetching:', info['title'])
        self.cursor.execute('SELECT title FROM articles WHERE url = ?', (info['url'],))
        row = self.cursor.fetchone()
        if row:
            # already fetched
            self.update_meta(info)
            return

        # fetch new
        content = extract_article(info['url'])
        self.save_article(info, content)

    def save_articles(self, articles):
        for article in articles:
            if article:
                self.fetch_article(article)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--max', type=int, default = 15, help = 'max page')
    parser.add_argument('-u', '--start_url', type=str, default = '/recommendations/notes', help = 'start url')
    parser.add_argument('-d', '--db_file', type=str, default = 'jianshu.db', help = 'start url')

    args = parser.parse_args()

    next_url = args.start_url
    max_page = args.max
    db_file = args.db_file

    crawler = Crawler(db_file)

    for i in range(max_page):
        print('Iteration: ', i)
        (articles, next_url) = extract_content(next_url)
        crawler.save_articles(articles)
        time.sleep(1)

if __name__ == '__main__':
    main()
