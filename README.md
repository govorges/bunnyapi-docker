## bunnyapi-docker
This is a Docker image built for my OpenBroadcast project. It serves as a connection between other services and the Bunny CDN's Storage API. Typically, this should be deployed alongside other services with an appropriately configured `compose.yaml`.

## Important Notes
This, being a service built for interfacing with a video-focused CDN, is built with a primary focus on video files. It will also likely require some tinkering to get working with others' projects (I've tried to mitigate this as much as I can while maintaining functionality for my own purposes). To make this easier on you to implement in your own projects, I will detail below some likely roadblocks or annoyances you might run into:
- This service **DOES NOT INJEST FILE DATA**. Being a service not intended for use on the edge, **bunnyapi-docker** does not take file uploads. **Explanation:** the route `/files/upload (POST)` is passed the request headers `local-file-path` and `target-file-path`.
    - **local-file-path** is the absolute path to your file **within the container instance**. This is typically accessed through the volume mount configured in your `compose.yaml`.
    - **target-file-path** is the target path on your Bunny Storage Zone and includes the filename + extension.
    - Example: 
        - Header **local-file-path**: `/home/app/uploads/file.mp4`
        - Header **target-file-path**: `/uploadedvideos/file.mp4` 
        - **Result**: The file at `/home/app/uploads/file.mp4` or `/volume-mount/file.mp4` is uploaded to your Bunny Storage Zone at `https://storage.bunnycdn.com/[YOUR STORAGE ZONE]/uploadedvideos/file.mp4`

## Quick-Start Guide (For troubleshooting/debugging)
So, you've found yourself wanting to run the `bunnyapi-docker` service but don't want to set up an entire node worth of services to get going. Understandable. In this repository you'll find a very minimal `compose.yaml` to get started.

 1. Configure **keys.env** (for production use you may find value in a more secure key store). 
    - **BUNNY_STORAGEZONE_KEY** is the API key for the particular Bunny storage zone this service should operate within. 
    - **BUNNY_STORAGEZONE_NAME** is the name of the Storage Zone, for example, `openbroadcast-public`. This is used visually within Bunny itself but for our purposes it is used to construct an API endpoint URL for file operations.
    - **BUNNY_STORAGE_REGION** is the name of your Storage Region which can be found **[here](https://docs.bunny.net/reference/storage-api#storage-endpoints)**. Examples:
        - If you're using the **Falkenstein, DE** region, leave **BUNNY_STORAGE_REGION** empty or unset.
        - uk
        - ny
        - la
        - sg
        - se
        - br
        - jh
        - syd
    - **BUNNY_ACCOUNT_KEY** is the API key for your Bunny account itself. This is for a highly specific use case and will likely not be necessary for testing the proper operation of this service. Simply put, we use the account API key exclusively for purging the cache of newly uploaded files of the same name. This isn't ideal but is necessary for the smooth operation of our MRSS feeds.
 2. Configure **compose.yaml**
    - By design, uploaded files will be placed into a mounted volume. The volume mount's `source` can be anywhere you want, but this is typically a storage drive shared between services. 
 3. Run as needed
 
## Routes 

- ### /files/upload 
    - Method: **POST** 
        - Required Headers: 
            - **local_file_path** - The local path (in the container instance, where your volume mount is) to the file you want to upload.
            - **target_file_path** - The path on your Storage Zone you want the file to be uploaded to, including the filename and extension.
        - Optional Headers: **None**
        - Responses:
            - **400** - A header was not set or was set incorrectly.
            - **200** - Success (Upload was queued, not finished)
    - Method: **GET**
        - TODO
- ### /files/list
    - Method: **GET**
        - Required Headers: 
            - **path** - The directory on your Storage Zone you want to list the files of. This value defaults to `/videos/`
        - Optional Headers: **None**
        - Responses:
            - **400** - A header was not set or was set incorrectly.
            - **200** - Success - Returns a JSON array of dictionaries containing file metadata.

- ### /files/delete
    - Method: **DELETE**
        - Required Headers: 
            - **target-file-path** - The file path on your Storage Zone of the file you want deleted.
        - Optional Headers: **None**        
        - Responses:
            - **400** - A header was not set or was set incorrectly.
            - **200** - Success (Delete request was sent, but you will want to independently verify this)
- ### /files/retrieve_metadata
    - Method: **GET**
        - Required Headers:
            - **target-file-path** - The file path on your Storage Zone of the file you want to retrieve metadata for.
        - Optional Headers: **None**
        - Responses:
            - **400** - A header was not set or was set incorrectly.
            - **200** - Success - Returns a JSON dictionary file metadata
- ### /cache/purge
    - Method: **POST**
        - Required Headers:
            - **url** - The **PULL ZONE URL** you want to purge the cache of, not the Storage Zone URL of a file. This requires `BUNNY_ACCOUNT_KEY` to be set in your environment.
        - Optional Headers: **None**
        - Responses: 
            - **400** - A header was not set or was set incorrectly.
            - **200** - Success (Cached data for the URL has been purged)
        