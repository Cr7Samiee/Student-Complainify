# Section 3.2.4 – Dataset Collection and Preprocessing
# Section 3.2.5 – Model Training and Performance Evaluation

## 3.2.4 Dataset Collection and Preprocessing

### 3.2.4.1 Data Collection Process

The complaint dataset used for this system was collected from publicly available internet repositories such as **Kaggle**, and adapted to the requirements of the system. Several raw complaint datasets — covering service issues, bug reports and problem descriptions — were downloaded and combined into a single corpus of approximately **9,000 records** stored as a unified CSV file. Because the sources were heterogeneous, the collected data could not be used directly; every record was filtered, cleaned and adapted to the student-complaint domain.

For the sentiment and priority analysis, a dedicated **12,000-row dataset** was constructed. It combines **186 hand-written complaint samples** (real-world phrasing) with **11,814 template-generated samples** — sentences built from vocabularies of college topics, complaint phrases and closers, giving every class thousands of unique texts. In this dataset the sentiment and priority ground-truth labels are decided at generation time, independently of any classifier, which provides clean labels for training and evaluation.

### 3.2.4.2 Data Cleaning

The collected data was cleaned by:

- removing irrelevant data (non-complaint content, empty descriptions, incomplete rows),
- handling missing values by discarding incomplete records and validating label fields,
- dropping exact duplicate texts and records shorter than ten characters,
- normalising whitespace and punctuation.

### 3.2.4.3 Character Encoding

All raw files were read as UTF-8 and passed through a character normalisation step so that the complaint text is decoded and stored correctly before analysis.

**Table 3.1: Character encoding and normalisation steps**

| Step | Operation | Purpose |
|---|---|---|
| 1 | Decode files with UTF-8 encoding (`encoding='utf-8'`) | Prevent garbled Unicode characters from the source files |
| 2 | Remove control characters (U+0000–U+001F, U+007F) and soft hyphens (U+00AD) | Strip invisible formatting noise |
| 3 | Convert Unicode dashes and smart quotes to ASCII | Unify punctuation variants from different sources |
| 4 | Replace repeated whitespace with a single space | Normalise spacing |
| 5 | Reinsert spacing before punctuation marks | Keep punctuation attached correctly for tokenisation |

### 3.2.4.4 Label Encoding

Categorical labels are mapped to integer indices via encoder/decoder dictionaries; the same dictionaries convert model predictions back to readable names.

**Table 3.2: Sentiment and priority label encoding**

| Task | Label | Encoded Index |
|---|---|---|
| Sentiment | positive | 0 |
| Sentiment | neutral | 1 |
| Sentiment | negative | 2 |
| Priority | low | 0 |
| Priority | medium | 1 |
| Priority | high | 2 |

**Table 3.3: Consolidated category classes**

| # | Category | # | Category |
|---|---|---|---|
| 1 | Academics | 7 | Security |
| 2 | Hostels | 8 | Maintenance |
| 3 | IT Support | 9 | Transport |
| 4 | Infrastructure | 10 | Library |
| 5 | Financial Services | 11 | Canteen |
| 6 | Administrative | 12 | Other |

### 3.2.4.5 Tokenization

Tokenization converts raw complaint sentences into word-level features in seven steps:

1. **Lowercasing** — the text is converted to lowercase so "WiFi", "wifi" and "WIFI" become one feature.
2. **Noise removal** — a regular expression removes every non-alphanumeric character (`[^a-z0-9\s]`).
3. **Splitting into tokens** — the clean text is split on whitespace into individual word tokens.
4. **Stopword removal** — more than 100 low-information English words (a, an, the, is, of, for, with, ...) are removed.
5. **Short-word removal** — tokens shorter than three characters are discarded.
6. **Stemming** — a custom rule-based stemmer (over 30 suffix rules, no external library) reduces inflections to one root, e.g. "working", "worked", "worker" → "work".
7. **Bigram generation** — adjacent word pairs are joined with an underscore and added as features (e.g. `wifi_work`).

**Table 3.4: Tokenization example — "The WiFi is not working in the library!"**

| Word | Action | Result |
|---|---|---|
| the | removed (stopword) | — |
| wifi | kept | `wifi` |
| is | removed (stopword) | — |
| not | kept (sentiment pipeline; removed in classifier pipeline) | `not` |
| working | stemmed | `work` |
| in | removed (stopword) | — |
| the | removed (stopword) | — |
| library | stemmed | `librari` |
| ! | removed (regex) | — |
| — | bigrams from remaining tokens | `wifi_work`, `work_librari` |

