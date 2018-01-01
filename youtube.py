import sys
import httplib2
from youtube_config import *
from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow

# Creates the resource object for interacting with the YouTube API
# Sets up OAuth 2.0 for authorized requests if necessary
def create_resource_object(id, username, arguments):
    global youtube

    if (id or username):
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
            developerKey=DEVELOPER_KEY)
    else:
        flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
            message=MISSING_CLIENT_SECRETS_MESSAGE,
            scope=YOUTUBE_READONLY_SCOPE)

        storage = Storage("%s-oauth2.json" % sys.argv[0])
        credentials = storage.get()

        if credentials is None or credentials.invalid:
            credentials = run_flow(flow, storage, arguments)
        elif credentials.access_token_expired:
            credentials.refresh(httplib2.Http())

        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
            http=credentials.authorize(httplib2.Http()))

    return youtube

# Creates a request for the user's playlists using their channel ID
def create_id_request(id):
    return youtube.playlists().list(
        part="id,snippet",
        fields="items(id,snippet/title),nextPageToken",
        channelId=id,
        maxResults=PLAYLIST_SEARCH_MAX_RESULTS
    )

# Creates a request for the user's playlists using their username
# First uses a channel request to obtain channel ID from username
def create_username_request(username):
    channel_request = youtube.channels().list(
        part="id",
        forUsername=username,
        maxResults=PLAYLIST_SEARCH_MAX_RESULTS
    )

    channel_response = channel_request.execute()

    try:
        return youtube.playlists().list(
            part="id,snippet",
            fields="items(id,snippet/title),nextPageToken",
            channelId=channel_response["items"][0]["id"],
            maxResults=PLAYLIST_SEARCH_MAX_RESULTS
        )
    except IndexError:
        sys.exit("No channel found for {}".format(username))

# Creates an authenticated request for accessing the user's private playlists
def create_private_request():
    return youtube.playlists().list(
        part="id,snippet",
        fields="items(id,snippet/title),nextPageToken",
        mine="true",
        maxResults=PLAYLIST_SEARCH_MAX_RESULTS
    )

# Creates a channel request necessary for obtaining the channel's
# related playlists, via channel ID
def create_id_channel_request(id):
    return youtube.channels().list(
        part="contentDetails",
        fields="items(contentDetails/relatedPlaylists)",
        id=id
    )

# Creates a channel request necessary for obtaining the channel's
# related playlists, via username
def create_username_channel_request(username):
    return youtube.channels().list(
        part="contentDetails",
        fields="items(contentDetails/relatedPlaylists)",
        forUsername=username
    )

# Creates a channel request necessary for obtaining the channel's
# related playlists, via authentication
def create_private_channel_request():
    return youtube.channels().list(
        part="contentDetails",
        fields="items(contentDetails/relatedPlaylists)",
        mine="true"
    )

# Create request for obtaining the user's related playlists
def create_related_request(channel_request):
    playlist_id_list = []

    channel_response = channel_request.execute()

    # Traverse channel_response to create list of related playlist IDs
    for channel in channel_response["items"]:
        for playlist, playlist_id in channel["contentDetails"]["relatedPlaylists"].items():
            playlist_id_list.append(playlist_id)

    return youtube.playlists().list(
        part="id,snippet",
        fields="items(id,snippet/title),nextPageToken",
        id=",".join(playlist_id_list),
        maxResults=PLAYLIST_SEARCH_MAX_RESULTS
    )

def create_playlist_items_request(playlist_id):
    return youtube.playlistItems().list(
        part="snippet,status",
        fields="items(snippet/title,snippet/resourceId/videoId,status),nextPageToken",
        playlistId=playlist_id,
        maxResults=VIDEO_SEARCH_MAX_RESULTS
   )

def create_video_search_request(video_title):
    return youtube.search().list(
        part="id,snippet",
        fields="items(id/videoId,snippet/title)",
        q=video_title,
        type="video",
        maxResults=VIDEO_SEARCH_MAX_RESULTS
    )

def create_playlist_items_insert_request(playlist_id, position, new_video_id):
    return youtube.playlistItems().insert(
       part="contentDetails,id,snippet",
       body={
           "kind": "youtube#playlistItem",
           "snippet": {
               "playlistId": playlist_id,
               "position": position,
               "resourceId": new_video_id,
           }
       }
   )

def create_next_page_request(resource_type, request, response):
   if resource_type == "playlist":
       return youtube.playlists().list_next(request, response)
   elif resource_type == "playlistItem":
       return youtube.playlistItems().list_next(request, response)
   else:
       raise ValueError("Expected resource_type \"playlist\" or \"playlistItem\"")

def create_video_list_request(id):
    return youtube.videos().list(
        part="contentDetails,snippet",
        fields="items(contentDetails/regionRestriction,snippet/title)",
        id=id
    )
