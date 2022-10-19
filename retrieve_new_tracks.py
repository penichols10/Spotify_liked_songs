import requests
import base64
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv


def combine_dictionaries_with_same_keys(dict_to_update, new_dict):
    '''
    Combines two dictionaries, each having exactly the same keys.
    Parameters: dict_to_update, a dictionary to be updated with values from the second dictionary. May be empty.
                new_dict, a dictionary with values to be used to update dict_to_update.
    Returns: dict_to_update. If this was empty as an input, it will be returned identically to new_dict. Otherwise,
             it will contain keys mapped to lists of values from both of the input dictionaries.
    '''
    if dict_to_update == {}:
        dict_to_update = {key: [] for key in new_dict}
    for key in new_dict:
        dict_to_update[key].append(new_dict[key])
    return dict_to_update


def get_oath():
    '''
    Gets an OAth token using the Spotify API.
    Returns: token, the string OAth token
    '''
    load_dotenv()
    client_id = os.environ.get('CLIENT_ID')
    client_secret = os.environ.get('CLIENT_SECRET')
    url = 'https://accounts.spotify.com/api/token'

    message = f'{client_id}:{client_secret}'
    message_bytes = message.encode('ascii')
    message_64 = base64.b64encode(message_bytes)
    message_64_str = message_64.decode('ascii')

    headers = {'Authorization': f'Basic {message_64_str}'}

    body = {'grant_type': 'client_credentials'}

    req = requests.post(url=url, headers=headers, data=body)

    token = req.json()['access_token']
    return token


def get_track_info(song, oath_token, artist='', album=''):
    '''
    Gets basic information about a track, notably a unique identifier as well as some features like
    popularity, whether the track is explicit, etc.
    Parameters: song, string name of a song
                oath_token, string oath token
                artists, string artist name
                album, string album name
    Return: Either a dictionary with the information described above, or None if the track is not found.
    '''
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

    if len(req.json()['tracks']['items']) > 0:
        return req.json()['tracks']['items'][0]
    else:
        return None


def parse_track_info(track_info):
    '''
    Retrieves and modifies desired information returned by the search API endpoint.
    Parameters: track_info a dictionary containing basic information about a track.
    Returns: output_dict, a dictionary of desired information from the track_info input formatted for convenience.
    '''
    if track_info == None:
        return None
    else:
        output_dict = {'id': [], 'track_name': [], 'artist': [], 'album_name': [], 'album_release_year': [],\
             'album_track_num': [], 'album_track_placement': [], 'duration_min': [], 'explicit': [], 'popularity': []}
        output_dict['id'] = track_info['id']
        output_dict['track_name'] = track_info['name']
        # keep just the first artist
        output_dict['artist'] = track_info['artists'][0]['name']
        output_dict['album_name'] = track_info['album']['name']
        output_dict['album_release_year'] = track_info['album']['release_date'].split('-')[0]  # extract year from date in YYYY-MM-DD format
        output_dict['album_track_num'] = track_info['track_number']
        output_dict['album_track_placement'] = track_info['track_number'] / track_info['album']['total_tracks']
        output_dict['duration_min'] = track_info['duration_ms']/1000/60
        output_dict['explicit'] = int(track_info['explicit'])
        output_dict['popularity'] = track_info['popularity']

        return output_dict


def multiple_tracks_info(songs, artists=[], albums=[]):
    '''
    Gets the basic track information for multiple sons. This is essentially just a way to call
    get_track_info on multiple songs and have the information returned in a useful format.
    Parameters: songs, a list of string song names
                artists, a list of string artist names
                albums, a list of string album names
    Returns: track_info, a dictionary containing basic track information for multiple songs. Keys are strings, values are lists,
    '''
    oath_token = get_oath()
    tracks_info = {}
    for i, song in enumerate(songs):
        new_info = parse_track_info(get_track_info(song, oath_token, artists[i], albums[i]))
        if not new_info:
            print(f'Could not find the song {song} on Spotify')
        else:
            tracks_info = combine_dictionaries_with_same_keys(tracks_info, new_info)
    return tracks_info


def multiple_audio_features(track_info):
    '''
    Retrieves audio features for multiple tracks. Identifies each track using the 'id' key in the input
    track info.
    Parameters: track_info, a dictionary of basic track information for one or more tracks, notably containing the 'id' key,
                which maps to a list of string identifiers for songs.
    Returns: audio_feature_dict, a dictionary where each key is some audio feature (ex. loudness, valence), and each value
             is a list of values for each input song.
    '''
    oath_token = get_oath()

    # Retrieve the audio features
    api_url = 'https://api.spotify.com/v1/audio-features'
    headers = {'Content-Type': 'application/json',
               'Authorization': f'Bearer {oath_token}'}

    track_ids = ','.join(track_info['id'])
    req = requests.get(f'{api_url}?ids={track_ids}', headers=headers)
    print(f'Audio feature request {req}')
    audio_feature_json = req.json()['audio_features']

    # Store the audio features
    audio_feature_dict = {}
    for song in audio_feature_json:
        audio_feature_dict = combine_dictionaries_with_same_keys(audio_feature_dict, song)

    # delete unwanted keys
    del audio_feature_dict['type']
    del audio_feature_dict['uri']
    del audio_feature_dict['track_href']
    del audio_feature_dict['analysis_url']
    del audio_feature_dict['duration_ms']

    return audio_feature_dict


def multiple_audio_features_track_info(songs, artists=[], albums=[]):
    '''
    Finds both the basic track information and detailed audio features for multiple songs.
    Parameters: songs, a list of string song names
                artists, a list of string artist names
                albums, a list of string album names
    Returns: a combined dictionary of basic track info and audio features for multiple songs
    '''

    track_info = multiple_tracks_info(songs, artists=artists, albums=albums)
    if len(track_info.keys()) == 0:  # i.e. if no songs found, return None
        return None

    audio_features = multiple_audio_features(track_info)
    # Combine track info and audio featurs and return
    return track_info | audio_features
