import argparse
import os
from page import Page

parser = argparse.ArgumentParser()

parser.add_argument('--link', help="URL of CHYOA start", type=str)
parser.add_argument('--images', help="Download images", type=bool, default=True)
parser.add_argument('--directory','-d', help="Directory to store downloaded files", default=os.getcwd(), type=str)

args = vars(parser.parse_args())

print("Collecting Links")
page = Page(args['link'], "", args['directory'], args['images'])
print("Links Collected")
print("Building HTML Files")
page.createHTML()
print("Download Complete")