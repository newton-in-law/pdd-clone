#!/usr/bin/env python3
"""Data refresh for the clone only (no charts, no pages): NeoWs log, MPC circulars, sky positions, map points, Sentry.
Each step is allowed to fail on its own; the previous data is kept."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import refresh_all as R
def safe(name, fn, *a):
    try: return fn(*a)
    except Exception as ex: print(f'{name} failed, previous data kept: {ex}', flush=True); return None
safe('neows', R.step_neows)
recent = safe('mpec', R.step_mpec) or []
sky = safe('sky', R.step_sky, recent) or {}
sent = safe('sentry', R.step_sentry) or []
if sky: safe('watch', R.step_watch, sky, {r['des'] for r in sent})
else: print('watch: no sky positions this run (MPC or Horizons unreachable), previous map points kept', flush=True)
