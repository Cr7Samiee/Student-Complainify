"""Live sentiment x priority analysis against the MySQL complaints table.

Produces a JSON blob consumed by /analysis:
  matrix       - {category: {priority: n}} for non-positive complaints (red/orange heat)
  green        - {category: {priority: n}} for positive/thank-you complaints (green heat)
  pink         - closed but still-negative complaints (Resolved + Negative + High/Medium)
  category_totals, sentiment_totals, priority_totals

Run standalone to refresh the JSON cache:
    python ml/gen_analysis.py
"""

import json
import os
import sys

import pymysql

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(BASE, 'data', 'live_analysis.json')


def load_config():
    cfg = dict(
        host=os.environ.get('DB_HOST', '127.0.0.1'),
        port=int(os.environ.get('DB_PORT', 3306)),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'complainify'),
        charset='utf8mb4',
    )
    env_file = os.path.join(BASE, '.env')
    if os.path.isfile(env_file):
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            cfg['host'] = os.environ.get('DB_HOST', cfg['host'])
            cfg['port'] = int(os.environ.get('DB_PORT', cfg['port']))
            cfg['user'] = os.environ.get('DB_USER', cfg['user'])
            cfg['password'] = os.environ.get('DB_PASSWORD', cfg['password'])
            cfg['database'] = os.environ.get('DB_NAME', cfg['database'])
        except ImportError:
            pass
    return cfg


def fetch_rows():
    conn = pymysql.connect(**load_config(), cursorclass=pymysql.cursors.DictCursor)
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT category, priority, sentiment, status,
                ticket_id, subject, description, fullname,
                date_format(created_at, '%d %b %Y') date
                FROM complaints
                WHERE priority IN ('High', 'Medium', 'Low')
                  AND sentiment IN ('Positive', 'Neutral', 'Negative')""")
            return cur.fetchall()
    finally:
        conn.close()


def build_analysis(rows):
    cats = sorted({r['category'] or 'Other' for r in rows})
    prios = ['Low', 'Medium', 'High']
    matrix = {c: {p: 0 for p in prios} for c in cats}
    green = {c: {p: 0 for p in prios} for c in cats}
    sentiment_totals = {'Positive': 0, 'Neutral': 0, 'Negative': 0}
    priority_totals = {'Low': 0, 'Medium': 0, 'High': 0}
    pink = []

    for r in rows:
        cat = r['category'] or 'Other'
        pri = r['priority'] if r['priority'] in prios else 'Low'
        sent = r['sentiment'] if r['sentiment'] in sentiment_totals else 'Neutral'
        sentiment_totals[sent] += 1
        priority_totals[pri] += 1
        if sent == 'Positive':
            green[cat][pri] += 1
        else:
            matrix[cat][pri] += 1
        if r['status'] == 'Resolved' and sent == 'Negative' and pri in ('High', 'Medium'):
            pink.append({
                'ticket_id': r['ticket_id'], 'category': cat, 'priority': pri,
                'subject': r['subject'], 'description': (r['description'] or '')[:140],
                'student': r['fullname'] or 'Anonymous', 'date': r['date'],
            })

    pink.sort(key=lambda p: p['date'], reverse=True)
    return {
        'matrix': matrix, 'green': green,
        'pink': pink[:40], 'pink_total': len(pink),
        'sentiment_totals': sentiment_totals,
        'priority_totals': priority_totals,
    }


def main():
    rows = fetch_rows()
    data = build_analysis(rows)
    with open(OUT_PATH, 'w') as f:
        json.dump(data, f, indent=2)
    print('rows:', len(rows))
    print('sentiment:', data['sentiment_totals'])
    print('priority :', data['priority_totals'])
    print('pink (closed, still negative):', data['pink_total'])
    print('wrote:', OUT_PATH)


if __name__ == '__main__':
    main()
