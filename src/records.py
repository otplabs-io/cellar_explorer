"""Load a wine record with the shared records it points to merged in.
A wine's sheet copy lives in its own content block. Facts shared across vintages live in producers/<id>/producer.json:
the producer's printed name and its story fill content.producer and content.family unless the wine sets its own."""
import json,os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def producer(pid):
    return json.load(open(os.path.join(ROOT,'producers',pid,'producer.json'),encoding='utf-8'))
def load_wine(path):
    cfg=json.load(open(path,encoding='utf-8'))
    pid=(cfg.get('identity') or {}).get('producer')
    if pid:
        p=producer(pid); c=cfg['content']
        c.setdefault('producer',p['name'])
        if p.get('story'): c.setdefault('family',p['story'])
        if p.get('story_title'): c.setdefault('family_title',p['story_title'])
    return cfg
