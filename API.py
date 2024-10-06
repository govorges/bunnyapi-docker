from flask import Flask, request, make_response, jsonify
from Bunny import BunnyHandler
from os import path
import json
import datetime

HOME_DIR = path.dirname(path.realpath(__file__))
UPLOAD_DIR = path.join(HOME_DIR, "uploads")

api = Flask(__name__)
bunny = BunnyHandler()

def BuildHTTPResponse(
        headers: dict = None,
        status_code = 200, **kwargs
    ):

    type = kwargs.get("type")
    message = kwargs.get("message")
    message_name = kwargs.get("message_name")

    route = kwargs.get("route")
    method = kwargs.get("method")

    object_data = kwargs.get("object_data")


    resp = make_response()
    resp.status_code = status_code

    if headers is not None:
        resp.headers = headers
    else:
        resp.headers.set("Content-Type", "application/json")
        resp.headers.set("Server", "video")
        resp.headers.set("Date", datetime.datetime.now())
        
    data = {
        "type": type, # Response type

        "message": message, # Response type message
        "message_name": message_name, # Response data object name (internal)

        "route": route, # Request route
        "method": method, # Request method
        
        "object_data": object_data # Response data object
    }

    resp.set_data(
        json.dumps(data, indent=4)
    )

    return resp

@api.route("/status", methods=["GET"])
def status():
    return f"Alive!"

@api.route("/files/upload", methods=["POST"])
def files_misc_upload_POST():
    response_data = {
        "type": None,

        "message": None,
        "message_name": None,

        "route": "/files/upload",
        "method": request.method,

        "data": None
    }

    local_file_path = request.headers.get("local-file-path")
    if local_file_path is None or local_file_path == "":
        response_data["type"] = "FAIL"
        response_data["message"] = "The header \"local-file-path\" is not set or is set incorrectly"
        response_data["message_name"] = "local_file_path_missing"

    target_file_path = request.headers.get("target-file-path")
    if target_file_path is None or target_file_path == "":
        response_data["type"] = "FAIL"
        response_data["message"] = "The header \"target-file-path\" is not set or is set incorrectly"
        response_data["message_name"] = "target_file_path_missing"

    if response_data["type"] is not None:
        return BuildHTTPResponse(**response_data, status_code=400)
    
    deleteLocal = request.headers.get("deleteLocal", False)

    response = bunny.bunny_UploadFile(
        local_file_path = local_file_path,
        target_file_path = target_file_path,
        content_type = "application/octet-stream",
        deleteLocal = deleteLocal
    )

    for key in response.keys():
        response_data[key] = response[key]

    return BuildHTTPResponse(**response)

@api.route("/files/list", methods=["GET"])
def files_list():
    response_data = {
        "type": None,

        "message": None,
        "message_name": None,

        "route": "/files/list",
        "method": request.method,

        "data": None
    }
    path = request.headers.get("path")
    if path is None or path == "":
        response_data["type"] = "FAIL"
        response_data["message"] = "Header \"path\" is not set or is set incorrectly."
        response_data["message_name"] = "path_missing"

        return make_response(**response_data, status_code=400)

    file_list_response = bunny.bunny_ListFiles(path)

    return BuildHTTPResponse(**file_list_response)

@api.route("/files/delete", methods=["DELETE"])
def files_delete():
    target_file_path = request.headers.get("target-file-path")
    if target_file_path is None or target_file_path == "" or len(target_file_path) > 100:
        return make_response("Header \"target_file_path\" is not set or is set incorrectly.", 400)

    bunny.bunny_DeleteFile(target_file_path=target_file_path)

    return make_response("Success", 200)

@api.route("/files/retrieve_metadata", methods=["GET"])
def files_retrieve():
    target_file_path = request.headers.get("target-file-path")
    if target_file_path is None or target_file_path == "" or len(target_file_path) > 100:
        return make_response("Header \"target-file-path\" is not set or is set incorrectly.", 400)

    fileData = bunny.bunny_GetFileData(target_file_path=target_file_path)
    return jsonify(fileData)

@api.route("/cache/purge", methods=["POST"])
def cache_purge():
    target_url = request.args.get("url")
    if target_url is None or target_url == "":
        return make_response("Argument \"url\" is not set or is set incorrectly.", 400)
    
    bunny.bunny_PurgeLinkCache(target_url)

    return make_response(f"Cache purge of {target_url} successful", 200)

@api.route("/stream/create-signature", methods=["GET"])
def upload_createSignature():
    videoID = request.headers.get("videoID")
    if videoID is None or videoID == "":
        return make_response("Header \"videoID\" is not set or is set incorrectly.", 400)
    
    signature, signature_expiration_time, library_id = bunny.bunny_GenerateTUSSignature(videoID=videoID)
    signatureData = {
        "signature": signature,
        "signature_expiration_time": signature_expiration_time,
        "library_id": library_id 
    }
    return jsonify(signatureData)

@api.route("/stream/create-video", methods=["GET"])
def Stream_createVideo():
    videoTitle = request.headers.get("title")
    if videoTitle is None or videoTitle == "":
        return make_response("Header \"title\" was not set or was set incorrectly.", 400)
    
    video = bunny.bunny_CreateVideoInLibrary(title=videoTitle)
    return video

@api.route("/stream/update-video", methods=["POST"])
def Stream_updateVideo():
    video_guid = request.headers.get("guid")
    if video_guid is None or video_guid == "":
        return make_response("Header \"guid\" was not set or was set incorrectly.", 400)
    
    payload = request.json
    if payload is None or payload == "":
        return make_response("JSON payload was not set or was set incorrectly.", 400)
    
    r = bunny.bunny_UpdateVideoInLibrary(guid=video_guid, payload=payload)

    return make_response(r.text, 200)

@api.route("/stream/retrieve-video", methods=["GET"])
def Stream_retrieveVideo():
    video_guid = request.headers.get("guid")
    if video_guid is None or video_guid == "":
        return make_response("Header \"guid\" was not set or was set incorrectly.", 400)
    
    videoData = bunny.bunny_RetrieveVideoInLibrary(video_guid)

    return jsonify(videoData)