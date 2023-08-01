from xml.etree.ElementTree import (
    Element, SubElement, Comment, tostring,
)


from .filesystem import *
import urllib.parse

def _strange_404FOLD(elem):
    propstat = SubElement(elem, "d:propstat")

    prop = SubElement(propstat, "d:prop")
    SubElement(prop, "d:displayname")
    SubElement(prop, "d:getcontenttype")
    SubElement(prop, "d:getcontentlength")
    SubElement(prop, "d:creationdate")


    SubElement(propstat, "d:status").text = "HTTP/1.1 404 Not Found"

def _strange_404FIL(elem):
    propstat = SubElement(elem, "d:propstat")
    prop = SubElement(propstat, "d:prop")
    SubElement(prop, "d:displayname")
    SubElement(prop, "d:creationdate")

    SubElement(propstat, "d:status").text = "HTTP/1.1 404 Not Found"



def _under_dict_to_prop(elem, dict, host, kodi=False):
    host = host if not host.endswith("/") else host[:-1]


    href = dict.get("href").format("/remote.php/dav/files/").replace("//", "/")
    if dict.get("type") == "collection":
        if not href.endswith("/"):
            href = href + "/"
    SubElement(elem, "d:href").text = urllib.parse.quote(href)


    propstat = SubElement(elem, "d:propstat")
    
    prop = SubElement(propstat, "d:prop")
    SubElement(propstat, "d:status").text="HTTP/1.1 200 OK"


    if dict.get("type") == "collection":
        SubElement(SubElement(prop, "d:resourcetype"), "d:collection")
        if not kodi:
            _strange_404FOLD(elem)
    else:
        SubElement(prop, "d:resourcetype")
        SubElement(prop, "d:getcontenttype").text = dict.get("type")
        if not kodi:
            _strange_404FIL(elem)
    
    SubElement(prop, "d:getlastmodified").text = str(dict.get("getlastmodified")) if "getlastmodified" in dict else None
    SubElement(prop, "d:getetag").text = str(dict.get("getetag")) if "getetag" in dict else None

    
    if "name" in dict: SubElement(prop, "d:displayname").text = str(dict.get("name"))
    
    if not kodi:
        

        SubElement(prop, "oc:permissions").text = str(dict.get("permissions")) if "permissions" in dict else None
        SubElement(prop, "oc:id").text = str(dict.get("id")) if "id" in dict else None

        if "size" in dict: SubElement(prop, "oc:size").text = str(dict.get("size"))
        SubElement(prop, "oc:privatelink").text = dict.get("privatelink").format(host) if "privatelink" in dict else None
        SubElement(prop, "oc:share-types").text = dict.get("share-types") if "share-types" in dict else None
    if kodi:

        if "size" in dict: SubElement(prop, "d:getcontentlength").text = str(dict.get("size")) if "size" in dict else None
    elif dict.get("type") != "collection":
        if "size" in dict: SubElement(prop, "d:getcontentlength").text = str(dict.get("size")) if "size" in dict else None


def dictToProp(dict, host, kodi=False):
    
    root = Element('d:multistatus')
    root.set("xmlns:d", "DAV:")
    root.set("xmlns:s", "http://sabredav.org/ns")
    root.set("xmlns:oc","http://owncloud.org/ns")
    _under_dict_to_prop(SubElement(root, "d:response"), dict, host, kodi=kodi)


    if "contents" in dict:
        for c in dict["contents"]:
            _under_dict_to_prop(SubElement(root, "d:response"), c, host, kodi=kodi)
    
    r = tostring(root).decode("utf-8")
    # print(r)
    return r

