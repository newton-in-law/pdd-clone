#!/usr/bin/env python3
"""Two LOCAL mock-ups of the PDD clone (nothing is published).
 mock1 = the clone as it is, with: a story right after Space Watch, images on two side ads, the newscast, then three ad tiles.
 mock2 = narrower margins: Space Watch / Asteroids today / Cumulative plots in a 25% left column, the rest in the middle,
         ads + biggest stories in the right rail, a 7-tile ad carousel, visitor counter and last-updated stamp in the footer.
Both use the paper's own type (Georgia body, Playfair Display headings, monospace labels, accent #de7c7c).
Usage: build_mocks.py        -> ../../../mockups/mock1/index.html and mock2/index.html"""
import os, re, sys, json, shutil, subprocess, datetime, html as H, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
MK = os.environ.get('MOCKDIR') or os.path.join(ROOT, 'mockups'); M1 = os.path.join(MK, 'mock1'); M2 = os.path.join(MK, 'mock2')
LIVE = 'https://planetary-defense-daily.newsroomfloor.com'
os.makedirs(M1, exist_ok=True)
subprocess.run([sys.executable, os.path.join(HERE, 'build_clone.py'), M1], check=True)       # fresh clone = base
h0 = open(os.path.join(M1, 'index.html'), encoding='utf-8').read()

# ---------- helpers
def span(h, start):
    t = re.match(r'<(\w+)', h[start:]).group(1); d = 0
    for x in re.finditer(r'<(/?)%s\b[^>]*>' % t, h[start:]):
        d += -1 if x.group(1) else 1
        if d == 0: return start, start + x.end()
def grab(h, marker, back=True):
    i = h.index(marker); i = h.rfind('<', 0, i) if (back and not marker.startswith('<')) else i
    s, e = span(h, i); return s, e, h[s:e]
def img(url, name):
    os.makedirs(os.path.join(M1, 'img'), exist_ok=True); p = os.path.join(M1, 'img', name)
    if not os.path.exists(p):
        try: open(p, 'wb').write(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=40).read())
        except Exception as e: print('image failed', url, e); return url
    return 'img/' + name
R = 'https://relics.luisafernanda.space/assets/wm/'
IMG_SCI = 'img/radar-echo-black.png'   # copied from the LuWeb RadarEcho folder (name in black variant)
if not os.path.exists(os.path.join(M1, 'img', 'radar-echo-black.png')): shutil.copy(os.path.join(HERE, '..', 'home', 'ad-images', 'radar-echo-black.png'), os.path.join(M1, 'img', 'radar-echo-black.png'))
IMG_NEWS = img(R + 'mockups/design__apophis-2029__sweatshirt-0-front.jpg', 'wear-the-news.jpg')

# ---------- the paper's own type, applied to the three Space Watch parts
TYPE = r'''
#swx{font:400 17px/1.72 Georgia,"Times New Roman",serif!important;color:#d6dfee}
#swx[data-w]{max-width:none!important;padding:0!important;width:auto!important;left:0!important;transform:none!important;position:static!important}
#swx p,#swx .td,#swx .ca-desc p,#swx .capd p,#swx .capwide p,#swx li{font:400 16.96px/1.72 Georgia,"Times New Roman",serif!important;color:#d6dfee!important}
#swx a{color:#de7c7c;text-decoration:none}#swx a:hover{text-decoration:underline}
#swx p.kicker,#swx .kicker{font:700 9.6px ui-monospace,Menlo,monospace!important;letter-spacing:.16em!important;text-transform:uppercase;color:#de7c7c!important}
#swx h2{font:900 29.6px/1.06 "Playfair Display",Georgia,serif!important;color:#eef2fa!important;letter-spacing:-.005em;border-bottom:1px solid #2c3b57}
#swx h3,#swx .dd2 h3,#swx .side h3,#swx .dd2.ast h3,#swx b.ct1,#swx .capd>summary b.ct1,#swx .capwide>b:first-child{font:700 19.5px/1.25 "Playfair Display",Georgia,serif!important;color:#eef2fa!important}
#swx .tk{font:900 26px/1.15 "Playfair Display",Georgia,serif!important;color:#eef2fa!important;letter-spacing:-.005em}
#swx details>summary,#swx #space-watch>details>summary{font:700 11.52px/1.4 system-ui,"Helvetica Neue",Helvetica,Arial,sans-serif!important;letter-spacing:.16em!important;text-transform:uppercase;color:#eef2fa!important}
#swx .capd>summary,#swx .tdd>summary{font:400 17.6px/1.5 Georgia,"Times New Roman",serif!important;letter-spacing:0!important;text-transform:none!important;color:#a2afc6!important}
#swx .map-key,#swx .map-key *,#swx .pos,#swx .ctrl .pos,#swx .mb{font:600 11.52px ui-monospace,Menlo,monospace!important;letter-spacing:.02em;color:#a2afc6!important}
#swx .ctrl button{font-family:system-ui,"Helvetica Neue",Arial,sans-serif!important}
#swx table.sortable th{font:700 10px ui-monospace,Menlo,monospace!important;letter-spacing:.08em;text-transform:uppercase;color:#95a3bb!important}
#swx table.sortable td{font:400 13.76px/1.4 system-ui,"Helvetica Neue",Helvetica,Arial,sans-serif!important;color:#d6dfee}
#swx p.tk{font:900 26px/1.15 "Playfair Display",Georgia,serif!important;color:#eef2fa!important}
#swx .tile b{font:700 16px/1.15 "Playfair Display",Georgia,serif!important;color:#eef2fa!important}
#swx .tile .tt{font:400 13.76px/1.45 system-ui,"Helvetica Neue",Arial,sans-serif!important;color:#a2afc6!important}
#swx .tile .tg{font:600 9.28px ui-monospace,Menlo,monospace!important;letter-spacing:.14em;text-transform:uppercase;color:#95a3bb!important}
#swx .tile .tb{font:700 13.12px "Helvetica Neue",Helvetica,Arial,sans-serif!important;letter-spacing:.04em}
.sp-img{display:block;width:100%;height:auto;max-height:260px;object-fit:contain;background:#fff;margin:0 0 .55rem}.sp-img[src*=radar]{background:#000}.tile .ti img[src*=radar]{background:#000}
'''
CSS_FIX = ('#swx{box-sizing:border-box;width:min(1560px,97vw)!important;max-width:none!important;position:relative;left:50%;transform:translateX(-50%);font-size:18.3px!important}',
           '#swx:not([data-w]){box-sizing:border-box;width:min(1560px,97vw)!important;max-width:none!important;position:relative;left:50%;transform:translateX(-50%)}')
def tile(href, tag, imgh, title, text, btn):
    return (f'<a class="tile" href="{href}" target="_blank" rel="noopener"><span class="tg">{tag}</span><span class="ti">{imgh}</span>'
            f'<b>{title}</b><span class="tt">{text}</span><span class="tb">{btn}</span></a>')
NFI = '<img src="img/nrf-icon.png" alt="Newsroom Floor">'
PDI = f'<img src="{LIVE}/logo/planetary-defense-daily/dark" alt="Planetary Defense Daily">'
XI = '<span class="xl"><svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M18.2 2H21l-6.5 7.4L22 22h-6l-4.7-6.1L5.8 22H3l7-8L2 2h6.1l4.2 5.6L18.2 2zm-1 18h1.6L7 3.8H5.3L17.2 20z"/></svg></span>'
YI = '<span class="xl" style="background:#c4302b;color:#fff"><svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M21.6 7.2a2.5 2.5 0 0 0-1.8-1.8C18.2 5 12 5 12 5s-6.2 0-7.8.4A2.5 2.5 0 0 0 2.4 7.2C2 8.8 2 12 2 12s0 3.2.4 4.8a2.5 2.5 0 0 0 1.8 1.8C5.8 19 12 19 12 19s6.2 0 7.8-.4a2.5 2.5 0 0 0 1.8-1.8c.4-1.6.4-4.8.4-4.8s0-3.2-.4-4.8zM10 15V9l5.2 3z"/></svg></span>'
T_NEWS = tile(LIVE + '/go/sec-0', 'Ad', f'<img src="{IMG_NEWS}" alt="">', 'The news you can wear', 'Real headlines, painted in art, on almost anything.', 'Pick a day')
T_SCI = tile(LIVE + '/go/sec-1', 'Ad', f'<img src="{IMG_SCI}" alt="">', 'Wear the science', 'Apophis, Arecibo and Radar Echo art, printed to order.', 'Shop the art')
T_SUB = tile(LIVE + '/#subscribe', 'Ad', PDI, 'Subscribe', 'The daily briefing in your inbox.', 'Subscribe')
T_NF = tile('https://newsroomfloor.com', 'Ad', NFI, 'Newsroom Floor', 'Build and check your own AI newspaper.', 'Visit Newsroom Floor')
T_OWN = tile('https://newsroomfloor.com', 'Ad', NFI, 'Want your own newsroom?', 'An automated newsroom, made for you.', 'Make your own')
T_X = tile('https://x.com/newtons_in_laws', 'Ad', XI, 'Follow us on X', 'New stories and charts as they land.', 'Follow @newtons_in_laws')
T_YT = tile('https://www.youtube.com/@PlanetaryDefenseDaily', 'Ad', YI, 'Visit our YouTube channel', 'The daily newscast, with people talking.', 'youtube.com/@PlanetaryDefenseDaily')
def with_type(h, extra=''):
    assert CSS_FIX[0] in h, 'breakout rule not found'
    h = h.replace(CSS_FIX[0], CSS_FIX[1])
    return h.replace('</head>', '<style id="mock-type">' + TYPE + extra + '</style></head>', 1)
def side_images(pl):          # images on "Wear the science" and "The news you can wear"
    for name, src in (('WEAR THE SCIENCE', IMG_SCI), ('THE NEWS YOU CAN WEAR', IMG_NEWS)):
        pl = re.sub(r'(<a class="sp-block sp-promo sp-card"[^>]*>)(<div class="sp-hrow"><div class="sp-h notranslate">%s)' % re.escape(name),
                    r'\1<img class="sp-img" src="%s" alt="">\2' % src, pl, count=1)
    return pl

