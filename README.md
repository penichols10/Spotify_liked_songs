# Introduction
In this project, I made a tool to compare songs on Spotify to songs that I have liked previously. First, I performed a K-Means clustering analysis on my liked songs. Second, I trained a linear support vector machine to classify songs, using the cluster assignments as labels. I then use a simple outlier detection method by converting log transformed distances to assigned cluster centers to Z-scores. 

The tool takes a new song, looks it up on Spotify using Spotify's API, retrieves basic information and audio features, classifies it using the support vector machine and calculates a Z-score based on its distance to its assigned cluster. If the Z-score is above some threshold, a message is printed about it being an outlier, otherwise a message is printed about its cluster assignment.

# To Do
The logical next step is to build some sort of user interface (including anticipating user errors). While this would be nice to do, the main goal of the project was to work with the Spotify API, so this will likely remain a work in progress for a while. 

It would also be good to extend the tool to classify more than one song at a time.


# Contents
The repository contains the following
* liked_songs.csv - a csv file containing the data used for analysis
* get_my_liked_songs.py - used to retrieve my liked songs
* liked_spotify_songs.ipynb - notebook containing analysis
* retrieve_and_classify - contains code used to search for new songs and classify them in the manner described above
* classification_pipeline.sav - used to classify new songs. Contains standard scaler, principal components analysis and an SVM. Trained on a subset of my liked songs.
* trained_kmeans.sav - clustering information for my liked songs