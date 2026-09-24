"""The report: one self-contained HTML file (data inlined, no server)."""
import json

CSS = r"""
:root{
  --bg:#F2F5F6; --surface:#FFFFFF; --ink:#15222A; --ink2:#4E5E68; --muted:#7A8891; --rule:#DCE3E7;
  --google:#B8412B; --jev:#0E8FA6; --fine:#6E8A1E; --unsure:#8A969E;
  --t1:#0A5F6F; --t2:#0E8FA6; --t3:#8FCAD5; --wash:#E6F3F5; --googlewash:#F7E7E3;
  --focus:#0E8FA6;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#121A1F; --surface:#1A242A; --ink:#E8EEF1; --ink2:#AEBBC2; --muted:#83929A; --rule:#2C3A42;
  --google:#E0664E; --jev:#2FA3B8; --fine:#7F9B34; --unsure:#7D8B93;
  --t1:#6FD0E0; --t2:#2FA3B8; --t3:#1E5E6A; --wash:#17323A; --googlewash:#3A211C;
}}
:root[data-theme="dark"]{
  --bg:#121A1F; --surface:#1A242A; --ink:#E8EEF1; --ink2:#AEBBC2; --muted:#83929A; --rule:#2C3A42;
  --google:#E0664E; --jev:#2FA3B8; --fine:#7F9B34; --unsure:#7D8B93;
  --t1:#6FD0E0; --t2:#2FA3B8; --t3:#1E5E6A; --wash:#17323A; --googlewash:#3A211C;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Archivo",system-ui,sans-serif;
  font-size:17px;line-height:1.5;font-variant-numeric:tabular-nums}
.wrap{max-width:1160px;margin:0 auto;padding:40px 24px 80px}
h1,h2,h3{font-stretch:112%;font-weight:700;letter-spacing:-.01em;margin:0}
h1{font-size:clamp(30px,4.4vw,52px);line-height:1.06;max-width:22ch}
h2{font-size:clamp(22px,2.4vw,28px);line-height:1.15;margin-bottom:6px}
h3{font-size:19px}
p{margin:0}
.context{color:var(--ink2);font-size:15px;margin-bottom:28px;display:flex;gap:14px;flex-wrap:wrap;align-items:center}
.context b{color:var(--ink);font-weight:600}
.lede{font-size:19px;color:var(--ink2);max-width:62ch;margin-top:16px}
section{margin-top:64px}
.sub{color:var(--ink2);max-width:66ch;margin-bottom:22px}
.panel{background:var(--surface);border:1px solid var(--rule);border-radius:14px}
code,.path{font-family:"Archivo",sans-serif;font-stretch:88%;font-weight:600}
.path{word-break:break-all}
.tag{display:inline-flex;align-items:center;gap:7px;font-size:14px;font-weight:600;white-space:nowrap}
.tag i{width:10px;height:10px;border-radius:3px;display:inline-block;flex:none}
.muted{color:var(--muted)}
button{font:inherit;color:inherit}
:focus-visible{outline:3px solid var(--focus);outline-offset:2px;border-radius:6px}
.themebtn{margin-left:auto;background:none;border:1px solid var(--rule);border-radius:999px;padding:4px 12px;
  font-size:14px;color:var(--ink2);cursor:pointer}
/* pipeline strip */
.flow{display:grid;grid-template-columns:repeat(4,1fr);gap:0;margin-top:36px}
.flow>div{padding:18px 20px;border-left:1px solid var(--rule)}
.flow>div:first-child{border-left:0;padding-left:0}
.flow .n{font-size:36px;font-weight:700;font-stretch:112%;line-height:1}
.flow .l{font-size:15px;color:var(--ink2);margin-top:6px;max-width:24ch}
.flow .who{font-size:13px;color:var(--muted);margin-top:10px}
/* bars */
.bar{height:10px;border-radius:0 4px 4px 0;background:var(--jev)}
.track{background:var(--rule);border-radius:0 4px 4px 0;height:10px;width:100%;position:relative;overflow:visible}
/* chips */
.chips{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}
.chip{border:1px solid var(--rule);background:var(--surface);border-radius:999px;padding:6px 14px;font-size:14px;
  font-weight:600;cursor:pointer;display:inline-flex;align-items:center;gap:8px}
.chip[aria-pressed="true"]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.chip i{width:9px;height:9px;border-radius:3px}
/* table */
table{width:100%;border-collapse:collapse;font-size:15px}
th{text-align:left;font-weight:600;color:var(--muted);font-size:13px;padding:10px 12px;border-bottom:1px solid var(--rule)}
td{padding:12px;border-bottom:1px solid var(--rule);vertical-align:top}
tr.row{cursor:pointer}
tr.row:hover td{background:var(--wash)}
tr.detail td{background:var(--bg);padding:18px 16px}
.num{text-align:right;white-space:nowrap}
pre.state{white-space:pre-wrap;font-family:"Archivo",sans-serif;font-stretch:92%;font-size:13px;color:var(--ink2);
  background:var(--surface);border:1px solid var(--rule);border-radius:10px;padding:14px;margin:8px 0 0;max-height:300px;overflow:auto}
.foot{margin-top:72px;padding-top:20px;border-top:1px solid var(--rule);color:var(--muted);font-size:14px;
  display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:18px}
.foot b{display:block;color:var(--ink);font-size:20px;font-stretch:112%}
.tip{position:fixed;pointer-events:none;background:var(--ink);color:var(--bg);font-size:13px;padding:8px 10px;
  border-radius:8px;max-width:280px;z-index:9;opacity:0;transition:opacity .12s}
@media (max-width:760px){
  .wrap{padding:28px 16px 60px}
  .flow{grid-template-columns:1fr 1fr}
  .flow>div:nth-child(3){border-left:0;padding-left:0}
  .hide-sm{display:none}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
"""

