#!/usr/bin/env python3
"""Chart set v13 (file kept as nea_charts_v11.py): applies the owner's comments of 18-19 Nov (v10-v12 reviews).
Every axis limit is computed from the data (it changes every 8 hours): padding so no point touches a limit,
sizes end at the next 0.05 km above the data, axes that must start at 0 (or at 1 LD for the 3D chart) are fixed.
Object types: PHA 💥, NEA 🪨, comet ☄️, main-belt asteroid 🥔; top 3 impact probabilities ⚠️.
Also writes <chart>.json next to impact/bubble PNGs: clickable hotspots (object data + SBDB / MPC links).
Usage: /usr/bin/python3 nea_charts_v11.py OUTDIR
"""
import sys, os, math, json, urllib.request, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nea_log as N
import nea_charts_v6 as V6
from nea_charts_v9 import (fnt, tw, elabel, data_rows, load_sentry, GOLD, WHITE, BLACK, ORANGE, YELLOW, LD, W, H)
from nea_charts_v10 import TX, SIZE_CLASSES, size_color, num, rot_rich, ticks_every, fig_cumulative
from PIL import Image, ImageDraw, ImageFont

EMO = {'pha': '\U0001F4A5', 'nea': '\U0001FAA8', 'comet': '☄️', 'mba': '\U0001F954',
       'warn': '⚠️', 'target': '\U0001F3AF'}
# size classes in km, scientific notation with the exponent as a superscript (1E-3 to 1E-2 km = 1 to 10 m, ...)
SIZE_LABELS = [[('1E', 'n'), ('-3', 's'), ('–1E', 'n'), ('-2', 's'), (' km', 'n')],
               [('1E', 'n'), ('-2', 's'), ('–1E', 'n'), ('-1', 's'), (' km', 'n')],
               [('1E', 'n'), ('-1', 's'), ('–1E', 'n'), ('0', 's'), (' km', 'n')],
               [('>1E', 'n'), ('0', 's'), (' km', 'n')]]
SBDB = 'https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr='
MPC = 'https://minorplanetcenter.net/db_search/show_object?object_id='

def otype(o):
    return 'comet' if o.get('comet') else 'mba' if o.get('mba') else 'pha' if o.get('pha') else 'nea'

TYPE_ITEMS = [('pha', None, 'PHA'), ('nea', None, 'NEA'), ('comet', None, 'Comet'), ('mba', None, 'Main-belt asteroid')]

def twp(t, sz):
    return V6.rich(t, sz, (0, 0, 0, 255)).size[0] - 4 if isinstance(t, list) else tw(t, sz)

def twp(t, sz):
    return V6.rich(t, sz, (0, 0, 0, 255)).size[0] - 4 if isinstance(t, list) else tw(t, sz)

def legend_widths(items, sep=40, sz=22, gap=10, icon=28):
    ik = lambda k: icon + 6 if k in EMO else 36
    widths = [ik(k) + gap + twp(t, sz) for k, c, t in items]
    return widths, sum(widths) + sep * (len(items) - 1)

def legend(img, th, items, y, cx, sep=40, left=None):
    """centred on cx, or left-justified at x=left."""
    sz = 22; gap = 10; icon = 28
    emo = lambda k: k in EMO
    ik = lambda k: icon + 6 if emo(k) else 36
    widths, total = legend_widths(items, sep)
    x = left if left is not None else cx - total / 2; d = ImageDraw.Draw(img)
    for (kind, col, txt), w in zip(items, widths):
        if emo(kind): N.emoji(img, EMO[kind], x + icon / 2, y, icon)
        elif kind == 'rect': d.rectangle([x, y - 9, x + 18, y + 9], fill=col)
        elif kind == 'line': d.line([x, y, x + 34, y], fill=th.pha, width=2)
        elif kind == 'dot': d.ellipse([x + 4, y - 5, x + 14, y + 5], fill=col)
        elif kind == 'dots': V6.dotted(d, (x, y), (x + 30, y), col, 2, 5, 5)
        elif kind == 'swatch': d.ellipse([x, y - 10, x + 20, y + 10], fill=col[:3] + (150,), outline=col[:3] + (255,), width=2)
        if isinstance(txt, list): V6.place_rich(img, (x + ik(kind) + gap - 10, y), txt, sz, th.fg, anchor='lm')
        else: N.text(img, (x + ik(kind) + gap - 6, y - (7 if kind == 'swatch' else 12)), txt, sz, th.fg)
        x += w + sep

def size_items(labels=None):
    return [('swatch', c + (255,), n) for (_, c), n in zip(SIZE_CLASSES, labels or SIZE_LABELS)]

def size_legend(img, th, y, cx, labels=None, left=None):
    legend(img, th, size_items(labels), y, cx, sep=26, left=left)

SIZE_KM_PLAIN = ['0.001–0.01 km', '0.01–0.1 km', '0.1–1 km', 'over 1 km']      # imp3: kilometres, no E notation
SIZE_M = ['1–10 m', '10–100 m', '100 m–1 km', 'over 1 km']                       # legend-box variant of the bubble charts

def e0(v):
    """E-notation with a single digit mantissa: 3E-4 (exponent as superscript)."""
    if v == 0: return [('0', 'n')]
    k = math.floor(math.log10(abs(v))); m = round(v / 10 ** k)
    if m == 10: m, k = 1, k + 1
    return [(f"{m}E", 'n'), (str(k), 's')]

WM_ALPHA = 40
def watermark(img, style):
    """tiled NEWSROOMFLOOR.COM, same recipe as the AI images (loop/WATERMARK-AGENT-INSTRUCTIONS.md step 1), lighter so the data stays readable."""
    fs = int(img.width / 38) - 1; f = fnt(fs); txt = 'NEWSROOMFLOOR.COM'
    tile = Image.new('RGBA', (int(tw(txt, fs)) + 40, fs + 30), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((20, 15), txt, font=f, fill=(225, 225, 225, WM_ALPHA) if style == 'dark' else (90, 90, 90, WM_ALPHA))
    tile = tile.rotate(30, expand=True, resample=Image.BICUBIC)
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); sx, sy = int(tile.width * 1.25), int(tile.height * 2.2); row = 0
    for y in range(-tile.height, img.height + tile.height, sy):
        off = sx // 2 if row % 2 else 0; row += 1
        for x in range(-tile.width + off, img.width + tile.width, sx): lay.paste(tile, (x, y), tile)
    return Image.alpha_composite(img.convert('RGBA'), lay)

def frame2(th, l1, l2, sub, L, R, T, B, subcol=None):
    img = Image.new('RGBA', (W, H), th.bg); d = ImageDraw.Draw(img)
    if l1:
        N.text(img, (60, 24), l1, 34, th.fg); N.text(img, (60, 68), l2, 28, th.fg); N.text(img, (60, 110), sub, 19, subcol or th.fg)
    else:
        N.text(img, (60, 40), l2, 34, th.fg); N.text(img, (60, 90), sub, 20, subcol or th.fg)
    d.rectangle([L, T, R, B], outline=th.fg, width=2)
    return img, d

# ---------- axes that follow the data ----------
def nice_ceil(v, step):
    return math.ceil(v / step - 1e-9) * step

def lin_step(span, target=8):
    raw = span / target; e = 10 ** math.floor(math.log10(raw))
    return next(m * e for m in (1, 2, 2.5, 5, 10) if m * e >= raw)

def lin_ticks(lo, hi, step=None):
    step = step or lin_step(hi - lo); v = math.ceil(lo / step - 1e-9) * step; out = []
    while v <= hi + 1e-9:
        out.append(round(v, 10)); v += step
    return out

def log_ticks(lo, hi, dense=True):
    out = []; ms = (1, 2, 3, 4, 5, 6, 7, 8, 9) if (dense and math.log10(hi / lo) < 1.4) else (1, 2, 3, 5, 7) if dense else (1, 2, 5)
    for k in range(math.floor(math.log10(lo)), math.ceil(math.log10(hi)) + 1):
        for m in ms:
            v = m * 10 ** k
            if lo <= v <= hi: out.append(v)
    return out

def thin(vals, ax, gap, horizontal=True):
    out = []; last = None
    for v in vals:
        p = ax.f(v)
        if last is None or abs(p - last) >= gap: out.append(v); last = p
    return out

def grow(lo, hi, log, flo, fhi, k=0.05):
    if log:
        f = (hi / lo) ** k
        return (lo / f if flo else lo), (hi * f if fhi else hi)
    s = (hi - lo) * k
    return (lo - s if flo else lo), (hi + s if fhi else hi)

