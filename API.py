from flask import Flask, request, make_response, jsonify
from Bunny import BunnyHandler
from os import path

from threading import Thread

HOME_DIR = path.dirname(path.realpath(__file__))
UPLOAD_DIR = path.join(HOME_DIR, "uploads")

api = Flask(__name__)
bunny = BunnyHandler()

class UploadWorker:
    def __init__(self, local_file_path, target_file_path) -> None:
        self.local_file_path = local_file_path
        self.target_file_path = target_file_path
        
        self.workerThread = Thread(target=self._target, daemon=True)

    def _target(self):
        bunny.bunny_UploadFile(
            local_file_path = self.local_file_path,
            target_file_path = self.target_file_path,
            content_type = "application/octet-stream"
        )
    

class UploadQueue:
    def __init__(self):
        self.ActiveUploadWorkers = []

    def CreateUploadWorker(self, local_file_path = None, target_file_path = None):
        worker = UploadWorker(local_file_path=local_file_path, target_file_path=target_file_path)
        self.ActiveUploadWorkers.append(worker)
        worker.workerThread.start()

uploadQueue = UploadQueue()

@api.route("/status", methods=["GET"])
def status():
    return f"Alive!"

@api.route("/files/upload", methods=["POST"])
def files_misc_upload_POST():
    local_file_path = request.headers.get("local-file-path")
    if local_file_path is None or local_file_path == "":
        return make_response("Header \"local-file-path\" is not set or is set incorrectly.", 400)

    target_file_path = request.headers.get("target-file-path")
    if target_file_path is None or target_file_path == "":
        return make_response("Header \"target-file-path\" is not set or is set incorrectly.", 400)
    
    uploadQueue.CreateUploadWorker(local_file_path=local_file_path, target_file_path=target_file_path)

    return make_response("Success", 200)

@api.route("/files/list", methods=["GET"])
def files_list():
    path = request.headers.get("path", "videos/")
    if path == "" or len(path) > 30:
        return make_response("Header \"path\" is not set or is set incorrectly.", 400)

    fileList = bunny.bunny_ListFiles(path)

    return jsonify(fileList)

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