HEAD = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>[[title]]</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800&display=swap" rel="stylesheet">
<style>[[css]][[extra]]</style></head><body><div class="wrap">"""

THEME_JS = """
const tb=document.getElementById('theme');
tb.onclick=()=>{const r=document.documentElement;const dark=r.dataset.theme?r.dataset.theme==='dark':matchMedia('(prefers-color-scheme:dark)').matches;
r.dataset.theme=dark?'light':'dark';tb.textContent=dark?'Dark':'Light';};
const tip=document.querySelector('.tip');
function showTip(e,h){tip.innerHTML=h;tip.style.opacity=1;tip.style.left=Math.min(e.clientX+14,innerWidth-300)+'px';tip.style.top=(e.clientY+14)+'px';}
function hideTip(){tip.style.opacity=0;}
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const pct=v=>Math.round(v*100)+'%';
"""

A_EXTRA = r"""
.hero{margin-top:40px;display:grid;grid-template-columns:1fr 1fr;gap:0;border-radius:16px;overflow:hidden;border:1px solid var(--rule)}
.side{padding:26px 28px;background:var(--surface)}
.side.g{background:var(--googlewash)}
.side.j{background:var(--wash)}
.side .who{font-weight:700;font-size:15px;display:flex;align-items:center;gap:8px}
.side .who i{width:12px;height:12px;border-radius:3px}
.side .page{font-size:clamp(20px,2.4vw,30px);font-weight:700;font-stretch:90%;margin:14px 0 10px;word-break:break-all}
.side .fact{color:var(--ink2);font-size:15px}
.side .fact b{color:var(--ink)}
.hero-q{grid-column:1/-1;background:var(--surface);padding:16px 28px;border-bottom:1px solid var(--rule);font-size:15px;color:var(--ink2)}
.hero-q strong{color:var(--ink);font-size:20px;font-stretch:105%}
.cluster{padding:22px 24px;margin-bottom:16px}
.pair{display:grid;grid-template-columns:1fr auto 1fr;gap:14px;align-items:center;margin-bottom:16px}
.pair .pg{padding:10px 14px;border-radius:10px;font-size:15px}
.pair .pg small{display:block;font-size:12px;font-weight:600;margin-bottom:2px}
.pair .g{background:var(--googlewash)} .pair .g small{color:var(--google)}
.pair .j{background:var(--wash)} .pair .j small{color:var(--jev)}
.pair .vs{color:var(--muted);font-size:14px}
.qrow{display:grid;grid-template-columns:minmax(0,1fr) 70px 150px 150px;gap:12px;font-size:15px;padding:7px 0;border-top:1px solid var(--rule);align-items:center}
.qrow.h{color:var(--muted);font-size:13px;border-top:0}
.pos{display:flex;align-items:center;gap:8px}
.pos i{width:9px;height:9px;border-radius:50%;flex:none}
.rules{display:grid;grid-template-columns:repeat(4,1fr);gap:0;padding:0}
.rule{padding:20px 22px;border-left:1px solid var(--rule)}
.rule:first-child{border-left:0}
.rule .c{font-size:30px;font-weight:700;font-stretch:112%}
.rule .t{font-weight:600;margin-top:4px;display:flex;gap:8px;align-items:center}
.rule .t i{width:10px;height:10px;border-radius:3px}
.rule p{font-size:14px;color:var(--ink2);margin-top:6px}
.dots{position:relative;height:90px;margin:18px 0 8px;border-bottom:1px solid var(--rule)}
.dot{position:absolute;width:10px;height:10px;border-radius:50%;box-shadow:0 0 0 2px var(--surface);transform:translate(-50%,50%)}
.thr{position:absolute;top:-6px;bottom:-4px;border-left:2px solid var(--ink)}
.thr span{position:absolute;top:-22px;left:6px;font-size:13px;font-weight:600;white-space:nowrap}
.axis{display:flex;justify-content:space-between;font-size:12px;color:var(--muted)}
.probrow{display:grid;grid-template-columns:minmax(0,1fr) 140px 44px;gap:10px;align-items:center;font-size:14px;margin:6px 0}
@media (max-width:760px){
  .hero{grid-template-columns:1fr}
  .pair{grid-template-columns:1fr}
  .pair .vs{display:none}
  .qrow{grid-template-columns:minmax(0,1fr) 60px}
  .qrow>:nth-child(3),.qrow>:nth-child(4){display:none}
  .rules{grid-template-columns:1fr 1fr}
  .rule:nth-child(3){border-left:0}
}
"""

A_BODY = r"""
<div class="context"><span><b>[[domain]]</b></span><span>[[days]] of Search Console data</span>
<span>Judged by Jev ([[model]])</span><button class="themebtn" id="theme">Dark</button></div>
<h1>Jev thinks Google is showing the wrong page for [[wrongN]] of your searches</h1>
<p class="lede">We found [[n]] searches where Google shows two or three of your pages. For each one, Jev read the search and the pages and picked which page should win. In [[wrongN]] cases, Google shows a different page from the one Jev picked.</p>

