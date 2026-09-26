import csv, re, json, os, math
from collections import Counter, defaultdict

CONFIDENCE_THRESHOLD = 0.35
AUTO_THRESHOLD = 0.90
SUGGEST_THRESHOLD = 0.60
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE, 'data', 'train_dataset.csv')
TEST_PATH = os.path.join(BASE, 'data', 'test_dataset.csv')
ENC_PATH = os.path.join(BASE, 'data', 'encoders', 'category_decoder.json')

with open(ENC_PATH) as f:
    CAT_DECODER = {int(k): v for k, v in json.load(f).items()}

STOPWORDS = set('a an the is are was were be been being have has had do does did will would shall should may might must can could of in on at by for with about against between into through during before after above below to from up down out off over under again further then once here there when where why how all each every both few more most other some such no nor not only own same so than too very just because as until while'.split())

def stem(w):
    if len(w) < 5: return w
    if w.endswith('ingly'): return w[:-5]
    if w.endswith('edly'): return w[:-4]
    if w.endswith('ying'): return w[:-4] + 'y'
    if w.endswith('ation'): return w[:-5]
    if w.endswith('ment'): return w[:-4]
    if w.endswith('able'): return w[:-4]
    if w.endswith('ible'): return w[:-4]
    if w.endswith('ness'): return w[:-4]
    if w.endswith('less'): return w[:-4]
    if w.endswith('ally'): return w[:-4]
    if w.endswith('sion'): return w[:-3] + 's'
    if w.endswith('tion'): return w[:-3] + 't'
    if w.endswith('ical'): return w[:-4]
    if w.endswith('ied'): return w[:-3] + 'y'
    if w.endswith('ies'): return w[:-3] + 'y'
    if w.endswith('ing'): return w[:-3]
    if w.endswith('ive'): return w[:-3]
    if w.endswith('ful'): return w[:-3]
    if w.endswith('ous'): return w[:-3]
    if w.endswith('ise'): return w[:-3]
    if w.endswith('ize'): return w[:-3]
    if w.endswith('ate'): return w[:-3]
    if w.endswith('ify'): return w[:-3]
    if w.endswith('ed'): return w[:-2]
    if w.endswith('er'): return w[:-2]
    if w.endswith('or'): return w[:-2]
    if w.endswith('ly'): return w[:-2]
    if w.endswith('al'): return w[:-2]
    if w.endswith('en'): return w[:-2]
    if w.endswith('s') and not w.endswith('ss'): return w[:-1]
    return w

def clean_and_tokenize(text, add_bigrams=True):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    tokens = [stem(t) for t in text.split() if t not in STOPWORDS and len(t) > 2]
    if add_bigrams and len(tokens) > 1:
        tokens += ['_'.join(tokens[i:i+2]) for i in range(len(tokens)-1)]
    return tokens

class MultinomialNB:
    def __init__(self, alpha=1.0, min_df=3, add_bigrams=True):
        self.alpha = alpha; self.min_df = min_df
        self.add_bigrams = add_bigrams
        self._trained = False

    def fit(self, texts, labels):
        self.classes = sorted(set(labels))
        n = len(texts)
        class_docs = Counter(labels)
        self.priors = {c: math.log(class_docs[c] / n) for c in self.classes}
        all_tokenized = [clean_and_tokenize(t, add_bigrams=self.add_bigrams) for t in texts]
        doc_freq = Counter()
        for tokens in all_tokenized:
            for token in set(tokens):
                doc_freq[token] += 1
        self.vocab = {word for word, freq in doc_freq.items() if freq >= self.min_df}
        self.word_counts = {c: defaultdict(int) for c in self.classes}
        self.class_total_words = {c: 0 for c in self.classes}
        for tokens, label in zip(all_tokenized, labels):
            for token in set(tokens):
                if token in self.vocab:
                    self.word_counts[label][token] += 1
                    self.class_total_words[label] += 1
        self.vocab_size = len(self.vocab)
        self._trained = True

    def save(self, path):
        data = {
            'alpha': self.alpha, 'min_df': self.min_df,
            'add_bigrams': self.add_bigrams,
            'classes': self.classes, 'priors': self.priors,
            'vocab': list(self.vocab), 'vocab_size': self.vocab_size,
            'class_total_words': self.class_total_words,
            'word_counts': {str(c): dict(wc) for c, wc in self.word_counts.items()}
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path):
        with open(path) as f:
            data = json.load(f)
        m = cls(alpha=data['alpha'], min_df=data['min_df'],
                add_bigrams=data.get('add_bigrams', True))
        m.classes = data['classes']
        m.priors = {int(k) if k.isdigit() else k: v for k, v in data['priors'].items()}
        m.vocab = set(data['vocab'])
        m.vocab_size = data['vocab_size']
        m.class_total_words = {int(k): v for k, v in data['class_total_words'].items()}
        m.word_counts = {int(c): defaultdict(int, {tok: cnt for tok, cnt in wc.items()}) for c, wc in data['word_counts'].items()}
        m._trained = True
        return m

    def predict_with_proba(self, text):
        if not self._trained:
            raise RuntimeError("Model not trained")
        tokens = clean_and_tokenize(text, add_bigrams=self.add_bigrams)
        scores = {}
        for c in self.classes:
            log_prob = self.priors[c]
            total_wc = self.class_total_words[c]
            for token in tokens:
                count = self.word_counts[c].get(token, 0)
                log_prob += math.log((count + self.alpha) / (total_wc + self.alpha * self.vocab_size))
            scores[c] = log_prob
        best = max(scores, key=scores.get)
        log_vals = list(scores.values())
        max_log = max(log_vals)
        exp_vals = [math.exp(v - max_log) for v in log_vals]
        total = sum(exp_vals)
        probs = {c: exp_vals[i] / total for i, c in enumerate(scores.keys())}
        return best, probs