# ================= MOCK 1
h = h0
s, e, castband = grab(h, '<section class="castband"'); h = h[:s] + h[e:]
s, e, pl = grab(h, 'class="pl pl-standard pl-hasad"')
row3 = '<div id="swx" data-w="row" style="margin:1.4rem 0"><div class="ad4" style="grid-template-columns:repeat(3,minmax(0,1fr))">' + T_NF + T_SUB + T_NEWS + '</div></div>'
h = h[:s] + side_images(pl) + castband + row3 + h[e:]
open(os.path.join(M1, 'index.html'), 'w', encoding='utf-8').write(with_type(h))
print('mock1 written')

# ================= MOCK 2
if os.path.exists(M2): shutil.rmtree(M2)
shutil.copytree(M1, M2, ignore=shutil.ignore_patterns('index.html'))
h = h0
bs, be, band = grab(h, '<div id="swx">')
sec = band
d1s, d1e, det1 = grab(sec, '<details>')
rest = sec[d1e:]
d2s, d2e, det2 = grab(rest, '<details>'); rest2 = rest[d2e:]
d3s, d3e, det3 = grab(rest2, '<details>')
a_s, a_e, ast = grab(det1, 'class="dd2 ast"')
mapdiv_s = ast.index('<div>'); ms, me = span(ast, mapdiv_s); mapdiv = ast[ms:me]; capdiv = ast[me:]
mapdiv = re.sub(r'<h3[^>]*>Asteroids today · map\s*(<button.*?</button>)</h3>', r'<div class="subrow"><h3 class="sub">ASTEROIDS TODAY</h3>\1</div>', mapdiv, flags=re.S)
mapdiv = re.sub(r'<div class="map-key"[^>]*>', '<div class="map-key">', mapdiv)
ptd = re.search(r'<p class="td">.*?</p>', capdiv, flags=re.S).group(0)
tw_s, tw_e, tw = grab(capdiv, '<div class="tw">')
c_s, c_e, cum = grab(det1, 'class="dd2 cum"'); cum = cum.replace('class="capwide cap-open"', 'class="capwide"')
_a, _b, _cw = grab(cum, 'class="capwide"'); cum = cum[:_a] + cum[_b:]      # the plots carry no caption
ad4_s, ad4_e, ad4 = grab(det1, 'class="ad4"')
tiles4 = re.findall(r'<a class="tile".*?</a>', ad4, flags=re.S); assert len(tiles4) == 4
AD_TOP = '<div class="ad4">' + ''.join(tiles4[:2]) + '</div>'; AD_LEFT = '<div class="ad4 adl">' + ''.join(tiles4[2:]) + '</div>'
left = ('<aside class="lcol"><div id="swx" data-w="l"><h2>SPACE WATCH!</h2>' + mapdiv +
        '<details class="tdd sbcap"><summary><span class="stext"><b class="ct1">Designations announced</b></span></summary>' + ptd + tw + '</details>'
        '<h3 class="sub plots">CUMULATIVE PLOTS</h3>' + cum + AD_LEFT + '</div></aside>')
sw_main = ('<div id="swx" data-w="m" class="swmain"><section id="space-watch"><p class="kicker">Space Watch</p><h2>SPACE WATCH</h2>' + det2 + det3 + '</section></div>')
ad4row = '<div id="swx" data-w="a">' + AD_TOP + '</div>'

