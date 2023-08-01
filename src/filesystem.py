import os, datetime, functools, subprocess
from flask import send_file, session
import mimetypes, shutil, time



def datetimeToStr(dt):
    return dt.astimezone(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")








class BaseFileSystem:
    def getProps(self, path, hrefAddition = None):
        raise NotImplemented("Overide getProps() in subclass")
    def sendFile(self, path, preview=False, x=None, y=None):
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
        raise NotImplemented("Overide mkfolder() in subclass")
class RecursiveFileSystem(BaseFileSystem):
    def getProps(self, path, hrefAddition = None):
        if  path.startswith("/"): path = path[1:]
        if not hrefAddition.endswith("/"): hrefAddition = hrefAddition + "/"


        path = hrefAddition + path
        return {
            "href": "{}"+path,
            "getlastmodified": "Thu, 22 Jun 2023 18:53:10 GMT",
            "getetag": str(hash(path)),
            "permissions": "RDNVCK",
            "id": path,
            "size": 0,
            "privatelink": "{}/f/" + str(hash(path)),
            "share-types": None,
            "type": "collection",


            "contents":
            [
                {
                    "href": "{}"+path+"/"+str(i)+"/",
                    "getlastmodified": "Thu, 22 Jun 2023 18:53:10 GMT",
                    "getetag": str(hash(path+ str(i))),
                    "permissions": "RDNVCK",
                    "id": path + str(i),
                    "size": 0,
                    "privatelink": "{}/f/" + str(hash(path+"/"+ str(i)) ),
                    "share-types": None,
                    "type": "collection"
                }
            for i in range(10)
            ]

        }



class BaseContainerFileSystem(BaseFileSystem):
    def __init__(self, *args):
        raise NotImplemented("BaseContainerFileSystem is abstract")


        # Example



        
    def pathHandler(self, path):
        if len(path) == 0: path = '/'


        if path == "/":
            return "root"


        segs = [v for v in path.split(os.sep) if len(v)!=0]
        obase = None
        base = self.map
        i = 0
        for seg in segs:
            names = [node["name"] for node in base]
            if seg in names:
                node = base[names.index(seg)]
                if node.get("type", "") == "folder":
                    i+=1
                    base = node["contents"]
                    obase=node
                else:
                    

                    return node["fs"], "/"+"/".join(segs[:i+1] )


            else:
                return 404

        return node
        

        
    def getProps(self, path, hrefAddition = None):
        ph = self.pathHandler(path)


        if ph == "root":
            return {
            "href": "{}"+hrefAddition,
            "getlastmodified": "Thu, 22 Jun 2023 18:53:10 GMT",
            "getetag": "/",
            "permissions": "RDNVCK",
            "id": "/",
            "size": 0,
            "privatelink": "{}/f/0",
            "share-types": None,
            "type": "collection",


            "contents":
            [
                {
                    "href": "{}"+hrefAddition+"/"+path+c["name"]+"/",
                    "getlastmodified":datetimeToStr(datetime.datetime.fromtimestamp(time.time())),
                    "getetag": str(hrefAddition+"/"+path+c["name"]+"/" ),
                    "permissions": "RDNVCK",
                    "id": str(hrefAddition+"/"+path+c["name"]+"/" ),
                    "size": 0,
                    "privatelink": "{}/f/" + str(hash(hrefAddition+"/"+path+c["name"]+"/" )),
                    "share-types": None,
                    "type": "collection"
                }
            for c in self.map
            ]

        }
        elif type(ph) is tuple:
            rpath = path[len(ph[1]):]
            if len(rpath) == 0: rpath = "/"


            return ph[0].getProps(rpath, hrefAddition=hrefAddition+ph[1])
        elif type(ph) is dict:
            hrefAddition = hrefAddition+path
            return {
                    "href": "{}"+hrefAddition,
                    "getlastmodified": "Thu, 22 Jun 2023 18:53:10 GMT",
                    "getetag": hrefAddition,
                    "permissions": "RDNVCK",
                    "id": hrefAddition,
                    "size": 0,
                    "privatelink": "{}/f/0",
                    "share-types": None,
                    "type": "collection",


                    "contents":
                    [
                        {
                            "href": "{}"+hrefAddition+"/"+c["name"]+"/",
                            "getlastmodified":datetimeToStr(datetime.datetime.fromtimestamp(time.time())),
                            "getetag": str(hrefAddition+"/"+c["name"]+"/"),
                            "permissions": "RDNVCK",
                            "id": (hrefAddition+"/"+c["name"]+"/"),
                            "size": 0,
                            "privatelink": "{}/f/" + str(hash(hrefAddition+"/"+c["name"]+"/") ),
                            "share-types": None,
                            "type": "collection"
                        }
                    for c in ph["contents"]
                    ]

                }


            
        
    def sendFile(self, path, preview=False, x=None, y=None):
        ph = self.pathHandler(path)
        if type(ph) is tuple:
            path = path[len(ph[1]):]
            if len(path) == 0: path = "/"

            return ph[0].sendFile(path, preview, x, y)
        else:
            return 404
    def putFile(self, path, request):
        ph = self.pathHandler(path)
        if type(ph) is tuple:
            path = path[len(ph[1]):]
            if len(path) == 0: path = "/"

            return ph[0].putFile(path, request)
        else:
            return 404
    def move(self, path, path2):
        ph = self.pathHandler(path)
        if type(ph) is tuple:
            ph2 = self.pathHandler(path2)

            if type(ph2) is not tuple:
                return 404
            if ph2[0] is not ph[0]:
                return 404


            path = path[len(ph[1]):]
            path2 = path2[len(ph2[1]):]




            return ph[0].move(path, path2)
        else:
            return 404
    def copy(self, path, path2):
        ph = self.pathHandler(path)
        if type(ph) is tuple:


            ph2 = self.pathHandler(path2)

            if type(ph2) is not tuple:
                return 404
            if ph2[0] is not ph[0]:
                return 404


            path = path[len(ph[1]):]
            path2 = path2[len(ph2[1]):]

            return ph[0].copy(path, path2)
        else:
            return 404
    def delete(self, path):
        ph = self.pathHandler(path)
        if type(ph) is tuple:
            path = path[len(ph[1]):]
            if len(path) == 0: path = "/"



            return ph[0].delete(path, path2)
        else:
            return 404
    def mkfolder(self, path):
        ph = self.pathHandler(path)
        if type(ph) is tuple:
            path = path[len(ph[1]):]
            if len(path) == 0: path = "/"


            return ph[0].mkfolder(path)
        else:
            return 404



def getFolderSize(folder):
    total_size = os.path.getsize(folder)
    for item in os.listdir(folder):
        itempath = os.path.join(folder, item)
        if os.path.isfile(itempath):
            total_size += os.path.getsize(itempath)
        elif os.path.isdir(itempath):
            total_size += getFolderSize(itempath)
    return total_size
    
class FolderShareFileSystem(BaseFileSystem):
    def __init__(self, path):
        self.path=os.path.abspath(os.path.expanduser(path))

        self.privateLinks = {}
    def propForOsPath(self, path, OSpath, hrefAddition=None):


        privateId = str(hash(path))
        self.privateLinks[privateId] = OSpath

        dt = datetime.datetime.fromtimestamp(os.path.getmtime(OSpath))
        
        return {            
            "href": "{}"+(hrefAddition if hrefAddition is not None else "")+path,
            "getlastmodified": datetimeToStr(dt),
            "getetag": str(hash(OSpath)),
            "permissions": "RDNVCK",
            "id": path,
            "size": getFolderSize(OSpath) if os.path.isdir(OSpath) else os.path.getsize(OSpath),
            "privatelink": "{}/f/" + privateId,
            "share-types": None,
            "type": "collection" if os.path.isdir(OSpath) else mimetypes.guess_type(OSpath)[0]
            }
    def getPathOnDisk(self, path, ignoreNotFound=False):
        if len(path) == 0:
            path = '/'

        if ".." in path:
            return 404, 404
        
        pathOnDisk = self.path if path == "/" else os.path.join(self.path, path if not path.startswith("/") else path[1:])

        # print(pathOnDisk, self.path)

        if not pathOnDisk.startswith(self.path) or not(os.path.exists(pathOnDisk) if not ignoreNotFound else True):
            return 404, 404
        return pathOnDisk, path
    def getProps(self, path, hrefAddition = None):


        hrefAddition = "" if hrefAddition is None else hrefAddition

        if len(path) == 0: path = '/'

        pathOnDisk, path = self.getPathOnDisk(path)

        

        if pathOnDisk == 404:
            return 404


        if not os.path.isfile(pathOnDisk):
            base = self.propForOsPath(path, pathOnDisk, hrefAddition=hrefAddition)

            base["contents"] = [
            self.propForOsPath(os.path.join(path, fileP), os.path.join(pathOnDisk, fileP), hrefAddition=hrefAddition)

            for fileP in os.listdir(pathOnDisk)
            ]

            return base
        else:
            return self.propForOsPath(path, pathOnDisk, hrefAddition=hrefAddition)


    def sendFile(self, path, preview=False, x=None, y=None):
        pathOnDisk, path = self.getPathOnDisk(path)
        if pathOnDisk == 404:
            return 404


        type_of_data = mimetypes.guess_type(path)[0]

        if not preview:
            return send_file(pathOnDisk)
        elif type_of_data.startswith("video") or type_of_data.startswith("image"):
            if type_of_data.startswith("video"):
                cmdArr = ["ffmpeg", "-i", pathOnDisk, "-vframes", "1", "-s", f"{x}x{y}", "-f", "apng", "-",  "-hide_banner", "-loglevel", "error"]
            elif type_of_data.startswith("image"):
                cmdArr = ["convert", pathOnDisk, "-resize", f"{x}x{y}", "-"]


            ffmpeg_cmd = subprocess.Popen(
                cmdArr,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                shell=False
            )
            b = b""
            while True:
                output = ffmpeg_cmd.stdout.read()
                if len(output) > 0:
                    b += output
                else:
                    error_msg = ffmpeg_cmd.poll()
                    if error_msg is not None:
                        break
            return b
    def putFile(self, path, request):
        pathOnDisk, _ = self.getPathOnDisk(path, ignoreNotFound=True)
        if pathOnDisk == 404:
            return 404

        f = open(pathOnDisk, "wb")
        f.write(request.data)
        f.close()

        return 201

    def move(self, path, path2):
        path1, _ = self.getPathOnDisk(path)
        path2, _ = self.getPathOnDisk(path2, ignoreNotFound=True)
        if path1 == 404 or path2 == 404:
            return 404

        shutil.move(path1, path2)

        return 201
    def copy(self, path, path2):
        path1, _ = self.getPathOnDisk(path)
        path2, _ = self.getPathOnDisk(path2, ignoreNotFound=True)
        if path1 == 404 or path2 == 404:
            return 404

        shutil.copy2(path1, path2)

        return 201

    def delete(self, path):
        path, _ = self.getPathOnDisk(path)
        if path == 404:
            return 404
        if os.path.isfile(path):
            os.remove(path)
        else:
            shutil.rmtree(path)

        return 204


    def mkfolder(self, path):
        
        pathOnDisk, _ = self.getPathOnDisk(path, ignoreNotFound=True)
        if pathOnDisk == 404:
            return 404

        os.mkdir(pathOnDisk)

        return 201



