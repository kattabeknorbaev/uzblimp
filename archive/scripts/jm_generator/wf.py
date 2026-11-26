"""Lookup in the full Latin word-frequency cache (cache/wordfreq_lat_full.sqlite, built by wordfreq_full.py + wordfreq_merge.py)."""
import sqlite3,os
_c=sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),'cache/wordfreq_lat_full.sqlite'))
import functools
@functools.lru_cache(maxsize=None)
def F(w):
    r=_c.execute('select n from wf where w=?',(w.lower(),)).fetchone();return r[0] if r else 0
