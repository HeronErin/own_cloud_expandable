from flask import Flask, jsonify, redirect, url_for, request, make_response, session
from .xmlBuilder import dictToProp
from .filesystem import *
import base64, random, json
from functools import wraps

import os

from urllib.parse import unquote


app = Flask(__name__)
try:
    app.secret_key = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "crypto", "secret.key"), "rb").read()
except FileNotFoundError:
    app.secret_key = os.urandom(32)


EDITION = "HeronErin cloud"


def secure(func):
    
    @wraps(func)
    def tmp(*args, **kwargs):
        is_correct = session.get("is_logged_in", False)

        Authorization_header = request.headers.get("Authorization")
        if Authorization_header is not None:
            user, password = base64.b64decode(Authorization_header.split(" ")[-1].encode("utf-8")).decode("utf-8").split(":")
            session["username"] = user
            is_correct = is_correct or app.auth(user, password)

        if is_correct:
            session["is_logged_in"] = True

            session["random_number"] = random.randrange(0, 1000000)

            return make_response(func(*args, **kwargs))
        else:
            resp = make_response("Authorization error", 401)
            resp.headers["WWW-Authenticate"] = 'Basic realm="ownCloud", charset="UTF-8"'
            
            return resp

    return tmp



@app.route("/status.php")
def status():
    return jsonify({"installed":"True","version":"10.12.2.1","versionstring":"10.12.2","edition":EDITION})
@app.route("/index.php/avatar/<path:path>")
@secure
def avatar(path):
    return jsonify({"data":{"displayname":session["username"]}})

@app.route("/ocs/v2.php/cloud/capabilities?format=json")
def capabilities():
    return jsonify({"ocs":{"meta":{"status":"ok","statuscode":200,"message":"OK","totalitems":"","itemsperpage":""},"data":{"version":{"major":10,"minor":12,"micro":2,"string":"10.12.2","edition":"Community","product":"ownCloud"},"capabilities":{"core":{"pollinterval":30000,"webdav-root":"remote.php/webdav","status":{"installed":True,"maintenance":false,"needsDbUpgrade":false,"version":"10.12.2.1","versionstring":"10.12.2","edition":"Community","productname":"ownCloud","product":"ownCloud","hostname":"09b7724d8dab"},"support-url-signing":True},"checksums":{"supportedTypes":["SHA1"],"preferredUploadType":"SHA1"},"files":{"privateLinks":True,"privateLinksDetailsParam":True,"bigfilechunking":True,"blacklisted_files":[".htaccess"],"blacklisted_files_regex":"\\.(part|filepart)$","favorites":True,"file_locking_support":True,"file_locking_enable_file_action":false,"undelete":True,"versioning":True},"dav":{"chunking":"1.0","reports":["search-files"],"propfind":{"depth_infinity":false},"trashbin":"1.0"},"files_sharing":{"api_enabled":True,"public":{"enabled":True,"password":{"enforced_for":{"read_only":false,"read_write":false,"upload_only":false,"read_write_delete":false},"enforced":false},"roles_api":True,"can_create_public_link":True,"expire_date":{"enabled":false},"send_mail":false,"social_share":True,"upload":True,"multiple":True,"supports_upload_only":True,"defaultPublicLinkShareName":"Public link"},"user":{"send_mail":false,"profile_picture":True,"expire_date":{"enabled":false}},"group":{"expire_date":{"enabled":false}},"remote":{"expire_date":{"enabled":false}},"resharing":True,"group_sharing":True,"auto_accept_share":True,"share_with_group_members_only":True,"share_with_membership_groups_only":True,"can_share":True,"user_enumeration":{"enabled":True,"group_members_only":false},"default_permissions":31,"providers_capabilities":{"ocinternal":{"user":["shareExpiration"],"group":["shareExpiration"],"link":["shareExpiration","passwordProtected"]},"ocFederatedSharing":{"remote":["shareExpiration"]}},"federation":{"outgoing":True,"incoming":True},"search_min_length":2},"notifications":{"ocs-endpoints":["list","get","delete"]}}}}})
@app.route("/ocs/v2.php/cloud/user")
@secure
def userString():
    return jsonify({"ocs":{"meta":{"status":"ok","statuscode":200,"message":"OK","totalitems":"","itemsperpage":""},"data":{"id":session["username"],"display-name":session["username"],"email":None,"language":"en"}}})

@app.route("/.well-known/<path:path>")
def wellknown(path):
    return redirect(request.host_url+"login", code=302)



@app.route("/remote.php/dav/<path:path>", methods=["PROPFIND", "HEAD", "GET", "PUT", "MOVE", "DELETE", "COPY", "MKCOL"])
@secure
def file(path):
    if path in ["files/BDMV/INDEX.BDM", "files/BDMV/index.bdmv", "files/VIDEO_TS/VIDEO_TS.IFO", "files/VIDEO_TS.IFO"]:
        return "Not found kodi", 404

    path = (path[5:])
    
    if path.endswith("/"): path = path[:-1]
    
    


    uname = "/"+ session["username"]
    startsWithUsername = path.startswith(uname)
    hrefAddition = ""
    if startsWithUsername:
        path = path[len(uname):]
        hrefAddition = uname



    if request.method == "PROPFIND" or request.method == "HEAD":
        



        data = app.fs_handler.getProps(path, hrefAddition=hrefAddition)
        if data == 404:
            return "Not found", 404

        # print("kodi", "Kodi" in request.headers.get("User-Agent", ""))
        xml = dictToProp(data, request.host_url, kodi="Kodi" in request.headers.get("User-Agent", ""))



        resp = make_response('<?xml version="1.0"?>\r\n' + xml, 207)
        resp.headers["Content-Type"] = "application/xml; charset=utf-8"


        return resp
    elif request.method == "GET":
        ret = app.fs_handler.sendFile(path, preview=bool(request.args.get("preview")), x=request.args.get("x"), y=request.args.get("y"))

        if ret == 404:
            path = path+ "/"
            ret = app.fs_handler.sendFile(path, preview=bool(request.args.get("preview")), x=request.args.get("x"), y=request.args.get("y"))
            if ret == 404:
                return "Not found get", 404

        return ret

    elif request.method == "PUT":
        return "", app.fs_handler.putFile(path, request)
    elif request.method == "MOVE" or request.method == "COPY":

        dst = request.headers.get("Destination")
        dst = unquote(dst[dst.find("/remote.php/dav/")+len("/remote.php/dav/files"):])

        if dst.startswith(uname): dst = dst[len(uname):]

        if request.method == "MOVE":
            return "", app.fs_handler.move(path, dst)
        elif request.method == "COPY":
            return "", app.fs_handler.copy(path, dst)
    elif request.method == "DELETE":
        return "", app.fs_handler.delete(path)
    elif request.method == "MKCOL":
        return "", app.fs_handler.mkfolder(path)




# smaller kodi paths
@app.route("/k/<path:path>", methods=["PROPFIND", "HEAD", "GET", "PUT", "MOVE", "DELETE", "COPY", "MKCOL"])
@secure
def kodiFile(path):
    return file("files/"+path)
@app.route("/k/", methods=["PROPFIND", "HEAD", "GET", "PUT", "MOVE", "DELETE", "COPY", "MKCOL"])
@secure
def kodiFil():
    return file("files/")


