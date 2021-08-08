import requests
from bs4 import BeautifulSoup
import os
import unicodedata
import re

class Page:
    def __init__(self, url, name, dir, filename="index", root=None, parent=None):
        self.root = root
        self.dir = dir
        self.content = BeautifulSoup(requests.get(url).text,'html.parser')
        self.filename = self.slugify(filename)+".html"
        #Name root directory according to story title
        if root == None:
            self.root = self
            self.traversed = []
            self.dir = dir + "/" + self.content.find("h1").text
            self.pageCurrent = 0

        self.parent = parent
        self.url = url
        self.name = name

        self.root.pageCurrent += 1
        print(str(self.root.pageCurrent) + " Links Scraped")

        self.getChildren()

        os.makedirs(self.dir+"/chapters", exist_ok=True)
    
    def getChildren(self):
        self.children = []
        temp = self.content.find("div",class_="question-content")
        links = BeautifulSoup(str(temp), 'html.parser')
        #Create new Page for each link in div
        for i in links.find_all("a", class_=""):
            href = i['href']

            child = Page(href,i.text, self.dir, filename=self.name+"-"+i.text,root=self.root, parent=self)
            self.children.append(child)
    
    def createHTML(self):
        #Base HTML
        html = BeautifulSoup("<!DOCTYPE html><html><head></head><body></body></html>", 'html.parser')
        
        #Add CSS
        head = html.find("head")
        stylesheet = html.new_tag("style")
        stylesheet.string=open(os.getcwd()+"/default.css").read()
        head.append(stylesheet)
        
        body = html.find("body")

        #Copy Story/Chapter header from chyoa.com
        try:
            header = self.content.find("header", class_="story-header")
            header.p.decompose()
        except AttributeError:
            try:
                header = self.content.find("header", class_="chapter-header")
                header.p.decompose()
            #Remnant from initial work (possibly redundant)
            except AttributeError:
                header = html.new_tag('h1')
                header.string = self.name
        body.append(header)

        #Copy main content from chyoa.com
        mainContent = self.content.find("div",class_="chapter-content")
        body.append(mainContent)

        #Div container for choice links
        linkContainer = html.new_tag('div')
        linkContainer['class'] = "linkContainer"

        body.append(self.content.find("header", class_="question-header"))

        body.append(linkContainer)

        #Adds text informing user that there are no more paths
        if not self.children:
            alert = html.new_tag("p")
            alert.string = "[No Further Paths]"
            linkContainer.append(alert)

        #Iterate through child Pages and add as links
        for i in self.children:
            link = html.new_tag("a")
            link.string = i.name
            link['href'] = i.dir+"/chapters/"+i.filename 
            link['class'] = "chapterLinks"
            linkContainer.append(link)

        #Div container for persistent options (return, restart, etc.)
        persistent = html.new_tag("div")
        persistent['class'] = "persistent"
        back = html.new_tag("a")

        #Link to return to previous page
        try:
            back.string = "Previous Chapter"
            back['href'] = self.dir+"/index.html" if self.parent==self.root else self.dir+"/chapters/"+self.parent.filename
            back['class'] = "styledLink prev"
            persistent.append(back)
        except AttributeError:
            #Case for first chapter
            pass
        
        #Link to original page on chyoa.com
        original = html.new_tag('a')
        original.string = "Link to Original"
        original['class'] = "styledLink"
        original['href'] = self.url

        #Link to return to beginning
        restart = html.new_tag("a")
        restart.string = "Restart"
        restart['class'] = "styledLink prev"
        restart['href'] = self.dir+"/index.html"

        #Add subelements to linkContainer
        persistent.append(restart)
        persistent.append(original)
        linkContainer.append(persistent)

        #Create HTML file in proper location
        if self.root == self:
            #index.html file in root directory
            published = open(self.dir+"/index.html", 'w', encoding='utf-8')
        else:
            #[chapter name].html file in 'chapters' directory
            published=open(self.dir+'/chapters/'+self.filename, 'w', encoding="utf-8")
        published.write(str(html.prettify()))

        #Create HTML for child Pages
        [i.createHTML() for i in self.children]

    #Function to convert page names into valid file paths
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

