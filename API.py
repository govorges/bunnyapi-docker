from flask import Flask, request, make_response, jsonify
from Bunny import BunnyHandler
from os import path

import time
from threading import Thread

HOME_DIR = path.dirname(path.realpath(__file__))
UPLOAD_DIR = path.join(HOME_DIR, "uploads")

api = Flask(__name__)
bunny = BunnyHandler()

class UploadWorker:
    def __init__(self, local_file_path, target_file_path) -> None:
        self.local_file_path = local_file_path
        self.target_file_path = target_file_path

        self.time_start = time.time()
        self.time_end = None
        
        self.workerThread = Thread(target=self._target, daemon=True)

    def _target(self):
        bunny.bunny_UploadFile(
            local_file_path = self.local_file_path,
            target_file_path = self.target_file_path,
            content_type = "application/octet-stream"
        )

        self.time_end = time.time()
    

class UploadQueue:
    def __init__(self):
        self.ActiveUploadWorkers = []

    def CreateUploadWorker(self, id, local_file_path = None, target_file_path = None):
        worker = UploadWorker(id=id, local_file_path=local_file_path, target_file_path=target_file_path)
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