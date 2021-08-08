import requests
from bs4 import BeautifulSoup, Tag
import os
import unicodedata
import re

class Page:
    def __init__(self, url, name, dir, root=None, parent=None):
        self.root = root
        self.dir = dir
        self.content = BeautifulSoup(requests.get(url).text,'html.parser')
        if root == None:
            self.root = self
            self.traversed = []
            self.dir = dir + "/" + self.content.find("h1").text
        self.parent = parent
        self.url = url
        self.name = name
        self.getChildren()
        os.makedirs(self.dir+"/chapters", exist_ok=True)
    
    def getChildren(self):
        self.children = []
        temp = self.content.find("div",class_="question-content")
        links = BeautifulSoup(str(temp), 'html.parser')
        for i in links.find_all("a", class_=""):
            href = i['href']
            if href not in self.root.traversed:
                self.root.traversed.append(href)
                child = Page(href, i.text, self.dir, root=self.root, parent=self)
                self.children.append(child)
    
    def createHTML(self):
        html = BeautifulSoup("<!DOCTYPE html><html><head></head><body></body></html>", 'html.parser')
        
        head = html.find("head")
        stylesheet = html.new_tag("style")
        stylesheet.string=open(os.getcwd()+"/default.css").read()
        head.append(stylesheet)
        
        body = html.find("body")

        try:
            header = self.content.find("header", class_="story-header")
            header.p.decompose()
        except AttributeError:
            try:
                header = self.content.find("header", class_="chapter-header")
                header.p.decompose()
            except AttributeError:
                header = html.new_tag('h1')
                header.string = self.name
        body.append(header)

        mainContent = self.content.find("div",class_="chapter-content")
        body.append(mainContent)

        linkContainer = html.new_tag('div')
        linkContainer['class'] = "linkContainer"

        body.append(self.content.find("header", class_="question-header"))

        body.append(linkContainer)

        if not self.children:
            alert = html.new_tag("p")
            alert.string = "[No Further Paths]"
            linkContainer.append(alert)

        for i in self.children:
            link = html.new_tag("a")
            link.string = i.name
            link['href'] = i.dir+"/chapters/"+self.slugify(i.name)+".html" 
            link['class'] = "chapterLinks"
            linkContainer.append(link)


        persistent = html.new_tag("div")
        persistent['class'] = "persistent"
        back = html.new_tag("a")
        try:
            back.string = "Previous Chapter"
            back['href'] = self.dir+"/index.html" if self.parent==self.root else self.dir+"/chapters/"+self.slugify(self.parent.name)+".html"
            back['class'] = "styledLink prev"
            persistent.append(back)
        except AttributeError:
            #Case for first chapter
            pass
        
        original = html.new_tag('a')
        original.string = "Link to Original"
        original['class'] = "styledLink"
        original['href'] = self.url

        restart = html.new_tag("a")
        restart.string = "Restart"
        restart['class'] = "styledLink prev"
        restart['href'] = self.dir+"/index.html"

        persistent.append(restart)
        persistent.append(original)
        linkContainer.append(persistent)

        if self.root == self:
            published = open(self.dir+"/index.html", 'w', encoding='utf-8')
        else:
            published=open(self.dir+'/chapters/'+self.slugify(self.name)+'.html', 'w', encoding="utf-8")
        published.write(str(html.prettify()))

        [i.createHTML() for i in self.children]

    def slugify(self, value, allow_unicode=False):
        """
        Taken from https://github.com/django/django/blob/master/django/utils/text.py
        Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
        dashes to single dashes. Remove characters that aren't alphanumerics,
        underscores, or hyphens. Convert to lowercase. Also strip leading and
        trailing whitespace, dashes, and underscores.
        """
        value = str(value)
        if allow_unicode:
            value = unicodedata.normalize('NFKC', value)
        else:
            value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
        value = re.sub(r'[^\w\s-]', '', value.lower())
        return re.sub(r'[-\s]+', '-', value).strip('-_')



if __name__ == "__main__":
    #Test 
    p = Page("", "Introduction", os.getcwd()+"/land")