# pieces of the paper
_, _, lead = grab(h0, 'class="lead"')
us, ue, under = grab(h0, 'class="under under-rows"')
_, _, castband = grab(h0, '<section class="castband"')
_, _, pladd = grab(h0, 'class="pl-ad"'); pladd = side_images(pladd)
try: _, _, plrail = grab(h0, 'class="pl-rail"')
except ValueError: plrail = ''; print('WARNING: the live paper has no pl-rail element now; building without the paper rail', flush=True)
fs, fe, foot = grab(h0, '<footer class="pfoot"', back=False)
lead_id = re.search(r'/story/([0-9a-f]{32})', lead).group(1)
# the second article: the most recent story that is not the lead
art2 = ''; art2_id = None
try:
    L = json.load(urllib.request.urlopen(urllib.request.Request(LIVE + '/api/v1/stories?limit=8', headers={'User-Agent': 'Mozilla/5.0'}), timeout=40))['stories']
    pick = next(x for x in L if x['id'] != lead_id and x.get('kind') in ('news', 'blog'))
    art2_id = pick['id']
    D = json.load(urllib.request.urlopen(urllib.request.Request(LIVE + '/api/v1/stories/' + pick['id'], headers={'User-Agent': 'Mozilla/5.0'}), timeout=40))
    paras = [re.sub(r'\[\^\d+\]', '', p).strip() for p in D['prose'].split('\n\n') if p.strip()]
    paras = [re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', H.escape(p)) for p in paras]
    by = D['byline']; url = D['url']
    art2 = ('<div class="lead art2"><span class="kick"><a href="%s/section/%s">%s</a></span><h2><a href="%s" style="color:inherit">%s</a></h2><p class="dek">%s</p>'
            '<div class="by"><img src="%s" alt=""><span>By <a href="%s" style="color:inherit">%s</a></span></div>'
            '<div class="leadlede leadfull">%s<a class="leadmore" href="%s">Read with its sources &rarr;</a></div></div>'
            % (LIVE, pick['category'].replace(' ', '%20'), H.escape(pick['category'].title()), url, H.escape(D['headline']), H.escape(D['dek']),
               by.get('avatar', ''), url, H.escape(by['name']), ''.join('<p>' + p + '</p>' for p in paras[:4]), url))
except Exception as ex:
    print('second article not built:', ex)
if art2_id: under = re.sub(r'<div class="item row".{0,2200}?</div></div>', lambda m: '' if art2_id in m.group(0) else m.group(0), under, flags=re.S)
car7 = ('<div id="swx" data-w="c" class="car7w"><button class="cb" data-d="-1" aria-label="Previous">&#8249;</button><div class="ad4 track" id="track7">'
        + T_NEWS + T_SCI + T_SUB + T_NF + T_OWN + T_X + T_YT + '</div><button class="cb" data-d="1" aria-label="Next">&#8250;</button></div>')

# ---------- stories: last-week carousel and the monthly top-10 (art comes from newsroomfloor.com/story-art/<id>)
def api(path):
    return json.load(urllib.request.urlopen(urllib.request.Request(LIVE + path, headers={'User-Agent': 'Mozilla/5.0'}), timeout=40))
os.makedirs(os.path.join(M1, 'img', 'art'), exist_ok=True)
def art(sid):
    f = os.path.join(M1, 'img', 'art', sid + '.jpg')
    if not os.path.exists(f):
        try: b = urllib.request.urlopen(urllib.request.Request('https://newsroomfloor.com/story-art/' + sid, headers={'User-Agent': 'Mozilla/5.0'}), timeout=40).read()
        except Exception: return None
        open(f, 'wb').write(b)
    return 'img/art/' + sid + '.jpg'
ALL = api('/api/v1/stories?limit=100')['stories']
today = datetime.datetime.utcnow().date()
def d(x): return datetime.date.fromisoformat(x['published_at'][:10])
week = [x for x in ALL if (today - d(x)).days <= 7][:14]
month = [x for x in ALL if (today - d(x)).days <= 30 and x['id'] != lead_id and x['kind'] != 'blog'][:10]
NOART = []
def noimg(x):
    NOART.append(x); return '<span class="noimg">Image requested</span>'
def ds(x): return d(x).strftime('%b %d, %Y').replace(' 0', ' ')
def card(x, extra=''):
    a = art(x['id']); pic = ('<img src="%s" alt="" loading="lazy">' % a) if a else noimg(x)
    return ('<div class="nc"><a class="ncp" href="%s" target="_blank" rel="noopener">%s</a><a class="nct" href="%s" target="_blank" rel="noopener">%s</a>%s</div>'
            % (x['url'], pic, x['url'], H.escape(x['headline']), extra))
news7 = ('<div id="swx" data-w="n" class="car7w newsw"><p class="kicker" style="margin:0">The week in news</p></div>')
news7 = ('<section class="weekw"><p class="sechd">THE WEEK IN NEWS</p><div class="carw"><button class="cb" data-d="-1" aria-label="Previous">&#8249;</button><div class="track ntrack">'
         + ''.join(card(x, '<span class="nd">%s</span>' % ds(x)) for x in week) + '</div><button class="cb" data-d="1" aria-label="Next">&#8250;</button></div></section>')
read5, share5 = month[:5], month[5:10]
def toprow(title, xs, unit):
    return ('<p class="sechd">%s</p><div class="top5">%s</div>' % (title, ''.join(card(x, '<span class="nd">&mdash; %s</span>' % unit) for x in xs)))
top10 = ('<section class="topw">' + toprow('MOST READ THIS MONTH', read5, 'reads') + toprow('MOST SHARED THIS MONTH', share5, 'shares') +
         '<p class="note">Sample order: the reads and shares counter is not connected yet.</p></section>')
open(os.path.join(MK, 'TODO-story-art.md'), 'w').write('# Stories shown in the mock-ups without an AI image (request one)\n\n' + ''.join('- %s  %s  %s\n' % (ds(x), x['id'], x['headline']) for x in {y['id']: y for y in NOART}.values()))
castrow = '<div class="castrow">' + castband + '<div id="swx" data-w="t"><div class="ad4 casttiles">' + T_X + T_YT + '</div></div></div>'
now = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
foot = foot.replace('<nav class="pf-nav">', '<span class="pf-visit">You are visitor number #<b id="vcount">300</b></span><nav class="pf-nav">', 1)
foot = foot.replace('<span class="pf-cred">', '<span class="pf-upd">Last updated ' + now + '</span><span class="pf-cred">', 1)
center = ('<div class="mcol">' + lead + ad4row + '<div class="after">' + sw_main + art2 + news7 + castrow + top10 + '<div class="under under-rows m2news">' + re.sub(r'^<div[^>]*>|</div>$', '', under) + '</div>' + car7 + '</div></div>')
right = '<div class="m2r">' + pladd + plrail + '</div>'
grid = '<div class="m2">' + left + center + right + '</div>'
# replace everything from the Space Watch band to the footer with the new grid
bs, be, _ = grab(h0, '<div id="swx">')
h = h0[:bs] + grid + h0[fe:]
h = h[:h.index('<footer class="pfoot"')] if False else h
h = h.replace(foot[:0], '')
# the original footer text was cut off with fe; put the edited footer back in
h = h.replace(grid, grid + foot, 1)
M2CSS = r'''
.wrap{max-width:min(1760px,98vw)!important}
.m2{display:grid;grid-template-columns:25% minmax(0,1fr) 280px;gap:26px;align-items:start;margin-top:1rem}
.lcol,.mcol,.m2r{min-width:0}
.lcol #swx h2{border-bottom:1px solid #2c3b57;padding-bottom:6px;margin:0 0 .6rem}
#swx .subrow{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:.4rem 0 .5rem}
#swx .sub{margin:0!important;letter-spacing:.08em;text-transform:uppercase;font:700 11.52px/1.4 system-ui,"Helvetica Neue",Arial,sans-serif!important;letter-spacing:.16em!important;color:#de7c7c!important;border-top:3px solid #eef2fa;padding-top:.4rem}
#swx .sub.plots{margin-top:1.1rem!important;display:block}
.lcol #swx .dd2.cum{display:flex;flex-direction:column;gap:6px;padding:0;margin:0}
.lcol #swx .dd2.cum>div:not(.capwide){order:1}.lcol #swx .dd2.cum .capwide{order:2;grid-column:auto!important;max-height:none;padding:0}
.lcol #swx .capd>summary{display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden}
.lcol #swx .capd[open]>summary{display:block;-webkit-line-clamp:unset}
.lcol #swx .tdd{margin-top:.5rem}
.lcol #swx .tw{max-width:100%;overflow-x:auto}.lcol #swx table.sortable th,.lcol #swx table.sortable td{padding:4px 4px;white-space:nowrap;font-size:12.5px!important}
.lcol #swx svg{max-width:100%;height:auto}
#swx.swmain details>summary::after,#swx.swmain #space-watch>details>summary::after{font-size:1.7em!important}
#swx.swmain #space-watch>h2,#swx.swmain .kicker{margin-top:0}
#swx[data-w="a"] .ad4{grid-template-columns:repeat(4,minmax(0,1fr))}
.mcol>.lead{margin-bottom:.4rem}.mcol .art2{margin:1.6rem 0 .6rem;padding-top:1rem;border-top:3px solid #eef2fa}
.mcol .castband{margin:1.2rem 0 .8rem}.mcol .m2news{margin:.2rem 0 1.2rem!important}
.car7w{display:flex;align-items:center;gap:8px;margin:1rem 0 1.4rem!important}
.car7w .track{display:flex!important;flex:1;min-width:0;overflow-x:auto;scroll-snap-type:x mandatory;gap:12px;scrollbar-width:none;padding:0!important}
.car7w .track::-webkit-scrollbar{display:none}
.car7w .track .tile{flex:0 0 calc((100% - 36px)/4);scroll-snap-align:start;min-width:0}
.car7w .cb{flex:0 0 auto;width:38px;height:38px;border:1px solid #2c3b57;background:#121e33;color:#eef2fa;font:700 22px/1 system-ui;border-radius:3px;cursor:pointer}
.pf-top,.pf-bot{display:flex;justify-content:space-between;align-items:center;flex-direction:row!important;gap:.6rem 1.4rem;flex-wrap:wrap}
.pf-visit,.pf-upd{font:600 10.56px ui-monospace,Menlo,monospace;letter-spacing:.12em;text-transform:uppercase;color:#a2afc6;text-align:center;flex:1}
.pf-visit b{color:#eef2fa}
.m2{zoom:.84}
.after{width:80%;margin:0}
.lcol #swx .adl{grid-template-columns:1fr!important;margin-top:1rem}
.sechd{font:700 11.5px/1.4 system-ui,"Helvetica Neue",Arial,sans-serif;letter-spacing:.16em;color:#de7c7c;border-top:3px solid #eef2fa;padding-top:.45rem;margin:1.4rem 0 .6rem}
.carw{display:flex;align-items:center;gap:8px}
.carw .track{display:flex;flex:1;min-width:0;overflow-x:auto;scroll-snap-type:x mandatory;gap:12px;scrollbar-width:none}
.carw .track::-webkit-scrollbar{display:none}
.carw .cb{flex:0 0 auto;width:34px;height:34px;border:1px solid #2c3b57;background:#121e33;color:#eef2fa;font:700 20px/1 system-ui;border-radius:3px;cursor:pointer}
.nc{display:flex;flex-direction:column;gap:6px;min-width:0}
.ntrack .nc{flex:0 0 calc((100% - 48px)/5);scroll-snap-align:start}
.ncp{display:block;aspect-ratio:16/9;background:#0f1a2e;border:1px solid #2c3b57;overflow:hidden}
.ncp img{width:100%;height:100%;object-fit:cover;display:block}
.noimg{display:flex;align-items:center;justify-content:center;height:100%;font:600 10px ui-monospace,Menlo,monospace;letter-spacing:.12em;text-transform:uppercase;color:#a2afc6;border:1px dashed #5a6b8c}
.nct{font:700 13.5px/1.25 "Playfair Display",Georgia,serif;color:#eef2fa}.nct:hover{color:#de7c7c}
.nd{font:600 10px ui-monospace,Menlo,monospace;letter-spacing:.1em;text-transform:uppercase;color:#a2afc6}
.top5{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px}
.topw .note{font:italic 12px Georgia,serif;color:#a2afc6;margin:.6rem 0 1.6rem}
.castrow{display:grid;grid-template-columns:minmax(0,1fr) 190px;gap:12px;align-items:stretch}
.castrow .castband{margin:1.2rem 0 .8rem}
.castrow{align-items:start!important}.casttiles{display:flex!important;flex-direction:column;gap:10px;margin:1.2rem 0 .8rem}.casttiles .tile{flex:1;margin:0}.casttiles .tile .ti img,.casttiles .xl{max-height:56px}
@media(max-width:1100px){.after{width:100%}.top5{grid-template-columns:repeat(2,minmax(0,1fr))}.ntrack .nc{flex-basis:calc((100% - 12px)/2)}.castrow{grid-template-columns:1fr}.m2{grid-template-columns:minmax(0,1fr)}.m2r{order:3}.car7w .track .tile{flex-basis:calc((100% - 12px)/2)}}
'''
JS2 = '''<script>(function(){try{var k='pdd_mock_visits',n=parseInt(localStorage.getItem(k)||'299',10)+1;localStorage.setItem(k,n);var e=document.getElementById('vcount');if(e)e.textContent=n}catch(x){}
document.querySelectorAll('.car7w .track,.carw .track').forEach(function(t,ix){var box=t.parentNode;var go=function(d){var c=t.firstElementChild;var w=t.children[1]?t.children[1].offsetLeft-c.offsetLeft:c.offsetWidth+12;if(d>0&&t.scrollLeft+t.clientWidth>=t.scrollWidth-4)t.scrollTo({left:0,behavior:'smooth'});else if(d<0&&t.scrollLeft<4)t.scrollTo({left:t.scrollWidth,behavior:'smooth'});else t.scrollBy({left:d*w,behavior:'smooth'})};
box.querySelectorAll('.cb').forEach(function(b){b.onclick=function(){go(+b.dataset.d)}});var p=0;t.onmouseenter=function(){p=1};t.onmouseleave=function(){p=0};setInterval(function(){if(!p)go(1)},5000+ix*700)});})()</script>'''
shutil.copytree(os.path.join(M1, 'img'), os.path.join(M2, 'img'), dirs_exist_ok=True)
h = with_type(h, M2CSS).replace('</body>', JS2 + '</body>')
open(os.path.join(M2, 'index.html'), 'w', encoding='utf-8').write(h)
print('mock2 written', len(h))

# ================= MOCK 3: one single column, 80% of the page width, no side panels
M3 = os.path.join(MK, 'mock3')
if os.path.exists(M3): shutil.rmtree(M3)
shutil.copytree(M2, M3, ignore=shutil.ignore_patterns('index.html', 'open.html'))
band3 = band.replace(ad4, '', 1).replace('<div id="swx">', '<div id="swx" data-w="b" class="swband">', 1)
rail3 = '<div class="m3rail">' + pladd + plrail + '</div>'
one = ('<div class="m3">' + lead + ad4row + band3 + art2 + news7 + castrow + top10 +
       '<div class="under under-rows m2news">' + re.sub(r'^<div[^>]*>|</div>$', '', under) + '</div>' + car7 + rail3 + '</div>')
h3 = h0[:bs] + one + h0[fe:]
h3 = h3.replace(one, one + foot, 1)
M3CSS = r'''
.m3{width:95.2vw;margin:1rem auto 0;zoom:.84}   /* 95.2 x .84 = 80% of the page */
.m3 .lead p,.m3 .lead .leadlede,.m3 .lead .leadfull,.m3 .art2 p,.m3 .art2 .leadlede{max-width:none!important}
.m3 #swx[data-w="a"]{margin:0}
.m3 .swband{margin:1.6rem 0}
.m3 #swx.swband h2{margin-top:0}
.m3rail .pl-ad,.m3rail .pl-rail{width:100%}
.m3rail .sp-stack{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}
.m3rail{margin:1rem 0 2rem}
@media(max-width:900px){.m3{width:94vw}.m3rail .sp-stack{grid-template-columns:1fr}}
'''
open(os.path.join(M3, 'index.html'), 'w', encoding='utf-8').write(with_type(h3, M2CSS + M3CSS).replace('</body>', JS2 + '</body>'))
open(os.path.join(M3, 'open.html'), 'w', encoding='utf-8').write(open(os.path.join(M3, 'index.html'), encoding='utf-8').read().replace('<details>', '<details open>'))
print('mock3 written')

# ================= MOCK 4: left 30% (Asteroids today + Cumulative tally + ads) | right 70% (image of the day, news, LOOKING UP!, rest of the paper)
M4 = os.path.join(MK, 'mock4')
if os.path.exists(M4): shutil.rmtree(M4)
shutil.copytree(M2, M4, ignore=shutil.ignore_patterns('index.html', 'open.html'))
# -- left column
_, _, cum4 = grab(det1, 'class="dd2 cum"')
_a, _b, _cw = grab(cum4, 'class="capwide'); cum4 = cum4[:_a] + cum4[_b:]
cum4 = re.sub(r'<figcaption><b>([^<]*)</b><details class="capd"><summary>(.*?)</summary>(.*?)</details></figcaption>',
              r'<figcaption><details class="capd"><summary><b class="ct1">\1</b></summary><p class="cs">\2</p>\3</details></figcaption>', cum4, flags=re.S)
assert 'class="ct1">Cumulative NEAs since first capture' in cum4
left4 = ('<aside class="lcol"><div id="swx" data-w="l">' + mapdiv.replace('ASTEROIDS TODAY', 'ASTEROIDS TODAY') +
         '<details class="tdd sbcap"><summary><span class="stext"><b class="ct1">Designations announced</b></span></summary>' + ptd + tw + '</details>'
         '<h3 class="sub plots">CUMULATIVE TALLY</h3>' + cum4 +
         '<hr class="wline">' + '<div class="ad4 adl">' + T_X + T_NEWS + tiles4[0] + '</div></div></aside>')
# -- image of the day: the newest story that has an AI picture
iotd = ''
try:
    for x in ALL:
        a = art(x['id'])
        if not a: continue
        pg = urllib.request.urlopen(urllib.request.Request(x['url'], headers={'User-Agent': 'Mozilla/5.0'}), timeout=40).read().decode('utf-8', 'ignore')
        cap = H.unescape(re.search(r'<figure class="sart">.*?<img[^>]*alt="([^"]*)"', pg, flags=re.S).group(1))
        made = 'An AI illustration, painted by the Newsroom Floor art station for this story. The picture is pinned with a signed fingerprint (SHA-256 hash, Ed25519 signature), so anyone can check that it has not been changed.'
        try:
            sys.path.insert(0, os.path.join(ROOT, 'loop')); import nrfpdd
            rc = json.load(urllib.request.urlopen(urllib.request.Request('https://newsroomfloor.com/api/v1/papers/planetary-defense-daily/stories/%s/art-receipt' % x['id'],
                           headers={'Authorization': 'Bearer ' + nrfpdd.key, 'User-Agent': 'Mozilla/5.0'}), timeout=40))
            made = ('An AI illustration, painted on %s by %s from the story text. Its SHA-256 fingerprint (%s&hellip;) is signed with Ed25519, so anyone can check that the picture has not been changed since it was painted.'
                    % (rc['painted_at'][:10], H.escape(rc['signer']), rc['image_hash'][:12]))
        except Exception as ex: print('receipt not read:', ex)
        tw_url = 'https://x.com/intent/tweet?text=' + urllib.parse.quote(x['headline']) + '&url=' + urllib.parse.quote(x['url'])
        iotd = ('<section class="iotd"><p class="sechd" style="margin-top:0">IMAGE OF THE DAY</p><a class="iimg" href="%s" target="_blank" rel="noopener"><img src="%s" alt="%s"></a>'
                '<div class="icap"><p class="ic1"><b>%s</b> <span class="ai">AI illustration</span></p><p class="ic2">From the story <a href="%s" target="_blank" rel="noopener">%s</a>.</p>'
                '<details class="idet"><summary>How this picture was made</summary><p>%s</p></details>'
                '<a class="xshare" href="%s" target="_blank" rel="noopener">%s<span>Share on X</span></a></div></section>'
                % (x['url'], a, H.escape(cap), H.escape(cap), x['url'], H.escape(x['headline']), made, tw_url, XI.replace('class="xl"', 'class="xs"')))
        break
except Exception as ex: print('image of the day not built:', ex)
look = ('<div id="swx" data-w="m" class="swmain look4"><section id="space-watch"><h2 class="look">LOOKING UP!</h2>' + det2 + det3 + '</section></div>')
rail4 = '<div class="m3rail">' + pladd + plrail + '</div>'
right4 = ('<div class="mcol">' + iotd + '<div class="under under-rows m2news">' + re.sub(r'^<div[^>]*>|</div>$', '', under) + '</div>' + look +
          lead + ad4row + art2 + news7 + castrow + top10 + car7 + rail4 + '</div>')
g4 = '<div class="m2 m4">' + left4 + right4 + '</div>'
h4 = h0[:bs] + g4 + h0[fe:]; h4 = h4.replace(g4, g4 + foot, 1)
M4CSS = r'''
.m4{grid-template-columns:30% minmax(0,1fr)!important;gap:30px!important}
.m4 #swx .sub{font:700 14.2px/1.4 system-ui,"Helvetica Neue",Arial,sans-serif!important}
.m4 #swx hr.wline{border:0;border-top:3px solid #eef2fa;margin:1.3rem 0 1rem}
.m4 #swx .adl{display:flex!important;flex-direction:column;gap:12px;grid-template-columns:none!important;padding:0!important;margin:0!important}
.m4 #swx .dd2.cum .slide figcaption{display:block!important;margin-top:.4rem}
.m4 #swx .dd2.cum .capd{border-top:1px solid #2c3b57;margin:0}
.m4 #swx .dd2.cum .capd>summary{display:flex!important;justify-content:space-between;align-items:center;gap:10px;padding:.55rem 0!important;cursor:pointer;-webkit-line-clamp:unset!important}
.m4 #swx .dd2.cum .capd>summary::after{content:"+"!important;font:400 26px/1 system-ui!important;color:#de7c7c;flex:0 0 auto;float:none}
.m4 #swx .dd2.cum .capd[open]>summary::after{content:"\2212"!important}
.m4 #swx .dd2.cum .capd>summary b.ct1{font:700 15.5px/1.25 "Playfair Display",Georgia,serif!important;color:#eef2fa!important}
.m4 #swx .dd2.cum .capd p{margin:.3rem 0 .6rem}
.m4 .sechd{font-size:12px}
.iotd{margin:0 0 1rem}
.iimg{display:block;border:1px solid #2c3b57;background:#0f1a2e}.iimg img{display:block;width:100%;height:auto;max-height:520px;object-fit:cover;object-position:center 35%}
.icap{padding:.7rem 0 0}.icap p{margin:0 0 .4rem;font:400 16px/1.55 Georgia,"Times New Roman",serif;color:#d6dfee}
.icap .ic1 b{font:700 19px/1.25 "Playfair Display",Georgia,serif;color:#eef2fa}
.icap .ai{font:600 10px ui-monospace,Menlo,monospace;letter-spacing:.12em;text-transform:uppercase;color:#de7c7c;margin-left:.5rem}
.icap a{color:#de7c7c;text-decoration:none}.icap a:hover{text-decoration:underline}
.idet{border-top:1px solid #2c3b57;border-bottom:1px solid #2c3b57;margin:.5rem 0 .8rem}
.idet summary{list-style:none;display:flex;justify-content:space-between;align-items:center;padding:.55rem 0;cursor:pointer;font:700 11.5px system-ui,Arial,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:#eef2fa}
.idet summary::-webkit-details-marker{display:none}.idet summary::after{content:"+";font:400 26px/1 system-ui;color:#de7c7c}.idet[open] summary::after{content:"\2212"}
.xshare{display:inline-flex;align-items:center;gap:.45rem;font:600 13px system-ui,Arial,sans-serif;color:#eef2fa!important;border:1px solid #2c3b57;padding:.4rem .9rem}.xshare:hover{background:#16233a;text-decoration:none!important}.xshare svg{width:14px;height:14px}.xshare .xs{display:inline-flex}
#swx.look4 h2.look{font:900 32.3px/1.06 "Playfair Display",Georgia,serif!important;color:#de7c7c!important;border-bottom:1px solid #2c3b57;margin:1.4rem 0 .7rem;letter-spacing:.01em}
.m4 .mcol>.lead{margin-top:1.6rem;padding-top:1rem;border-top:3px solid #eef2fa}
'''
open(os.path.join(M4, 'index.html'), 'w', encoding='utf-8').write(with_type(h4, M2CSS + M4CSS).replace('</body>', JS2 + '</body>'))
open(os.path.join(M4, 'open.html'), 'w', encoding='utf-8').write(open(os.path.join(M4, 'index.html'), encoding='utf-8').read().replace('<details>', '<details open>'))
print('mock4 written')

# ================= MOCKS 5 and 6: 30/70 split, LOOKING UP! right after the image of the day.
#  mock5 = LOOKING UP! as drop-downs (+/-);  mock6 = LOOKING UP! as pop-out boxes (nothing is dropped)
from mock56_assets import MAPJS, LBJS, POPJS, UIJS, CSS as M56CSS
def fetch(url, fallback=None):
    try: return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=40).read()
    except Exception as ex:
        print('fetch failed', url, ex); return fallback
