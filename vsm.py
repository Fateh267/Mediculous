from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
import numpy as np


def find_similar_files(directory_path, search_string, threshold=0.6):
    """
    This function searches for files in the given directory that have a similar string to the search string.
    The threshold parameter determines the minimum similarity ratio required for a file to be considered a match.
    """
    file_paths = []
    file_contents = []
    for filename in os.listdir(directory_path):
        filepath = os.path.join(directory_path, filename)
        if os.path.isfile(filepath):
            with open(filepath, "r") as file:
                file_content = file.read()
                file_paths.append(filename)
                file_contents.append(file_content)

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(file_contents)
    search_vector = vectorizer.transform([search_string])

    cosine_similarities = cosine_similarity(search_vector, tfidf_matrix).flatten()
    sorted_indices = np.argsort(cosine_similarities)[::-1]
    matches = [os.path.splitext(file_paths[index])[0] for index in sorted_indices if cosine_similarities[index] >= threshold]

    return matches[:5]

directory_path = "Corpus"
search_string = "heartburn"
threshold = 0.1

matches = find_similar_files(directory_path, search_string, threshold)

print(f"Found {len(matches)} matches: {matches}")
