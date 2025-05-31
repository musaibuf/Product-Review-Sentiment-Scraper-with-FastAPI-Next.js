from textblob import TextBlob

def get_sentiment(text: str):
    """
    Analyzes text and returns sentiment label and score.
    """
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity # Score between -1 (negative) and 1 (positive)

    # You can adjust these thresholds
    if polarity > 0.05:  # Consider slightly positive as Positive
        label = "Positive"
    elif polarity < -0.05: # Consider slightly negative as Negative
        label = "Negative"
    else:
        label = "Neutral" # Close to zero
        
    return label, polarity