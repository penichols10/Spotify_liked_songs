import requests
import pandas as pd
import time

# SEARCHES FOR AN ARTIST
'''api_url = 'https://api.spotify.com/v1/search'
auth = 'Bearer BQDI7U-2QaLVOpcrtJlt0-hM5k-Fz2Ow2meqBH5W5VPtyVgO2unNo3qz65RYTsHWsw5XPr_7YHHaIQCiVdG7xDKPxhevws-rJLQ4xq52D8uWP6chWPh8vO1xTnNB8tZFyiXtJBxPMciB0T1MlDQb_QJq9TUryE_CJhJJn9LPXI0nWJKEDzRpwKD-q_I'

q = 'insomnium'
type_ = 'artist'

headers = {'Authorization': auth, 'Content-Type': 'application/json'}

req = requests.get(api_url+f'?q={q}&type={type_}', headers=headers)
print(req.json())'''

auth = 'Bearer BQBtaB64UR6KUpmvGu5j1KBeGeB-Itaf_u-GBTz5zRMoQ1uJWRFAXtfa5WyBnYusGbY7pq0BWihmw8BMyyxB7M1rB2N8AdT0o3QjIJ_HD4ElfgeZp1PbuK6l_q9W74NTGtdyYgVww8kRXuWMKloNno5-4v9H_S83laALcj_Qp6tKiA5p0PYBieCoPog'


def get_liked_songs(auth, offset):
    # Finds my playlists
    api_url =  'https://api.spotify.com/v1/me/tracks'

    headers = {'Content-Type': 'application/json', 'Authorization': auth}

    # This first request lets me get the total number of items
    req = requests.get(f'{api_url}?limit=50&offset={offset}', headers=headers) # 50 is the largest number of songs you can request
    print(req)
    req_json = req.json()['items']


    playlist_dict = {'id':[], 'track_name':[], 'artist':[], 'album_name':[], 'album_release_date':[], 'album_track_num': [], 'album_track_placement': [], 'genre':[], 'duration_ms':[], 'explicit':[], 'popularity':[]}
    for song in req_json:
        song = song['track']
        playlist_dict['id'].append(song['id'])
        playlist_dict['track_name'].append(song['name'])
        playlist_dict['artist'].append(song['artists'][0]['name']) # keep just the first artist
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
    api_url =  'https://api.spotify.com/v1/audio-features'

    headers = {'Content-Type': 'application/json', 'Authorization': auth}

    req_json = requests.get(f'{api_url}?ids={ids}', headers=headers).json()['audio_features']


    audio_feature_dict = {key:[] for key in req_json[0].keys()}
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


# Find number of liked songs
api_url =  'https://api.spotify.com/v1/me/tracks'

headers = {'Content-Type': 'application/json', 'Authorization': auth}

# This first request lets me get the total number of items
req = requests.get(api_url, headers=headers)
print(req)
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

df_audio_features = pd.DataFrame.from_dict(audio_feature_dict)
df_songs = pd.DataFrame.from_dict(playlist_dict)
df = df_songs.merge(df_audio_features, on='id')
print(df.head(), df.shape)

df.to_csv('liked_songs.csv')