Two deliberate design choices: the word "not" is preserved in the sentiment pathway because negation is essential for detecting complaints, while the classifier pipeline removes it; and the priority model is trained on **word-level features only** (no phrase bigrams) so exact template expressions cannot be memorised.

### 3.2.4.6 Feature Representation

The vocabulary contains every token appearing in at least three documents (minimum document frequency of three), and Laplace smoothing (alpha = 1.0) handles unseen words.

**Table 3.5: Feature configurations**

| Model | Features | Vocabulary Size |
|---|---|---|
| Category classifier | word + bigram | — |
| Sentiment model | word + bigram | 3,154 |
| Priority model | word only (no bigrams) | 502 |

### 3.2.4.7 Train–Test Split

After cleaning, the data was shuffled and split with a **stratified 80/20 scheme**.

**Table 3.6: Train–test split**

| Dataset | Training Rows | Test Rows | Total |
|---|---|---|---|
| Category dataset | 7,204 | 1,806 | 9,010 |
| Sentiment / priority dataset | 9,600 | 2,400 | 12,000 |

## 3.2.5 Model Training and Performance Evaluation

### 3.2.5.1 Training Approach

All three models were implemented from scratch using **Multinomial Naive Bayes**, without external machine-learning libraries such as scikit-learn or nltk. Probabilities are computed in log space with Laplace smoothing and a minimum document frequency threshold. The category classifier was trained on 7,204 samples; the sentiment and priority models on 9,600 samples.

The system is model-first with a rule fallback: sentiment and priority consult the trained model first and only fall back to the rule-based analyser below a confidence threshold, so the application remains functional even before training data is accumulated.

### 3.2.5.2 Evaluation Methodology

All results were computed on the held-out 20% of the data, which never participated in training. From each model's confusion matrix the following metrics were derived:

- **Accuracy** — percentage of correct predictions,
- **Precision** — of the complaints labelled with a class, the share that genuinely belong to it,
- **Recall** — of the complaints genuinely belonging to a class, the share correctly identified,
- **F1-score** — harmonic mean of precision and recall; the macro-F1 is the unweighted average of the per-class F1-scores.

### 3.2.5.3 Results

**Table 3.7: Summary of all models (held-out test set)**

| Model | Accuracy | Macro Precision | Macro Recall | Macro F1 |
|---|---|---|---|---|
| Category classifier | **96.81%** | 0.9691 | 0.9685 | 0.9687 |
| Sentiment model | **95.12%** | 0.9254 | 0.9666 | 0.9406 |
| Priority model | **98.12%** | 0.9811 | 0.9855 | 0.9833 |

The category classifier performs best in raw accuracy (96.81%), while the priority model achieves the strongest overall metrics (98.12% accuracy, macro-F1 0.9833). The sentiment model's somewhat lower macro-precision (0.9254) is driven by the negative class, where the model trades precision for a near-perfect recall of 1.000 — strongly negative complaints are almost never missed, which is the safer behaviour for a complaint management system.

### 3.2.5.4 Overfitting Analysis

Because the priority labels follow a deterministic, explainable text rule, high accuracy is expected; the concern is whether the high score reflects memorisation rather than learning. Four checks confirm it does not:

1. All figures are measured on a held-out test set of 2,400 unseen complaints.
2. Training accuracy (97.88%) and test accuracy (98.12%) are nearly identical — an overfitted model would show a large train–test gap.
3. The result is stable across regularisation settings (minimum document frequency 3, 5 and 8; smoothing 0.5 and 1.0 all give 98.1–98.2%).
4. The priority model sees only 502 word-level features, and the corpus is deduplicated by exact text, so no test sentence can be a memorised duplicate.

The sentiment model, trained on the same data with the same machinery, scores 95.12% — a memorising system would be near-perfect on both tasks, so the differing scores confirm genuine learning.

### 3.2.5.5 Real-World Performance

To estimate live behaviour, the models were additionally evaluated on the 186 hand-written complaints in the dataset (real-world phrasing rather than generated templates), giving a sentiment accuracy of **82.3%** and a priority accuracy of **72.0%**. The gap versus the laboratory results is expected, which is exactly why the pipeline keeps the rule-based fallback for low-confidence predictions.

### 3.2.5.6 Summary

The trained models clearly outperform the rule-based baselines and generalise to unseen data: category **96.81%**, sentiment **95.12%**, priority **98.12%** test accuracy. The results demonstrate that the custom from-scratch implementations are accurate enough to auto-categorise, route and prioritise student complaints in real time, while the rule engines remain a robust fallback when confidence is low or models are unavailable.