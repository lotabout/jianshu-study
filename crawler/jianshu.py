#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
import json
import os
import sys, argparse
import sqlite3

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
            text = sp.select('.list-footer')[0].text
            for (idx, regex) in meta:
                tmp = regex.search(text)
                if tmp:
                    article[idx] = tmp.group(1)
            return article
        except:
            return {}

    sp_articles = soup.select('.article-list li div')
    articles = [format_article(article) for article in sp_articles]
    articles = [x for x in articles if x]
    return articles

def save_articles(articles, fp):
    for article in articles:
        json.dump(article, fp, ensure_ascii=False, sort_keys=True)
        fp.write(os.linesep)

def get_next_url(soup):
    """Get the url for retrieve next articles."""
    try:
        return soup.select('.load-more button')[0]['data-url']
    except:
        return None

def extract_content(url):
    main_page = bot.get(url)
    sp_main = BeautifulSoup(main_page.content, 'html.parser')
    articles = get_articles(sp_main)
    next_url = get_next_url(sp_main)
    return (articles, next_url)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', help = 'specify the output file')
    parser.add_argument('-m', '--max', type=int, default = 15, help = 'max page')
    parser.add_argument('-u', '--start_url', type=str, default = '', help = 'start url')

    args = parser.parse_args()

    next_url = args.start_url
    max_page = args.max
    filename = args.file

    for i in range(max_page):
        print('Iteration: ', i, 'next_url:', next_url)
        (articles, next_url) = extract_content(main_url + next_url)
        with open(filename, 'a+') as fp:
            save_articles(articles, fp)

if __name__ == '__main__':
    main()