tle = (fetch('https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=tle', b'') or b'').decode().strip().splitlines()
tle = [l.strip() for l in tle if l.strip()]
ISS = tle[1:3] if len(tle) >= 3 else ['1 25544U 98067A   26324.88180268  .00009897  00000+0  18414-3 0  9991', '2 25544  51.6319 244.6605 0007389  48.0812 312.0806 15.49518511596048']
sat_js = fetch('https://cdnjs.cloudflare.com/ajax/libs/satellite.js/4.1.4/satellite.min.js')
WTIME = re.search(r'"time": "([^"]+)"', h0).group(1)
X_SVG = re.search(r'<svg.*?</svg>', XI, flags=re.S).group(0)
LOGO_URL = LIVE + '/logo/planetary-defense-daily/dark'
PRE = ('<script>window.WATCH=WATCH;window.PDD_LOGO=%s;window.ISS_TLE=%s;window.X_SVG=%s;</script>' % (json.dumps(LOGO_URL), json.dumps(ISS), json.dumps(X_SVG)))

def patch_scripts(h):
    m = re.search(r'<script id="swx-map">(.*?)</script>', h, flags=re.S); c = m.group(1)
    pre = c[:c.index(';\n', c.index('const WATCH=')) + 2]
    w0 = c.index('window.WORLD='); w1 = c.index('\n  drawWorld();'); world = c[w0:w1] + ';\n'
    h = h.replace(m.group(0), '<script id="swx-map">' + pre + world + '</script>')
    h = re.sub(r'<script id="swx-v9">.*?</script>', '', h, flags=re.S)
    h = h.replace('if(cw.classList.contains("cap-open"))', 'if(cw&&cw.classList.contains("cap-open"))')
    return h

_a, _b, cum5 = grab(det1, 'class="dd2 cum"')
_c, _d, _cw = grab(cum5, 'class="capwide'); cum5 = cum5[:_c] + cum5[_d:]
cum5 = re.sub(r'<figcaption><b>([^<]*)</b><details class="capd"><summary>(.*?)</summary>(.*?)</details></figcaption>',
              r'<figcaption><details class="tdd sbcap"><summary><span class="stext"><b class="ct1">\1</b></span></summary><div class="td"><p>\2</p>\3</div></details></figcaption>', cum5, flags=re.S)
