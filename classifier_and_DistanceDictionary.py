import pickle
import numpy as np


class DistanceDictionary:
    def __init__(self, n_clusters):
        self.distances = {key: [] for key in range(1, n_clusters+1)}
        self.indices = {key: [] for key in range(1, n_clusters+1)}
        self.cluster_or_outlier = {key: [] for key in range(1, n_clusters+1)}
        self.keys = [key for key in self.distances]
        self.sorted_distances = []
        self.sorted_labels = []

    def append(self, cluster_label, distance_index_tuple):
        self.distances[cluster_label].append(distance_index_tuple[0])
        self.indices[cluster_label].append(distance_index_tuple[1])

    def update_cluster_distances(self, cluster_label, cluster_center):
        if len(self.distances[cluster_label]) > 0:
            self.distances[cluster_label] = np.linalg.norm(
                self.distances[cluster_label] - cluster_center, axis=1)
        return self.distances[cluster_label]

    def update_distances(self, cluster_centers):
        self.distances = {key: self.update_cluster_distances(
            key, cluster_centers[key-1]) for key in self.distances}

    def sort_distances_labels(self):
        all_distances = []
        all_indices = []
        cluster_labels = []
        for key in self.distances:
            all_distances.extend(self.distances[key])
            all_indices.extend(self.indices[key])
            cluster_labels.extend([key]*len(self.distances[key]))

        sorted_by_index = sorted(
            zip(all_distances, cluster_labels, all_indices), key=lambda x: x[2])
        self.sorted_distances = [dist_label_idx_tup[0] for dist_label_idx_tup in sorted_by_index]
        self.sorted_labels = [dist_label_idx_tup[1] for dist_label_idx_tup in sorted_by_index]
        return self.sorted_distances, self.sorted_labels

    def __iter__(self):
        for i, distance in self.distances:
            yield distance, self.indices[i]

    def __repr__(self):
        return f'Distances {self.distances}; Indices {self.indices}'


class SongClassifier:
    '''Class for classifying songs'''

    def __init__(self):
        self.pipeline = pickle.load(open('classification_pipeline.sav', 'rb'))
        self.StandardScaler = self.pipeline[0]
        self.kmeans = pickle.load(open('trained_kmeans.sav', 'rb'))
        self.thresholds = pickle.load(open('thresholds.sav', 'rb'))

        self.kmeans_labels = self.kmeans.labels_
        self.cluster_centers = self.kmeans.cluster_centers_
        self.distances = DistanceDictionary(len(set(self.kmeans_labels)))
        self.clusters_sorted_by_size = self.get_clusters_by_size()
        self.cluster_assignments = []

    def predict(self, songs):
        self.cluster_assignments = self.pipeline.predict(songs)
        self.calculate_distances(songs)
        sorted_distances, sorted_labels = self.distances.sort_distances_labels()

        label_or_outlier = []
        for i, distance in enumerate(sorted_distances):
            # Find appropriate threshold given cluster label
            label = sorted_labels[i]
            for i, cluster in enumerate(self.clusters_sorted_by_size):
                if label == cluster:
                    threshold = self.thresholds[i]
                    break
            # Label outliers
            if distance > threshold:
                label_or_outlier.append('Outlier')
            else:
                label_or_outlier.append(label)
        return label_or_outlier

    def calculate_distances(self, songs):
        scaled_songs = self.StandardScaler.transform(songs)
        for i, song in enumerate(scaled_songs):
            self.distances.append(self.cluster_assignments[i], (song, i))

        self.distances.update_distances(self.cluster_centers)
        return self.distances

    def get_clusters_by_size(self):
        '''
        Identifies the labels associated with the smallest, medium size, and largest cluster, assuming k=3.
        Returns: sorted_labels, a list of ints, each a cluster label, sorted by smallest to largest cluster
        '''
        # Find clusters in a way that can identify the smallest, largest, and middle sized one across different runx of the notebook
        dummy_labels = [i for i in range(1, len(self.kmeans_labels)+1)]
        cluster_sizes = [sum(self.kmeans_labels == i) for i in range(max(self.kmeans_labels)+1)]
        sorted_zip = sorted(zip(dummy_labels, cluster_sizes), key=lambda x: x[1])
        sorted_labels = [x[0] for x in sorted_zip]
        return sorted_labels
