import requests
import pandas as pd
import requests
import base64
import os
from dotenv import load_dotenv

def get_auth_token():
    '''
    Gets an authorization token with scope necessary to view my liked songs. Requires a login.

    '''
    load_dotenv()
    auth_url = 'https://accounts.spotify.com/authorize'
    token_url = 'https://accounts.spotify.com/api/token'

    client_id = os.environ.get('CLIENT_ID')
    client_secret = os.environ.get('CLIENT_SECRET')
    redirect_uri = 'https://open.spotify.com/'
    scope = 'user-library-read'

    # Get authorization code

    auth_arguments = {'client_id': client_id, 'response_type': 'code', 'redirect_uri': redirect_uri, 'scope': scope}

    auth_code = requests.get(auth_url, auth_arguments)

    auth_url = auth_code.url
    print(f'Authorization url: ', auth_url)
    print('Log in and input the authorization code:')
    auth_code = input()

    # Get token
    message = f'{client_id}:{client_secret}'
    message_bytes = message.encode('ascii')
    message_64 = base64.b64encode(message_bytes)
    message_64_str = message_64.decode('ascii')

    headers = {'Authorization': f'Basic {message_64_str}'}

    body = {'grant_type': 'authorization_code', 'code': auth_code, 'redirect_uri': redirect_uri}

    req = requests.post(url=token_url, headers=headers, data=body)
    print(f'Oath request: {req.json()}')

    # note this also returns a refresh token but at the moment no real benefit to using that
    token = req.json()['access_token']

    return token


def get_liked_songs(auth, offset):
    '''
    Retrieves a batch of song names and basic song information from my liked songs using
    the Spotify API.
    Parameters: auth, a token of appropriate scope to access my liked songs
                offset, the number of songs on the playlist to skip. Can think of this like
                pagination.
    Returns: playlist_dict, the song information in dictionary format
             ids, a string of the unique IDs for each song, to be used as inputs for another API
             call.
    '''
    # Finds my playlists
    api_url = 'https://api.spotify.com/v1/me/tracks'

    headers = {'Content-Type': 'application/json', 'Authorization': auth}

    # This first request lets me get the total number of items
    # 50 is the largest number of songs you can request
    req = requests.get(f'{api_url}?limit=50&offset={offset}', headers=headers)
    req_json = req.json()['items']

    playlist_dict = {'id': [], 'track_name': [], 'artist': [], 'album_name': [], 'album_release_date': [], \
        'album_track_num': [], 'album_track_placement': [], 'genre': [], 'duration_ms': [], 'explicit': [], 'popularity': []}
    for song in req_json:
        song = song['track']
        playlist_dict['id'].append(song['id'])
        playlist_dict['track_name'].append(song['name'])
        # keep just the first artist
        playlist_dict['artist'].append(song['artists'][0]['name'])
        playlist_dict['album_name'].append(song['album']['name'])
        playlist_dict['album_release_date'].append(song['album']['release_date'])
        playlist_dict['album_track_num'].append(song['track_number'])
        playlist_dict['album_track_placement'].append(song['track_number']/song['album']['total_tracks'])

        # Get genres if they have it. Despite the documentation, genres are often not returned
        if 'genres' in song['artists'][0].keys():
            playlist_dict['genre'].append(song['artists'][0]['genres'])
        else:
            playlist_dict['genre'].append('')
        playlist_dict['duration_ms'].append(song['duration_ms']/1000/60)
        playlist_dict['explicit'].append(song['explicit'])
        playlist_dict['popularity'].append(song['popularity'])

    ids = ','.join(playlist_dict['id'])
    return playlist_dict, ids


def get_features(ids, auth):
    '''
    Retrieves more detailed song information from the Spotify API for an arbitrary number of songs
    Parameters: ids, a comma separated string of unique song identifiers
                auth, a token needed to use the API.
    '''
    api_url = 'https://api.spotify.com/v1/audio-features'

    headers = {'Content-Type': 'application/json', 'Authorization': auth}

    req_json = requests.get(f'{api_url}?ids={ids}', headers=headers).json()[
        'audio_features']

    audio_feature_dict = {key: [] for key in req_json[0].keys()}
    for song in req_json:
        for key in song.keys():
            audio_feature_dict[key].append(song[key])

    # delete keys i don't need
    del audio_feature_dict['type']
    del audio_feature_dict['uri']
    del audio_feature_dict['track_href']
    del audio_feature_dict['analysis_url']
    del audio_feature_dict['duration_ms']

    return audio_feature_dict


auth = "Bearer " + get_auth_token()

api_url = 'https://api.spotify.com/v1/me/tracks'

headers = {'Content-Type': 'application/json', 'Authorization': auth}

# This first request lets me get the total number of items
req = requests.get(api_url, headers=headers)
num_liked = req.json()['total']

# Get all the songs
all_song_ids = []

playlist_dict, initial_ids = get_liked_songs(auth, 0)
audio_feature_dict = get_features(initial_ids, auth)
current_offset = 50

while current_offset <= num_liked:
    playlist_subset_dict, subset_ids = get_liked_songs(auth, current_offset)

    # Get info about the songs in the subset
    for key in playlist_dict.keys():
        playlist_dict[key].extend(playlist_subset_dict[key])

    # For each song, find its audio features
    subset_audio_features = get_features(subset_ids, auth)
    for key in audio_feature_dict.keys():
        audio_feature_dict[key].extend(subset_audio_features[key])

    current_offset += 50

# Save the song data using Pandas
df_audio_features = pd.DataFrame.from_dict(audio_feature_dict)
df_songs = pd.DataFrame.from_dict(playlist_dict)
df = df_songs.merge(df_audio_features, on='id')
print(df.head(), df.shape)

df.to_csv('liked_songs.csv')