assert 'tdd sbcap"><summary><span class="stext"><b class="ct1">Cumulative NEAs' in cum5
svgmap = re.search(r'<svg id="pdd-map".*?</svg>', mapdiv, flags=re.S).group(0)
mapblock = ('<div class="subrow"><h3 class="sub">ASTEROIDS TODAY</h3><span class="mbtns"><button id="mapme" class="mb">\U0001F4CD My location</button><button id="mapbig" class="mb" aria-label="Enlarge the map">Enlarge ⤢</button></span></div>'
            + svgmap + '<div class="map-key">\U0001FAA8 Other NEO · \U0001F4A5 PHA · ☄️ Will enter Earth’s atmosphere · \U0001F6F0️ ISS orbit · ☀️ Sun · \U0001F319 Moon · shaded = night</div>'
            '<p class="mapcap">Designations announced in the <a href="https://minorplanetcenter.net/mpec/RecentMPECs.html" target="_blank" rel="noopener">Minor Planet Center’s circulars (MPECs)</a>, located with JPL data; last updated '
            + WTIME + ', refreshed automatically every 8 hours. Click an object icon to see what we know about it.</p>')
MODAL = ('<div class="mm" id="mapmodal" hidden role="dialog" aria-label="Asteroids today, map"><div class="mmbox"><div class="mmhead"><b>Asteroids today · map</b>'
         '<span class="mmtabs"><button data-v="world" class="on">Map</button><button data-v="sat">Satellite</button><button data-v="street">Streets</button></span><button class="mmx" aria-label="Close the map">×</button></div>'
         '<div class="mmmap"><svg id="mapbig-svg" viewBox="0 0 960 500"></svg><div id="lmap"></div><img class="wm" alt="" src="' + LOGO_URL + '">'
         '<div class="mmctl"><button class="zin" aria-label="Zoom in">+</button><button class="zout" aria-label="Zoom out">−</button><button class="zreset" aria-label="Reset">⟲</button><button class="zme" aria-label="Show my location">\U0001F4CD</button></div>'
         '<div class="ocard" id="ocard2" hidden></div></div>'
         '<div class="mmleg"><span>\U0001FAA8 Other NEO</span><span>\U0001F4A5 PHA (potentially hazardous)</span><span>☄️ Will enter Earth’s atmosphere</span><span>\U0001F6F0️ ISS now · solid = next orbit, dashed = last 50 min</span>'
         '<span>☀️ Sun overhead</span><span>\U0001F319 Moon overhead (current phase)</span><span>\U0001F4CD You (only if you share your location)</span><span>shaded = night · green = land · blue = sea</span></div>'
         '<p class="mmcap">Designations announced in the <a href="https://minorplanetcenter.net/mpec/RecentMPECs.html" target="_blank" rel="noopener">Minor Planet Center’s circulars (MPECs)</a>, located with JPL data; last updated '
         + WTIME + ', refreshed automatically every 8 hours. Click an object icon (or its name) to see what we know about it: a card with type, announcement, MPEC and position, with links to JPL and the MPC. '
         'ISS orbit from CelesTrak elements; Sun and Moon positions computed for now. Drag to pan, scroll to zoom; Satellite and Streets views zoom down to cities.</p>'
         '<div class="mmfoot"><a id="mapshare" class="xshare" target="_blank" rel="noopener">' + X_SVG + '<span>Share on X</span></a></div></div></div>')
LIBS = ('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css"><style>.leaflet-container img{max-width:none!important}</style>'
        '<script src="satellite.min.js"></script><script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>')
OPT = ('<div class="optbar"><button class="ox" aria-label="Minimise">–</button><div class="row"><b>MOCK-UP</b> split of the 30/70 columns ends:</div>'
       '<div class="row sp"><button data-s="1">① after the tally</button><button data-s="2">② after 3rd ad</button><button data-s="3" class="on">③ aligned</button></div>'
       '<div class="row">Watermark (click a chart): <span class="wmb"><button data-w="A" class="on">A</button><button data-w="B">B</button><button data-w="C">C</button></span></div></div>')
def inner(d):
    s = re.sub(r'^<details><summary>.*?</summary>', '', d, flags=re.S); assert s.endswith('</details>'); return s[:-len('</details>')]

for popout in (False, True):
    name = 'mock6' if popout else 'mock5'; D = os.path.join(MK, name)
    if os.path.exists(D): shutil.rmtree(D)
    shutil.copytree(M4, D, ignore=shutil.ignore_patterns('index.html', 'open.html', 'test.html'))
    if sat_js: open(os.path.join(D, 'satellite.min.js'), 'wb').write(sat_js)
    # left column
    left = ('<aside class="lcol"><div id="swx" data-w="l">' + mapblock +
            '<details class="tdd sbcap"><summary><span class="stext"><b class="ct1">Designations announced</b></span></summary>' + ptd + tw + '</details>'
            '<h3 class="sub plots">CUMULATIVE TALLY</h3>' + cum5 + '<hr class="wline"><div id="adslotL"><div id="adtiles" class="ad4 adl">' + T_X + T_NEWS + tiles4[0] + '</div></div></div></aside>')
    # image of the day: the actions row (how it was made + Share on X) on one line; "how it was made" is a floating banner
    iot = ('<section class="iotd"><p class="sechd" style="margin-top:0">IMAGE OF THE DAY</p><a class="iimg" href="%s" target="_blank" rel="noopener"><img src="%s" alt="%s"></a>'
           '<div class="icap"><p class="ic1"><b>%s</b> <span class="ai">AI illustration</span></p><p class="ic2">From the story <a href="%s" target="_blank" rel="noopener">%s</a>.</p>'
           '<div class="iact"><button class="idetb" aria-expanded="false">How this picture was made <i>+</i></button><a class="xshare" href="%s" target="_blank" rel="noopener">%s<span>Share on X</span></a></div></div>'
           '<div class="floatb" hidden><button class="mmx" aria-label="Close">×</button><b>How this picture was made</b><p>%s</p></div></section>'
           % (x['url'], a, H.escape(cap), H.escape(cap), x['url'], H.escape(x['headline']), tw_url, X_SVG.replace('<svg', '<svg class="xs"'), made))
    news = '<div class="under under-rows m2news">' + re.sub(r'^<div[^>]*>|</div>$', '', under) + '</div>'
    pops = ''
    if popout:
        tiles = ('<div class="poptiles">'
                 '<button class="poptile" data-pop="pop-ca"><span class="pt-thumb"><img src="charts/3-diameter-vs-distance-log-dark.png" alt=""></span><span class="pt-body"><b>Close approaches</b><span class="pt-n">TOP 15 · NEXT 7 DAYS</span>'
                 '<span class="pt-d">The 15 near-Earth asteroids that pass closest to Earth this week: 6 charts with captions and a sortable table (time, object, LD, size, H, first seen, velocity).</span><span class="pt-open">Open ↗</span></span></button>'
                 '<button class="poptile" data-pop="pop-ir"><span class="pt-thumb"><img src="charts/imp3b-timeline-century-alert-dark.png" alt=""></span><span class="pt-body"><b>Impact risk</b><span class="pt-n">JPL SENTRY · 15 HIGHEST PALERMO</span>'
                 '<span class="pt-d">The objects with the highest cumulative impact risk: the century timeline and distance vs Torino/Palermo, with the sortable table.</span><span class="pt-open">Open ↗</span></span></button></div>')
        look5 = '<div id="swx" data-w="m" class="swmain look4"><section id="space-watch"><h2 class="look">LOOKING UP!</h2>' + tiles + '</section></div>'
        pops = ''.join('<div class="pop" id="%s" hidden role="dialog" aria-label="%s"><div class="popbox"><div class="pophead"><b>%s</b><button class="mmx" aria-label="Close">×</button></div><div id="swx" data-w="p">%s</div></div></div>'
                       % (pid, ttl, ttl, inner(dd)) for pid, ttl, dd in (('pop-ca', 'CLOSE APPROACHES · TOP 15 NEXT 7 DAYS', det2), ('pop-ir', 'IMPACT RISK', det3)))
    else:
        look5 = '<div id="swx" data-w="m" class="swmain look4"><section id="space-watch"><h2 class="look">LOOKING UP!</h2>' + det2 + det3 + '</section></div>'
    right = '<div class="mcol">' + iot + look5 + news + '</div>'
    rest = '<div class="mcol rest5">' + lead + ad4row + art2 + news7 + castrow + top10 + car7 + '<div class="m3rail">' + pladd + plrail + '</div></div>'
    g = ('<div class="m2 m4 m5 s3">' + left + right + '</div><div id="swx" data-w="ar" class="adrow5"><div id="adslotRow"></div></div>' + rest + pops)
    hh = h0[:bs] + g + h0[fe:]; hh = hh.replace(g, g + foot, 1)
    hh = patch_scripts(hh)
    hh = with_type(hh, M2CSS + '\n'.join(l for l in M4CSS.split('\n') if '.dd2.cum .capd' not in l) + M56CSS + '.m3rail{margin:1rem 0 2rem}.m3rail .sp-stack{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}')
    hh = hh.replace('</head>', LIBS + '</head>', 1)
    hh = hh.replace('</body>', MODAL + OPT + PRE + '<script>' + MAPJS + '</script><script>' + LBJS + '</script><script>' + (POPJS if popout else '') + '</script>' + JS2 + '<script>' + UIJS + '</script></body>')
    open(os.path.join(D, 'index.html'), 'w', encoding='utf-8').write(hh)
    open(os.path.join(D, 'open.html'), 'w', encoding='utf-8').write(hh.replace('<details>', '<details open>'))
    print(name, 'written', len(hh))

