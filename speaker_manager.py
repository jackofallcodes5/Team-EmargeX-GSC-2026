import numpy as np
from scipy.spatial.distance import cosine

class SpeakerManager:
    def __init__(self, threshold=0.8):
        """
        threshold: Cosine similarity threshold to consider vectors from the same speaker.
        (Higher = stricter, common range 0.7 - 0.9)
        """
        self.speakers = {}  # Map index to average vector
        self.threshold = threshold

    def get_speaker_label(self, new_vector):
        """Compare new vector with known speaker vectors."""
        if not new_vector:
            return "Unknown"

        new_vector = np.array(new_vector)
        
        best_match = None
        best_score = -1

        for label, avg_vector in self.speakers.items():
            # Cosine similarity is 1 - cosine distance
            score = 1 - cosine(new_vector, avg_vector)
            if score > best_score:
                best_score = score
                best_match = label

        if best_match is not None and best_score >= self.threshold:
            # Update the speaker's average vector with the new observation (running average)
            self.speakers[best_match] = (self.speakers[best_match] + new_vector) / 2
            return f"Speaker {best_match}"
        else:
            # Create a new speaker
            new_id = len(self.speakers) + 1
            self.speakers[new_id] = new_vector
            print(f"\n[System] New Speaker Detected: {new_id}")
            return f"Speaker {new_id}"
