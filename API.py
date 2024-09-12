from flask import Flask, request, make_response, jsonify
from Bunny import BunnyHandler
from os import path

import time
from threading import Thread
from os import remove

HOME_DIR = path.dirname(path.realpath(__file__))
UPLOAD_DIR = path.join(HOME_DIR, "uploads")

api = Flask(__name__)
bunny = BunnyHandler()

class UploadWorker:
    def __init__(self, id, local_file_path = None, target_file_path = None) -> None:
        self.id = id
        self.local_file_path = local_file_path
        self.target_file_path = target_file_path
        self.time_start = time.time()
        self.time_end = None
        
        self.workerThread = Thread(target=self._target, daemon=True)

    def _target(self):
        if self.id is not None:
            bunny.bunny_UploadFile(
                local_file_path = path.join(UPLOAD_DIR, f"{self.id}.png"),
                target_file_path = f"/videos/{self.id}.png",
                content_type = "application/octet-stream"
            )
            remove(path.join(UPLOAD_DIR, f"{self.id}.png"))

            bunny.bunny_UploadFile(
                local_file_path = path.join(UPLOAD_DIR, f"{self.id}.mp4"),
                target_file_path = f"/videos/{self.id}.mp4",
                content_type = "application/octet-stream"
            )
            remove(path.join(UPLOAD_DIR, f"{self.id}.mp4"))
        elif self.local_file_path is not None and self.target_file_path is not None:
            bunny.bunny_UploadFile(
                local_file_path = self.local_file_path,
                target_file_path = self.target_file_path,
                content_type = "application/octet-stream"
            )
            if ".xml" in self.target_file_path:
                bunny.bunny_PurgeLinkCache(f"https://openbroadcast.b-cdn.net/{self.target_file_path}")


        self.time_end = time.time()
    

class UploadQueue:
    def __init__(self):
        self.ActiveUploadWorkers = []
        self.poller = Thread(target=self.WorkerPoll, daemon=True).start()

    def CreateUploadWorker(self, id, local_file_path = None, target_file_path = None):
        worker = UploadWorker(id=id, local_file_path=local_file_path, target_file_path=target_file_path)
        self.ActiveUploadWorkers.append(worker)
        worker.workerThread.start()

uploadQueue = UploadQueue()

@api.route("/status", methods=["GET"])
def status():
    return f"Alive!"

@api.route("/files/upload", methods=["POST"])
def files_upload_POST():
    id = request.headers.get("id")
    if id is None or id == "" or len(id) > 20:
        return make_response("Header \"id\" is not set or is set incorrectly.", 400)

    uploadQueue.CreateUploadWorker(id=id)

    return make_response("Video is queued to be uploaded.", 200)

@api.route("/files/misc_upload", methods=["POST"])
def files_misc_upload_POST():
    local_file_path = request.headers.get("local-file-path")
    if local_file_path is None or local_file_path == "":
        return make_response("Header \"local-file-path\" is not set or is set incorrectly.", 400)

    target_file_path = request.headers.get("target-file-path")
    if target_file_path is None or target_file_path == "":
        return make_response("Header \"target-file-path\" is not set or is set incorrectly.", 400)
    
    uploadQueue.CreateUploadWorker(id = None, local_file_path=local_file_path, target_file_path=target_file_path)

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

@api.route("/files/retrieve", methods=["GET"])
def files_retrieve():
    target_file_path = request.headers.get("target-file-path")
    if target_file_path is None or target_file_path == "" or len(target_file_path) > 100:
        return make_response("Header \"target-file-path\" is not set or is set incorrectly.", 400)

    fileData = bunny.bunny_GetFileData(target_file_path=target_file_path)
    return jsonify(fileData)

@api.route("/cache/purge", methods=["GET"])
def cache_purge():
    target_url = request.args.get("url")
    if target_url is None or target_url == "":
        return make_response("Argument \"url\" is not set or is set incorrectly.", 400)
    
    bunny.bunny_PurgeLinkCache(target_url)

    return make_response(f"Cache purge of {target_url} successful", 200)