NICE = [1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10]
def snap_hi(v):
    e = 10 ** math.floor(math.log10(v)); return next(n for n in NICE if n >= v / e - 1e-9) * e
def snap_lo(v):
    e = 10 ** math.floor(math.log10(v)); return max(n for n in NICE if n <= v / e + 1e-9) * e

def fit_axes(pts, xs, ys, L, R, T, B, m=14):
    """pts (xv, yv, r_px). xs/ys = [lo, hi, log, fixed_lo]. Grows limits until no marker touches a limit."""
    xs, ys = list(xs), list(ys)
    for _ in range(80):
        ax = N.Ax(xs[0], xs[1], L, R, xs[2]); ay = N.Ax(ys[0], ys[1], B, T, ys[2])
        bx_lo = bx_hi = by_lo = by_hi = False
        for xv, yv, r in pts:
            x, y = ax.f(xv), ay.f(yv)
            bx_hi |= x + r > R - m; bx_lo |= (x - r < L + m) and not xs[3]
            by_hi |= y - r < T + m; by_lo |= (y + r > B - m) and not ys[3]
        if not (bx_lo or bx_hi or by_lo or by_hi): break
        xs[0], xs[1] = grow(xs[0], xs[1], xs[2], bx_lo, bx_hi); ys[0], ys[1] = grow(ys[0], ys[1], ys[2], by_lo, by_hi)
    for a in (xs, ys):                      # round logarithmic limits outwards to a clean value (never inwards)
        if a[2]: a[0], a[1] = snap_lo(a[0]), snap_hi(a[1])
    return xs, ys

def dgrid(img, th, ax_x, ax_y, xt, yt, L, R, T, B):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    col = (255, 255, 255, 75) if th.fg == WHITE else (0, 0, 0, 60)
    for v in xt:
        x = ax_x.f(v)
        if L < x < R: V6.dotted(d, (x, T), (x, B), col, 1, 2, 6)
    for v in yt:
        y = ax_y.f(v)
        if T < y < B: V6.dotted(d, (L, y), (R, y), col, 1, 2, 6)
    img.alpha_composite(lay)

def corner_ticks(ts, lo, ax, gap=30):
    """add the start value of an axis (bottom corner) unless a tick already sits on it."""
    return [lo] + [t for t in ts if abs(ax.f(t) - ax.f(lo)) >= gap and t != lo]