<div class="hero" id="hero"></div>

<div class="flow" id="flow"></div>

<section>
<h2>Where the mix-up happens</h2>
<p class="sub">Each group below is one pair of pages that keep getting mixed up. Position is the average Google position over the period, so lower is better. Jev’s pick is about which page fits the search best, not a prediction of which one would rank higher. Sometimes Google’s page ranks better today, and the question is where your internal links and focus should point.</p>
<div id="clusters"></div>
</section>

<section>
<h2>Jev judged, the rules decided</h2>
<p class="sub">Jev only returns probabilities. These plain Python rules turn them into an outcome, and you can change any number and re-run for free.</p>
<div class="panel rules" id="rules"></div>
</section>

<section>
<h2>Jev wasn't sure how to fix it, so it didn't get a vote</h2>
<p class="sub">We also asked Jev what to do: leave it, strengthen the right page, differentiate, or merge. Each dot is one search, placed by Jev's confidence in its suggested fix. Only [[fixActed]] of [[n]] reached the [[fixThr]] bar, so every fix decision stays with a person.</p>
<div class="panel" style="padding:34px 26px 18px">
<div class="dots" id="dots"></div>
<div class="axis"><span>0% confident</span><span>50%</span><span>100%</span></div>
</div>
</section>

<section>
<h2>Every search Jev judged</h2>
<p class="sub">Click any row to see exactly what Jev was shown and how it split its answer.</p>
<div class="chips" id="chips"></div>
<div class="panel" style="overflow-x:auto"><table><thead><tr><th>Search</th><th class="num">Impressions</th>
<th class="hide-sm">Google shows</th><th class="hide-sm">Jev picks</th><th>Outcome</th></tr></thead><tbody id="tbody"></tbody></table></div>
</section>

<div class="foot">
<div><b>[[n]]</b>Jev decisions</div>
<div><b>$[[cost]]</b>Jev cost for all of them</div>
<div><b>[[tokens]]</b>tokens read</div>
<div><b>[[p50]] ms</b>median response, via OpenRouter</div>
</div>
</div><div class="tip"></div>
<script>
const D=[[data]];
""" + THEME_JS + r"""
const OUT={wrong:['Wrong page winning','var(--google)'],split:['Pages splitting signals','var(--jev)'],
  fine:['Right page already winning','var(--fine)'],unsure:['Jev not sure','var(--unsure)']};
