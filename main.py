from html.parser import HTMLParser
from pathlib import Path
from sys import argv

import requests


class SwapPagesParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.num_pages = []
        self.inLink = None

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            for name, value in attrs:
                if name == 'class' and value == 'pagination':
                    self.inLink = True

    def handle_endtag(self, tag):
        if tag == "div":
            self.inLink = False

    def handle_data(self, data):
        if self.inLink and data.isnumeric():
            self.num_pages = int(data)


class SwapProductsParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.products = []
        self.inLink = None

    def handle_starttag(self, tag, attrs):
        if tag == 'span':
            for name, value in attrs:
                if name == 'class' and value == 'grid-product__title':
                    self.inLink = True

    def handle_endtag(self, tag):
        if tag == "span":
            self.inLink = False

    def handle_data(self, data):
        if self.inLink:
            self.products.append(data)


def main():
    url = "https://shop.clevertech.biz/password"
    catalog_url = "https://shop.clevertech.biz/collections/all?page={}"
    file_name = "clever_products.txt"
    delimiter = "\n"

    with requests.Session() as session:
        # Authenticate
        payload = {'form_type': 'storefront_password',
                   'utf8': '%E2%9C%93',
                   'password': password}
        session.request("POST", url, data=payload)

        # Get num of pages
        page_parser = SwapPagesParser()
        response = session.get(catalog_url.format(1))
        page_parser.feed(response.text)
        num_pages = page_parser.num_pages

        # Fetch products from shop catalog
        parser = SwapProductsParser()
        for i in range(num_pages):
            response = session.get(catalog_url.format(i + 1))
            parser.feed(response.text)
        live_products = parser.products

        # Fetch stored products
        if not Path(file_name).is_file():
            f = open(file_name, "w")
            f.write(delimiter.join(live_products))
            f.close()
            previous_products = live_products
        else:
            f = open(file_name, "r")
            products_content = f.read()
            f.close()
            previous_products = products_content.split(delimiter)
        live_products.sort()
        previous_products.sort()

        # Check for differences
        diff = list(set(live_products) - set(previous_products))
        if len(diff) > 0:
            print(", ".join(diff))
            f = open(file_name, "w")
            f.write(delimiter.join(parser.products))
            f.close()


if __name__ == '__main__':
    password = argv[1]
    main()
