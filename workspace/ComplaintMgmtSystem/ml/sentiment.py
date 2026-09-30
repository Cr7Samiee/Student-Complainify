import re

import env

_APPRECIATION = re.compile(
    r'\b(thank|appreciate|grateful|excellent|wonderful|amazing|great|'
    r'fixed|resolved|solved|helpful|happy|satisfied|delighted|impressed)\b',
    re.IGNORECASE
)

_NEG_PATTERNS = re.compile(
    r'\b(not\s+work(?:ing)?|doesn.?t\s+work|dont\s+work|wont\s+work|'
    r'not\s+function(?:ing)?|stole|theft|robbery|harass\w*|'
    r'no\s+(?:response|reply|action|update)|'
    r'no\s+one\s+(?:listens|cares|responds)|'
    r'nobody\s+(?:listens|cares|responds)|'
    r'never\s+(?:fixed|resolved|addressed|solved)|'
    r'nothing\s+(?:done|works?|happens)|'
    r'stale|spoiled|rotten|foul|smelly|infest\w*|'
    r'leak(?:ing|s|ed)?|broken|crack(?:ed)?|dirty|filthy|malfunction\w*|'
    r'overcharg\w*|rude|unsafe|cheat\w*|unhygienic|abuse|threaten\w*|'
    r'refus\w*|ignor\w*|delay(?:s|ed)?|terribl\w*|frustrat\w*|awful|'
    r'horribl\w*|disgust\w*|worst|bad(?!ly)?\b)\b',
    re.IGNORECASE
)

# Strong negative language -> clearly frustrated, not just a mild complaint.
# Mirror of the dataset generator's STRONG_NEG pool (v6 convention): the
# sentiment/priority ground truth labels every text containing one of these
# phrases as 'negative', everything milder is 'neutral'.
_STRONG_NEG = re.compile(
    r'\b(stol\w*|steal\w*|theft|robbery|harass\w*|abuse|threaten\w*|assault|'
    r'unsafe|unhygienic|filthy|rotten|stale|spoiled|foul|smelly|infest\w*|'
    r'disgust\w*|terribl\w*|horribl\w*|awful|broken|crack(?:ed)?|'
    r'leak(?:ing|s|ed)?|malfunction\w*|not\s+work(?:ing)?|not\s+fixed|'
    r'never\s+fixed|no\s+(?:response|reply|action|update)|'
    r'no\s+one\s+(?:responds|listens|cares)|nobody\s+(?:responds|listens|cares)|'
    r'ignored|ignor\w*|refus\w*|overcharg\w*|rude|delay(?:s|ed)?|serious|'
    r'emergency|danger\w*|damag\w*|unresolved|fight\w*|insult\w*|cheat\w*|'
    r'molest\w*)\b',
    re.IGNORECASE
)

# Polite informational requests ("please share the syllabus", "how can I.") -
# these are not appreciation, force to Neutral instead of Positive.
_REQUEST = re.compile(
    r'\b(?:please|kindly|pls)\s+(?:share|send|provide|give|inform|update|forward|'
    r'attach|tell|arrange|schedule|check|confirm|review|consider)\b|'
    r'\bhow\s+(?:do|can|should)\s+[a-z]|'
    r'\b(?:can|could)\s+(?:you|u)\s+please|'
    r'\bi\s+(?:want|need|would\s+like)\b',
    re.IGNORECASE
)


# Mild problem-report words: not strong enough for 'negative', but enough to
# veto an absurd 'positive' verdict ("The bus was late again" is not Positive).
_MILD_NEG = re.compile(
    r'\b(late|issue|problem\w*|not\s+getting|not\s+available|non-functional|'
    r'unavailable|outdated|missing|no\s+proper|hasn.?t\b|haven.?t\b|'
    r'not\s+been|slow|long|wait\w*|takes?\s+too\s+long)\b',
    re.IGNORECASE
)


def _sub_label(score):
    if score <= -0.5:
        return 'Angry / Frustrated'
    if score <= -0.05:
        return 'Dissatisfied'
    if score >= 0.5:
        return 'Appreciative'
    if score >= 0.05:
        return 'Satisfied'
    return 'Informational'


def analyze_sentiment_rules(text):
    """From-scratch pattern-based sentiment (no external lexicon/VADER).

    Same output schema as analyze_sentiment(); used as the fallback when the
    trained model is unavailable or unconfident, and as the honest baseline
    in the study notebooks.
    """
    if _STRONG_NEG.search(text):
        label, score = 'Negative', -0.7
    elif _APPRECIATION.search(text) and not _NEG_PATTERNS.search(text):
        label, score = 'Positive', 0.7
    elif _REQUEST.search(text) and not _APPRECIATION.search(text):
        label, score = 'Neutral', 0.0
    elif _NEG_PATTERNS.search(text):
        label, score = 'Neutral', -0.15
    else:
        label, score = 'Neutral', 0.0

    return {
        'label': label,
        'sub_label': _sub_label(score),
        'score': score,
        'neg_words': 0,
        'pos_words': 0,
        'total_sentiment_words': 0,
        'negations': 0,
        'model': 'rule_based',
        'ml_confidence': None,
    }


def analyze_sentiment(text):
    # Unambiguous strong complaint language wins over the model: the NB model
    # is trained on synthetic data and can miss real-world phrasing
    # ("wifi broken, nobody responds" -> model guessed Positive).
    if _STRONG_NEG.search(text):
        return analyze_sentiment_rules(text)

    ml = env.ml_sentiment(text)
    if ml and ml['confidence'] >= 0.45 and not (
            ml['label'] == 'Positive'
            and (_NEG_PATTERNS.search(text) or _MILD_NEG.search(text))):
        # Dataset convention: 'negative' requires STRONG complaint language
        # (ml/generate_sentiment_priority_data.py STRONG_NEG). Mild reports
        # ("water not getting on time, Wi-Fi issue") are neutral — urgency is
        # handled by the priority model, not sentiment.
        if ml['label'] == 'Negative' and not _STRONG_NEG.search(text):
            return analyze_sentiment_rules(text)
        # Continuous score from class probabilities: pos=+1, neu=0, neg=-1.
        label = ml['label']
        return {
            'label': label,
            'sub_label': _sub_label(ml['score']),
            'score': round(ml['score'], 3),
            'neg_words': 0,
            'pos_words': 0,
            'total_sentiment_words': 0,
            'negations': 0,
            'model': 'multinomial_nb',
            'ml_confidence': ml['confidence'],
        }

    return analyze_sentiment_rules(text)


def sentiment_priority_boost(sentiment_label, current_priority):
    boosts = {
        'Negative': {'Low': 'Medium', 'Medium': 'High', 'High': 'High'},
        'Neutral': {'Low': 'Low', 'Medium': 'Medium', 'High': 'High'},
        'Positive': {'Low': 'Low', 'Medium': 'Medium', 'High': 'High'},
    }
    return boosts.get(sentiment_label, {}).get(current_priority, current_priority)
