import datetime, time, os, json, requests, base64, functools, mimetypes
from flask import Response, request

from werkzeug.datastructures import Headers

from cachetools import cached, TTLCache

class PermaDict(dict):
    def __init__(self, path, default = None):
        self.path = path
        default = {} if default is None else default
        if os.path.exists(path):
            default = json.load(open(path, "r"))
        super().__init__(default)
    def save(self):
        f = open(self.path, "w")
        f.write(json.dumps(dict(self)))
        f.close()
class PermaList(list):
    def __init__(self, path, default = None):
        self.path = path
        default = [] if default is None else default
        if os.path.exists(path):
            default = json.load(open(path, "r"))
        super().__init__(default)
    def save(self):
        f = open(self.path, "w")
        f.write(json.dumps(list(self)))
        f.close()


headers = {
    'authority': 'www.wcofun.org',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'accept-language': 'en-US,en;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'sec-gpc': '1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'referer': 'https://www.wcofun.net/'
}

def proxiedVideo(href):
    print(request.headers)
    link = resolveLinks(href)
    def gen(re):
        for chunk in r.iter_content(chunk_size=8192): 
            yield chunk

    r = requests.get(link, stream=True, headers=headers if request.headers.get("Range") is None else {**headers, "Range": request.headers["Range"]})
    r.raise_for_status()
    resp = Response(gen(r), mimetype = r.headers["Content-Type"])
    for k, v in r.headers.items():
        resp.headers[k]=v

    return resp
    
    


@cached(cache=TTLCache(maxsize=128, ttl=10*60))
def getImg(href):
    return requests.get(href).content


@cached(cache=TTLCache(maxsize=128, ttl=10*60))
def wcoSearchForAnime(query):
    r = requests.post("https://www.wcofun.org/search", data={"catara": query, "konuara": "series"}, headers=headers)
    if r.status_code == 200:
        res = []
        for show in r.text.split('<ul class="items">')[1].split('div class="img"'):
            if len(show) < 20:
                continue
            res.append([show.split('a href="')[1].split('"')[0], show.split('img alt="')[1].split('"')[0],  show.split('src="')[1].split('"')[0]])
        return res


    else:
        print("Error on search", r.text)
        return r.status_code



@cached(cache=TTLCache(maxsize=128, ttl=10*60))
def getEpisodes(href):
    r = requests.get(href, headers=headers)
    res = []
    for ep in r.text.split('<div class="cat-eps">')[1:]:
        ep = ep.split("</div>")[0]
        res.append([ep.split('a href="')[1].split('"')[0], 
            ep.split(">")[1].split("<")[0].replace(r'&amp;', '&').replace(r'&quot;', '"').replace('\u2606', ' ').replace(r'&#8216;', '‘').replace(r'&#8221;', '”').replace(r'&#8211;', '–')\
            .replace(r'&#038;', '&').replace(r'&#8217;', '’').replace(r'&#8220;', '“')\
            .replace(r'&#8230;', '…').replace(r'&#160;', ' ')
            ])
    res.reverse()
    return res
def decodeIframe(lis, offset):
    end = ""
    for b in lis:
        i = int("".join([i for i in list(base64.b64decode(b).decode("utf-8")) if i.isdigit()]))-offset
        end+=chr(i)
    return end
@cached(cache=TTLCache(maxsize=128, ttl=10*60))
def resolveLinks(href, use_hd=False):
    r = requests.get(href, headers=headers)
    preFrame = r.text.split("</div><script>var")[1]
    lst = preFrame.split("[")[1].split("]")[0]
    lst = json.loads(f"[{lst}]")

    offset = int(preFrame.split(")) - ")[1].split(")")[0])

    src =  decodeIframe(lst, offset).split("src=\"")[1].split('"')[0]
    r = requests.get(src, headers=headers)
    
    newUrl = "https://www.wcofun.net"+r.text.split('getJSON("')[-1].split("\"")[0]

    r = requests.get(newUrl, headers={**headers, "X-Requested-With":"XMLHttpRequest"} )
    jso = r.json()
    print(jso)
    return (jso.get("server") if jso.get("server") else "https://cdn.cizgifilmlerizle.com") + "/getvid?evid="+ (jso.get("hd") if use_hd and jso.get("hd") else  jso["enc"])






filesystem=None # Imported by file
datetimeToStr=None 



if not os.path.exists("/tmp/wco"):
   os.mkdir("/tmp/wco")

searches = PermaList("/tmp/wco/searches.json")
nameToHref = PermaDict("/tmp/wco/ShowNameToHref.json")
nameToImg = PermaDict("/tmp/wco/ShowNameToImg.json")
eppToHref = PermaDict("/tmp/wco/eppToHref.json")



def root(hrefAddition):
    tm = datetimeToStr(datetime.datetime.fromtimestamp(time.time()))
    return  {          
            "href": "{}"+hrefAddition,
            "getlastmodified": tm,
            "getetag": hrefAddition,
            "permissions": "RDNVCK",
            "id": hrefAddition,
            "size": 0,
            "privatelink": "{}/f/0",
            "share-types": None,
            "type": "collection",


            "contents":[
                {
                    "href": "{}"+hrefAddition+"/"+name+"/",
                    "getlastmodified": tm,
                    "getetag": str(hrefAddition+"/"+name+"/"),
                    "permissions": "RDNVCK",
                    "id": (hrefAddition+"/"+name+"/"),
                    "size": 0,
                    "privatelink": "{}/f/" + str(hash(hrefAddition+"/"+name+"/") ),
                    "share-types": None,
                    "type": "collection"
                } for name in ["Favorites", "Search","Cartoons","Dubbed Anime", "Settings"]


            ]
    }

