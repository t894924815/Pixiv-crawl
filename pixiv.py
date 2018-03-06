# coding=utf-8
import os
from concurrent import futures
import sys, getopt
import threading

import requests
from bs4 import BeautifulSoup
import json
import urllib2
from pprint import pprint

result = set()
lock = threading.Lock()
total = 1
max = 10
r18 = False
dir = ''
key = ''

headers = {
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/56.0.2924.87 Safari/537.36'
}

proxies = {
    "http": "http://127.0.0.1:1080",
    "https": "https://127.0.0.1:1080",
}

def main(argv):
    global key, max, dir
    page = 100
    try:
        opts, args = getopt.getopt(argv, "hk:s:d:p:", ["key=", "star=", "dir=", "page="])
    except getopt.GetoptError:
        print 'test.py -k <key> -s <star> -d <dir> -p <page>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'test.py -k <key> -s <star> -d <dir> -p <page>'
            sys.exit()
        elif opt in ("-k", "--key"):
            key = arg
        elif opt in ("-s", "--star"):
            max = arg
        elif opt in ("-d", "--dir"):
            dir = arg + '\\'
        elif opt in ("-p", "--page"):
            page = arg
    if key == '':
        print('require key to search! -h for help')
        return
    if dir == '':
        print('require dir to save! -h for help')
        return
    # Windows平台
    print '关键词：'.decode('utf-8').encode('gb2312'), key.decode('utf-8').encode('gb2312')
    print 'start下限：'.decode('utf-8').encode('gb2312'), max.decode('utf-8').encode('gb2312')
    print '输出目录：'.decode('utf-8').encode('gb2312'), dir.decode('utf-8').encode('gb2312')
    urls = get_urls(key, int(page))
    with futures.ThreadPoolExecutor(15) as executor:
        executor.map(crawl, urls)
    pprint(sorted(result, key=lambda v: v[1], reverse=True))  # 按star数降序排序


def get_cookies():
    with open("cookies.txt", 'r') as f:
        _cookies = {}
        for row in f.read().split(';'):
            k, v = row.strip().split('=', 1)
            _cookies[k] = v
        return _cookies


cookies = get_cookies()


def crawl(url):
    global total
    req = requests.get(url, headers=headers, cookies=cookies, proxies=proxies).text
    bs = BeautifulSoup(req, 'lxml').find('input', id="js-mount-point-search-result-list")['data-items']
    bs = json.loads(bs)
    for b in bs:
        try:
            detail = "https://www.pixiv.net/member_illust.php?mode=medium&illust_id=" + b['illustId']
            req = requests.get(detail, headers=headers, cookies=cookies, proxies=proxies).text
            star = BeautifulSoup(req, 'lxml').find('dd', class_="rated-count").string
            if int(star) < int(max):
                # print(' star < max')
                continue
            if r18 and BeautifulSoup(req, 'lxml').find('a', href="/tags.php?tag=R-18") is not None:
                continue
            with lock:
                org = BeautifulSoup(req, 'lxml').find('img', class_='original-image')
                if org is None:
                    uorg = BeautifulSoup(req, 'lxml').find('div', class_='works_display')
                    original = uorg.img['src']
                    fname = uorg.img['alt'] + '_' + b['illustId'] + original[original.rfind('.'):]
                    print(' not single img!')
                else:
                    original = org['data-src']
                    fname = org['alt'] + '_' + b['illustId'] + original[original.rfind('.'):]
                result.add((original, int(star)))
                print(' title: ' + fname + ' illustId: ' + b['illustId'] + ' star: ' + star + ' total: ' + str(total))
                total += 1
            down_file(original, fname)
        except:
            pass


def get_urls(search, page):
    fmt = 'https://www.pixiv.net/search.php?word={}&order=date_d&p={}'
    return [fmt.format(search, p) for p in range(1, page)]


def down_file(url, name):
    proxy_support = urllib2.ProxyHandler(proxies)
    opener = urllib2.build_opener(proxy_support)
    urllib2.install_opener(opener)
    request = urllib2.Request(url, headers={"Referer": url})

    if not os.path.exists(dir + key):
        os.mkdir(dir + key)
    with open(dir + key + '\\' + name, 'wb') as f:
        f.write(urllib2.urlopen(request).read())
        f.close()


if __name__ == "__main__":
    main(sys.argv[1:])