# ---------- numbers beside the markers, never on top ----------
def place_labels(th, img, items, circles, bounds, size=16):
    dark = th.fg == WHITE; tcol, scol, lcol = (WHITE, (0, 0, 0, 255), (235, 235, 235, 255)) if dark else (BLACK, (255, 255, 255, 255), (70, 70, 70, 255))
    d = ImageDraw.Draw(img); placed = []; x0, y0, x1, y1 = bounds
    for x, y, r, t in items:
        w, h = tw(t, size) + 8, size + 8; best = None
        for dist in (r + 14, r + 26, r + 40, r + 58, r + 80):
            for a in (-50, -15, 20, 55, 90, 125, 160, 195, 230, 265, -80, 305):
                cx, cy = x + dist * math.cos(math.radians(a)), y + dist * math.sin(math.radians(a))
                bx0, by0, bx1, by1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
                if bx0 < x0 or bx1 > x1 or by0 < y0 or by1 > y1: continue
                if any(max(bx0 - px, 0, px - bx1) ** 2 + max(by0 - py, 0, py - by1) ** 2 < (pr + 3) ** 2 for px, py, pr in circles): continue
                if any(bx0 < q[2] + 2 and bx1 > q[0] - 2 and by0 < q[3] + 2 and by1 > q[1] - 2 for q in placed): continue
                best = (cx, cy, a, bx0, by0, bx1, by1); break
            if best: break
        if not best:
            cx, cy = x + (r + 20), y - (r + 20); best = (cx, cy, -45, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
        cx, cy, a, bx0, by0, bx1, by1 = best; placed.append((bx0, by0, bx1, by1))
        ux, uy = math.cos(math.radians(a)), math.sin(math.radians(a))
        d.line([x + ux * r, y + uy * r, cx - ux * (min(w, h) / 2 + 1), cy - uy * (min(w, h) / 2 + 1)], fill=lcol, width=1)
        d.text((cx, cy), t, font=fnt(size), fill=tcol, anchor='mm', stroke_width=2, stroke_fill=scol)

def save_hot(out, pts):
    json.dump({'w': W, 'h': H, 'pts': pts}, open(os.path.splitext(out)[0] + '.json', 'w'))

def card(des, sub, rows, url, links):
    """pop-out card: big linked designation (JPL SSD), type line, data table, extra links."""
    tr = ''.join(f'<tr><td>{a}</td><td>{b}</td></tr>' for a, b in rows)
    return (f'<a class="ct" href="{url}" target="_blank" rel="noopener">{des}</a><div class="cs">{sub}</div><table>{tr}</table>'
            f'<div class="cl">{links}</div>')

def lnk(u, t):
    return f'<a href="{u}" target="_blank" rel="noopener">{t}</a>'

def obj_info(r, rank=None):
    t = {'pha': 'Potentially hazardous asteroid', 'nea': 'Near-Earth asteroid', 'comet': 'Comet', 'mba': 'Main-belt asteroid'}[otype(r)]
    des = r['designation']; q = des.replace(' ', '%20')
    rows = ([('Rank by velocity', f'{rank} of 15')] if rank else []) + [
        ('Mean size', f"{r['dmid_km']*1000:.0f} m ({r['dmid_km']:.3f} km)"),
        ('Size range', f"{r['dmin_km']*1000:.0f}–{r['dmax_km']*1000:.0f} m"),
        ('Distance', f"{r['ld']:.1f} LD ({r['ld']*LD:,.0f} km)"),
        ('Velocity', f"{r['rel_velocity_kms']:.1f} km/s"),
        ('Approach (UTC)', r['approach_utc']),
        ('Absolute magnitude', f"H {r['H_mag']}"),
        ('Hazardous (PHA)', 'Yes' if r.get('pha') else 'No'),
        ('On Sentry risk list', 'Yes' if r.get('sentry') else 'No'),
        ('First seen', r.get('first_seen', '')),
        ('NEO ID', r['neo_id'])]
    return des, card(des, t, rows, f"{SBDB}{r['neo_id']}", lnk(f"{SBDB}{r['neo_id']}", 'JPL SSD (SBDB)') + ' · ' + lnk(f"{MPC}{q}", 'Minor Planet Center'))

# ---------- 0. cumulative NEAs: object-type emoji at every point, clickable day cards ----------
def day_card(day, objs, cum, kind):
    rows = []
    for r in objs[:12]:
        rows.append((lnk(f"{SBDB}{r['neo_id']}", r['designation']), f"{EMO[otype(r)]} {r['dmid_km']*1000:.0f} m · {r['ld']:.1f} LD"))
    if len(objs) > 12: rows.append(('…', f"+{len(objs) - 12} more"))
    if not objs: rows.append(('', 'none new on this day'))
    return (f'<span class="ct nl">{day.strftime("%d %b %Y")}</span><div class="cs">{kind} · {len(objs)} new · {cum} in total</div><table>'
            + ''.join(f'<tr><td>{a}</td><td>{b}</td></tr>' for a, b in rows) + '</table><div class="cl">'
            + lnk('https://www.minorplanetcenter.net/iau/NEO/toconfirm_tabular.html', 'MPC NEO Confirmation page') + '</div>')

def fig_cum(logd, style, out, log=True, start='2026-11-01'):
    th = N.Theme(style); fg = th.fg; end = dt.date.today().isoformat()
    days, d0, d1 = [], dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    while d0 <= d1: days.append(d0); d0 += dt.timedelta(days=1)
    seen, seen_p, tot, pha, new_all, new_pha = set(), set(), [], [], [], []
    for day in days:
        na, npha = [], []
        for r in sorted(logd['rows'], key=lambda r: r['approach_utc']):
            if r['approach_date'] != day.isoformat(): continue
            r = dict(r); r.setdefault('dmid_km', (r['diam_min_m'] * r['diam_max_m']) ** 0.5 / 1000); r.setdefault('ld', r['miss_ld'])
            if r['neo_id'] not in seen: seen.add(r['neo_id']); na.append(r)
            if r['pha'] and r['neo_id'] not in seen_p: seen_p.add(r['neo_id']); npha.append(r)
        tot.append(len(seen)); pha.append(len(seen_p)); new_all.append(na); new_pha.append(npha)
    L, R, T, B = 220, 1060, 160, 620
    img, d = N.frame(th, 'CUMULATIVE NEAs SINCE FIRST CAPTURE', f"{start} to {end} · DISTINCT NEAs BY CLOSE-APPROACH DATE · {'LOGARITHMIC' if log else 'LINEAR'} SCALE", L, R, T, B)
    top = max(tot + [1])
    ax_y = N.Ax(1, top * 1.2, B, T, True) if log else N.Ax(0, top * 1.1, B, T, False); ax_x = N.Ax(0, len(days) - 1, L, R, False)
    N.gridlines(img, th, ax_x, ax_y, L, R, T, B)
    step = max(1, math.ceil(len(days) / 16))
    for i, day in enumerate(days):
        x = ax_x.f(i)
        if (len(days) - 1 - i) % step: continue
        d.line([x, B, x, B + 6], fill=fg, width=2); N.text(img, (x + 4, B + 12), day.strftime('%b %d'), 20, fg, angle=45, anchor='tr')
    for v in ax_y.ticks():
        y = ax_y.f(v); d.line([L - 8, y, L, y], fill=fg, width=2); N.text(img, (L - 12, y), f"{v:g}", 24, fg, anchor='rm')
    yel = (119, 221, 119, 255) if style == 'dark' else (40, 150, 60, 255); pur = (178, 132, 214, 255) if style == 'dark' else (118, 64, 170, 255); hot = []   # NEAs green, PHAs purple (PDD palette)
    for series, col, key, newl, kind in ((tot, yel, 'nea', new_all, 'NEAs'), (pha, pur, 'pha', new_pha, 'PHAs')):
        pts = [(ax_x.f(i), ax_y.f(max(v, 1) if log else v)) for i, v in enumerate(series)]
        d.line(pts, fill=col, width=3)
        for i, (x, y) in enumerate(pts):
            N.emoji(img, EMO[key], x, y, 27)
            hot.append({'x': x / W, 'y': y / H, 'r': 15 / W, 't': f"{days[i].isoformat()} · {kind}", 'h': day_card(days[i], newl[i], series[i], kind)})
    ty = B + 100
    N.text(img, ((L + R) // 2, ty), 'CLOSE-APPROACH DATE', 26, fg, anchor='mt')
    N.text(img, (L - 108, (T + B) // 2), 'CUMULATIVE NEAs (count)', 26, fg, angle=90, anchor='cc')
    legend(img, th, [('nea', None, f'All NEAs ({tot[-1]})'), ('pha', None, f'PHA ({pha[-1]})')], ty + 84, (L + R) // 2)
    save_hot(out, hot); img.save(out)

# ---------- 1. distance vs velocity and size ----------
LIGHT_GOLD = (255, 228, 140, 255)

def serif_text(img, xy, s_, sz, color, anchor='mm'):
    f = ImageFont.truetype(N.PLAYFAIR, sz)
    try: f.set_variation_by_name('Black')
    except Exception: pass
    ImageDraw.Draw(img).text(xy, s_, font=f, fill=color, anchor=anchor)

def arrow(img, d, th, tip, direction, length=112, shaft=9, head=21, headlen=32, thin=False):
    """block arrow with white fill (clear on the transparent theme) and a 2 px black border; direction 'left' or 'up'."""
    x, y = tip
    if direction == 'left':
        pts = [(x, y), (x + headlen, y - head), (x + headlen, y - shaft), (x + length, y - shaft), (x + length, y + shaft), (x + headlen, y + shaft), (x + headlen, y + head)]
    else:
        pts = [(x, y), (x - head, y + headlen), (x - shaft, y + headlen), (x - shaft, y + length), (x + shaft, y + length), (x + shaft, y + headlen), (x + head, y + headlen)]
    if thin:                                                                       # 1 pt thinner, black fill, 1 pt gold border
        gold = (255, 201, 4, 255) if th.bg[3] else (196, 150, 0, 255)
        if th.bg[3]: d.polygon(pts, fill=(0, 0, 0, 255))
        d.line(pts + [pts[0]], fill=gold, width=1, joint='curve'); return
    if th.bg[3]: d.polygon(pts, fill=WHITE)
    d.line(pts + [pts[0]], fill=BLACK, width=2, joint='curve')

def dotted_box(d, col, x0, y0, x1, y1):
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))): V6.dotted(d, a, b, col, 2, 4, 5)

def fig_bubbles(rows, style, out, log=True, boxed=False):
    th = N.Theme(style); fg = th.fg; L, R, T, B = 150, 800, 258, 640
    sub = f"{len(rows)} CLOSEST NEAs · NEXT 7 DAYS · {'BOTH AXES LOGARITHMIC' if log else 'LINEAR SCALE'}"
    dts = sorted(str(r['approach_date'])[:10] for r in rows); rng = (dt.date.fromisoformat(dts[0]).strftime('%d %b') + ' – ' + dt.date.fromisoformat(dts[-1]).strftime('%d %b %Y')).upper()
    img, d = frame2(th, None, 'DISTANCE VS VELOCITY AND SIZE' + (' · ' + rng if boxed else ''), sub, L, R, T, B, th.pha if boxed else None)
    rad = lambda r: 8 + 1.6 * math.sqrt(r['dmid_km'] * 1000)
    pts = [(r['ld'], r['rel_velocity_kms'], rad(r)) for r in rows]
    xs = [min(r['ld'] for r in rows) * 0.8, max(r['ld'] for r in rows) * 1.1, True, False] if log else [0, max(r['ld'] for r in rows) * 1.05, False, True]
    ys = [min(r['rel_velocity_kms'] for r in rows) * 0.8, max(r['rel_velocity_kms'] for r in rows) * 1.1, True, False] if log else [0, max(r['rel_velocity_kms'] for r in rows) * 1.1, False, True]
    xs, ys = fit_axes(pts, xs, ys, L, R, T, B)
    if not log: xs[1] = nice_ceil(xs[1], 10); ys[1] = nice_ceil(ys[1], 5)
    ax_x = N.Ax(xs[0], xs[1], L, R, log); ax_y = N.Ax(ys[0], ys[1], B, T, log)
    xt = sorted(set(ticks_every(xs[0], xs[1], 10)) | (set(log_ticks(xs[0], xs[1], False)) if log else set()))
    xt = thin(xt, ax_x, 30)
    yt = log_ticks(ys[0], ys[1]) if log else lin_ticks(ys[0], ys[1], 5)
    if log: yt = thin(yt, ax_y, 24)
    dgrid(img, th, ax_x, ax_y, xt, yt, L, R, T, B)
    for v in corner_ticks(xt, xs[0], ax_x):
        x = ax_x.f(v); d.line([x, B, x, B + 8], fill=fg, width=2)
        N.text(img, (x + 4, B + 12), f"{v:g}" if v >= 1 or v == 0 else f"{v:.2f}", 19, fg, angle=45, anchor='tr')
    for v in xt:
        x = ax_x.f(v); d.line([x, T - 8, x, T], fill=fg, width=2)
        rot_rich(img, (x - 2, T - 14), elabel(v * LD), 17, fg, 45)
    for v in corner_ticks(yt, ys[0], ax_y, 22):
        y = ax_y.f(v); d.line([L - 8, y, L, y], fill=fg, width=2)
        N.text(img, (L - 12, y), f"{v:g}" if v >= 1 or v == 0 else f"{v:.2f}", 19, fg, anchor='rm')
    ordered = sorted(rows, key=lambda r: -r['rel_velocity_kms']); nm = {r['key']: i + 1 for i, r in enumerate(ordered)}
    bub = Image.new('RGBA', (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(bub); circles = []; hot = []
    for r in sorted(rows, key=lambda r: -r['dmid_km']):
        x, y, rr = ax_x.f(r['ld']), ax_y.f(r['rel_velocity_kms']), rad(r); c = size_color(r['dmid_km'])
        bd.ellipse([x - rr, y - rr, x + rr, y + rr], fill=c + (95,), outline=c + (255,), width=2)
    img.alpha_composite(bub); d = ImageDraw.Draw(img)
    for r in rows:
        x, y, rr = ax_x.f(r['ld']), ax_y.f(r['rel_velocity_kms']), rad(r); circles.append((x, y, rr))
        N.emoji(img, EMO[otype(r)], x, y, 27)
        t, h = obj_info(r, nm[r['key']]); hot.append({'x': x / W, 'y': y / H, 'r': max(rr, 14) / W, 't': f"{nm[r['key']]}. {t}", 'h': h})
    place_labels(th, img, [(ax_x.f(r['ld']), ax_y.f(r['rel_velocity_kms']), rad(r), str(nm[r['key']])) for r in rows], circles, (L + 3, T + 3, R - 3, B - 3))
    cx = (L + R) // 2; ty = B + 74
    N.text(img, (cx, ty), 'LUNAR DISTANCE (LD)', 26, fg, anchor='mt')
    N.text(img, (cx, T - 108), 'LUNAR DISTANCE (km)', 26, fg, anchor='mt')
    N.text(img, (TX, (T + B) // 2), 'RELATIVE VELOCITY (km/s)', 26, fg, angle=90, anchor='cc')
    # object list in a white box, as long as the LD axis title, with the title on the top line and a closing "15 CLOSEST NEAs" row
    bx0, bx1, by0, by1 = 832, W - 22, T, ty + 20; gold = th.pha; fs = 21; mid = (bx0 + bx1) / 2
    title = 'CLOSEST NEAs  TODAY' if boxed else 'SORTED BY VELOCITY (km/s)'; t_w = tw(title, fs)
    d.line([bx0, by0, mid - t_w / 2 - 10, by0], fill=fg, width=2); d.line([mid + t_w / 2 + 10, by0, bx1, by0], fill=fg, width=2)
    d.line([bx0, by0, bx0, by1], fill=fg, width=2); d.line([bx1, by0, bx1, by1], fill=fg, width=2); d.line([bx0, by1, bx1, by1], fill=fg, width=2)
    N.text(img, (mid, by0), title, fs, gold if boxed else fg, anchor='mm')
    top = by0 + 34; step = (by1 - 10 - top) / (len(ordered) + (2 if boxed else 1))
    for i, r in enumerate(ordered):
        y = top + i * step + step / 2
        N.text(img, (bx0 + 16, y), f"{nm[r['key']]}", fs, fg, anchor='lm'); N.emoji(img, EMO[otype(r)], bx0 + 16 + 50, y, 24)
        N.text(img, (bx0 + 16 + 72, y), r['designation'], fs, gold, anchor='lm')
        N.text(img, (bx1 - 16, y), f"{r['rel_velocity_kms']:.1f} km/s", fs, fg, anchor='rm')
    N.text(img, (mid, top + (len(ordered) + (1 if boxed else 0)) * step + step / 2), "SORTED BY VELOCITY (KM/S)" if boxed else f"{len(rows)} CLOSEST NEAs", fs, fg if boxed else gold, anchor='mm')
    if not boxed:
        legend(img, th, TYPE_ITEMS, ty + 62, cx); size_legend(img, th, ty + 104, cx)
    else:
        y1, y2 = ty + 80, ty + 143; lx = TX - 15                         # box left edge = left edge of the y-axis title
        l1, l2 = TYPE_ITEMS, size_items(SIZE_M)
        wid = max(legend_widths(l1)[1], legend_widths(l2, 26)[1]); x1b = lx + 32 + wid
        legend(img, th, l1, y1, 0, left=lx + 16); legend(img, th, l2, y2, 0, sep=26, left=lx + 16)
        dotted_box(d, fg, lx, y1 - 26, x1b, y2 + 26); ym = (y1 + y2) // 2
        vlen = ym + 30 - by1 - 14; hlen = max(112, min(vlen, 1124 - 150 - (x1b + 14)))   # horizontal arrow as long as the vertical one when room allows
        arrow(img, d, th, (x1b + 14, ym), 'left', length=hlen, shaft=8, thin=True); arrow(img, d, th, (1124, by1 + 14), 'up', length=vlen, shaft=8, thin=True)
        N.text(img, (x1b + 14 + hlen / 2, ym - 16), 'Object Type', 20, fg, anchor='mb'); N.text(img, (x1b + 14 + hlen / 2, ym + 16), 'Size', 20, fg, anchor='mt')
        serif_text(img, ((x1b + 14 + hlen + 1124 - 21) / 2, ym), 'LEGENDS', 38, LIGHT_GOLD if style == 'dark' else (196, 150, 0, 255), anchor='mm')
    save_hot(out, hot); img.save(out)

# ---------- 2. 3D ----------
def fig_3d(rows, style, out, grid=False, top=False, swap=False):
    """top=True: the LD values sit on the top line of the LD axis (the axis name stays on the bottom line)."""
    th = N.Theme(style); dark = style == 'dark'
    if dark:                                                              # PDD newspaper palette: navy ground, rose accent, pale ink, link blue
        th.bg = (11, 21, 38, 255); th.fg = (238, 242, 250, 255)
    fg = th.fg
    line = (222, 124, 124, 255) if dark else BLACK
    vline = (255, 228, 140, 255) if dark else (95, 95, 95, 255)
    wline = (138, 183, 234, 255) if dark else (120, 120, 120, 255)
    grid_col = (95, 95, 95, 255) if dark else (170, 170, 170, 255)
    img = Image.new('RGBA', (W, H), th.bg); d = ImageDraw.Draw(img)
    N.text(img, (60, 40), 'SIZE VS DISTANCE VS VELOCITY', 34, fg)
    N.text(img, (60, 90), f"{len(rows)} CLOSEST NEAs · NEXT 7 DAYS · LINEAR SCALE", 20, fg)
    xlo, xhi = 0.0, max(0.05, nice_ceil(max(r['dmid_km'] for r in rows) * 1.2, 0.05))   # always a free step above the largest object (0.3 now; hundreds of km works too)
    ylo = 1.0; yh = max(r['ld'] for r in rows) * 1.05; ystep = lin_step(yh - ylo, 6); yhi = nice_ceil(yh, ystep)
    zlo = 0.0; zhi = nice_ceil(max(r['rel_velocity_kms'] for r in rows) * 1.05, 5)
    ox, sx, oy, sy = 175, 530, 640, 400
    dep = (lambda r: r['rel_velocity_kms']) if swap else (lambda r: r['ld'])          # depth axis; swap = velocity in depth, lunar distance vertical
    ver = (lambda r: r['ld']) if swap else (lambda r: r['rel_velocity_kms'])
    (dlo, dhi), (vlo, vhi) = (((zlo, zhi), (ylo, yhi)) if swap else ((ylo, yhi), (zlo, zhi)))
    nu = lambda v: (v - xlo) / (xhi - xlo); nv = lambda v: (v - dlo) / (dhi - dlo); nw = lambda v: (v - vlo) / (vhi - vlo)
    P = lambda u, v, w: (ox + u * sx + v * 0.28 * sx, oy - w * sy - v * 0.22 * sy)
    xt = lin_ticks(xlo, xhi, 0.05 if xhi <= 1 else None); xt = [t for t in xt if t > 0] if len(xt) > 1 else xt
    yt = [ylo] + [t for t in lin_ticks(ylo, yhi, ystep) if t > ylo + ystep * 0.3]
    zt = lin_ticks(zlo, zhi, 5)
    dt, vt = (zt, yt) if swap else (yt, zt)
    if grid:
        for v in xt:
            V6.dotted(d, P(nu(v), 0, 0), P(nu(v), 1, 0), grid_col, 1, 2, 6); V6.dotted(d, P(nu(v), 0, 0), P(nu(v), 0, 1), grid_col, 1, 2, 6)
        for v in dt:
            V6.dotted(d, P(0, nv(v), 0), P(0, nv(v), 1), grid_col, 1, 2, 6)       # no grid on the LD (right) face of the cube
        for v in vt:
            V6.dotted(d, P(0, 0, nw(v)), P(1, 0, nw(v)), grid_col, 1, 2, 6); V6.dotted(d, P(0, 0, nw(v)), P(0, 1, nw(v)), grid_col, 1, 2, 6)
    corners = [(u, v, w) for u in (0, 1) for v in (0, 1) for w in (0, 1)]
    for a in corners:
        for b in corners:
            if a < b and sum(abs(p - q) for p, q in zip(a, b)) == 1:
                d.line([P(*a), P(*b)], fill=line, width=2)
    x, y = P(0, 0, 0); d.line([x, y, x, y + 10], fill=line, width=2); N.text(img, (x, y + 16), '0', 20, fg, anchor='mt')
    for v in xt:
        x, y = P(nu(v), 0, 0); d.line([x, y, x, y + 10], fill=line, width=2); N.text(img, (x, y + 16), f"{v:g}", 20, fg, anchor='mt')
    ang = math.degrees(math.atan2(0.22 * sy, 0.28 * sx)); ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    vs = 16 if top else 15
    TL = 20                                                               # tick marks twice as long, drawn inside the cube plane
    wl = wk = 0
    for v in dt:
        pl = [(f"{v:g}", 'n')]; pk = elabel(v * LD)
        wv = V6.rich(pl, vs, fg).size[0]; wkk = V6.rich(pk, vs, fg).size[0]; wl, wk = max(wl, wv), max(wk, wkk)
        x, y = P(1, nv(v), 0); d.line([x, y, x - TL, y], fill=line, width=2)          # bottom edge: LD (or velocity when swapped)
        rot_rich(img, (x + 9, y + 12 + wv), pl, vs, fg, 90)                              # read from the bottom up
        if not swap:
            x, y = P(1, nv(v), 1); d.line([x, y, x - TL, y], fill=line, width=2)      # top edge: km
            rot_rich(img, (x + 9, y - 10), pk, vs, fg, 90)
    ordered = sorted(rows, key=lambda r: -r['rel_velocity_kms']); nm = {r['key']: i + 1 for i, r in enumerate(ordered)}
    pos = {}; hot = []
    for r in rows:
        u, v = nu(r['dmid_km']), nv(dep(r)); V6.dotted(d, P(1, v, 0), P(u, v, 0), wline, 1, 3, 5)
    for r in sorted(rows, key=lambda r: -nv(dep(r))):
        u, v, w = nu(r['dmid_km']), nv(dep(r)), nw(ver(r))
        x0, y0 = P(u, v, 0); x1, y1 = P(u, v, w)
        V6.dotted(d, (x0, y0), (x1, y1), vline, 2, 5, 5)
        t = otype(r); N.emoji(img, EMO[t], x1, y1, 45 if t == 'pha' else 31); pos[r['key']] = (x1, y1)
        tt, h = obj_info(r, nm[r['key']]); hot.append({'x': x1 / W, 'y': y1 / H, 'r': 22 / W, 't': f"{nm[r['key']]}. {tt}", 'h': h})
    place_labels(th, img, [(pos[r['key']][0], pos[r['key']][1], 17, str(nm[r['key']])) for r in rows], [(pos[r['key']][0], pos[r['key']][1], 17) for r in rows], (60, 175, 905, 640), 15)
    x, y = P(0.5, 0, 0); N.text(img, (x, y + 52), 'OBJECT SIZE (km)', 26, fg, anchor='mt')
    bx, by = P(1, 0.5, 0); N.text(img, (bx + 4, by + 12 + wl + 30), 'RELATIVE VELOCITY (km/s)' if swap else 'LUNAR DISTANCE (LD)', 19, fg, angle=ang, anchor='cc')
    if not swap:
        tx_, ty_ = P(1, 0.5, 1); N.text(img, (tx_ + 4, ty_ - 10 - wk - 30), 'LUNAR DISTANCE (km)', 19, fg, angle=ang, anchor='cc')
    for wv_ in vt:                                                        # vertical axis values (front-left edge)
        x, y = P(0, 0, nw(wv_)); d.line([x - 10, y, x, y], fill=line, width=2); N.text(img, (x - 16, y), f"{wv_:g}", 20, fg, anchor='rm')
        if swap:                                                          # the same lunar distances in km on the front-right edge
            xr, yr = P(1, 0, nw(wv_)); d.line([xr, yr, xr + 10, yr], fill=line, width=2); V6.place_rich(img, (xr + 14, yr), elabel(wv_ * LD) + [(' km', 'n')], 14, fg, anchor='lm')
    N.text(img, (TX, P(0, 0, 0.5)[1]), 'LUNAR DISTANCE (LD)' if swap else 'RELATIVE VELOCITY (km/s)', 24, fg, angle=90, anchor='cc')
    lcx = P(0.5, 0, 0)[0] - 50                                            # legend under the object size axis
    legend(img, th, TYPE_ITEMS + ([('dots', vline, 'Distance'), ('dots', wline, 'Velocity')] if swap else [('dots', vline, 'Velocity'), ('dots', wline, 'Distance')]), oy + 132, 600, sep=26)   # one line
    big = max(rows, key=lambda r: r['dmid_km']); fast = max(rows, key=lambda r: r['rel_velocity_kms']); near = min(rows, key=lambda r: r['ld'])
    bt = f"TODAY'S BFC · Biggest: {big['designation']} · Fastest: {fast['designation']} · Closest: {near['designation']}"
    bw = tw(bt, 19) + 28; d.rectangle([40, H - 62, 40 + bw, H - 22], outline=fg, width=2); N.text(img, (54, H - 42), bt, 19, fg, anchor='lm')
    x0, x1b, y0b, y1b = 912, W - 16, 90, 650; gold = th.pha
    dotted_box(d, fg, x0, y0b, x1b, y1b)
    tt_ = 'SORTED BY VELOCITY (km/s)'; twd = tw(tt_, 20); N.text(img, ((x0 + x1b) / 2, y0b), tt_, 20, fg, anchor='mm') if False else None
    d.rectangle([(x0 + x1b) / 2 - twd / 2 - 8, y0b - 14, (x0 + x1b) / 2 + twd / 2 + 8, y0b + 14], fill=th.bg); N.text(img, ((x0 + x1b) / 2, y0b), tt_, 20, fg, anchor='mm')
    for i, r in enumerate(ordered):
        yy = 132 + i * 34
        N.emoji(img, EMO[otype(r)], x0 + 28, yy, 28); N.text(img, (x0 + 50, yy), f"{nm[r['key']]}", 20, fg, anchor='lm')
        N.text(img, (x0 + 84, yy), r['designation'], 18, gold, anchor='lm'); N.text(img, (x1b - 12, yy), f"{r['rel_velocity_kms']:.1f}", 18, fg, anchor='rm')
        h0 = [h for h in hot if h['t'].startswith(f"{nm[r['key']]}. ")][0]
        hot.append({'x': (x0 + 100) / W, 'y': yy / H, 'r': 20 / W, 't': h0['t'], 'h': h0['h']})
    save_hot(out, hot); img.save(out)

# ---------- 3. diameter vs distance ----------
def num_e(v):
    return [('0', 'n')] if v == 0 else elabel(v)

def fig_diameter(rows, style, out, log=True):
    th = N.Theme(style); fg = th.fg; L, R, T, B = 150, 1000, 160, 640
    sub = f"{len(rows)} CLOSEST NEAs · NEXT 7 DAYS · {'ALL AXES LOGARITHMIC' if log else 'LINEAR SCALE'}"
    img, d = frame2(th, None, 'DIAMETER VS DISTANCE', sub, L, R, T, B)
    pts = [(r['dmin_km'], r['ld'], 16) for r in rows] + [(r['dmax_km'], r['ld'], 16) for r in rows]
    xs = [min(r['dmin_km'] for r in rows) * 0.7, max(r['dmax_km'] for r in rows) * 1.05, True, False] if log else [0, max(r['dmax_km'] for r in rows) * 1.05, False, True]
    ys = [min(r['ld'] for r in rows) * 0.8, max(r['ld'] for r in rows) * 1.1, True, False] if log else [0, max(r['ld'] for r in rows) * 1.05, False, True]
    xs, ys = fit_axes(pts, xs, ys, L, R, T, B)
    if not log: xs[1] = nice_ceil(xs[1], 0.05); ys[1] = nice_ceil(ys[1], 10)
    ax_x = N.Ax(xs[0], xs[1], L, R, log); ax_y = N.Ax(ys[0], ys[1], B, T, log)
    xt = thin(log_ticks(xs[0], xs[1]), ax_x, 52) if log else lin_ticks(xs[0], xs[1], 0.05)
    yt = thin(log_ticks(ys[0], ys[1]), ax_y, 24) if log else lin_ticks(ys[0], ys[1], 10)
    dgrid(img, th, ax_x, ax_y, xt, yt, L, R, T, B)
    for v in corner_ticks(xt, xs[0], ax_x, 62):
        x = ax_x.f(v); d.line([x, B, x, B + 8], fill=fg, width=2); V6.place_rich(img, (x, B + 14), num_e(v), 19, fg, anchor='mt')
    for v in corner_ticks(yt, ys[0], ax_y, 22):
        y = ax_y.f(v)
        if v <= 0: N.text(img, (L - 12, y), '0', 19, fg, anchor='rm'); continue
        d.line([L - 8, y, L, y], fill=fg, width=2); N.text(img, (L - 12, y), f"{v:g}", 19, fg, anchor='rm')
    for v in yt:
        y = ax_y.f(v); d.line([R, y, R + 8, y], fill=fg, width=2); V6.place_rich(img, (R + 14, y), elabel(v * LD), 19, fg, anchor='lm')
    for r in rows:
        y = ax_y.f(r['ld']); x1, x2 = ax_x.f(r['dmin_km']), ax_x.f(r['dmax_km'])
        d.line([x1, y, x2, y], fill=th.pha, width=2)
        for xe in (x1, x2): d.line([xe, y - 9, xe, y + 9], fill=th.pha, width=2)      # end caps [ | ]
    hot = []
    for r in rows:
        t = otype(r); N.emoji(img, EMO[t], ax_x.f(r['dmid_km']), ax_y.f(r['ld']), 35 if t == 'pha' else 25)
        tt, h = obj_info(r); hot.append({'x': ax_x.f(r['dmid_km']) / W, 'y': ax_y.f(r['ld']) / H, 'r': 18 / W, 't': tt, 'h': h})
    ty = B + 66
    N.text(img, ((L + R) // 2, ty), 'OBJECT SIZE (km)', 26, fg, anchor='mt')
    N.text(img, (TX, (T + B) // 2), 'LUNAR DISTANCE (LD)', 26, fg, angle=90, anchor='cc')
    N.text(img, (R + 112, (T + B) // 2), 'LUNAR DISTANCE (km)', 26, fg, angle=90, anchor='cc')
    legend(img, th, TYPE_ITEMS + [('line', None, 'Error margin')], ty + 30 + 40, (L + R) // 2)
    save_hot(out, hot); img.save(out)

# ---------- 4. impact risk (JPL Sentry) ----------
def sentry_hot(o, kind_title=None):
    des = o['des']; q = des.replace(' ', '%20'); t = {'comet': 'Comet', 'pha': 'Potentially hazardous asteroid', 'mba': 'Main-belt asteroid', 'nea': 'Near-Earth object'}[otype(o)]
    rows = [('Palermo rank', f"{o['num']} of 15"), ('Palermo scale', o['ps']), ('Torino scale', o['ts']), ('Impact probability', f"{o['ip']:.2E}"),
            ('Possible impact', o['date'][:10]), ('Diameter', f"≈ {o.get('diam_km', 0)*1000:.0f} m ({o.get('diam_km', 0):.3f} km)"), ('Absolute magnitude', f"H {o['H']}")]
    if o.get('dist_au') is not None: rows.append(('Closest approach', f"{o['dist_au'] * 389.17:.1f} LD ({o['dist_au'] * 149597870.7:,.0f} km)"))
    url = f"{SBDB}{q}"
    return des, card(des, t, rows, url, lnk(f"https://cneos.jpl.nasa.gov/sentry/details.html#?des={q}", 'JPL Sentry') + ' · ' + lnk(url, 'JPL SSD (SBDB)') + ' · ' + lnk(f"{MPC}{q}", 'Minor Planet Center'))

def top3(objs):
    return {o['des'] for o in sorted(objs, key=lambda o: -o['ip'])[:3]}

def emo_of(o, t3):
    return 'warn' if o['des'] in t3 else otype(o)

IMP_TYPES = TYPE_ITEMS + [('warn', None, 'Top 3 probability')]

def culprit_of(objs):
    """the object behind the alert: highest cumulative Palermo among those that can hit within 200 years."""
    lim = dt.date.today().year + 200
    c = [o for o in objs if o.get('year') and o['year'] <= lim]
    return max(c, key=lambda o: o['ps']) if c else None

def sentry_list(img, d, th, objs, x0, y0, x1, y1, t3, title='BY POSSIBLE IMPACT YEAR'):
    """dotted box with the objects: emoji, number, designation, year (or range of years)."""
    fg = th.fg; dotted_box(d, fg, x0, y0, x1, y1); tt_ = tw(title, 19); mx = (x0 + x1) / 2
    d.rectangle([mx - tt_ / 2 - 8, y0 - 14, mx + tt_ / 2 + 8, y0 + 14], fill=th.bg); N.text(img, (mx, y0), title, 19, fg, anchor='mm')
    step = min(34, (y1 - y0 - 40) / max(len(objs), 1))
    for i, o in enumerate(sorted(objs, key=lambda o: (o['year'], o['num']))):
        yy = y0 + 34 + i * step; rg = str(o.get('range') or o.get('date') or int(o['year'])); a, _, b = rg.partition('-')
        N.emoji(img, EMO[emo_of(o, t3)], x0 + 26, yy, 26); N.text(img, (x0 + 46, yy), f"{o['num']}", 20, fg, anchor='lm')
        N.text(img, (x0 + 82, yy), o['des'], 17, th.pha, anchor='lm'); N.text(img, (x1 - 12, yy), a if (not b or a == b) else f"{a}–{b}", 17, fg, anchor='rm')

def impact_table(img, th, objs, t3, y0, hot=None):
    """data table under the chart: all the values we have, with a caption."""
    d = ImageDraw.Draw(img); fg = th.fg; cols = [('#', 70), ('OBJECT', 170), ('IMPACT YEAR(S)', 210), ('PROBABILITY', 150), ('PALERMO', 120), ('TORINO', 100), ('DIAMETER (km)', 170), ('DISTANCE (LD)', 150)]
    x = 40; xs = []
    for n, w in cols: xs.append(x); x += w
    for (n, w), xx in zip(cols, xs): N.text(img, (xx, y0), n, 17, th.pha)
    d.line([40, y0 + 26, W - 40, y0 + 26], fill=fg, width=1)
    for i, o in enumerate(sorted(objs, key=lambda o: (o['year'], o['num']))):
        yy = y0 + 52 + i * 32; rg = str(o.get('range') or o.get('date') or int(o['year']))
        a_, _, b_ = rg.partition('-'); vals = [str(o['num']), o['des'], (a_ if (not b_ or a_ == b_) else f'{a_}–{b_}'), f"{o['ip']:.1e}", f"{o['ps']:.2f}", str(o['ts']), f"{o.get('diam_km', 0):.3g}", ('—' if o.get('dist_au') is None else f"{o['dist_au'] * 389.17:.1f}")]
        N.emoji(img, EMO[emo_of(o, t3)], xs[0] + 14, yy, 22)
        for k, (v, xx) in enumerate(zip(vals, xs)):
            if k == 0: N.text(img, (xx + 34, yy), v, 17, fg, anchor='lm')
            else: N.text(img, (xx, yy), v, 17, th.pha if k == 1 else fg, anchor='lm')
    cy = y0 + 52 + len(objs) * 32 + 10
    import textwrap
    cap = ('Table: the 15 objects with the highest cumulative Palermo value on JPL’s Sentry risk table, ordered by possible impact year. Probability is the cumulative impact probability; the Palermo and Torino scales rate the risk; '
           'distance is the closest approach in lunar distances (LD) from NASA/JPL CNEOS. Source: JPL Sentry and CNEOS, refreshed automatically every 8 hours.')
    for k, ln in enumerate(textwrap.wrap(cap, 118)): N.text(img, (40, cy + 22 * k), ln, 16, fg)

def impact_dual(objs, style, out, alert=None, table=False):
    th = N.Theme(style); fg = th.fg; L, R, T, B = 150, 740, 290, 620
    pts = [o for o in objs if o.get('dist_au') is not None]; t3 = top3(objs); cul = culprit_of(objs) if alert and not alert[0].startswith('All Good') else None
    img, d = frame2(th, 'IMPACT RISK', 'DISTANCE VS TORINO AND PALERMO SCALES', f"{len(pts)} OF THE 15 HIGHEST-RISK OBJECTS (JPL SENTRY) HAVE A KNOWN APPROACH DISTANCE", L, R, T, B)
    ldv = {o['des']: o['dist_au'] * 389.17 for o in pts}
    rad = lambda o: 6 + 3 * math.sqrt(o.get('diam_km', 0.01) * 1000)
    lo_x = min(ldv.values()) * 0.8; hi_x = max(ldv.values()) + 1.0
    ps_lo = math.floor(min(o['ps'] for o in pts) - 1.5); ps_hi = math.ceil(max(o['ps'] for o in pts) + 1.5)
    ps_lo -= ps_lo % 2; ps_hi += ps_hi % 2
    ax_l = N.Ax(-0.6, 10.5, B, T, False); ax_r = N.Ax(ps_lo, ps_hi, B, T, False)
    fx = fit_axes([(ldv[o['des']], 1, rad(o)) for o in pts], [lo_x, hi_x, True, False], [0, 1, False, True], L, R, T, B)[0]
    ax_x = N.Ax(fx[0], fx[1], L, R, True)
    xt = thin(log_ticks(fx[0], fx[1]), ax_x, 36)
    dgrid(img, th, ax_x, ax_l, xt, [], L, R, T, B)
    for v in xt:
        x = ax_x.f(v); d.line([x, B, x, B + 8], fill=fg, width=2); N.text(img, (x + 4, B + 12), f"{v:g}", 22, fg, angle=45, anchor='tr')
    for kv in thin(log_ticks(fx[0] * LD, fx[1] * LD, False), N.Ax(fx[0] * LD, fx[1] * LD, L, R, True), 34):
        x = ax_x.f(kv / LD); d.line([x, T - 8, x, T], fill=fg, width=2); rot_rich(img, (x - 2, T - 14), elabel(kv), 19, fg, 45)
    for v in range(0, 11):
        y = ax_l.f(v); d.line([L - 8, y, L, y], fill=fg, width=2); N.text(img, (L - 12, y), f"{v}", 22, fg, anchor='rm')
    for v in range(ps_lo, ps_hi + 1, 2):
        y = ax_r.f(v); d.line([R, y, R + 8, y], fill=fg, width=2); N.text(img, (R + 12, y), f"{v}", 22, fg, anchor='lm')
    fill = Image.new('RGBA', (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(fill); circles = []; hot = []
    for o in pts:
        x = ax_x.f(ldv[o['des']]); yp = ax_r.f(o['ps']); rr = rad(o); c = size_color(o.get('diam_km', 0.01))
        fd.ellipse([x - rr, yp - rr, x + rr, yp + rr], fill=c + (110,), outline=c + (255,), width=2); circles.append((x, yp, rr))
    img.alpha_composite(fill); d = ImageDraw.Draw(img)
    for o in pts:
        x = ax_x.f(ldv[o['des']]); yt_ = ax_l.f(o['ts']); yp = ax_r.f(o['ps'])
        V6.dotted(d, (x, yt_), (x, yp), fg, 1, 3, 3)
        N.emoji(img, EMO['target'], x, yt_, 25)
        if cul is not None and o['des'] == cul['des']: culxy = (x, yp, 31, EMO[emo_of(o, t3)])           # flashes with the alert
        else: N.emoji(img, EMO[emo_of(o, t3)], x, yp, 31)
        t, h = sentry_hot(o); hot.append({'x': x / W, 'y': yp / H, 'r': 16 / W, 't': f"{o['num']}. {t}", 'h': h})
    place_labels(th, img, [(ax_x.f(ldv[o['des']]), ax_r.f(o['ps']), rad(o), str(o['num'])) for o in pts], circles, (L + 3, T + 3, R - 3, B - 3), 19)
    cx = 600; ty = B + 78
    N.text(img, (TX, (T + B) // 2), 'TORINO SCALE (0–10)', 24, fg, angle=90, anchor='cc')
    N.text(img, (R + 80, (T + B) // 2), 'PALERMO SCALE', 24, fg, angle=90, anchor='cc')
    N.text(img, ((L + R) // 2, ty), 'LUNAR DISTANCE (LD, log)', 26, fg, anchor='mt')
    N.text(img, ((L + R) // 2, T - 112), 'LUNAR DISTANCE (km, log)', 26, fg, anchor='mt')
    legend(img, th, IMP_TYPES + [('target', None, 'Torino')], ty + 78, cx); size_legend(img, th, ty + 122, cx, SIZE_M)      # one more line of space before the legend
    sentry_list(img, d, th, pts, 856, T, W - 16, B + 10, t3)
    save_hot(out, hot)
    if table:                                                                         # alternate version: the same chart with a data table and caption under it
        big = Image.new('RGBA', (W, H + 40 + 52 + len(pts) * 32 + 100), th.bg); big.alpha_composite(img); impact_table(big, th, pts, t3, H + 30); watermark(big, style).save(out); h2 = big.size[1]; hj = json.load(open(os.path.splitext(out)[0] + '.json')); hj['h'] = h2
        for q in hj['pts']: q['y'] = q['y'] * H / h2
        json.dump(hj, open(os.path.splitext(out)[0] + '.json', 'w')); return
    if alert:
        txt, col, sec = alert; a_ = img.copy(); N.text(a_, (60 + tw('IMPACT RISK', 34), 24), ': ' + txt, 34, col)
        if cul is not None: N.emoji(a_, culxy[3], culxy[0], culxy[1], culxy[2])
        watermark(a_, style).save(out, save_all=True, append_images=[watermark(img, style)], duration=[int(sec * 1000)] * 2, loop=0, format='PNG')
    else: img.save(out)

def impact_year(objs, style, out):
    """impact year (years from now, logarithmic) vs probability, with diameter on the right axis."""
    th = N.Theme(style); fg = th.fg; L, R, T, B = 160, 1000, 215, 590; y0 = dt.date.today().year; t3 = top3(objs)
    img, d = frame2(th, 'IMPACT RISK', 'POSSIBLE IMPACT YEAR VS PROBABILITY AND DIAMETER', f"15 OBJECTS · TOP 15 BY PALERMO · YEARS COUNTED FROM {y0}, LOGARITHMIC", L, R, T, B)
    yrs = {o['des']: max(o['year'] - y0, 1) for o in objs}; dia = lambda o: max(o.get('diam_km', 0.01), 1e-4)
    fx = fit_axes([(yrs[o['des']], o['ip'], 18) for o in objs], [min(yrs.values()) * 0.7, max(yrs.values()) * 1.3, True, False],
                  [min(o['ip'] for o in objs) / 2, max(o['ip'] for o in objs) * 2, True, False], L, R, T, B)
    ax_x = N.Ax(*fx[0][:2], L, R, True); ax_p = N.Ax(fx[1][0], fx[1][1], B, T, True)
    ax_d = N.Ax(min(dia(o) for o in objs) / 1.8, max(dia(o) for o in objs) * 1.8, B, T, True)
    xt = thin([t for t in log_ticks(fx[0][0], fx[0][1]) if t >= 1], ax_x, 36); pt_ = [10 ** e * m for e in range(-12, 1) for m in (1, 3) if fx[1][0] <= 10 ** e * m <= fx[1][1]]
    dt_ = thin(log_ticks(ax_d.lo, ax_d.hi), ax_d, 24)
    dgrid(img, th, ax_x, ax_p, xt, pt_, L, R, T, B)
    for v in xt:
        x = ax_x.f(v); d.line([x, B, x, B + 8], fill=fg, width=2)
        N.text(img, (x + 4, B + 12), f"{v:g} ({y0 + v:.0f})", 17, fg, angle=45, anchor='tr')
    for v in pt_:
        y = ax_p.f(v); d.line([L - 8, y, L, y], fill=fg, width=2); V6.place_rich(img, (L - 12, y), elabel(v), 19, fg, anchor='rm')
    for v in dt_:
        y = ax_d.f(v); d.line([R, y, R + 8, y], fill=fg, width=2); V6.place_rich(img, (R + 14, y), num(v), 19, fg, anchor='lm')
    grey = (170, 170, 170, 255) if fg == WHITE else (110, 110, 110, 255)
    for o in objs:
        x, y, yd = ax_x.f(yrs[o['des']]), ax_p.f(o['ip']), ax_d.f(dia(o))
        V6.dotted(d, (x, y), (R, yd), grey, 1, 3, 4); d.ellipse([R - 7, yd - 7, R + 7, yd + 7], fill=fg, outline=th.bg if th.bg[3] else None)
    hot = []; circles = []
    for o in objs:
        x, y = ax_x.f(yrs[o['des']]), ax_p.f(o['ip']); circles.append((x, y, 16)); N.emoji(img, EMO[emo_of(o, t3)], x, y, 30)
        t, h = sentry_hot(o); hot.append({'x': x / W, 'y': y / H, 'r': 16 / W, 't': f"{o['num']}. {t}", 'h': h})
    place_labels(th, img, [(ax_x.f(yrs[o['des']]), ax_p.f(o['ip']), 16, str(o['num'])) for o in objs], circles, (L + 3, T + 3, R - 3, B - 3))
    cx = (L + R) // 2; ty = B + 100
    N.text(img, (cx, ty), f'YEARS FROM {y0} (CALENDAR YEAR IN BRACKETS, LOG)', 26, fg, anchor='mt')
    N.text(img, (TX, (T + B) // 2), 'IMPACT PROBABILITY (log)', 24, fg, angle=90, anchor='cc')
    N.text(img, (R + 78, (T + B) // 2), 'DIAMETER (km, log)', 24, fg, angle=90, anchor='cc')
    legend(img, th, IMP_TYPES + [('dot', fg, 'Diameter')], ty + 62, cx)
    save_hot(out, hot); img.save(out)

def impact_timeline(objs, style, out, alert=None):
    """century timeline: empty centuries are skipped; inside each column objects sit at their year; height = probability."""
    th = N.Theme(style); fg = th.fg; L, R, T, B = 160, 1040, 215, 590; t3 = top3(objs); cul = culprit_of(objs) if alert and not alert[0].startswith('All Good') else None
    img, d = frame2(th, 'IMPACT RISK', 'IMPACT TIMELINE BY CENTURY, PROBABILITY AND DIAMETER', "EMPTY CENTURIES ARE SKIPPED · CIRCLE SIZE AND COLOUR = DIAMETER", L, R, T, B)
    y0 = dt.date.today().year; cents = sorted({int(o['year'] // 100) * 100 for o in objs}); n = len(cents); colw = (R - L) / n
    cs = lambda c: max(c, y0 - 12); span = lambda c: c + 100 - cs(c)               # the current century starts today
    rr_of = lambda o: 7 + 2.0 * math.sqrt(max(o.get('diam_km', 0.01), 1e-4) * 1000)
    ys_ = fit_axes([(1, o['ip'], rr_of(o)) for o in objs], [0.5, 2, False, True], [min(o['ip'] for o in objs) / 2, max(o['ip'] for o in objs) * 2, True, False], L, R, T, B)[1]
    ax_p = N.Ax(ys_[0], ys_[1], B, T, True)
    pt_ = [10 ** e * m for e in range(-12, 1) for m in (1, 3) if ys_[0] <= 10 ** e * m <= ys_[1]]
    dgrid(img, th, N.Ax(0, 1, L, R, False), ax_p, [], pt_, L, R, T, B)
    for i, c in enumerate(cents):
        x0 = L + i * colw
        if i: V6.dotted(d, (x0, T), (x0, B), (200, 200, 200, 120) if fg == WHITE else (0, 0, 0, 90), 1, 4, 4)
        N.text(img, (x0 + colw / 2, B + 36), f"{c}s", 22, fg, anchor='mt')
        for q in (0.25, 0.5, 0.75):
            xx = x0 + q * colw; d.line([xx, B, xx, B + 6], fill=fg, width=2); N.text(img, (xx, B + 10), f"{cs(c) + q * span(c):.0f}", 15, fg, anchor='mt')
    for v in pt_:
        y = ax_p.f(v); d.line([L - 8, y, L, y], fill=fg, width=2); V6.place_rich(img, (L - 12, y), e0(v), 19, fg, anchor='rm', sup=3)
    fill = Image.new('RGBA', (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(fill); circles = []; hot = []; XY = {}
    for o in objs:
        c = int(o['year'] // 100) * 100; x = L + cents.index(c) * colw + (0.05 + 0.9 * (o['year'] - cs(c)) / span(c)) * colw; y = ax_p.f(o['ip'])
        rr = rr_of(o); col = size_color(o.get('diam_km', 0.01)); XY[o['des']] = (x, y, rr)
        fd.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col + (110,), outline=col + (255,), width=2); circles.append((x, y, rr))
    img.alpha_composite(fill)
    for o in objs:
        x, y, rr = XY[o['des']]
        if cul is not None and o['des'] == cul['des']: culxy = (x, y, 28, EMO[emo_of(o, t3)])
        else: N.emoji(img, EMO[emo_of(o, t3)], x, y, 28)
        t, h = sentry_hot(o); hot.append({'x': x / W, 'y': y / H, 'r': max(rr, 14) / W, 't': f"{o['num']}. {t}", 'h': h})
    place_labels(th, img, [(XY[o['des']][0], XY[o['des']][1], XY[o['des']][2], str(o['num'])) for o in objs], circles, (L + 3, T + 3, R - 3, B - 3))
    cx = (L + R) // 2; ty = B + 76
    N.text(img, (cx, ty), 'POSSIBLE IMPACT YEAR (BY CENTURY)', 26, fg, anchor='mt')
    N.text(img, (TX, (T + B) // 2), 'IMPACT PROBABILITY (log)', 24, fg, angle=90, anchor='cc')
    legend(img, th, IMP_TYPES, ty + 64, cx); size_legend(img, th, ty + 106, cx, SIZE_KM_PLAIN)
    save_hot(out, hot)
    if alert:                                                    # flashing title: ': <alert>' on / off
        txt, col, sec = alert; a = img.copy(); N.text(a, (60 + tw('IMPACT RISK', 34), 24), ': ' + txt, 34, col)
        if cul is not None: N.emoji(a, culxy[3], culxy[0], culxy[1], culxy[2])
        watermark(a, style).save(out, save_all=True, append_images=[watermark(img, style)], duration=[int(sec * 1000)] * 2, loop=0, format='PNG')
    else: img.save(out)


TIERS = [('Lets see what happens!', (255, 105, 97, 255), 1.2), ('Time for everyone to look up!', (255, 182, 193, 255), 1.3),
         ('We are checking stuff out', (253, 253, 150, 255), 1.5), ('All Good, we keep looking up!', (119, 221, 119, 255), 1.7)]

def alert_level(objs, out_json=None):
    """highest Torino and (cumulative) Palermo value in the Sentry feed -> (text, colour, flash seconds)."""
    ps = [o['ps'] for o in objs]; ts = [o['ts'] for o in objs]; src = 'top-15 file'
    import datetime as _d; lim = _d.date.today().year + 200                  # only objects that can hit within the next two centuries trigger the alert
    try:
        data = json.load(urllib.request.urlopen('https://ssd-api.jpl.nasa.gov/sentry.api', timeout=25))['data']
        ps, ts = [], []
        for x in data:
            try:
                if int(str(x.get('range', x.get('date', '9999'))).split('-')[0]) > lim: continue
            except Exception: pass
            for key, lst, cast in (('ps_cum', ps, float), ('ts_max', ts, int)):
                try: lst.append(cast(x[key]))
                except Exception: pass
        src = f'JPL Sentry feed, {len(data)} objects (impact within 200 years: {len(ts)})'
    except Exception: pass
    mt, mp = max(ts or [0]), max(ps or [-99])
    tier = 0 if (mt >= 8 or mp >= 2.0) else 1 if (mt >= 5 or mp >= 0.0) else 2 if (mt >= 2 or mp >= -2.0) else 3
    if out_json: json.dump({'tier': 4 - tier, 'text': TIERS[tier][0], 'max_torino': mt, 'max_palermo': mp, 'source': src}, open(out_json, 'w'))
    return TIERS[tier]

def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    rows, logd = data_rows(); sent = load_sentry(); alert = alert_level(sent, os.path.join(out, 'alert.json'))
    P_ = lambda n: os.path.join(out, n)
    if not rows: print('WARNING: no close approaches in the next 7 days; skipping the charts that need them', flush=True)
    for style in ('dark', 'transparent'):
        if rows: fig_bubbles(rows, style, P_(f'1-3-distance-velocity-size-log-{style}.png'), True)
        if rows: fig_bubbles(rows, style, P_(f'1-3c-distance-velocity-size-log-legends-{style}.png'), True, boxed=True)
        if rows: fig_bubbles(rows, style, P_(f'1-3b-distance-velocity-size-linear-{style}.png'), False)
        if rows: fig_bubbles(rows, style, P_(f'1-3d-distance-velocity-size-linear-legends-{style}.png'), False, boxed=True)
        fig_cum(logd, style, P_(f'07-cumulative-log-{style}.png'), log=True)
        fig_cum(logd, style, P_(f'08-cumulative-linear-{style}.png'), log=False)
        if rows: fig_3d(rows, style, P_(f'2-3-3d-{style}.png'))
        if rows: fig_3d(rows, style, P_(f'2-3c-3d-ld-top-{style}.png'), top=True)
        if rows: fig_diameter(rows, style, P_(f'3-diameter-vs-distance-log-{style}.png'), True)
        if rows: fig_diameter(rows, style, P_(f'3b-diameter-vs-distance-linear-{style}.png'), False)
        impact_dual(sent, style, P_(f'imp1-distance-torino-palermo-{style}.png'), alert=alert)
        impact_dual(sent, style, P_(f'imp1b-distance-torino-palermo-table-{style}.png'), table=True)
        impact_timeline(sent, style, P_(f'imp3-timeline-century-{style}.png'))
        impact_timeline(sent, style, P_(f'imp3b-timeline-century-alert-{style}.png'), alert=alert)
    if rows: fig_3d(rows, 'dark', P_('2-3-3d-dark-grid.png'), grid=True)
    for style in ('dark', 'transparent') if rows else (): fig_3d(rows, style, P_(f'2-3d-3d-swapped-axes-{style}.png'), swap=True)
    for f in sorted(os.listdir(out)):                                   # sign every chart (the flashing ones are signed frame by frame)
        if f.endswith('.png') and 'alert' not in f:
            im = Image.open(P_(f)).convert('RGBA'); watermark(im, 'transparent' if 'transparent' in f else 'dark').save(P_(f))
    print(len([f for f in os.listdir(out) if f.endswith('.png')]), 'charts; alert:', alert[0])

if __name__ == '__main__':
    main()
