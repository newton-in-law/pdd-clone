#!/usr/bin/env python3
"""NEA capture log for Newsroom Floor's Planetary Defense Daily and Space Luisa.

1. Fetches near-Earth objects from NASA NeoWs (api.nasa.gov/neo/rest/v1/feed).
2. Looks up each object's discovery date and site in JPL SBDB (ssd-api.jpl.nasa.gov/sbdb.api).
3. Appends new rows to nea_log.json (never duplicates; key = NEO id + approach date).
4. Rebuilds nea_log.xlsx from the JSON (a single sheet "NEA").
5. Draws the charts into --charts OUTDIR.

Usage:
  /usr/bin/python3 nea_log.py --start 2026-11-01 --end 2026-11-22 --charts OUTDIR
"""
import argparse, datetime as dt, json, math, os, re, time, urllib.parse, urllib.request, zipfile
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
LOG_JSON = os.path.join(HERE, 'nea_log.json')
LOG_XLSX = os.path.join(HERE, 'nea_log.xlsx')
NEOWS_KEY = os.environ.get('NASA_API_KEY') or 'DEMO_KEY'
LD_KM = 384400.0
COLUMNS = ['key', 'neo_id', 'name', 'designation', 'approach_utc', 'approach_date', 'miss_km', 'miss_ld',
           'rel_velocity_kms', 'H_mag', 'diam_min_m', 'diam_max_m', 'pha', 'sentry',
           'discovery_date', 'discovery_site', 'discovery_name', 'discovery_ref', 'first_seen', 'jpl_url', 'source']
PHA_EMOJI = '\U0001F4A5'    # boom
ROCK_EMOJI = '\U0001FAA8'   # rock


# ---------- data ----------
def get_json(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode())


def fetch_feed(start, end):
    out, s, e = [], dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    while s <= e:
        c = min(e, s + dt.timedelta(days=6))           # NeoWs allows 7-day windows
        d = get_json(f"https://api.nasa.gov/neo/rest/v1/feed?start_date={s}&end_date={c}&api_key={NEOWS_KEY}")
        for day in d['near_earth_objects'].values():
            out.extend(day)
        s = c + dt.timedelta(days=1)
        time.sleep(1)
    return out


def designation(name):
    m = re.search(r'\(([^)]+)\)', name)
    return m.group(1) if m else name.strip()


def discovery(des):
    try:
        d = get_json('https://ssd-api.jpl.nasa.gov/sbdb.api?sstr=' + urllib.parse.quote(des) + '&discovery=1')
        disc = d.get('discovery') or {}
        return {'discovery_date': disc.get('date'), 'discovery_site': disc.get('location'),
                'discovery_name': disc.get('name'), 'discovery_ref': disc.get('ref')}
    except Exception:
        return {}


def normalize(o, captured_on):
    ca = o['close_approach_data'][0]
    dia = o['estimated_diameter']['meters']
    return {
        'key': f"{o['neo_reference_id']}|{ca['close_approach_date']}",
        'neo_id': o['neo_reference_id'], 'name': o['name'], 'designation': designation(o['name']),
        'approach_utc': ca['close_approach_date_full'], 'approach_date': ca['close_approach_date'],
        'miss_km': float(ca['miss_distance']['kilometers']), 'miss_ld': float(ca['miss_distance']['lunar']),
        'rel_velocity_kms': float(ca['relative_velocity']['kilometers_per_second']),
        'H_mag': o['absolute_magnitude_h'],
        'diam_min_m': dia['estimated_diameter_min'], 'diam_max_m': dia['estimated_diameter_max'],
        'pha': bool(o['is_potentially_hazardous_asteroid']), 'sentry': bool(o['is_sentry_object']),
        'jpl_url': o['nasa_jpl_url'], 'first_seen': captured_on,
        'source': 'NASA NeoWs feed (api.nasa.gov); JPL SBDB discovery (ssd-api.jpl.nasa.gov)',
    }


def load_log():
    if os.path.exists(LOG_JSON):
        return json.load(open(LOG_JSON, encoding='utf-8'))
    return {'rows': []}


