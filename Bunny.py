import requests
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

        self.uploadreached = False

        if not self.bunny_ConnectionAlive():
            raise SystemError("Bunny connection has failed! (NOT AUTH RELATED)")

    def bunny_ConnectionAlive(self):
        requestURL = "https://api.bunny.net/region"
        r = requests.get(requestURL)

        if r.status_code == 200:
            return True
        else:
            return False

    def bunny_UploadFile(self, local_file_path, target_file_path, content_type):
        requestHeaders = {
            "AccessKey": self.bunny_StorageZone_API_Key,
            "Content-Type": content_type,
            "accept": "application/json",
        }
        requestURL = self.bunny_StorageZoneEndpoint + target_file_path
        
        requests.put(requestURL, data=open(local_file_path, "rb"), headers=requestHeaders)
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
        requestURL = self.bunny_StorageZoneEndpoint + target_file_path

        requests.delete(requestURL, headers=requestHeaders)

    def bunny_PurgeLinkCache(self, url):
        requestHeaders = {
            "AccessKey": self.bunny_Account_API_Key
        }
        requestURL = f"https://api.bunny.net/purge?url={url}"            
        requests.post(requestURL, headers=requestHeaders)
    
    def bunny_GetFileData(self, target_file_path):
        folderData = self.bunny_ListFiles(target_file_path.rsplit("/", 1)[0])
        for item in folderData:
            if item["ObjectName"] == target_file_path.rsplit('/', 1)[-1]:
                fileData = item
                break

        return fileData