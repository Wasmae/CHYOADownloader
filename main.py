import argparse
import os
from page import Page

import sys

class recursionlimit:
    def __init__(self, limit):
        self.limit = limit
        self.old_limit = sys.getrecursionlimit()

    def __enter__(self):
        sys.setrecursionlimit(self.limit)

    def __exit__(self, type, value, tb):
        sys.setrecursionlimit(self.old_limit)

parser = argparse.ArgumentParser()

parser.add_argument('--link', help="URL of CHYOA start", type=str)
parser.add_argument('--links', help="Multiple URLS", type=str)
parser.add_argument('--images', help="Download images", type=bool, default=True)
parser.add_argument('--directory','-d', help="Directory to store downloaded files", default=os.getcwd(), type=str)

args = vars(parser.parse_args())





with recursionlimit(30000):
    print(sys.getrecursionlimit())
    if args['links']:
        links = []
        for i in args['links'].split(","):
            print("Collecting Links From " + i)
            page = Page(i, "", args['directory'], args['images'])
            print("Links Collected")
            print("Building HTML Files")
            page.createHTML()
            print("Download Complete")
        print("All Files Downloaded")
    else:
        print("Collecting Links")
        page = Page(args['link'], "", args['directory'], args['images'])
        print("Links Collected")
        print("Building HTML Files")
        page.createHTML()
        print("Download Complete")