def append_rows(new_rows):
    log = load_log()
    idx = {r['key']: i for i, r in enumerate(log['rows'])}
    added = 0
    for r in new_rows:
        if r['key'] in idx:
            old = log['rows'][idx[r['key']]]
            keep_first = old.get('first_seen')
            log['rows'][idx[r['key']]] = {**old, **r, 'first_seen': keep_first}
        else:
            log['rows'].append(r)
            added += 1
    log['updated'] = dt.date.today().isoformat()
    json.dump(log, open(LOG_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return added


# ---------- xlsx (no openpyxl needed) ----------
def col_name(i):
    s, i = '', i + 1
    while i:
        i, rem = divmod(i - 1, 26)
        s = chr(65 + rem) + s
    return s


def write_xlsx(rows, path):
    def cell(ref, v):
        if v is None or v == '':
            return ''
        if isinstance(v, bool):
            return f'<c r="{ref}" t="inlineStr"><is><t>{"Sí" if v else "No"}</t></is></c>'
        if isinstance(v, (int, float)):
            return f'<c r="{ref}"><v>{v}</v></c>'
        return f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(v))}</t></is></c>'
    body = ['<row r="1">' + ''.join(cell(f'{col_name(j)}1', h) for j, h in enumerate(COLUMNS)) + '</row>']
    for i, r in enumerate(rows, start=2):
        body.append(f'<row r="{i}">' + ''.join(cell(f'{col_name(j)}{i}', r.get(h)) for j, h in enumerate(COLUMNS)) + '</row>')
    X = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    sheet = (X + '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
             + ''.join(body) + '</sheetData></worksheet>')
    ct = (X + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
          '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
    rels = (X + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
    wb = (X + '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
          '<sheets><sheet name="NEA" sheetId="1" r:id="rId1"/></sheets></workbook>')
    wbrels = (X + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
              '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ct)
        z.writestr('_rels/.rels', rels)
        z.writestr('xl/workbook.xml', wb)
        z.writestr('xl/_rels/workbook.xml.rels', wbrels)
        z.writestr('xl/worksheets/sheet1.xml', sheet)


# ---------- charts (PIL) ----------
from PIL import Image, ImageDraw, ImageFont

import os as _os
_FD = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'fonts')
# macOS fonts when present; otherwise (GitHub Actions, Linux) the fonts bundled in ./fonts. CHART_FONTS=bundled forces the bundled ones.
BUNDLED = _os.environ.get('CHART_FONTS') == 'bundled' or not _os.path.exists('/System/Library/Fonts/Supplemental/Arial.ttf')
FR = _os.path.join(_FD, 'LiberationSans-Regular.ttf') if BUNDLED else '/System/Library/Fonts/Supplemental/Arial.ttf'            # Liberation Sans is metric-compatible with Arial
FB = _os.path.join(_FD, 'LiberationSans-Bold.ttf') if BUNDLED else '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
EMOJI_FONT = _os.path.join(_FD, 'NotoColorEmoji.ttf') if BUNDLED else '/System/Library/Fonts/Apple Color Emoji.ttc'
EMOJI_SIZE = 109 if BUNDLED else 160                                                                                              # Noto Color Emoji has a single 109 px bitmap size
PLAYFAIR = _os.path.join(_FD, 'PlayfairDisplay.ttf')                                                                              # the newspaper's header font
W, H = 1200, 900
SUP = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹', '-': '⁻'}
MES_ES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
LD_KM = 384400.0
GOLD = (255, 199, 0, 255)
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
STR = {
    'en': dict(disp_title='Diameter vs Distance', disp_sub='{n} NEAs · next 7 days · {scale}',
               scale_log='logarithmic scale', scale_lin='linear scale',
               bub_title='Distance vs Velocity and Size',
               bub_sub='{n} NEAs · next 7 days · {scale} · bubble area = mean size',
               x_dist_log='Lunar Distance (LD | Km | log)', x_dist_lin='Lunar Distance (LD | Km)',
               y_vel='Relative Velocity (km/s)', size_key='Bubble size key · mean size (km)',
               d3_title='Size vs Distance vs Velocity - 3D plot', d3_sub='{n} NEAs · next 7 days · {scale}',
               x_size_log='Object Size (km | log)', x_size_lin='Object Size (km)',
               y_dist_log='Lunar Distance (LD | Km | log)', y_dist_lin='Lunar Distance (LD | Km)',
               leg_stem='Vertical line = velocity above the floor', leg_edge='Box edges = the three axes',
               pc_title='Parallel coordinates · size, distance, velocity', pc_sub='{n} NEAs · next 7 days · {scale}',
               pc_size='Size (km)', pc_dist='Distance (LD | Km)', pc_vel='Velocity (km/s)',
               cum_title='Cumulative NEAs since first capture',
               cum_sub='{start} to {end} · distinct NEAs by close-approach date (NASA feed) · {scale}',
               leg_pha='Potentially hazardous (PHA)', leg_rock='Other NEA', leg_unc='Size uncertainty range',
               list_title='PHA first · size km · LD', x_date='Close-approach date', y_cnt='Cumulative NEAs',
               cum_all='All NEAs', cum_pha='PHA'),
    'es': dict(disp_title='Diámetro vs Distancia', disp_sub='{n} NEA · próximos 7 días · {scale}',
               scale_log='escala logarítmica', scale_lin='escala lineal',
               bub_title='Distancia vs Velocidad y Tamaño',
               bub_sub='{n} NEA · próximos 7 días · {scale} · área de burbuja = tamaño medio',
               x_dist_log='Distancia Lunar (LD | Km | log)', x_dist_lin='Distancia Lunar (LD | Km)',
               y_vel='Velocidad relativa (km/s)', size_key='Clave de tamaño de burbuja · tamaño medio (km)',
               d3_title='Tamaño vs Distancia vs Velocidad - gráfica 3D', d3_sub='{n} NEA · próximos 7 días · {scale}',
               x_size_log='Tamaño del objeto (km | log)', x_size_lin='Tamaño del objeto (km)',
               y_dist_log='Distancia Lunar (LD | Km | log)', y_dist_lin='Distancia Lunar (LD | Km)',
               leg_stem='Línea vertical = velocidad sobre el piso', leg_edge='Aristas = los tres ejes',
               pc_title='Coordenadas paralelas · tamaño, distancia, velocidad', pc_sub='{n} NEA · próximos 7 días · {scale}',
               pc_size='Tamaño (km)', pc_dist='Distancia (LD | Km)', pc_vel='Velocidad (km/s)',
               cum_title='NEA acumulados desde la primera captura',
               cum_sub='{start} a {end} · NEA distintos por fecha de acercamiento (feed de NASA) · {scale}',
               leg_pha='Potencialmente peligroso (PHA)', leg_rock='Otro NEA', leg_unc='Rango de incertidumbre de tamaño',
               list_title='PHA primero · tamaño km · LD', x_date='Fecha de acercamiento', y_cnt='NEA acumulados',
               cum_all='Todos los NEA', cum_pha='PHA'),
}


class Theme:
    def __init__(self, style):
        if style == 'dark':      # solid black background, gold / light gray / white
            self.bg = (0, 0, 0, 255); self.fg = WHITE; self.grid = (70, 70, 70, 255)
            self.pha = GOLD; self.other = (200, 200, 200, 255); self.line = GOLD
        else:                    # transparent background, black text, dark yellow / dark gray
            self.bg = (0, 0, 0, 0); self.fg = BLACK; self.grid = (190, 190, 190, 255)
            self.pha = (184, 134, 11, 255); self.other = (80, 80, 80, 255); self.line = BLACK


def font(sz, bold=True):
    return ImageFont.truetype(FB if bold else FR, sz)


def km_val(km):
    """Scientific notation in km, value only (no unit), e.g. 1.35×10⁶."""
    if km <= 0:
        return '0'
    e = 3 * int(math.floor(math.log10(km) / 3))
    m = km / 10 ** e
    return f"{m:.4g}×10^{e}"


def ld_km_label(ld):
    return f"{ld:.3g} | {km_val(ld * LD_KM)}"


def text(img, xy, s, sz, color, angle=0, anchor='lt'):
    f = font(sz)
    if angle == 0:
        ImageDraw.Draw(img).text(xy, s, font=f, fill=color, anchor=anchor)
        return
    probe = ImageDraw.Draw(Image.new('RGBA', (4, 4)))
    bb = probe.textbbox((0, 0), s, font=f)
    w, h = bb[2] - bb[0] + 10, bb[3] - bb[1] + 10
    layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((5 - bb[0], 5 - bb[1]), s, font=f, fill=color)
    rot = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    rw, rh = rot.size
    x, y = xy
    px, py = {'rc': (x - rw, y - rh // 2), 'cc': (x - rw // 2, y - rh // 2), 'lc': (x, y - rh // 2),
              'tr': (x - rw, y)}[anchor]
    img.alpha_composite(rot, (max(0, int(px)), max(0, int(py))))


_EMO = None


def emoji(img, ch, cx, cy, px=30):
    global _EMO
    if _EMO is None:
        _EMO = ImageFont.truetype(EMOJI_FONT, EMOJI_SIZE)
    layer = Image.new('RGBA', (220, 220), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((20, 10), ch, font=_EMO, embedded_color=True)
    bb = layer.getbbox()
    if not bb:
        return
    layer = layer.crop(bb)
    s = px / max(layer.size)
    layer = layer.resize((max(1, int(layer.width * s)), max(1, int(layer.height * s))), Image.LANCZOS)
    img.alpha_composite(layer, (max(0, int(cx - layer.width / 2)), max(0, int(cy - layer.height / 2))))


def range_line(d, x1, x2, y):
    """Gold bar with a white outline: the size uncertainty range."""
    d.line([x1, y, x2, y], fill=WHITE, width=4)
    d.line([x1, y, x2, y], fill=GOLD, width=2)


class Ax:
    def __init__(self, lo, hi, p0, p1, log=False):
        self.lo, self.hi, self.p0, self.p1, self.log = lo, hi, p0, p1, log

    def f(self, v):
        if self.log:
            v, lo, hi = math.log10(max(v, 1e-12)), math.log10(self.lo), math.log10(self.hi)
        else:
            lo, hi = self.lo, self.hi
        return self.p0 + (v - lo) / (hi - lo) * (self.p1 - self.p0)

    def ticks(self):
        if self.log:
            out = []
            for k in range(math.floor(math.log10(self.lo)), math.ceil(math.log10(self.hi)) + 1):
                for m in (1, 2, 5):
                    v = m * 10 ** k
                    if self.lo <= v <= self.hi:
                        out.append(v)
            return out
        raw = (self.hi - self.lo) / 6
        e = 10 ** math.floor(math.log10(raw))
        step = next(m * e for m in (1, 2, 2.5, 5, 10) if m * e >= raw)
        out, v = [], math.ceil(self.lo / step) * step
        while v <= self.hi + 1e-9:
            out.append(round(v, 10)); v += step
        return out


def frame(theme, title, sub, L, R, T, B, border=True):
    img = Image.new('RGBA', (W, H), theme.bg)
    d = ImageDraw.Draw(img)
    text(img, (60, 40), title, 34, theme.fg)
    text(img, (60, 90), sub, 20, theme.fg)
    if border:
        d.rectangle([L, T, R, B], outline=theme.fg, width=2)
    return img, d


def legend(img, theme, S, y, unc=False):
    emoji(img, PHA_EMOJI, 130, y, 30); text(img, (160, y - 12), S['leg_pha'], 22, theme.fg)
    emoji(img, ROCK_EMOJI, 530, y, 30); text(img, (560, y - 12), S['leg_rock'], 22, theme.fg)
    if unc:
        range_line(ImageDraw.Draw(img), 730, 770, y)
        text(img, (785, y - 12), S['leg_unc'], 22, theme.fg)


def draw_xticks(img, theme, ax, row_y, labels_fn, size=20):
    d = ImageDraw.Draw(img)
    for v in ax.ticks():
        x = ax.f(v)
        d.line([x, row_y - 8, x, row_y - 2], fill=theme.fg, width=2)
        text(img, (x + 4, row_y), labels_fn(v), size, theme.fg, angle=45, anchor='tr')


def draw_yticks_left(img, theme, ax, L, labels_fn, size=20):
    d = ImageDraw.Draw(img)
    for v in ax.ticks():
        y = ax.f(v)
        d.line([L - 8, y, L, y], fill=theme.fg, width=2)
        text(img, (L - 12, y), labels_fn(v), size, theme.fg, angle=45, anchor='rc')


def gridlines(img, theme, ax_x, ax_y, L, R, T, B):
    d = ImageDraw.Draw(img)
    for v in ax_x.ticks():
        x = ax_x.f(v); d.line([x, T, x, B], fill=theme.grid, width=1)
    for v in ax_y.ticks():
        y = ax_y.f(v); d.line([L, y, R, y], fill=theme.grid, width=1)


def dispersion_chart(rows, theme, S, log, out):
    L, R, T, B = 250, 940, 160, 600
    scale = S['scale_log'] if log else S['scale_lin']
    img, d = frame(theme, S['disp_title'], S['disp_sub'].format(n=len(rows), scale=scale), L, R, T, B)
    ax_x = Ax(min(r['dmin_km'] for r in rows) * 0.7 if log else 0, max(r['dmax_km'] for r in rows) * 1.2, L, R, log)
    ax_y = Ax(min(r['ld'] for r in rows) * 0.8 if log else 0, max(r['ld'] for r in rows) * 1.15, B, T, log)
    gridlines(img, theme, ax_x, ax_y, L, R, T, B)
    draw_xticks(img, theme, ax_x, B + 14, lambda v: f"{v:g}")
    d = ImageDraw.Draw(img)
    ticks = ax_y.ticks() if log else [v for v in range(0, int(ax_y.hi) + 1, 10) if v >= ax_y.lo]
    for v in ticks:                             # right axis only: LD | Km (linear: every 10 LD)
        y = ax_y.f(v)
        d.line([R, y, R + 8, y], fill=theme.fg, width=2)
        text(img, (R + 12, y), ld_km_label(v), 20 if log else 16, theme.fg, angle=45, anchor='lc')
    for r in rows:
        range_line(d, ax_x.f(r['dmin_km']), ax_x.f(r['dmax_km']), ax_y.f(r['ld']))
    for r in sorted(rows, key=lambda r: r['pha']):   # rocks first, PHA drawn on top
        emoji(img, PHA_EMOJI if r['pha'] else ROCK_EMOJI, ax_x.f(r['dmid_km']), ax_y.f(r['ld']), 30 if r['pha'] else 20)
    text(img, ((L + R) // 2, B + 118), S['x_size_log'] if log else S['x_size_lin'], 28, theme.fg, anchor='mt')
    text(img, (R + 170, (T + B) // 2), S['y_dist_log'] if log else S['y_dist_lin'], 26, theme.fg, angle=90, anchor='cc')
    legend(img, theme, S, 850, unc=True)
    img.save(out)


def tres_sets_chart(rows, theme, S, log, out, variant='default'):
    L, R, T, B = 230, 840, 160, 560
    scale = S['scale_log'] if log else S['scale_lin']
    img, d = frame(theme, S['bub_title'], S['bub_sub'].format(n=len(rows), scale=scale), L, R, T, B)
    ax_x = Ax(min(r['ld'] for r in rows) * 0.8 if log else 0, max(r['ld'] for r in rows) * 1.15, L, R, log)
    ax_y = Ax(min(r['rel_velocity_kms'] for r in rows) * 0.8 if log else 0,
              max(r['rel_velocity_kms'] for r in rows) * 1.15, B, T, log)
    gridlines(img, theme, ax_x, ax_y, L, R, T, B)
    draw_xticks(img, theme, ax_x, B + 14, lambda v: f"{v:g}")
    draw_xticks(img, theme, ax_x, B + 52, lambda v: km_val(v * LD_KM))
    draw_yticks_left(img, theme, ax_y, L, lambda v: f"{v:g}")
    # numbering: PHA first, then by size; the same number is used in the list
    ordered = sorted(rows, key=lambda r: (not r['pha'], -r['dmid_km']))
    num = {r['key']: i + 1 for i, r in enumerate(ordered)}
    show_list = variant != 'top'
    bub = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bub)
    rows_draw = sorted(rows, key=lambda r: r['pha'])          # rocks first, PHA on top
    for r in rows_draw:
        x, y = ax_x.f(r['ld']), ax_y.f(r['rel_velocity_kms'])
        rad = 8 + 1.6 * math.sqrt(r['dmid_km'] * 1000)
        col = theme.pha if r['pha'] else theme.other
        bd.ellipse([x - rad, y - rad, x + rad, y + rad], fill=col[:3] + (70,), outline=col, width=2)
    img.alpha_composite(bub)
    dd = ImageDraw.Draw(img)
    for r in rows_draw:
        x, y = ax_x.f(r['ld']), ax_y.f(r['rel_velocity_kms'])
        emoji(img, PHA_EMOJI if r['pha'] else ROCK_EMOJI, x, y - 4, 26)
        if show_list:
            dd.text((x, y + 14), str(num[r['key']]), font=font(15), fill=WHITE, anchor='mm',
                    stroke_width=2, stroke_fill=(0, 0, 0, 255))
    text(img, ((L + R) // 2, B + 150), S['x_dist_log'] if log else S['x_dist_lin'], 28, theme.fg, anchor='mt')
    text(img, (L - 64, (T + B) // 2), S['y_vel'], 28, theme.fg, angle=90, anchor='cc')
    if show_list:
        x0 = 880
        text(img, (x0, 146), S['list_title'], 18, theme.fg)
        y = T + 8
        for r in ordered:
            emoji(img, PHA_EMOJI if r['pha'] else ROCK_EMOJI, x0 + 9, int(y) + 9, 15)
            text(img, (x0 + 26, int(y)), f"{num[r['key']]}. {r['designation']}  {r['dmid_km']:.3f} km · {r['ld']:.1f} LD", 15, theme.fg)
            y += 16.5
    if variant == 'top':
        legend(img, theme, S, 140)
        d = ImageDraw.Draw(img)
        text(img, (60, 815), S['size_key'], 22, theme.fg)
        cx = (L + R) // 2
        for i, km in enumerate([0.01, 0.05, 0.10]):
            x, y = cx - 220 + i * 220, 868
            rad = 8 + 1.6 * math.sqrt(km * 1000)
            d.ellipse([x - rad, y - rad, x + rad, y + rad], outline=theme.fg, width=2)
            text(img, (x + rad + 10, y - 11), f"{km:.2f} km", 20, theme.fg)
    else:
        legend(img, theme, S, 850)
    img.save(out)


def scatter3d_chart(rows, theme, S, log, out):
    """Oblique 3D box: X size (front, left to right), Y distance (right side, running back), Z velocity (left, vertical)."""
    scale = S['scale_log'] if log else S['scale_lin']
    img, d = frame(theme, S['d3_title'], S['d3_sub'].format(n=len(rows), scale=scale), 0, 0, 0, 0, border=False)
    tf = (lambda v: math.log10(v)) if log else (lambda v: v)
    itf = (lambda v: 10 ** v) if log else (lambda v: v)
    xs = [tf(r['dmid_km']) for r in rows]; ys = [tf(r['ld']) for r in rows]; zs = [tf(r['rel_velocity_kms']) for r in rows]

    def norm(vals):
        lo, hi = min(vals), max(vals)
        span = (hi - lo) or 1
        return lo, hi, (lambda v: (v - lo) / span)
    xlo, xhi, nx = norm(xs); ylo, yhi, ny = norm(ys); zlo, zhi, nz = norm(zs)
    ox, sx, oy, sy = 200, 560, 700, 400

    def P(u, v, w):
        return ox + u * sx + v * 0.28 * sx, oy - w * sy - v * 0.22 * sy
    corners = [(u, v, w) for u in (0, 1) for v in (0, 1) for w in (0, 1)]
    for a_ in corners:
        for b_ in corners:
            if a_ < b_ and sum(abs(p - q) for p, q in zip(a_, b_)) == 1:
                d.line([P(*a_), P(*b_)], fill=theme.line, width=2)
    for t in [0, 0.25, 0.5, 0.75, 1]:                       # X: ticks and values below the front edge
        x, y = P(t, 0, 0)
        d.line([x, y, x, y + 10], fill=theme.line, width=2)
        text(img, (x, y + 16), f"{itf(xlo + t * (xhi - xlo)):.3g}", 20, theme.fg, anchor='mt')
    for t in [0, 0.5, 1]:                                   # Y: ticks and LD | Km values on the right
        x, y = P(1, t, 0)
        d.line([x, y, x + 10, y], fill=theme.line, width=2)
        text(img, (x + 16, y), ld_km_label(itf(ylo + t * (yhi - ylo))), 18, theme.fg, anchor='lm')
    for t in [0.25, 0.5, 0.75, 1]:                          # Z: ticks and values on the left
        x, y = P(0, 0, t)
        d.line([x, y, x - 10, y], fill=theme.line, width=2)
        text(img, (x - 16, y), f"{itf(zlo + t * (zhi - zlo)):.3g}", 20, theme.fg, anchor='rm')
    order = sorted(range(len(rows)), key=lambda i: -ny(ys[i]))   # far (back) first, near last
    for i in order:
        r = rows[i]
        u, v, w = nx(xs[i]), ny(ys[i]), nz(zs[i])
        x0, y0 = P(u, v, 0); x1, y1 = P(u, v, w)
        d.line([x0, y0, x1, y1], fill=theme.line, width=2)
        emoji(img, PHA_EMOJI if r['pha'] else ROCK_EMOJI, x1, y1, 30)
    x, y = P(0.5, 0, 0); text(img, (x, y + 60), S['x_size_log'] if log else S['x_size_lin'], 26, theme.fg, anchor='mt')
    x, y = P(1, 0.5, 0)
    ang = math.degrees(math.atan2(0.22 * sy, 0.28 * sx))   # the distance edge's own angle
    text(img, (x + 10, y + 45), S['y_dist_log'] if log else S['y_dist_lin'], 24, theme.fg, angle=ang, anchor='cc')
    x, y = P(0, 0.5, 0.5); text(img, (110, y - 60), S['y_vel'], 24, theme.fg, angle=90, anchor='cc')
    legend(img, theme, S, 850)
    d = ImageDraw.Draw(img)
    d.line([130, 868, 130, 892], fill=theme.line, width=3)
    text(img, (160, 872), S['leg_stem'], 22, theme.fg)
    text(img, (640, 872), S['leg_edge'], 22, theme.fg)
    img.save(out)


def parallel_chart(rows, theme, S, log, out):
    """Parallel coordinates: one vertical axis per variable, one line per object."""
    L, R, T, B = 120, 1080, 200, 690
    scale = S['scale_log'] if log else S['scale_lin']
    img, d = frame(theme, S['pc_title'], S['pc_sub'].format(n=len(rows), scale=scale), L, R, T, B)
    tf = (lambda v: math.log10(v)) if log else (lambda v: v)
    itf = (lambda v: 10 ** v) if log else (lambda v: v)
    cols = [
        ('pc_size', [tf(r['dmid_km']) for r in rows], 240, lambda v: f"{itf(v):.3g}"),
        ('pc_dist', [tf(r['ld']) for r in rows], 600, lambda v: ld_km_label(itf(v))),
        ('pc_vel', [tf(r['rel_velocity_kms']) for r in rows], 960, lambda v: f"{itf(v):.3g}"),
    ]
    norms = []
    for key, vals, x, fmt in cols:
        lo, hi = min(vals), max(vals)
        span = (hi - lo) or 1
        norms.append((lambda v, lo=lo, span=span: (v - lo) / span))
        d.line([x, T, x, B], fill=theme.fg, width=3)
        text(img, (x, T - 40), S[key], 24, theme.fg, anchor='mm')
        text(img, (x + 14, B), fmt(lo), 20, theme.fg, angle=45, anchor='lc')
        text(img, (x + 14, T), fmt(hi), 20, theme.fg, angle=45, anchor='lc')
    for i, r in sorted(enumerate(rows), key=lambda t: t[1]['pha']):
        pts = [(x, B - norms[k](vals[i]) * (B - T)) for k, (key, vals, x, fmt) in enumerate(cols)]
        d.line(pts, fill=theme.pha if r['pha'] else theme.other, width=3)
        emoji(img, PHA_EMOJI if r['pha'] else ROCK_EMOJI, pts[0][0], pts[0][1], 26)
    legend(img, theme, S, 850)
    img.save(out)


def cumulative_chart(rows, theme, S, log, out, start, end):
    days, d0, d1 = [], dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    while d0 <= d1:
        days.append(d0); d0 += dt.timedelta(days=1)
    seen_all, seen_pha, tot, pha = set(), set(), [], []
    for day in days:
        for r in rows:
            if r['approach_date'] == day.isoformat():
                seen_all.add(r['neo_id'])
                if r['pha']:
                    seen_pha.add(r['neo_id'])
        tot.append(len(seen_all)); pha.append(len(seen_pha))
    L, R, T, B = 200, 1040, 160, 600
    scale = S['scale_log'] if log else S['scale_lin']
    img, d = frame(theme, S['cum_title'], S['cum_sub'].format(start=start, end=end, scale=scale), L, R, T, B)
    top = max(tot + [1])
    ax_y = Ax(1, top * 1.2, B, T, True) if log else Ax(0, top * 1.15, B, T, False)
    ax_x = Ax(0, max(len(days) - 1, 1), L, R, False)
    gridlines(img, theme, ax_x, ax_y, L, R, T, B)
    for i, day in enumerate(days):
        x = ax_x.f(i)
        d.line([x, B, x, B + 6], fill=theme.fg, width=2)
        lab = day.strftime('%b %d') if S is STR['en'] else f"{day.day:02d} {MES_ES[day.month - 1]}"
        text(img, (x + 4, B + 12), lab, 22, theme.fg, angle=45, anchor='tr')
    for v in ax_y.ticks():                                  # bigger, closer to the axis
        y = ax_y.f(v)
        d.line([L - 8, y, L, y], fill=theme.fg, width=2)
        text(img, (L - 12, y), f"{v:g}", 26, theme.fg, anchor='rm')
    for series, col in ((tot, theme.other), (pha, theme.pha)):
        pts = [(ax_x.f(i), ax_y.f(max(v, 1 if log else v))) for i, v in enumerate(series)]
        d.line(pts, fill=col, width=4)
        for x, y in pts:
            d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=col, outline=theme.fg)
    text(img, ((L + R) // 2, B + 130), S['x_date'], 28, theme.fg, anchor='mt')
    text(img, (60, (T + B) // 2), S['y_cnt'], 28, theme.fg, angle=90, anchor='cc')
    d.rectangle([260, 850, 280, 870], fill=theme.other)
    text(img, (292, 846), f"{S['cum_all']} ({tot[-1] if tot else 0})", 22, theme.fg)
    d.rectangle([700, 850, 720, 870], fill=theme.pha)
    text(img, (732, 846), f"{S['cum_pha']} ({pha[-1] if pha else 0})", 22, theme.fg)
    img.save(out)


def draw_charts(outdir, start, end, lang):
    S = STR[lang]
    out = os.path.join(outdir, lang)
    os.makedirs(out, exist_ok=True)
    log = load_log()
    today = dt.date.today()
    snap = [r for r in log['rows']
            if today <= dt.date.fromisoformat(r['approach_date']) <= today + dt.timedelta(days=6)]
    for r in snap:
        r['dmin_km'] = r['diam_min_m'] / 1000; r['dmax_km'] = r['diam_max_m'] / 1000
        r['dmid_km'] = math.sqrt(r['dmin_km'] * r['dmax_km'])
        r['ld'] = r['miss_ld']
    dk, tr = Theme('dark'), Theme('transparent')
    names = [
        ('01-diameter-vs-distance-log-dark.png', lambda p: dispersion_chart(snap, dk, S, True, p)),
        ('02-diameter-vs-distance-linear-dark.png', lambda p: dispersion_chart(snap, dk, S, False, p)),
        ('03-distance-velocity-size-log-dark.png', lambda p: tres_sets_chart(snap, dk, S, True, p)),
        ('04-distance-velocity-size-linear-dark.png', lambda p: tres_sets_chart(snap, dk, S, False, p)),
        ('05-diameter-vs-distance-log-transparent.png', lambda p: dispersion_chart(snap, tr, S, True, p)),
        ('06-diameter-vs-distance-linear-transparent.png', lambda p: dispersion_chart(snap, tr, S, False, p)),
        ('07-cumulative-log-transparent.png', lambda p: cumulative_chart(log['rows'], tr, S, True, p, start, end)),
        ('08-cumulative-linear-transparent.png', lambda p: cumulative_chart(log['rows'], tr, S, False, p, start, end)),
        ('09-3d-log-dark.png', lambda p: scatter3d_chart(snap, dk, S, True, p)),
        ('10-3d-linear-dark.png', lambda p: scatter3d_chart(snap, dk, S, False, p)),
        ('11-3d-log-transparent.png', lambda p: scatter3d_chart(snap, tr, S, True, p)),
        ('12-3d-linear-transparent.png', lambda p: scatter3d_chart(snap, tr, S, False, p)),
        ('13-parallel-log-dark.png', lambda p: parallel_chart(snap, dk, S, True, p)),
        ('14-parallel-linear-dark.png', lambda p: parallel_chart(snap, dk, S, False, p)),
        ('15-parallel-log-transparent.png', lambda p: parallel_chart(snap, tr, S, True, p)),
        ('16-parallel-linear-transparent.png', lambda p: parallel_chart(snap, tr, S, False, p)),
    ]
    if lang == 'en':   # English-only variants of 03/04 with the legend under the title and the size key at the bottom
        names += [
            ('03b-distance-velocity-size-log-dark-legend-top.png', lambda p: tres_sets_chart(snap, dk, S, True, p, 'top')),
            ('04b-distance-velocity-size-linear-dark-legend-top.png', lambda p: tres_sets_chart(snap, dk, S, False, p, 'top')),
        ]
    made = []
    for fn, make in names:
        p = os.path.join(out, fn)
        make(p)
        made.append(p)
    return made


# ---------- main ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', default='2026-11-01')
    ap.add_argument('--end', default=(dt.date.today() + dt.timedelta(days=6)).isoformat())
    ap.add_argument('--charts', default=None, help='folder for the PNG charts (not saved to the repo unless given)')
    ap.add_argument('--no-sbdb', action='store_true', help='skip the discovery lookup')
    ap.add_argument('--no-fetch', action='store_true', help='charts only: do not call NASA, use the stored log')
    a = ap.parse_args()

    today = dt.date.today().isoformat()
    feed = [] if a.no_fetch else fetch_feed(a.start, a.end)
    new = [normalize(o, today) for o in feed]
    if not a.no_sbdb:
        cache = {}
        for r in new:
            des = r['designation']
            if des not in cache:
                cache[des] = discovery(des)
                time.sleep(0.3)
            r.update(cache[des])
    added = append_rows(new)
    log = load_log()
    write_xlsx(sorted(log['rows'], key=lambda r: (not r['pha'], r['approach_date'], r['name'])), LOG_XLSX)
    print(f"fetched {len(new)} rows, added {added} new, log total {len(log['rows'])}")
    if a.charts:
        for lang in ('en', 'es'):
            for p in draw_charts(a.charts, a.start, a.end, lang):
                print(p)


if __name__ == '__main__':
    main()
