# Introduction
In this project, I made a tool to compare songs on Spotify to songs that I have liked previously. First, I performed a K-Means clustering analysis on my liked songs. Second, I trained a linear support vector machine to classify songs, using the cluster assignments as labels. I then use a simple outlier detection method by converting log transformed distances to assigned cluster centers to Z-scores. 

The tool takes a new song, looks it up on Spotify using Spotify's API, retrieves basic information and audio features, classifies it using the support vector machine. The distance between the song and the centroid of the cluster associated with the class to which the song was assigned is calculated. If the distance is beyond a threshold, the song is considered an outlier. A message is printed about its cluster assignment.

NOTE: to the extent this remains a CLI tool, I've provided example inputs to keep my secret information secret. Creating Spotify apps is free, so feel free to put your own client ID and client secret in the retrieve_new_tracks.py file to confirm the app works.


# Contents
The repository contains the following:
### Related to Playlist Retrieval
* get_my_liked_songs.py - used to retrieve my liked songs

## Related to the notebook
* liked_spotify_songs.ipynb - notebook containing analysis of my liked songs on spotify
* liked_songs.csv - a csv file containing the data used for analysis
### Related to the classifier app
* main.py - a command line tool that asks users for information about songs, retrieves those songs from the Spotify API, and labels them either as part of a class or an outlier
* classifier_and_DistanceDictionary.py - contains a classifier class and data structure class used to simplify code for the new song classifier
* retrieve_new_tracks.py - code used to retrieve new songs from the Spotify API
* classification_pipeline.sav - used to classify new songs. Contains standard scaler, principal components analysis and a linear SVM. Trained on a subset of my liked songs.
* trained_kmeans.sav - clustering information for my liked songs
* iqr_based_thresholds.sav - stores distances from cluster centers, beyond which a song is considerd an outlier

# To Do
In the future, I may created some web front end for this.