const S=D.stats,R=D.rules;
// hero: the biggest cluster's biggest query
const hq=D.items.filter(r=>r.out==='wrong').sort((a,b)=>b.impr-a.impr)[0]||D.items.slice().sort((a,b)=>b.impr-a.impr)[0];
const hj=hq.pages[hq.owner],hg=hq.pages[0];
document.getElementById('hero').innerHTML=`
 <div class="hero-q">Someone searches <strong>“${esc(hq.q)}”</strong> &nbsp;${hq.impr} times in this period</div>
 <div class="side g"><div class="who"><i style="background:var(--google)"></i>Google shows</div>
   <div class="page">${esc(hg.p)}</div>
   <div class="fact"><b>${hg.impr}</b> of the impressions, average position <b>${hg.pos}</b></div></div>
 <div class="side j"><div class="who"><i style="background:var(--jev)"></i>Jev says this page fits better</div>
   <div class="page">${esc(hj.p)}</div>
   <div class="fact"><b>${pct(hq.ownerConf)}</b> confident, but Google shows it only <b>${hj.impr}</b> times, at position <b>${hj.pos}</b></div></div>`;
document.getElementById('flow').innerHTML=[
 [S.n,'searches where 2 or more of your pages show up','Python, from Search Console'],
 [S.n,'judged: which page should win, and is it really the same need','Jev, one call each'],
 [D.counts.wrong,'where Google shows a different page from Jev’s pick','Rules, confidence '+pct(R.owner)+' or more'],
 [S.wrongImpr.toLocaleString(),'impressions going to the wrong page','Python, adding it up']]
 .map(([n,l,w])=>`<div><div class="n">${n}</div><div class="l">${l}</div><div class="who">${w}</div></div>`).join('');
// clusters
document.getElementById('clusters').innerHTML=D.clusters.slice(0,6).map(c=>`
 <div class="panel cluster">
  <div class="pair"><div class="pg g"><small>Google shows</small><span class="path">${esc(c.google)}</span></div>
   <div class="vs">instead of</div>
   <div class="pg j"><small>Jev’s pick</small><span class="path">${esc(c.jev)}</span></div></div>
  <div class="qrow h"><span>${c.queries.length} search${c.queries.length>1?'es':''}, ${c.impr} impressions</span><span class="num">Impr.</span><span>Google’s page</span><span>Jev’s page</span></div>
  ${c.queries.sort((a,b)=>b.impr-a.impr).map(q=>`<div class="qrow"><span>${esc(q.q)}</span><span class="num">${q.impr}</span>
   <span class="pos"><i style="background:var(--google)"></i>position ${q.gpos}</span>
   <span class="pos"><i style="background:var(--jev)"></i>position ${q.jpos}</span></div>`).join('')}
 </div>`).join('')+(D.clusters.length>6?`<p class="muted">Plus ${D.clusters.length-6} smaller pairs in the full table below.</p>`:'');
// rules
const RULES=[['wrong',`Jev is ${pct(R.owner)}+ sure and picked a different page from Google’s.`],
 ['split',`Google’s page is right, but Jev scores the rivals as the same need (${pct(R.split)}+).`],
 ['fine','Google’s page is right and the other pages serve a different need.'],
 ['unsure',`Jev is under ${pct(R.owner)} sure. We don’t guess, it goes to review.`]];
document.getElementById('rules').innerHTML=RULES.map(([k,t])=>`<div class="rule"><div class="c">${D.counts[k]||0}</div>
 <div class="t"><i style="background:${OUT[k][1]}"></i>${OUT[k][0]}</div><p>${t}</p></div>`).join('');
// dots
const dots=document.getElementById('dots');const lanes={};
const FIXC={leave:'var(--fine)',strengthen:'var(--jev)',differentiate:'var(--unsure)',merge:'var(--google)'};
dots.innerHTML=`<div class="thr" style="left:${R.fix*100}%"><span>act on it at ${pct(R.fix)}</span></div>`+
 D.items.map(r=>{const b=Math.round(r.fixConf*50);lanes[b]=(lanes[b]||0)+1;
  return `<div class="dot" data-q="${esc(r.q)}" data-f="${r.fix}" data-c="${r.fixConf}" style="left:${r.fixConf*100}%;bottom:${(lanes[b]-1)*13}px;background:${FIXC[r.fix]}"></div>`}).join('');
