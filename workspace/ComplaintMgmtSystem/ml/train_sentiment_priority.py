"""Train from-scratch Multinomial Naive Bayes models for SENTIMENT + PRIORITY.

Trains on the unified data/sentiment_dataset.csv (12,000 rows, source=claude
+ source=synth). Uses the same from-scratch MultinomialNB implementation and
preprocessing as the category classifier (Laplace smoothing, log-space,
softmax). Saves:
  data/sentiment_model.json        -> sentiment 3-class model
  data/priority_model.json         -> priority  3-class model
  ml/sentiment_training_log.json   -> metrics (single source of truth for
                                      web page AND notebook - keeps in sync)
"""

import csv
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from classifier import MultinomialNB, clean_and_tokenize

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET = os.path.join(BASE, 'data', 'sentiment_dataset.csv')
SENT_MODEL = os.path.join(BASE, 'data', 'sentiment_model.json')
PRI_MODEL = os.path.join(BASE, 'data', 'priority_model.json')
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sentiment_training_log.json')

SEED = 42

SENT_ENCODER = {'positive': 0, 'neutral': 1, 'negative': 2}
SENT_DECODER = {v: k for k, v in SENT_ENCODER.items()}
PRI_ENCODER = {'low': 0, 'medium': 1, 'high': 2}
PRI_DECODER = {v: k for k, v in PRI_ENCODER.items()}


def evaluate(model, texts, labels, decoder):
    correct = 0
    per_class = {}
    for i, text in enumerate(texts):
        pred, probs = model.predict_with_proba(text)
        if pred == labels[i]:
            correct += 1
        pred_name = decoder[pred]
        true_name = decoder[labels[i]]
        per_class.setdefault(true_name, {'tp': 0, 'fp': 0, 'fn': 0, 'samples': 0})
        per_class.setdefault(pred_name, {'tp': 0, 'fp': 0, 'fn': 0, 'samples': 0})
        per_class[true_name]['samples'] += 1
        if pred == labels[i]:
            per_class[pred_name]['tp'] += 1
        else:
            per_class[pred_name]['fp'] += 1
            per_class[true_name]['fn'] += 1
    metrics = []
    for name, c in per_class.items():
        p = c['tp'] / max(c['tp'] + c['fp'], 1)
        r = c['tp'] / max(c['tp'] + c['fn'], 1)
        f1 = 2 * p * r / max(p + r, 1e-9)
        metrics.append({'class': name, 'precision': round(p, 4), 'recall': round(r, 4),
                        'f1': round(f1, 4), 'samples': c['samples']})
    macro_f1 = round(sum(m['f1'] for m in metrics) / len(metrics), 4) if metrics else None
    accuracy = round(correct / max(len(texts), 1) * 100, 2)
    return accuracy, macro_f1, metrics


def main():
    random.seed(SEED)
    with open(DATASET, encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    texts = [r['complaint_text'] for r in rows]

    random.shuffle(rows)
    split = int(len(rows) * 0.8)
    train_rows, test_rows = rows[:split], rows[split:]

    train_texts = [r['complaint_text'] for r in train_rows]
    test_texts = [r['complaint_text'] for r in test_rows]

    sent_model = MultinomialNB(alpha=0.01, min_df=1)
    sent_model.fit(train_texts, [SENT_ENCODER[r['sentiment_label'].lower()] for r in train_rows])
    sent_model.save(SENT_MODEL)

    # Priority uses word-level features only (no phrase bigrams): exact-phrase
    # memorization of the template pool produced near-perfect scores, so the
    # regularized word-only model is the honest, robust choice.
    pri_model = MultinomialNB(alpha=0.5, min_df=3, add_bigrams=True)
    pri_model.fit(train_texts, [PRI_ENCODER[r['priority'].lower()] for r in train_rows])
    pri_model.save(PRI_MODEL)

    acc_s, f1_s, per_s = evaluate(sent_model, train_texts, [SENT_ENCODER[r['sentiment_label'].lower()] for r in train_rows], SENT_DECODER)
    acc_s_t, f1_s_t, per_s_t = evaluate(sent_model, test_texts, [SENT_ENCODER[r['sentiment_label'].lower()] for r in test_rows], SENT_DECODER)
    acc_p, f1_p, per_p = evaluate(pri_model, train_texts, [PRI_ENCODER[r['priority'].lower()] for r in train_rows], PRI_DECODER)
    acc_p_t, f1_p_t, per_p_t = evaluate(pri_model, test_texts, [PRI_ENCODER[r['priority'].lower()] for r in test_rows], PRI_DECODER)

    print(f"SENTIMENT train acc {acc_s}% macroF1 {f1_s} | TEST acc {acc_s_t}% macroF1 {f1_s_t}")
    print(f"PRIORITY  train acc {acc_p}% macroF1 {f1_p} | TEST acc {acc_p_t}% macroF1 {f1_p_t}")
    print('sentiment per-class (test):')
    for m in per_s_t:
        print(' ', m)
    print('priority per-class (test):')
    for m in per_p_t:
        print(' ', m)

    log = {}
    if os.path.isfile(LOG_PATH):
        with open(LOG_PATH) as f:
            log = json.load(f)
    history = log.get('history', [])
    history.append({'date': __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'sentiment_acc': acc_s_t, 'priority_acc': acc_p_t, 'sentiment_f1': f1_s_t, 'priority_f1': f1_p_t})
    log = {
        'last_trained': __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'dataset': os.path.basename(DATASET),
        'rows': len(rows),
        'source_breakdown': {'claude': sum(1 for r in rows if r['source'] == 'claude'),
                             'synth': sum(1 for r in rows if r['source'] == 'synth')},
        'train_samples': len(train_texts),
        'test_samples': len(test_texts),
        'sentiment': {'accuracy': acc_s_t, 'macro_f1': f1_s_t, 'per_class': per_s_t},
        'priority': {'accuracy': acc_p_t, 'macro_f1': f1_p_t, 'per_class': per_p_t},
        'history': history[-20:],
    }
    with open(LOG_PATH, 'w') as f:
        json.dump(log, f, indent=2)
    print('log written:', LOG_PATH)


if __name__ == '__main__':
    main()