_model = None

CATEGORY_NORMALIZE = {
    'Fees / Finance': 'Financial Services',
    'Security / Discipline': 'Security',
    'Administration': 'Administrative',
}

RULE_BASED_CATEGORIES = [
    {
        'category': 'Administrative',
        'confidence': 0.95,
        'topic_terms': {
            'hackathon', 'hackthon', 'hackaton', 'event', 'competition',
            'seminar', 'workshop', 'fest', 'festival', 'orientation',
            'program', 'ceremony', 'club', 'conference'
        },
        'issue_terms': {
            'manage', 'management', 'mismanag', 'organize', 'organization',
            'arrange', 'arrangement', 'coordination', 'coordinat', 'schedule',
            'registration', 'venue', 'bad', 'poor', 'worst'
        },
    },
]

def rule_based_categorize(text):
    tokens = set(clean_and_tokenize(text, add_bigrams=False))
    raw_words = set(re.findall(r'[a-z0-9]+', text.lower()))
    words = tokens | raw_words
    for rule in RULE_BASED_CATEGORIES:
        if words & rule['topic_terms'] and words & rule['issue_terms']:
            return rule['category'], rule['confidence']
    return None

MODEL_PARAMS_PATH = os.path.join(BASE, 'data', 'model_params.json')

def get_model():
    global _model
    if _model is None:
        if os.path.isfile(MODEL_PARAMS_PATH):
            try:
                _model = MultinomialNB.load(MODEL_PARAMS_PATH)
                return _model
            except: pass
        with open(DATA_PATH, encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        texts = [r['text'] for r in rows]
        labels = [int(r['category_encoded']) for r in rows]
        _model = MultinomialNB(alpha=0.01, min_df=1)
        _model.fit(texts, labels)
        try:
            _model.save(MODEL_PARAMS_PATH)
        except: pass
    return _model

def predict_top3(text):
    model = get_model()
    pred, probs = model.predict_with_proba(text)
    sorted_cats = sorted(probs.items(), key=lambda x: x[1], reverse=True)
    result = []
    for enc_cat, prob in sorted_cats[:3]:
        cat_name = CATEGORY_NORMALIZE.get(CAT_DECODER[enc_cat], CAT_DECODER[enc_cat])
        result.append({'category': cat_name, 'confidence': round(prob, 4)})
    return result

def categorize(text):
    rule_match = rule_based_categorize(text)
    if rule_match:
        cat, conf = rule_match
        return {
            'category': cat,
            'confidence': conf,
            'tier': 'auto' if conf >= AUTO_THRESHOLD else 'suggest'
        }

    model = get_model()
    pred, probs = model.predict_with_proba(text)
    conf = probs[pred]

    if conf < CONFIDENCE_THRESHOLD:
        return {'category': 'Other', 'confidence': conf, 'tier': 'unknown'}

    cat = CAT_DECODER[pred]
    cat = CATEGORY_NORMALIZE.get(cat, cat)

    if conf >= AUTO_THRESHOLD:
        tier = 'auto'
    elif conf >= SUGGEST_THRESHOLD:
        tier = 'suggest'
    else:
        tier = 'unknown'

    return {'category': cat, 'confidence': conf, 'tier': tier}

def auto_categorize(text):
    result = categorize(text)
    return result['category'], result['confidence']

def detect_anomaly(text):
    model = get_model()
    tokens = clean_and_tokenize(text)
    token_set = set(tokens)
    unknown_tokens = [t for t in token_set if t not in model.vocab]
    known_ratio = len(token_set - set(unknown_tokens)) / max(len(token_set), 1)

    pred, probs = model.predict_with_proba(text)
    max_prob = max(probs.values())

    flags = []
    if len(tokens) < 5:
        flags.append('too_short')
    if known_ratio < 0.3:
        flags.append('many_unknown_words')
    if max_prob < 0.30:
        flags.append('low_category_confidence')
    if len(unknown_tokens) > max(3, len(token_set) * 0.5):
        flags.append('high_unusual_vocabulary')

    return {
        'is_anomaly': len(flags) >= 2,
        'flags': flags,
        'known_token_ratio': round(known_ratio, 2),
        'max_category_confidence': round(max_prob, 2),
        'unknown_tokens': unknown_tokens[:10]
    }
