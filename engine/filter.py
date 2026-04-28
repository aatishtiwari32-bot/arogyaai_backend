import re
from nltk.stem import PorterStemmer
ps = PorterStemmer()
stop_words = set([
    "i", "have", "is", "am", "are", "the", "a", "an", "and", "or",
    "to", "of", "in", "on", "for", "with", "my", "me", "he", "she", "there", "because", "that", "having", "while", "around", "experiencing"
])

def preprocess(text: str):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)   
    words = text.split()
    processed = [ps.stem(word) for word in words if word not in stop_words]
    return processed    
    