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

    object = kwargs.get("object")


    resp = make_response()
    resp.status_code = status_code

    if headers is not None:
        resp.headers = headers
    else:
        resp.headers.set("Content-Type", "application/json")
        resp.headers.set("Server", "bunnyapi")
        resp.headers.set("Date", datetime.datetime.now())
        
    data = {
        "type": type, # Response type

        "message": message, # Response type message
        "message_name": message_name, # Response data object name (internal)

        "route": route, # Request route
        "method": method, # Request method
        
        "object": object # Response data object
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

        "object": None
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
    
    deleteLocal = request.headers.get("deleteLocal", True)

    response = bunny.bunny_UploadFile(
        local_file_path = local_file_path,
        target_file_path = target_file_path,
        content_type = "application/octet-stream",
        deleteLocal = deleteLocal
    )

    for key in response.keys():
        response_data[key] = response[key]

    return BuildHTTPResponse(**response_data)

@api.route("/files/list", methods=["GET"])
def files_list():
    response_data = {
        "type": None,

        "message": None,
        "message_name": None,

        "route": "/files/list",
        "method": request.method,

        "object": None
    }
    path = request.headers.get("path")
    if path is None or path == "":
        response_data["type"] = "FAIL"
        response_data["message"] = "Header \"path\" is not set or is set incorrectly."
        response_data["message_name"] = "path_missing"

        return make_response(**response_data, status_code=400)

    response = bunny.bunny_ListFiles(path)

    for key in response.keys():
        response_data[key] = response[key]

    return BuildHTTPResponse(**response_data)

@api.route("/files/delete", methods=["DELETE"])
def files_delete():
    response_data = {
        "type": None,

        "message": None,
        "message_name": None,

        "route": "/files/delete",
        "method": request.method,

        "object": None
    }
    target_file_path = request.headers.get("target-file-path")
    if target_file_path is None or target_file_path == "":
        response_data["type"] = "FAIL"
        response_data["message"] = "Header \"target_file_path\" is not set or is set incorrectly."
        response_data["message_name"] = "target_file_path_missing"

        return BuildHTTPResponse(**response_data, status_code=400)

    response = bunny.bunny_DeleteFile(target_file_path=target_file_path)

    for key in response.keys():
        response_data[key] = response[key]

    return BuildHTTPResponse(**response_data)

@api.route("/files/retrieve_metadata", methods=["GET"])
def files_retrieve():
    response_data = {
        "type": None,

        "message": None,
        "message_name": None,

        "route": "/files/retrieve_metadata",
        "method": request.method,

        "object": None
    }
    target_file_path = request.headers.get("target-file-path")
    if target_file_path is None or target_file_path == "":
        response_data["type"] = "FAIL"
        response_data["message"] = "Header \"target_file_path\" is not set or is set incorrectly."
        response_data["message_name"] = "target_file_path_missing"

        return BuildHTTPResponse(**response_data, status_code=400)

    response = bunny.bunny_GetFileData(target_file_path=target_file_path)

    for key in response.keys():
        response_data[key] = response[key]

    return BuildHTTPResponse(**response_data)

@api.route("/cache/purge", methods=["POST"])
def cache_purge():
    response_data = {
        "type": None,

        "message": None,
        "message_name": None,

        "route": "/cache/purge",
        "method": request.method,

        "object": None
    }
    target_url = request.args.get("url")
    if target_url is None or target_url == "":
        response_data["type"] = "FAIL"
        response_data["message"] = "Argument \"url\" is not set or is set incorrectly."
        response_data["message_name"] = "target_file_path_missing"

        return BuildHTTPResponse(response_data, status_code=400)
    
    response = bunny.bunny_PurgeLinkCache(target_url)

    for key in response.keys():
        response_data[key] = response[key]

    return BuildHTTPResponse(**response_data)

@api.route("/stream/create-signature", methods=["GET"])
def upload_createSignature():
    response_data = {
        "type": None,

        "message": None,
        "message_name": None,

        "route": "/stream/create-signature",
        "method": request.method,

        "object": None
    }

    videoID = request.headers.get("videoID")
    if videoID is None or videoID == "":
        response_data["type"] = "FAIL"
        response_data["message"] = "Header \"videoID\" is not set or is set incorrectly."
        response_data["message_name"] = "video_id_missing"
    
    signature, signature_expiration_time, library_id = bunny.bunny_GenerateTUSSignature(videoID=videoID)
    signatureData = {
        "signature": signature,
        "signature_expiration_time": signature_expiration_time,
        "library_id": library_id 
    }

    response_data["type"] = "SUCCESS"
    response_data["message"] = "TUS signature generated successfully."
    response_data["message_name"] = "create_signature_success"
    response_data["object"] = signatureData

    return BuildHTTPResponse(**response_data)

@api.route("/stream/create-video", methods=["GET"])
def Stream_createVideo():
    response_data = {
        "type": None,

        "message": None,
        "message_name": None,

        "route": "/stream/create-video",
        "method": request.method,

        "object": None
    }

    videoTitle = request.headers.get("title")
    if videoTitle is None or videoTitle == "":
        response_data["type"] = "FAIL"
        response_data["message"] = "Header \"title\" is not set or is set incorrectly."
        response_data["message_name"] = "video_title_missing"

        return BuildHTTPResponse(**response_data, status_code=400)
    
    response = bunny.bunny_CreateVideoInLibrary(title=videoTitle)

    for key in response.keys():
        response_data[key] = response[key]

    return BuildHTTPResponse(**response_data)

@api.route("/stream/update-video", methods=["POST"])
def Stream_updateVideo():
    response_data = {
        "type": None,

        "message": None,
        "message_name": None,

        "route": "/stream/update-video",
        "method": request.method,

        "object": None
    }

    video_guid = request.headers.get("guid")
    if video_guid is None or video_guid == "":
        response_data["type"] = "FAIL"
        response_data["message"] = "Header \"guid\" is not set or is set incorrectly."
        response_data["message_name"] = "video_guid_missing"
    
    payload = request.json
    if payload is None or payload == "":
        response_data["type"] = "FAIL"
        response_data["message"] = "JSON payload is not set or is set incorrectly."
        response_data["message_name"] = "video_payload_missing"

    if response_data["type"] == "FAIL":
        return BuildHTTPResponse(response_data, status_code=400)
    
    response = bunny.bunny_UpdateVideoInLibrary(guid=video_guid, payload=payload)

    for key in response.keys():
        response_data[key] = response[key]

    return BuildHTTPResponse(**response_data)

@api.route("/stream/retrieve-video", methods=["GET"])
def Stream_retrieveVideo():
    response_data = {
        "type": None,

        "message": None,
        "message_name": None,

        "route": "/stream/retrieve-video",
        "method": request.method,

        "object": None
    }
    video_guid = request.headers.get("guid")
    if video_guid is None or video_guid == "":
        response_data["type"] = "FAIL"
        response_data["message"] = "Header \"guid\" was not set or was set incorrectly."
        response_data["message_name"] = "video_guid_missing"

        return BuildHTTPResponse(**response_data)
    
    response = bunny.bunny_RetrieveVideoInLibrary(video_guid)

    for key in response.keys():
        response_data[key] = response[key]

    return BuildHTTPResponse(**response_data)