dots.nextElementSibling.insertAdjacentHTML('afterend',`<div class="chips" style="margin:18px 0 0">${Object.entries(FIXC).map(([k,c])=>`<span class="tag"><i style="background:${c}"></i>${k}</span>`).join('')}</div>`);
dots.querySelectorAll('.dot').forEach(d=>{d.onmousemove=e=>showTip(e,`<b>${d.dataset.q}</b><br>Suggested: ${d.dataset.f}, ${pct(+d.dataset.c)} sure`);d.onmouseleave=hideTip;});
// table
let filter='all';
const chips=document.getElementById('chips');
function drawChips(){chips.innerHTML=[['all','All',null]].concat(Object.entries(OUT).map(([k,v])=>[k,v[0],v[1]]))
 .map(([k,l,c])=>`<button class="chip" aria-pressed="${filter===k}" data-k="${k}">${c?`<i style="background:${c}"></i>`:''}${l} <span class="muted">${k==='all'?D.items.length:(D.counts[k]||0)}</span></button>`).join('');
 chips.querySelectorAll('button').forEach(b=>b.onclick=()=>{filter=b.dataset.k;drawChips();drawTable();});}
function drawTable(){const tb=document.getElementById('tbody');
 tb.innerHTML=D.items.filter(r=>filter==='all'||r.out===filter).map((r,i)=>`
 <tr class="row" tabindex="0" data-i="${D.items.indexOf(r)}"><td>${esc(r.q)}</td><td class="num">${r.impr}</td>
 <td class="hide-sm"><span class="path">${esc(r.pages[0].p)}</span></td>
 <td class="hide-sm"><span class="path">${esc(r.pages[r.owner].p)}</span> <span class="muted">${pct(r.ownerConf)}</span></td>
 <td><span class="tag"><i style="background:${OUT[r.out][1]}"></i>${OUT[r.out][0]}</span></td></tr>`).join('');
 tb.querySelectorAll('tr.row').forEach(tr=>{const open=()=>{const nx=tr.nextElementSibling;
  if(nx&&nx.classList.contains('detail')){nx.remove();return;}
  const r=D.items[tr.dataset.i];
  tr.insertAdjacentHTML('afterend',`<tr class="detail"><td colspan="5">
   <h3 style="font-size:16px;margin-bottom:6px">Which page should win</h3>
   ${r.pages.map((p,k)=>`<div class="probrow"><span class="path">${esc(p.p)} <span class="muted" style="font-weight:400">${p.impr} impr., pos. ${p.pos}</span></span>
    <div class="track"><div class="bar" style="width:${p.prob*100}%;background:${k===r.owner?'var(--jev)':'var(--unsure)'}"></div></div><span class="num">${pct(p.prob)}</span></div>`).join('')}
   <p style="margin-top:12px;font-size:14px;color:var(--ink2)">Same need: <b>${pct(r.same)}</b>. Searcher wants: <b>${r.intent}</b>. Suggested fix: <b>${r.fix}</b> at ${pct(r.fixConf)}. Answered in ${r.ms} ms.</p>
   <details style="margin-top:10px"><summary style="cursor:pointer;font-size:14px;font-weight:600">What Jev was shown</summary><pre class="state">${esc(r.state)}</pre></details>
   </td></tr>`);};
  tr.onclick=open;tr.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();open();}};});}
drawChips();drawTable();
</script></body></html>"""



def fill(tpl, **kw):
    for k, v in kw.items():
        tpl = tpl.replace("[[" + k + "]]", str(v))
    return tpl


def render(a, domain):
    s = a["stats"]
    return fill(HEAD, title="Cannibalization Check", css=CSS, extra=A_EXTRA) + fill(
        A_BODY, domain=domain, model=s["model"], n=s["n"], wrongN=a["counts"].get("wrong", 0),
        fixActed=s["fixActed"], fixThr=f"{int(a['rules']['fix']*100)}%", cost=f"{s['cost']:.4f}",
        tokens=f"{s['tokens']:,}", p50=int(s["p50"]), days=a["days"],
        data=json.dumps(a, ensure_ascii=False))