# ================= MOCK 7: mock 6 + synced carousels with bigger thumbnails (+30/+40/+50%), Top-10 sourced carousel + 4 social cards,
#                   today's newscast tile in the left column, split ends aligned (3), three ways to lay out the rest.
from mock7_assets import JS7, CSS7
M7 = os.path.join(MK, 'mock7'); D = M7
if os.path.exists(D): shutil.rmtree(D)
shutil.copytree(M4, D, ignore=shutil.ignore_patterns('index.html', 'open.html', 'test.html'))
if sat_js: open(os.path.join(D, 'satellite.min.js'), 'wb').write(sat_js)
# -- today's newscast, read from the live front page
live = urllib.request.urlopen(urllib.request.Request(LIVE + '/?lang=en', headers={'User-Agent': 'Mozilla/5.0'}), timeout=40).read().decode('utf-8', 'ignore')
cb = re.search(r'<section class="castband".*?</section>', live, flags=re.S).group(0)
cast_mp4 = re.search(r'data-cb="([^"]+)"', cb).group(1); cast_poster = re.search(r'<img src="([^"]+)"', cb).group(1)
cast_ep = re.search(r'Episode</span>\s*(\d+)\s*&middot;\s*([\d:]+)', cb); ep_n, ep_t = cast_ep.group(1), cast_ep.group(2)
_cd = re.search(r'The (\d{4}-\d{2}-\d{2}) edition', cb) or re.search(r'the-day-(\d{4}-\d{2}-\d{2})', cb) or re.search(r'(\d{4}-\d{2}-\d{2})', cb)
cast_day = _cd.group(1) if _cd else datetime.date.today().isoformat()
YT_URL = 'https://www.youtube.com/@PlanetaryDefenseDaily'
YT_SVG = re.search(r'<svg.*?</svg>', YI, flags=re.S).group(0)
POPSVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3h7v7M10 21H3v-7M21 3l-8 8M3 21l8-8"/></svg>'
newscast = ('<div class="ncast"><b class="nck">Today’s newscast · Episode %s · %s</b>'
            '<div class="ncv" data-src="%s"><video preload="none" poster="%s" playsinline></video><button class="ncplay" aria-label="Play the newscast">▶</button></div>'
            '<p class="ncs">The %s edition, drawn from the paper’s live front page.</p>'
            '<div class="ncb"><button class="ncpop" data-tip="Open in a larger player" aria-label="Open in a larger player">%s</button>'
            '<a class="ncall" href="%s/cast/all" target="_blank" rel="noopener" data-tip="All newscasts" aria-label="All newscasts"><img src="%s" alt="PDD"></a>'
            '<a class="ncyt" href="%s" target="_blank" rel="noopener" data-tip="Watch on YouTube" aria-label="Watch on YouTube">%s<span>YouTube</span></a></div></div>'
            % (ep_n, ep_t, cast_mp4, cast_poster, cast_day, POPSVG, LIVE, LOGO_URL, YT_URL, YT_SVG))
CASTPOP = '<div id="castpop" hidden role="dialog" aria-label="Today’s newscast"><div class="cpb"><div class="mmhead"><b>Today’s newscast · Episode %s · %s</b><button class="mmx" aria-label="Close">×</button></div><video controls playsinline></video></div></div>' % (ep_n, ep_t)
# -- top 10 sourced articles, last 7 days (today and the 6 days before), ranked by the number of sources
top = []; wk = []
try:      # public API only (no key): sources = distinct source names among a story's cited facts, facts = number of cited facts
    td = datetime.datetime.utcnow().date()
    for s_ in ALL:
        if (td - datetime.date.fromisoformat(s_['published_at'][:10])).days > 6 or s_.get('kind') == 'blog': continue
        cf = api('/api/v1/stories/' + s_['id']).get('cited_facts') or []
        wk.append(dict(s_, sources=len({(f.get('source') or '').lower().replace('www.', '') for f in cf}), facts=len(cf)))
    wk.sort(key=lambda s_: (-s_['sources'], -s_['facts'], s_['published_at']))
    top = wk[:10]
except Exception as ex: print('top sourced not built:', ex)
LOGO_L = LIVE + '/logo/planetary-defense-daily'
def ttile(i, s_):
    ph = ('<span class="ph ph%d"><img src="%s" alt=""><span>Image coming soon</span></span>' % (i % 3 + 1, LOGO_L if i % 3 == 1 else LOGO_URL))
    u = LIVE + '/story/' + s_['id']; d_ = datetime.date.fromisoformat(s_['published_at'][:10]).strftime('%b %d, %Y').replace(' 0', ' ')
    if not s_.get('art'): NOART.append({'id': s_['id'], 'headline': s_['headline'], 'published_at': s_['published_at']})
    return ('<article class="tt"><a class="ttt" href="%s" target="_blank" rel="noopener">%s</a><a class="tti" href="%s" target="_blank" rel="noopener" aria-label="Open the article">%s'
            '<img class="art" src="%s/story-art/%s/sm" alt="" loading="lazy" onerror="this.remove()"></a><span class="ttd">%s · %d sources</span></article>'
            % (u, H.escape(s_['headline']), u, ph, LIVE, s_['id'], d_, s_['sources']))
IGI = '<span class="xl" style="background:linear-gradient(45deg,#f9a03f,#e1306c,#833ab4);color:#fff"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="17.2" cy="6.8" r="1.2" fill="currentColor"/></svg></span>'
FBI = '<span class="xl" style="background:#1877f2;color:#fff"><svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M14 8V6.5c0-.7.2-1 1.1-1H17V2h-2.7C11.4 2 10 3.6 10 6v2H8v3.4h2V22h4V11.4h2.7L17 8z"/></svg></span>'
T_IG = tile('#', 'Coming soon', IGI, 'Follow us on Instagram', 'Pictures and short videos, soon.', 'Coming soon').replace('class="tile"', 'class="tile soon"')
T_FB = tile('#', 'Coming soon', FBI, 'Follow us on Facebook', 'Our page is on its way.', 'Coming soon').replace('class="tile"', 'class="tile soon"')
tops = ('<section class="tops"><h2 class="topt">Top 10 sourced articles last 7 days</h2><div class="tcar"><button class="tcb prev" aria-label="Previous">‹</button><div class="ttrack">'
        + ''.join(ttile(i, s_) for i, s_ in enumerate(top)) + '</div><button class="tcb next" aria-label="Next">›</button></div>'
        '<div class="tdots">' + '<button class="dot" aria-label="Article %d"></button>' * 0 + ''.join('<button class="dot" aria-label="Article %d"></button>' % (k + 1) for k in range(len(top))) + '</div>'
        '<div id="swx" data-w="so" class="socials"><div class="ad4 soc">' + T_X + T_YT + T_IG + T_FB + '</div></div></section>')
open(os.path.join(MK, 'TODO-story-art.md'), 'w').write('# Stories shown in the mock-ups without an AI image (request one)\n\n' + ''.join('- %s  %s  %s\n' % (str(x_['published_at'])[:10], x_['id'], x_['headline']) for x_ in {y_['id']: y_ for y_ in NOART}.values()))
# -- left column: map, designations, tally (no ads), newscast
cum7 = cum5.replace(' data-auto', '')
left7 = ('<aside class="lcol"><div id="swx" data-w="l">' + mapblock +
         '<details class="tdd sbcap"><summary><span class="stext"><b class="ct1">Designations announced</b></span></summary>' + ptd + tw + '</details>'
         '<h3 class="sub plots">CUMULATIVE TALLY</h3>' + cum7 + '<hr class="wline">' + newscast + '</div></aside>')
# -- LOOKING UP! as pop-out tiles whose thumbnails are carousels (kept in step with the tally)
CA_IMGS = ['3-diameter-vs-distance-log-dark.png', '3b-diameter-vs-distance-linear-dark.png', '2-3-3d-dark-grid.png', '2-3d-3d-swapped-axes-dark.png', '1-3c-distance-velocity-size-log-legends-dark.png', '1-3d-distance-velocity-size-linear-legends-dark.png']
IR_IMGS = ['imp3b-timeline-century-alert-dark.png', 'imp1b-distance-torino-palermo-table-dark.png']
def thumbs(ims): return '<span class="pt-thumb"><span class="ptc-set" data-i="0">' + ''.join('<img class="%s" src="charts/%s" alt="">' % ('on' if k == 0 else '', f) for k, f in enumerate(ims)) + '</span><span class="ptn">1 / %d</span></span>' % len(ims)
tiles7 = ('<div class="poptiles">'
          '<button class="poptile" data-pop="pop-ca">' + thumbs(CA_IMGS) + '<span class="pt-body"><b>Close approaches</b><span class="pt-n">TOP 15 · NEXT 7 DAYS</span>'
          '<span class="pt-d">The 15 near-Earth asteroids that pass closest to Earth this week: 6 charts with captions and a sortable table.</span><span class="pt-open">Open ↗</span></span></button>'
          '<button class="poptile" data-pop="pop-ir">' + thumbs(IR_IMGS) + '<span class="pt-body"><b>Impact risk</b><span class="pt-n">JPL SENTRY · 15 HIGHEST PALERMO</span>'
          '<span class="pt-d">The objects with the highest cumulative impact risk: century timeline and distance vs Torino/Palermo, with the sortable table.</span><span class="pt-open">Open ↗</span></span></button></div>')
look7 = '<div id="swx" data-w="m" class="swmain look4"><section id="space-watch"><h2 class="look">LOOKING UP!</h2>' + tiles7 + '</section></div>'
pops7 = ''.join('<div class="pop" id="%s" hidden role="dialog" aria-label="%s"><div class="popbox"><div class="pophead"><b>%s</b><button class="mmx" aria-label="Close">×</button></div><div id="swx" data-w="p">%s</div></div></div>'
                % (pid, ttl, ttl, inner(dd)) for pid, ttl, dd in (('pop-ca', 'CLOSE APPROACHES · TOP 15 NEXT 7 DAYS', det2), ('pop-ir', 'IMPACT RISK', det3)))
iot7 = iot  # image of the day (+ floating "how made" banner) as built for mock 5/6
right7 = '<div class="mcol">' + iot7 + look7 + tops + '</div>'
news7l = '<div class="under under-rows m2news">' + re.sub(r'^<div[^>]*>|</div>$', '', under) + '</div>'
rest7 = ('<div class="mcol rest7 la"><div class="c-lead">' + lead + ad4row + '</div><div class="c-art2">' + art2 + '</div><div class="c-week">' + news7 + '</div>'
         '<div class="c-side"><div class="c-heads">' + news7l + '</div><div class="c-rail m3rail">' + pladd + plrail + '</div></div>'
         '<div class="c-top10">' + top10 + '</div><div class="c-adcar">' + car7 + '</div></div>')
g7 = '<div class="m2 m4 m5 s3">' + left7 + right7 + '</div>' + rest7 + pops7
h7 = h0[:bs] + g7 + h0[fe:]; h7 = h7.replace(g7, g7 + foot, 1); h7 = patch_scripts(h7)
OPT7 = ('<div class="optbar"><button class="ox" aria-label="Minimise">–</button><div class="row"><b>MOCK-UP</b> split of the 30/70 columns ends: ③ aligned</div>'
        '<div class="row">Thumbnails bigger by: <span class="szb"><button data-z="30">+30%</button><button data-z="40" class="on">+40%</button><button data-z="50">+50%</button></span></div>'
        '<div class="row">After the split: <span class="lyb"><button data-l="a" class="on">A · 70/30</button><button data-l="b">B · rows</button><button data-l="c">C · side rail</button></span></div>'
        '<div class="row">Watermark (click a chart): <span class="wmb"><button data-w="A" class="on">A</button><button data-w="B">B</button><button data-w="C">C</button></span></div></div>')
