import sys
import requests
from pyemojify import emojify
from bs4 import BeautifulSoup as bs


def get_link(url):
    return "Link: https://slickdeals.net{}".format(url)


def print_deals(deals):
    benki, all_else = [], []
    for d in deals:
        ele = d.find("div", attrs={"class":"priceLine"})
        ele = ele["title"]
        link = d.find("div", attrs={"class":"itemBottomRow"})
        link = link["data-href"]
        if d.find("span", attrs={"class":"fire icon icon-fire"}):
            benki.append((ele, link))
        else:
            all_else.append((ele, link))

    for d in benki:
        print("{}  {}\n{}\n".format(emojify(":fire:"), d[0], get_link(d[1])))

    for d in all_else:
        print("{}\n{}\n".format(d[0], get_link(d[1])))


def get_to_work(soup):
    frontpage = soup.find_all("div",
                              attrs={"data-module-name":"Frontpage Slickdeals"})
    if not frontpage:
        print("Something went wrong {}".format(emojify(":disappointed:")))
        sys.exit(1)

    fp_deals = frontpage[0]
    all_deals = filter(lambda x: x.get("data-threadid"), fp_deals.find_all("div"))
    print_deals(list(all_deals))


def main():
    page = requests.get("https://slickdeals.net")
    if page.status_code != 200:
        print("Can't connect to slickdeals {}".format(emojify(":disappointed:")))
    else:
        get_to_work(bs(page.text, "html.parser"))


if __name__ == '__main__':
    main()