def search(hrefAddition):
    tm = datetimeToStr(datetime.datetime.fromtimestamp(time.time()))
    return  {          
            "href": "{}"+hrefAddition+"/Search",
            "getlastmodified": tm,
            "getetag": hrefAddition+"/Search",
            "permissions": "RDNVCK",
            "id": hrefAddition+"/Search",
            "size": 0,
            "privatelink": "{}/f/0",
            "share-types": None,
            "type": "collection",


            "contents":[
                {
                    "href": "{}"+hrefAddition+"/Search/"+name+"/",
                    "getlastmodified": tm,
                    "getetag": str(hrefAddition+"/Search/"+name+"/"),
                    "permissions": "RDNVCK",
                    "id": (hrefAddition+"/Search/"+name+"/"),
                    "size": 0,
                    "privatelink": "{}/f/" + str(hash(hrefAddition+"/Search/"+name+"/") ),
                    "share-types": None,
                    "type": "collection"
                } for name in ["Create a folder to search"] + searches


            ]
    }




def episodePage(hrefAddition, href):
    
    if href is not None:

        res = getEpisodes(href)
        names = []
        i = 0
        for href, name in res:
            i+=1
            if name in eppToHref:
                while eppToHref.get(name) != href:
                    name = name + "."
                    if not name in eppToHref:
                        break
            name+=".mp4"
            tm = datetimeToStr(datetime.datetime.fromtimestamp(time.time()-i))
            eppToHref[name] = href
            names.append(name)
        eppToHref.save()
        return  {          
                "href": "{}"+hrefAddition,
                "getlastmodified": tm,
                "getetag": hrefAddition,
                "permissions": "RDNVCK",
                "id": hrefAddition,
                "size": 0,
                "privatelink": "{}/f/0",
                "share-types": None,
                "type": "collection",


                "contents":[
                    {
                        "href": "{}"+hrefAddition + name+"/",
                        "getlastmodified": tm,
                        "getetag": str(hrefAddition+"/"+name+"/"),
                        "permissions": "RDNVCK",
                        "id": (hrefAddition+"/"+name+"/"),
                        
                        "privatelink": "{}/f/" + str(hash(hrefAddition+"/"+name+"/") ),
                        "share-types": None,
                        "type": "video/mp4"
                    } for name in names


                ]
        }

def searchMenu(hrefAddition, path):
    tm = datetimeToStr(datetime.datetime.fromtimestamp(time.time()))

    term = path[len("/Search/"):]

    hrefAddition = hrefAddition +  path + "/"
    

    if "/" in term:
        return episodePage(hrefAddition, nameToHref.get(term.split("/")[1]))

    if term != "Create a folder to search":
        res = wcoSearchForAnime(term)
        names = []
        for href, name, image in res:
            if name in nameToHref:
                while nameToHref.get(name) != href:
                    name = name + "."
                    if not name in nameToHref:
                        break
            nameToHref[name] = href
            nameToImg[name] = image
            names.append(name)
        nameToHref.save()
        nameToImg.save()
        return  {          
                "href": "{}"+hrefAddition,
                "getlastmodified": tm,
                "getetag": hrefAddition,
                "permissions": "RDNVCK",
                "id": hrefAddition,
                "size": 0,
                "privatelink": "{}/f/0",
                "share-types": None,
                "type": "collection",


                "contents":[
                    {
                        "href": "{}"+hrefAddition + name+"/",
                        "getlastmodified": tm,
                        "getetag": str(hrefAddition+"/"+name+"/"),
                        "permissions": "RDNVCK",
                        "id": (hrefAddition+"/"+name+"/"),
                        "size": 0,
                        "privatelink": "{}/f/" + str(hash(hrefAddition+"/"+name+"/") ),
                        "share-types": None,
                        "type": "collection"
                    } for name in names


                ]
        }
class WcoFileSystem:
    def __init__(self):
        global datetimeToStr
        datetimeToStr=filesystem.datetimeToStr
    def getProps(self, path, hrefAddition = None):
        if len(path) == 0: path = "/"

        if path == "/":
            return root(hrefAddition if hrefAddition is not None else "")
        elif path == "/Search":
            return search(hrefAddition if hrefAddition is not None else "")
        elif path.startswith("/Search/"):
            return searchMenu(hrefAddition if hrefAddition is not None else "", path)
        else:
            print(path)


        # raise NotImplemented("Overide getProps() in subclass")
    def sendFile(self, path, preview=False, x=None, y=None):
        if path.startswith("/Search/"):
            if path.endswith("/"): path = path[:-1]
            showName = path.split("/")[-2]
            eppName = path.split("/")[-1]


            img = nameToImg.get(showName)
            vhref = eppToHref.get(eppName)
            if preview and img is not None:
                return Response(getImg(img), mimetype=mimetypes.guess_type(img)[0])
            elif vhref is not None:
                return proxiedVideo(vhref)
                
        raise NotImplemented("Overide sendFile() in subclass")
    def putFile(self, path, request):
        raise NotImplemented("Overide putFile() in subclass")
    def move(self, path, path2):
        raise NotImplemented("Overide move() in subclass")
    def copy(self, path, path2):
        raise NotImplemented("Overide copy() in subclass")
    def delete(self, path):
        raise NotImplemented("Overide delete() in subclass")
    def mkfolder(self, path):
        if path.startswith("/Search/"):

            searches.append(path[8:])
            searches.save()
            return 201
        raise NotImplemented("Overide mkfolder() in subclass")