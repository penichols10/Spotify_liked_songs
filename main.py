from classifier_and_DistanceDictionary import SongClassifier
from retrieve_new_tracks import multiple_audio_features_track_info
import numpy as np
import pickle
from dotenv import load_dotenv

def song_dict_to_str(song_dict, info_features):
    '''
    Converts artist, album and track names stored in dictionary format to a list of strings
    Parameters: song_dict, dictionary containing basic track information and audio features
                info_features, list of strings identifying album, artist, and track names
    returns: song_strings, a ilst of strings in the format "SONG_NAME by ARTIST_NAME off of the album ALBUM_NAME"
    '''
    songs_info = np.asarray([song_dict[feature] for feature in info_features])
    songs_info = np.rot90(songs_info)
    song_strings = []

    for song in songs_info:
        song_strings.append(
            f'{song[0]} by {song[1]} off of the album {song[2]}')

    return song_strings


def classify_and_print(songs, artists=[], albums=[], test_mode=False, test_inputs = {}):
    '''
    For a list of songs, classifies each or identifies it as an outlier, then prints the results to the console.
    Parameters: song, string name of a song
                artists, string artist name
                album, string album name 
    Returns: None
    '''
    clf = SongClassifier()
    info_features = ['track_name', 'artist', 'album_name']
    analysis_features = analysis_features = ['duration_min', 'danceability', 'key', 'energy', 'loudness',
                                             'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo', 'time_signature']

    # Test mode if .env unavailable
    if test_mode:
        song_dict = test_inputs
    else:
        song_dict = multiple_audio_features_track_info(songs, artists, albums)

    if song_dict == None:
        print('No songs found on Spotify.')
        return

    # Convert the analysis features for all songs to a numpy array
    song_analysis_features = [song_dict[feature]
                              for feature in analysis_features]
    song_analysis_features = np.asarray(song_analysis_features)
    song_analysis_features = np.rot90(song_analysis_features)

    # Predictions
    predictions = clf.predict(song_analysis_features)

    # Get artist and album information into more useful format
    songs_info = song_dict_to_str(song_dict, info_features)

    # Text output
    # returns in order [small, medium, large]
    clusters_sorted_by_size = clf.get_clusters_by_size()

    for i, label in enumerate(predictions):
        if label == clusters_sorted_by_size[0]:
            print(f'{songs_info[i]} is probably quiet or low energy. It may be ambient, deone, classical or contain acoustic instruments.')
        elif label == clusters_sorted_by_size[1]:
            print(f'{songs_info[i]} is probably high energy. It may be long or dark.')
        elif label == clusters_sorted_by_size[2]:
            print(f'{songs_info[i]} is probably high energy. It may be upbeat or rhythmically driven.')
        else:
            print(f'{songs_info[i]} is unlike your usual taste in music.')
    return


def get_song_from_input():
    songs = []
    artists = []
    albums = []
    print('Please follow the input instructions')
    print('Press Enter to skip an input. Note song names are mandatory.')
    print('Type Done() to quit')
    while True:
        # Require a song name input
        song_input = ''
        song_input_fail = False
        while len(song_input) == 0:
            if song_input_fail:
                print('You must enter a song name')
            song_input = input('Song Name: ')
            song_input_fail = True
        songs.append(song_input)
        artists.append(input('Artist Name: '))
        albums.append(input('Album Name: '))
        continue_input = input('Do you want to enter more songs? [y/n]: ')
        # Allow user to add more songs or break loop
        if continue_input.lower() == 'n':
            break

    return songs, artists, albums


# Example inputs



def main():
    # Test inputs for is .env available
    # songs = ['Down with the Sun', 'Return to Forever', 'Doom\'s Bride', 'Neverita', 'fakesong', 'Heliopolis', 'Amanaemonesia', 'Only Time', 'Iron Age']
    # artists = ['Insomnium', 'Romantic Warrior', 'Warhorse', 'Bad Bunny', 'fakeartist', 'Nite', '', 'Enya', 'Ka']
    # albums = ['', '', '', '', "", '', '',  'A Day Without Rain', '']

    # Loads example inputs if .env unavalable
    if not load_dotenv():
        songs, artists, albums = get_song_from_input()
        classify_and_print(songs, artists, albums)
    else:
        print('Information necessary for API authentication unavailable, reverting to example inputs.')
        song_dict = pickle.load( open('no_dotenv_test_input.sav', 'rb'))
        classify_and_print(songs, artists, albums, test_mode=True, test_inputs=song_dict)


if __name__ == "__main__":
    

    main()
