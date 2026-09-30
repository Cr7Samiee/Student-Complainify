import env

# ML priority is used when its confidence is at least this high.
ML_CONFIDENCE = 0.55

# Deterministic ground-truth vocabulary (mirror of
# generate_sentiment_priority_data.py assign_priority): a negative-text is
# 'High' only when one of these markers appears anywhere in the sentence.
HIGH_HINTS = (
    'remains completely unavailable', 'has never been repaired',
    'stopped working again', 'is out of order since morning',
    'nothing has been done yet', 'no one from the office follows up',
    'students have already reported it',
    'this is a serious problem', 'it can no longer be ignored',
    'warning signs were clear',
    'emergency', 'danger', 'unsafe', 'stale', 'unhygienic', 'harass',
    'theft', 'leak', 'no water', 'life threatening', 'injury',
)

# Neutral texts carrying a deadline/window/timeline/form/schedule noun are
# 'Medium'; everything else neutral is 'Low'.
NEU_MEDIUM_HINTS = ('deadline', 'window', 'timeline', 'form', 'schedule')


def compute_priority_rules(text, sentiment_label, sentiment_score, anomaly=None):
    """Mirror of the dataset's deterministic ground-truth rule.

    Priority is a text-only function: positive -> Low; negative -> High when
    a high-risk marker appears, otherwise Medium; neutral -> Medium when a
    deadline/window/timeline/form/schedule noun appears, otherwise Low.

    Returns (priority, score, reason). score keeps the same scale as the ML
    path (High = 3, Medium = 2, Low = 0).
    """
    low = ' ' + text.lower() + ' '
    if anomaly and anomaly.get('is_anomaly'):
        return 'High', 3, 'flagged as anomalous'
    if sentiment_label == 'Positive':
        return 'Low', 0, 'positive tone'
    if sentiment_label == 'Negative':
        if any(h in low for h in HIGH_HINTS):
            return 'High', 3, 'high-risk marker detected'
        return 'Medium', 2, 'strong complaint without high-risk marker'
    if any(m in low for m in NEU_MEDIUM_HINTS):
        return 'Medium', 2, 'deadline/window/timeline/schedule marker'
    return 'Low', 0, 'neutral baseline'


# Representative weighted score for each ML priority class, so the app's
# score field keeps the same meaning as the rules (High >= 3, Medium 1-2, Low <= 0).
_ML_SCORE = {'High': 3, 'Medium': 2, 'Low': 0}


def compute_priority(text, sentiment_label, sentiment_score, anomaly=None):
    """Trained-model-first priority engine.

    Consults the Multinomial NB priority model (data/priority_model.json)
    when its confidence is >= ML_CONFIDENCE; falls back to the weighted
    rules otherwise. Anomaly-flagged complaints always go through the rules
    so the manual-review boost is never lost.

    Returns (priority, score, reason).
    """
    if not (anomaly and anomaly.get('is_anomaly')):
        ml = env.ml_priority(text)
        if ml and ml['confidence'] >= ML_CONFIDENCE:
            return (ml['priority'], _ML_SCORE[ml['priority']],
                    f'Multinomial NB model (confidence {ml["confidence"]*100:.0f}%)')

    return compute_priority_rules(text, sentiment_label, sentiment_score, anomaly)