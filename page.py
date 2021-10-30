import requests
from bs4 import BeautifulSoup
import os
import unicodedata
import re
import shutil


class Page:
    def __init__(self, url, name, dir, downloadImages, filename="index", root=None, parent=None, id=0, propagate=True):
        self.root = root
        self.dir = dir
        self.content = BeautifulSoup(requests.get(url).text,'html.parser')
        self.filename = self.slugify(filename)+".html"
        self.downloadImages = downloadImages
        #Name root directory according to story title
        if root == None:
            self.root = self
            self.traversed = []
            self.dir = dir + "/" + self.content.find("h1").text
            self.pageCurrent = 0
            os.makedirs(self.dir+"/images", exist_ok=True)
            os.makedirs(self.dir+"/chapters", exist_ok=True)
            self.known = {}

        self.parent = parent
        self.url = url
        self.name = name
        self.id = id
        self.propagate = propagate

        if propagate:
            self.root.pageCurrent += 1
            print(str(self.root.pageCurrent) + " Links Scraped" + " | Parent chain: " + self.recurseParents())  

            self.root.known[url] = filename
            self.getChildren()



    def recurseParents(self):
        return ""
        ''' current = self.parent
        ids = [self.id]
        while current != None:
            ids.append(current.id)
            current = current.parent
        retval = ""
        for i in ids:
            retval = retval + str(i) + " to "
        return retval[:-3]'''

    def __str__(self):
        retval = "Children: \n"
        try:
            for i in self.children:
                retval += "------" + str(i)
        except AttributeError:
            pass
        return retval


    def getChildren(self):
        self.children = []
        temp = self.content.find("div",class_="question-content")
        links = BeautifulSoup(str(temp), 'html.parser')
        #Create new Page for each link in div
        count = 1
        for i in links.find_all("a", class_=""):
            href = i['href']

            if (not (href in self.root.known.keys())):
                child = Page(href,i.text, self.dir, self.downloadImages,filename=self.name+"-"+i.text,root=self.root, parent=self, id=self.id+count)
            else:
                child = Page(href,i.text, self.dir, self.downloadImages,filename=self.root.known.get(href),root=self.root, parent=self, id=self.id+count, propagate=False)

            self.children.append(child)
            count+= 1
    
    def createHTML(self):
        if not self.propagate:
            return

        #Base HTML
        with open('default.html', 'r') as f:
            html = BeautifulSoup(f.read(), 'html.parser')

        if(self.downloadImages):
            if(self.root == self):
                try:
                    coverImage = self.content.find("div",class_="cover").find("img")
                    if(coverImage):
                        name = self.slugify(coverImage['alt'])
                        savePath = self.dir + "/images/" + name
                        self.saveImage(coverImage['src'],savePath)
                        coverImage['src'] = "./images/" + name if self.root == self else "../images/" + name
                except AttributeError:
                    pass
            try:
                contentImages = self.content.find('div',class_="chapter-content").find_all('img')
            except AttributeError:
                contentImages = []

            for i in range(len(contentImages)):
                image = contentImages[i]
                name = self.slugify(str(i)+self.name)
                savePath = "./images/" + name if self.root == self else "../images/" + name
                imgPath = image['src']
                try:
                    self.saveImage(imgPath, self.dir + "/images/" + name)
                except (requests.exceptions.InvalidSchema) as err:
                    pass
                image['src'] = savePath

        head = html.find("head")
        
        stylesheet = [link for link in html.findAll("link") if "style.css" in link.get("href", [])][0]

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
        try:
            mainContent = self.content.find("div",class_="chapter-content")
            body.append(mainContent)
        except ValueError:
            print("Unable to fetch content at " + self.url)

        #Div container for choice links
        linkContainer = html.new_tag('div')
        linkContainer['class'] = "linkContainer"

        try:
            body.append(self.content.find("header", class_="question-header"))
        except ValueError:
            pass

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
            link['href'] = "./chapters/"+i.filename if self.root == self else i.filename 
            link['class'] = "chapterLinks"
            linkContainer.append(link)

        #Div container for persistent options (return, restart, etc.)
        persistent = html.new_tag("div")
        persistent['class'] = "persistent"
        back = html.new_tag("a")

        #Link to return to previous page
        try:
            back.string = "Previous Chapter"
            back['href'] = "../index.html" if self.parent==self.root else self.parent.filename
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
        restart['href'] = "../index.html"

        #Add subelements to linkContainer
        persistent.append(restart)
        persistent.append(original)
        linkContainer.append(persistent)

        #Create HTML file in proper location
        if self.root == self:
            #index.html file in root directory
            published = open(self.dir+"/index.html", 'w', encoding='utf-8')

            stylesheet['href'] = "chapters/style.css"

            css = open(self.dir+"/chapters/style.css", 'w', encoding='utf-8')
            with open('default.css', 'r') as f:
                css.write(f.read())
                css.close()
        else:
            #[chapter name].html file in 'chapters' directory
            published=open(self.dir+'/chapters/'+self.filename, 'w', encoding="utf-8")
        published.write(str(html.prettify()))
        published.close()

        #Create HTML for child Pages
        [i.createHTML() for i in self.children]

    def saveImage(self, url, file):
        try:
            r = requests.get(url, stream = True)
        except requests.exceptions.MissingSchema:
            r = requests.get("http://" + url, stream=True)
        except requests.exceptions.SSLError:
            print("Unable to download image from " + url)
            return
        except requests.exceptions.TooManyRedirects:
            print("Unable to download image from " + url)
            return
        except requests.exceptions.ConnectionError:
            print("Unable to download image from " + url)
            return
        except requests.exceptions.InvalidURL:
            print(url + " is invalid url")
            return

        # Check if the image was retrieved successfully
        if r.status_code == 200:
            # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
            r.raw.decode_content = True
            
            # Open a local file with wb ( write binary ) permission.
            with open(file,'wb') as f:
                shutil.copyfileobj(r.raw, f)
        else:
            print("Unable to download image from " + url)

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
        thing = re.sub(r'[-\s]+', '-', value).strip('-_')
        if len(thing) > 248:
            thing = thing[::248]
        return thing





if __name__ == "__main__":
    #Test 
    p = Page("", "Introduction", os.getcwd()+"/land")

