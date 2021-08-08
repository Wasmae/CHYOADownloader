import argparse
import os
from page import Page

parser = argparse.ArgumentParser()

parser.add_argument('--link', help="URL of CHYOA start", type=str)
parser.add_argument('--directory','-d', help="Directory to store downloaded files", default=os.getcwd(), type=str)

args = vars(parser.parse_args())

print(args)


page = Page(args['link'], "", args['directory'])
page.createHTML()