css7 = M2CSS + '\n'.join(l for l in M4CSS.split('\n') if '.dd2.cum .capd' not in l) + M56CSS + CSS7 + '.m3rail{margin:0}'
h7 = with_type(h7, css7).replace('</head>', LIBS + '</head>', 1)
h7 = h7.replace('</body>', MODAL + CASTPOP + OPT7 + PRE + '<script>' + MAPJS + '</script><script>' + LBJS + '</script><script>' + POPJS + '</script>' + JS2 + '<script>' + JS7 + '</script></body>')
open(os.path.join(D, 'index.html'), 'w', encoding='utf-8').write(h7)
open(os.path.join(D, 'open.html'), 'w', encoding='utf-8').write(h7.replace('<details>', '<details open>'))
print('mock7 written', len(h7), 'top sourced:', len(top), 'without art:', sum(1 for s_ in top if not s_.get('art')))

# ================= MOCK 8: mock 7 with the owner's choices (30/70 aligned, thumbnails +60%, side-rail layout, watermark C lighter),
#                   page content 85% wide, first article under LOOKING UP! (read more / share on X), small images with links on every news item.
SHOW_READS = False          # "Most read / Most shared this month": kept here, not shown until a reads/shares counter exists
M8 = os.path.join(MK, 'mock8'); D = M8
if os.path.exists(D): shutil.rmtree(D)
shutil.copytree(M4, D, ignore=shutil.ignore_patterns('index.html', 'open.html', 'test.html', 'mobile.html'))
if sat_js: open(os.path.join(D, 'satellite.min.js'), 'wb').write(sat_js)
_mini_n = [0]; _seen_noart = {}
def ph_html(n):
    return '<span class="ph ph%d"><img src="%s" alt=""></span>' % (n % 3 + 1, LOGO_L if n % 3 == 1 else LOGO_URL)
def small_img(sid, cls, headline=''):
    _mini_n[0] += 1; u = LIVE + '/story/' + sid
    if art(sid) is None: _seen_noart[sid] = headline
    return ('<a class="%s" href="%s" target="_blank" rel="noopener" aria-label="Open the article">%s<img class="art" src="%s/story-art/%s/sm" alt="" loading="lazy" onerror="this.remove()"></a>'
            % (cls, u, ph_html(_mini_n[0]), LIVE, sid))
def add_minis(html_):
    def f(m):
        sid = m.group(3); hl = re.search(r'>([^<]+)</a></h2>', html_[m.end():m.end() + 800])
        return m.group(1) + small_img(sid, 'mini', hl.group(1) if hl else '') + m.group(2)
    return re.sub(r'(<div class="item row"[^>]*>)(<h2 class="st"><a href="%s/story/([0-9a-f]{32}))' % re.escape(LIVE), lambda m: f(type('M', (), {'group': lambda self, k: ([None, m.group(1), m.group(2), m.group(3)])[k], 'end': lambda self: m.end()})()), html_)
heads8 = '<div class="under under-rows m2news">' + add_minis(re.sub(r'^<div[^>]*>|</div>$', '', under)) + '</div>'
rail8 = add_minis(pladd + plrail)
# first article: image (small, linked), text at the size of the paper's own articles, "Read more" tab, Share on X
lead_hl = re.search(r'<h2><a [^>]*>([^<]*)</a></h2>', lead).group(1)
lead_url = LIVE + '/story/' + lead_id
fa_img = small_img(lead_id, 'fa-img', lead_hl)
lead8 = lead.replace('<div class="leadlede leadfull">', '<div class="leadlede leadfull">' + fa_img, 1)
tw_lead = 'https://x.com/intent/tweet?text=' + urllib.parse.quote(H.unescape(lead_hl)) + '&url=' + urllib.parse.quote(lead_url)
fa8 = ('<section class="fa">' + lead8 + '<div class="fa-act"><button class="fa-more" aria-expanded="false"><span>Read more</span> <i>▾</i></button>'
       '<a class="xshare" href="%s" target="_blank" rel="noopener">%s<span>Share on X</span></a></div></section>' % (tw_lead, X_SVG.replace('<svg', '<svg class="xs"')))
art2_8 = art2
if art2_id: art2_8 = art2.replace('<div class="leadlede leadfull">', '<div class="leadlede leadfull">' + small_img(art2_id, 'fa-img', ''), 1)
right8 = '<div class="mcol">' + iot7 + look7 + fa8 + '</div>'
ads_side = ad4row
reads8 = ('<div class="c-top10">' + top10 + '</div>') if SHOW_READS else ''
rest8 = ('<div class="mcol rest7 ld"><div class="c-art2">' + art2_8 + '</div><div class="c-week">' + news7 + '</div><div class="c-tops">' + tops + '</div><div class="c-adcar">' + car7 + '</div>'
         '<div class="c-side"><div class="c-heads">' + heads8 + '</div><div class="c-rail m3rail">' + rail8 + '</div><div class="c-ads2">' + ads_side + '</div></div>' + reads8 + '</div>')
g8 = '<div class="m2 m4 m5 s3">' + left7 + right8 + '</div>' + rest8 + pops7
h8 = h0[:bs] + g8 + h0[fe:]; h8 = h8.replace(g8, g8 + foot, 1); h8 = patch_scripts(h8)
open(os.path.join(MK, 'TODO-story-art.md'), 'w').write('# Stories shown in the mock-ups without an AI image (request one)\n\n' + ''.join('- %s  %s\n' % (k_, v_) for k_, v_ in sorted(_seen_noart.items())))
CSS8 = r'''
/* ===== mock 8 ===== */
html.pt60{--ptw:60.8%}
.m5,.rest7{width:calc(85vw/.84);margin-left:auto!important;margin-right:auto!important}
.m5 .mcol{display:flex;flex-direction:column}
.fa{border-top:3px solid #eef2fa;margin-top:1.4rem;padding-top:1rem;position:relative}
.fa .lead{border:0!important;padding:0!important;margin:0!important}
.fa .lead h2,.fa .lead h2 a{font-size:calc(2.6rem/.84)!important;line-height:1.08}
.fa .leadlede,.fa .leadlede p,.rest7 .art2 .leadlede,.rest7 .art2 .leadlede p{max-width:none!important}
.fa .leadlede p,.rest7 .art2 .leadlede p{font-size:calc(1.06rem/.84)!important;line-height:1.72!important}
.fa .leadlede{max-height:11.5em;overflow:hidden;position:relative}
.fa .leadlede::after{content:"";position:absolute;left:0;right:0;bottom:0;height:4.5em;background:linear-gradient(rgba(11,21,38,0),#0b1526 85%);pointer-events:none}
.fa.open .leadlede{max-height:none}.fa.open .leadlede::after{display:none}
.fa-img{float:right;width:176px;margin:0 0 .6rem 1.1rem;position:relative;display:block;aspect-ratio:4/3;border:1px solid #2c3b57;overflow:hidden;background:#0f1a2e}
.fa-img img.art{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.fa-act{display:flex;align-items:center;justify-content:space-between;gap:12px;border-top:1px solid #2c3b57;border-bottom:1px solid #2c3b57;margin-top:.4rem;padding:.35rem 0}
.fa-more{display:flex;align-items:center;gap:.6rem;background:none;border:0;color:#eef2fa;cursor:pointer;font:700 11.5px system-ui,Arial,sans-serif;letter-spacing:.14em;text-transform:uppercase;padding:.25rem 0}.fa-more i{font:400 22px/1 system-ui;font-style:normal;color:#de7c7c}
.mini{position:relative;display:block;width:76px;aspect-ratio:4/3;border:1px solid #2c3b57;overflow:hidden;background:#0f1a2e;float:left;margin:2px 12px 4px 0}
.mini img.art{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}.mini .ph img,.fa-img .ph img{height:60%}.mini .ph span{display:none}
.item.row{overflow:hidden}
.rest7.ld{grid-template-columns:7fr 3fr;grid-template-areas:"art2 side" "week side" "tops side" "adcar side"}
.c-tops{grid-area:tops}.rest7.ld .c-side{display:flex;flex-direction:column;gap:22px;grid-area:side;position:sticky;top:10px;align-self:start}.rest7.ld .c-heads,.rest7.ld .c-rail{grid-area:auto}
.c-ads2 #swx[data-w="a"] .ad4,.c-ads2 .ad4{grid-template-columns:1fr!important;padding:0!important}
.rest7 .art2{border-top:3px solid #eef2fa}
.wmC{opacity:.34!important}
@media(max-width:1100px){
 .m5,.rest7{width:calc(94vw/.84)}
 .rest7.ld{grid-template-columns:1fr!important;grid-template-areas:none!important}.rest7.ld .c-side{position:static}
 .fa .lead h2,.fa .lead h2 a{font-size:calc(1.9rem/.84)!important}.fa-img{width:120px}
 .poptiles{grid-template-columns:1fr!important}.poptile{flex-direction:column}.poptile .pt-thumb{flex:0 0 auto!important;width:100%}
 .tt{flex-basis:calc((100% - 14px)/2)}.ncb{flex-wrap:wrap}
 .iact{flex-wrap:wrap}.tcar .tcb{width:28px}
}
@media(max-width:560px){.tt{flex-basis:100%}.rest7 .ntrack .nc,.ntrack .nc{flex-basis:calc((100% - 12px)/2)!important}#swx .soc{grid-template-columns:repeat(2,minmax(0,1fr))}.fa-img{width:104px}.car7w .track .tile{flex-basis:72%!important}}
'''
FAJS = r'''(function(){var f=document.querySelector('.fa'),b=document.querySelector('.fa-more');if(!f||!b)return;b.onclick=function(){var o=f.classList.toggle('open');b.setAttribute('aria-expanded',o);b.querySelector('span').textContent=o?'Show less':'Read more';b.querySelector('i').textContent=o?'▴':'▾'}})();'''
LB8 = LBJS.replace("wm='A'", "wm='C'").replace('class="wm wmA"', 'class="wm wmC"')
LB8 = re.sub(r'<span class="wmsw">.*?</span>', '', LB8, flags=re.S)
css8 = M2CSS + '\n'.join(l for l in M4CSS.split('\n') if '.dd2.cum .capd' not in l) + M56CSS + CSS7 + '.m3rail{margin:0}' + CSS8
h8 = with_type(h8, css8).replace('</head>', LIBS + '</head>', 1)
h8 = h8.replace('</body>', MODAL + CASTPOP + PRE + '<script>' + MAPJS + '</script><script>' + LB8 + '</script><script>' + POPJS + '</script>' + JS2 + '<script>' + JS7.replace("' pt40'", "' pt60'") + '</script><script>' + FAJS + '</script></body>')
open(os.path.join(D, 'index.html'), 'w', encoding='utf-8').write(h8)
open(os.path.join(D, 'open.html'), 'w', encoding='utf-8').write(h8.replace('<details>', '<details open>'))
open(os.path.join(D, 'mobile.html'), 'w', encoding='utf-8').write('<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>PDD mock-up 8, phone view</title><body style="margin:0;background:#222;display:flex;justify-content:center;padding:20px"><iframe src="index.html" style="width:390px;height:844px;border:10px solid #000;border-radius:28px;background:#0b1526"></iframe></body>')
print('mock8 written', len(h8), 'images missing:', len(_seen_noart))

