import requests
import hashlib
import datetime
import os

class BunnyHandler:
    def __init__(self):
        self.bunny_StorageZone_API_Key = os.environ["BUNNY_STORAGEZONE_KEY"]
        self.bunny_Account_API_Key = os.environ["BUNNY_ACCOUNT_KEY"]

        if os.getenv("BUNNY_STORAGEZONE") is not None and os.getenv("BUNNY_STORAGE_REGION") != "":
            self.bunny_Region = f'{os.environ["BUNNY_STORAGE_REGION"]}.'
        else:
            self.bunny_Region = ""
        self.bunny_StorageZoneName = os.environ["BUNNY_STORAGEZONE_NAME"]
        self.bunny_StorageZoneEndpoint = "https://" + self.bunny_Region + "storage.bunnycdn.com" + "/" + self.bunny_StorageZoneName

        self.bunny_StreamLibrary_ID = os.environ["BUNNY_STREAMLIBRARY_ID"]
        self.bunny_StreamLibrary_Key = os.environ["BUNNY_STREAMLIBRARY_KEY"]

        self.bunny_PullZoneRoot = os.environ["BUNNY_PULL_ZONE_ROOT"]

        if not self.bunny_ConnectionAlive():
            raise SystemError("Bunny connection has failed! (NOT AUTH RELATED)")

    def bunny_ConnectionAlive(self):
        requestURL = "https://api.bunny.net/region"
        r = requests.get(requestURL)

        if r.status_code == 200:
            return True
        else:
            return False

    def bunny_UploadFile(self, local_file_path, target_file_path, content_type = "application/octet-stream", purge = True, deleteLocal = False):
        responseData = {
            "type": None,
            "message": None,
            "message_name": None,
            "status_code": None
        }

        requestHeaders = {
            "AccessKey": self.bunny_StorageZone_API_Key,
            "Content-Type": content_type,
            "accept": "application/json",
        }
        
        if target_file_path[0] != "/": # This + deleteLocal's logic can be a possibly dangerous combination if not cleaned properly.
            target_file_path = f"/{target_file_path}"

        requestURL = self.bunny_StorageZoneEndpoint + target_file_path
        
        # 201 -	The file was uploaded successfully.
        # 400 - The file was uploaded unsuccessfully.
        # 401 - Invalid AccessKey, region hostname, or file passed in a non raw binary format.
        bunnyRequest = requests.put(requestURL, data=open(local_file_path, "rb"), headers=requestHeaders)
        if bunnyRequest.status_code == 201:
            responseData["type"] = "SUCCESS"
            responseData["message"] = "The file was uploaded successfully."
            responseData["message_name"] = "upload_success"
        elif bunnyRequest.status_code == 400:
            responseData["type"] = "FAIL"
            responseData["message"] = "The file was not uploaded."
            responseData["message_name"] = "upload_failed"
        elif bunnyRequest.status_code == 401:
            responseData["type"] = "FAIL"
            responseData["message"] = "Invalid AccessKey, region hostname, or file passed in a non raw binary format."
            responseData["message_name"] = "invalid_auth"
        responseData["status_code"] = bunnyRequest.status_code

        if bunnyRequest.status_code != 201:
            return responseData

        # Handling `purge` and `deleteLocal` before returning.
        try:
            if purge:
                self.bunny_PurgeLinkCache(f"{self.bunny_PullZoneRoot}{target_file_path}")
        except:
            responseData["type"] = "WARN"
            responseData["message"] = "File uploaded but link not successfully purged."
            responseData["message_name"] = "upload_success_link_not_purged"
            responseData["status_code"] = 400

        try:
            if deleteLocal: # local_file_path can be unsafe. verify file exists as a normal file before removing.
                if os.path.isfile(local_file_path):
                    # local_file_path could still be escaping to critical directories
                    for str in ["..", ":", "<", ">", "\"", "|", "?", "*"]: 
                        if str in local_file_path:
                            raise ValueError("Invalid char in local_file_path")
                    os.remove(local_file_path)
        except ValueError:
            if responseData["type"] != "WARN":
                responseData["type"] = "WARN"
                responseData["message"] = "File uploaded but local file was not successfully deleted. This is likely due to an invalid local_file_path value."
                responseData["message_name"] = "upload_success_local_not_deleted"
                responseData["status_code"] = 400
            else: # Both the local deletion and the URL cache purge failed.
                responseData["type"] = "WARN"
                responseData["message"] = "File uploaded but local file not deleted and link not purged."
                responseData["message_name"] = "upload_success_local_not_deleted_link_not_purged"
                responseData["status_code"] = 400

        return responseData

    def bunny_ListFiles(self, path: str):
        requestHeaders = {
            "AccessKey": self.bunny_StorageZone_API_Key,
            "accept": "application/json"
        }
        requestURL = self.bunny_StorageZoneEndpoint + "/" + path

        fileList = requests.get(requestURL, headers=requestHeaders).json()
        return fileList

    def bunny_DeleteFile(self, target_file_path):
        requestHeaders = {
            "AccessKey": self.bunny_StorageZone_API_Key,
            "accept": "application/json"
        }

        if target_file_path[0] != "/":
            target_file_path = f"/{target_file_path}"

        requestURL = self.bunny_StorageZoneEndpoint + target_file_path

        requests.delete(requestURL, headers=requestHeaders)

    def bunny_PurgeLinkCache(self, url):
        requestHeaders = {
            "AccessKey": self.bunny_Account_API_Key
        }
        requestURL = f"https://api.bunny.net/purge?url={url}"            
        requests.post(requestURL, headers=requestHeaders)
    
    def bunny_GetFileData(self, target_file_path):
        if target_file_path[0] != "/":
            target_file_path = f"/{target_file_path}"
            
        folderData = self.bunny_ListFiles(target_file_path.rsplit("/", 1)[0])
        fileData = {}
        for item in folderData:
            if item["ObjectName"] == target_file_path.rsplit('/', 1)[-1]:
                fileData = item
                break

        return fileData
    
    def bunny_CreateVideoInLibrary(self, title: str):
        requestHeaders = {
            "AccessKey": self.bunny_StreamLibrary_Key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        requestData = {
            "title": title
        }
        requestURL = f"https://video.bunnycdn.com/library/{self.bunny_StreamLibrary_ID}/videos"

        resp = requests.post(requestURL, headers=requestHeaders, json=requestData)
        return resp.json()
    
    def bunny_GenerateTUSSignature(self, videoID):
        '''Generates a pre-signed authentication signature for TUS (resumable uploads) used by Bunny's Stream API.'''
        signature_library_id = self.bunny_StreamLibrary_ID
        signature_expiration_time = int((datetime.datetime.now() + datetime.timedelta(hours=2)).timestamp())
        signature = hashlib.sha256((signature_library_id + self.bunny_StreamLibrary_Key + str(signature_expiration_time) + str(videoID)).encode())
        
        return (signature.hexdigest(), signature_expiration_time, signature_library_id)
    
    def bunny_UpdateVideoInLibrary(self, guid: str, payload: dict):
        validPayloadKeys = ['title', 'collectionId', 'chapters', 'moments', 'metaTags']

        requestPayload = {}
        for value in validPayloadKeys:
            requestPayload[value] = payload.get(value)
            if requestPayload[value] is None:
                requestPayload.pop(value)
        
        requestURL = f"https://video.bunnycdn.com/library/{self.bunny_StreamLibrary_ID}/videos/{guid}"

        requestHeaders = {
            "AccessKey": self.bunny_StreamLibrary_Key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        r = requests.post(requestURL, json=requestPayload, headers=requestHeaders)

        return r

    def bunny_RetrieveVideoInLibrary(self, guid: str):
        requestHeaders = {
            "AccessKey": self.bunny_StreamLibrary_Key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        requestURL = f"https://video.bunnycdn.com/library/{self.bunny_StreamLibrary_ID}/videos/{guid}"

        r = requests.get(requestURL, headers=requestHeaders)
        return r.json()
