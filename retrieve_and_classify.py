import requests
import base64
from urllib.parse import quote_plus
import numpy as np
import pandas as pd
from scipy import stats
import pickle

def get_oath():
    '''
    Gets an OAth token using the Spotify API.
    '''
    client_id = '93934e50e4b64a5ba01175526a5430e5'
    client_secret = '048b5e6a364840ecb9a43ab17ef15f40'
    url = 'https://accounts.spotify.com/api/token'

    message = f'{client_id}:{client_secret}'
    message_bytes = message.encode('ascii')
    message_64 = base64.b64encode(message_bytes)
    message_64_str = message_64.decode('ascii')

    headers = {'Authorization': f'Basic {message_64_str}'}

    body = {'grant_type':'client_credentials'}


    req = requests.post(url=url, headers=headers, data=body)
    print(f'Oath request {req}')

    token = req.json()['access_token']
    return token

def get_track_info(song, oath_token, artist='', album=''):
    endpoint = 'https://api.spotify.com/v1/search'
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {oath_token}'}

    query_string = f'track:{song}'
    limit = 1
    return_type = 'track'

    # Add artist/track to query string if available
    if artist != '':
        artist = artist
        query_string += f' artist:{artist}'
    if album != '':
        album = album
        query_string += f' album:{album}'

    # Encode query string and type
    query_string = quote_plus(query_string)
    return_type = quote_plus(return_type)

    url = f'{endpoint}?q={query_string}&type={return_type}&limit={limit}'
    req = requests.get(url=url, headers=headers)
    print(f'Track info request {req}')

    if len(req.json()['tracks']['items']) > 0:
        return req.json()['tracks']['items'][0]
    else:return None

def parse_track_info(track_info):
    '''
    Gets useful info out of the JSON that the API search endpoint returns
    '''
    if track_info == None:
        print('No track info found')
        return None
    else:
        output_dict = {'id':[], 'track_name':[], 'artist':[], 'album_name':[], 'album_release_year':[], 'album_track_num': [], 'album_track_placement': [], 'duration_min':[], 'explicit':[], 'popularity':[]}
        output_dict['id'].append(track_info['id'])
        output_dict['track_name'].append(track_info['name'])
        output_dict['artist'].append(track_info['artists'][0]['name']) # keep just the first artist
        output_dict['album_name'].append(track_info['album']['name'])
        output_dict['album_release_year'].append(track_info['album']['release_date'].split('-')[0]) # extract year from date in YYYY-MM-DD format
        output_dict['album_track_num'].append(track_info['track_number'])
        output_dict['album_track_placement'].append(track_info['track_number']/track_info['album']['total_tracks'])
        output_dict['duration_min'].append(track_info['duration_ms']/1000/60)
        output_dict['explicit'].append(track_info['explicit'])
        output_dict['popularity'].append(track_info['popularity'])
        
        return output_dict

def get_track_audio_features(track_id, oath_token):
    '''
    Retrieves audio features for the track with the provided id
    '''
    api_url =  'https://api.spotify.com/v1/audio-features'

    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {oath_token}'}
    req = requests.get(f'{api_url}/{track_id}', headers=headers)
    print(f'Audio feature request {req}')
    audio_feature_dict = req.json()
    audio_feature_dict = {key:[value] for key, value in audio_feature_dict.items()}


    # delete unwanted keys
    del audio_feature_dict['type']
    del audio_feature_dict['uri']
    del audio_feature_dict['track_href']
    del audio_feature_dict['analysis_url']
    del audio_feature_dict['duration_ms']

    return audio_feature_dict

def get_track_info_features(song, oath_token, artist='', album=''):
    '''
    Gets the track information and audio features for a given song
    '''
    track_info = parse_track_info(get_track_info(song, oath_token, artist, album))
    audio_features = get_track_audio_features(track_info['id'][0], oath_token) # recall track_info values are lists
    track_info_features = audio_features | track_info

    return track_info_features


def classify_songs(songs):
    '''
    Takes in a dictionary of songs and their features
    Returns a dictionary with clusters or 'Outliers' as keys and songs as values
    '''
    numerical = ['album_track_num', 'album_track_placement', 'album_release_year', 'duration_min', 'popularity', 'danceability', 'energy', 'key', 'loudness', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo', 'time_signature']

    songs = pd.DataFrame.from_dict(songs)

    # Load Models
    pipeline = pickle.load(open('classification_pipeline.sav', 'rb'))
    trained_kmeans = pickle.load(open('trained_kmeans.sav', 'rb'))
    test_log_distances = pickle.load(open('test_log_distances.sav', 'rb'))

    cluster_dict = {1:[], 2:[], 3:[], 'Outliers':[]}
    song_audio_features = songs[numerical]

    # Predict_clusters
    y_pred = pipeline.predict(song_audio_features)

    # Find Z-scores
    # make an array of assigned cluster centers
    assigned_centers = trained_kmeans.cluster_centers_[y_pred - 1]
    scaled_songs = pipeline['scaler'].transform(song_audio_features)
    
    distances = np.linalg.norm(scaled_songs - assigned_centers, axis=1)
    new_log_distances = np.log(1+distances)
    log_distances = np.concatenate([test_log_distances, new_log_distances])
    distance_zscore = stats.zscore(log_distances)
    new_zscores = distance_zscore[-len(new_log_distances):]
    for i, song in enumerate(songs.values):

        if np.abs(new_zscores[i]) > 2:
            cluster_dict['Outliers'].append(song[13:16])
        else:
            cluster_dict[y_pred[i]].append(song[13:16])
    return cluster_dict

def retrieve_and_classify(song, artist='', album=''):
    oath_token = get_oath()
    track_info_features = get_track_info_features(song, oath_token, artist, album)

    cluster_dict = classify_songs(track_info_features)
    print(cluster_dict.keys())
    for key in cluster_dict.keys():
        if len(cluster_dict[key]) > 0:
            for song in cluster_dict[key]:
                track_name =  song[0]
                artist =  song[1]
                album_name = song[2]

                if key == 'Outliers':
                    print(f'Not sure why you like {track_name} by {artist} off of {album_name}.')
                elif key == 1:
                    print(f'You may like {track_name} by {artist} off of {album_name} because it is dark, aggressive, or heavy.')
                elif key == 2:
                    print(f'You may like {track_name} by {artist} off of {album_name} because it is melodic or upbeat.')
                elif key == 2:
                    print(f'You may like {track_name} by {artist} off of {album_name} because it is light, atmospheric, or classical.')

retrieve_and_classify('Down with the Sun', artist='Insomnium')