# ================= MOCK 9: mock 8 with the bottom restructured: two real columns (no shared rows, so no blank gaps),
#                   the four social tiles leave "Top 10 sourced" and join one full-width "Ads" carousel together with the two side ads (now tiles).
M9 = os.path.join(MK, 'mock9'); D = M9
if os.path.exists(D): shutil.rmtree(D)
shutil.copytree(M8, D, ignore=shutil.ignore_patterns('index.html', 'open.html', 'mobile.html'))
SID = re.compile(r'/story/([0-9a-f]{32})')
front = {lead_id} | ({art2_id} if art2_id else set())          # the front-page and main stories stay where they are
top9 = [s_ for s_ in wk if s_['id'] not in front][:10]            # the 10 with the most sources (wk is sorted by sources); they live only here
ids_top = {s_['id'] for s_ in top9}
def drop_top(h_): return re.sub(r'<div class="item row".{0,2200}?</div></div>', lambda m: '' if (set(SID.findall(m.group(0))) & ids_top) else m.group(0), h_, flags=re.S)
heads9 = drop_top(heads8); rail9 = drop_top(add_minis(plrail))
used0 = front | ids_top | set(SID.findall(heads9)) | set(SID.findall(rail9))
def item_row(x):
    by = x.get('byline') or {}; hrs = int((datetime.datetime.utcnow() - datetime.datetime.fromisoformat(x['published_at'].replace('Z', '')).replace(tzinfo=None)).total_seconds() // 3600)
    ago = ('%dh' % hrs) if hrs < 48 else ('%dd' % (hrs // 24))
    u = LIVE + '/story/' + x['id']
    return ('<div class="item row" data-sec="%s">%s<h2 class="st"><a href="%s" style="color:inherit">%s</a></h2><div class="by"><img src="%s" alt="" loading="lazy"><span>By %s <span class="ago">&middot; %s</span></span></div></div>'
            % (H.escape(x.get('category', '')), small_img(x['id'], 'mini', x['headline']), u, H.escape(x['headline']), by.get('avatar', ''), H.escape(by.get('name', '')), ago))
n_have = len(SID.findall(heads9)) + len(SID.findall(rail9)) ; n_have = len(set(SID.findall(heads9)) | set(SID.findall(rail9)))
cand = [x for x in ALL if x['id'] not in used0 and x['kind'] != 'blog']
refill = cand[:max(0, 10 - n_have)]
rail9 = rail9.rstrip()
rail9 = (rail9[:-6] + ''.join(item_row(x) for x in refill) + '</div>') if rail9.endswith('</div>') else rail9 + ''.join(item_row(x) for x in refill)
used0 |= {x['id'] for x in refill}
left_over = [x for x in ALL if x['id'] not in used0 and x['kind'] != 'blog'][:14]
news9 = ('<section class="weekw"><p class="sechd">MORE RECENT NEWS</p><div class="carw"><button class="cb" data-d="-1" aria-label="Previous">&#8249;</button><div class="track ntrack">'
         + ''.join(card(x, '<span class="nd">%s</span>' % ds(x)) for x in left_over) + '</div><button class="cb" data-d="1" aria-label="Next">&#8250;</button></div></section>')
print('week carousel:', len(left_over), 'stories, oldest', min(ds(x) for x in left_over) if left_over else '-')
tops9 = ('<section class="tops"><h2 class="topt">Top 10 sourced articles last 7 days</h2><div class="tcar"><button class="tcb prev" aria-label="Previous">‹</button><div class="ttrack">'
        + ''.join(ttile(i, s_) for i, s_ in enumerate(top9)) + '</div><button class="tcb next" aria-label="Next">›</button></div>'
        '<div class="tdots">' + ''.join('<button class="dot" aria-label="Article %d"></button>' % (k + 1) for k in range(len(top9))) + '</div></section>')
T_FIND = tile('https://relics.luisafernanda.space', 'Ad', PDI, 'Space finds we actually love', 'Hand-picked space finds, from books and jewelry to decor and clothing. Affiliate links.', 'Take a peek!')
ads9_tiles = tiles4[0] + tiles4[1] + T_FIND + T_NEWS + T_SCI + T_NF + T_OWN + T_X + T_YT + T_IG + T_FB
ads9 = ('<section class="ads9"><h2 class="topt">Ads</h2><div id="swx" data-w="c" class="car7w"><button class="cb" data-d="-1" aria-label="Previous">&#8249;</button>'
        '<div class="ad4 track" id="track7">' + ads9_tiles + '</div><button class="cb" data-d="1" aria-label="Next">&#8250;</button></div></section>')
rest9 = ('<div class="mcol rest7 r9"><div class="r9l"><div class="c-art2">' + art2_8 + '</div><div class="c-week">' + news9 + '</div></div>'
         '<div class="r9r"><div class="c-heads">' + heads9 + '</div><div class="c-rail m3rail">' + rail9 + '</div></div></div>'
         '<div class="mcol rest7 r9b"><div class="c-tops">' + tops9 + '</div></div>' + ads9)
g9 = '<div class="m2 m4 m5 s3">' + left7 + right8 + '</div>' + rest9 + pops7
h9 = h0[:bs] + g9 + h0[fe:]; h9 = h9.replace(g9, g9 + foot, 1); h9 = patch_scripts(h9)
CSS9 = r'''
/* ===== mock 9 ===== */
.rest7.r9{grid-template-columns:7fr 3fr!important;grid-template-areas:none!important;gap:22px;align-items:start}
.r9l,.r9r{display:flex;flex-direction:column;gap:20px;min-width:0}
.r9l>*,.r9r>*{margin:0!important}
.r9 .c-week .car7w,.r9 .weekw{margin:0!important}
.r9 .tops{margin:0!important}
.r9 .c-rail{width:100%}
.ads9{width:calc(76.5vw/.84);margin:24px auto 0;zoom:.84;border-top:3px solid #eef2fa;padding-top:.8rem}
.ads9 .topt{margin:0 0 .5rem}
.ads9 .car7w{margin:.4rem 0 1.2rem!important}
.fa-img{width:150px}
.r9b{display:block!important;margin-top:20px}
.ads9 .car7w .track .tile{flex:0 0 calc((100% - 40px)/4)!important}.ads9 .tile .tb{max-width:100%;white-space:normal;overflow-wrap:anywhere}
.pfoot a,.pfoot span,.pfoot b,.pfoot p{font-size:15px!important;line-height:1.5}.pfoot .pf-name{font-size:28px!important}.pfoot .pf-tag,.pfoot .pf-addr,.pfoot .pf-disc{font-size:14px!important}
@media(max-width:1100px){.rest7.r9{grid-template-columns:1fr!important}.ads9{width:calc(94vw/.84)}}
@media(max-width:560px){.ads9 .car7w .track .tile{flex-basis:72%!important}}
'''

ADSJS = r"""(function(){var box=document.querySelector('.ads9 .car7w');if(!box)return;var c=box.cloneNode(true);box.parentNode.replaceChild(c,box);var t=c.querySelector('.track');t.style.position='relative';var k=0,n=t.children.length,paused=false;
function vis(){var a=t.children[1].offsetLeft-t.children[0].offsetLeft,w=Math.round(t.clientWidth/a);return Math.max(1,w)}
function go(i){var m=n-vis();if(i>m)i=0;if(i<0)i=m;k=i;t.scrollTo({left:t.children[k].offsetLeft-t.children[0].offsetLeft,behavior:'smooth'})}
c.querySelectorAll('.cb').forEach(function(b){b.onclick=function(){go(k+(+b.dataset.d))}});
c.onmouseenter=function(){paused=true};c.onmouseleave=function(){paused=false};setInterval(function(){if(!paused&&!document.hidden)go(k+1)},6000)})();"""
css9 = css8 + CSS9
h9 = with_type(h9, css9).replace('</head>', LIBS + '</head>', 1)
h9 = h9.replace('</body>', MODAL + CASTPOP + PRE + '<script>' + MAPJS + '</script><script>' + LB8 + '</script><script>' + POPJS + '</script>' + JS2 + '<script>' + JS7.replace("' pt40'", "' pt60'") + '</script><script>' + FAJS + '</script><script>' + ADSJS + '</script></body>')
open(os.path.join(D, 'index.html'), 'w', encoding='utf-8').write(h9)
open(os.path.join(D, 'open.html'), 'w', encoding='utf-8').write(h9.replace('<details>', '<details open>'))
open(os.path.join(D, 'mobile.html'), 'w', encoding='utf-8').write(open(os.path.join(M8, 'mobile.html')).read().replace('mock-up 8', 'mock-up 9'))
if os.path.isdir(os.path.join(M1, 'img', 'art')): shutil.copytree(os.path.join(M1, 'img', 'art'), os.path.join(D, 'img', 'art'), dirs_exist_ok=True)
print('mock9 written', len(h9))

# ---- publish: with SITE_OUT set (GitHub Action), mock 9 becomes the clone's page
if os.environ.get('SITE_OUT'):
    so = os.environ['SITE_OUT']; os.makedirs(so, exist_ok=True)
    shutil.copytree(M9, so, dirs_exist_ok=True, ignore=shutil.ignore_patterns('open.html', 'mobile.html', 'test.html'))
    print('site written to', so)
