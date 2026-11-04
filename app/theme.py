"""Styling + small HTML helpers for the dashboard. All HTML is single-line so Streamlit's markdown does not treat it as code."""
import base64, functools, html
from pathlib import Path

e = html.escape
CLS = {"Low": "low", "Medium": "med", "High": "high", "n/a": "na"}
CSS = """<style>
.hero.plain{background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 200' preserveAspectRatio='none'><path d='M0 200 L0 140 L90 70 L170 120 L270 30 L370 110 L450 60 L560 130 L650 50 L800 140 L800 200Z' fill='%23062a24'/><path d='M0 200 L0 170 L120 120 L230 160 L340 100 L480 165 L600 110 L720 160 L800 130 L800 200Z' fill='%23041c18'/></svg>"),linear-gradient(180deg,#0B3A33,#04201b);background-size:100% 55%,100% 100%;background-position:bottom,center}
[class*=st-key-panel_]{background:linear-gradient(160deg,#092B29,#072422)!important;border:1px solid #14473d!important;border-radius:14px;box-shadow:0 6px 24px rgba(0,0,0,.25)}
.ph{margin:0 0 6px!important;color:#D9B85F!important;font-family:'Cormorant Garamond',serif!important;font-size:1.3rem!important}
.kpi b.long{font-size:1.1rem;line-height:1.7rem}
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;700&family=Inter:wght@400;600&display=swap');
:root{--card:#092B29;--em:#20C979;--mint:#9ACD9B;--gold:#D9B85F;--txt:#E8F3EC;--mut:#8FB5A3}
html,body,[class*="css"]{font-family:Inter,sans-serif}
.stApp{background:radial-gradient(1200px 600px at 70% -10%,#0B3A33 0%,#031411 60%)}
[data-testid=stSidebar]{background:#021713;border-right:1px solid #0f3b33}
h1,h2,h3{font-family:'Cormorant Garamond',serif!important;color:var(--txt)}
.brand{font-family:'Cormorant Garamond',serif;font-size:1.5rem;letter-spacing:2px;color:var(--txt);line-height:1.1;margin:4px 0 14px}
.brand small{display:block;color:var(--gold);font-size:.7rem;letter-spacing:3px}
.quote{font-family:'Cormorant Garamond',serif;font-style:italic;color:var(--mint);border-top:1px solid #14473d;padding-top:10px;margin-top:18px}
.hero{border-radius:16px;padding:34px 30px 70px;margin-bottom:16px;border:1px solid #14473d;background-color:#04201b;background-size:100% 100%;background-repeat:no-repeat}
.hero h1{font-size:clamp(2rem,5vw,3.4rem);letter-spacing:3px;margin:0;line-height:1.05}
.hero p{color:var(--mint);margin:8px 0 0;font-size:1.05rem}
.hero .tag{float:right;border:1px solid #1f6b58;border-radius:99px;padding:3px 12px;font-size:.75rem;color:var(--em);background:rgba(3,20,17,.6)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:12px;margin-bottom:14px}
.kpi{background:linear-gradient(160deg,#0C3330,#072422);border:1px solid #14473d;border-radius:14px;padding:14px 16px}
.kpi span{display:block;color:var(--mut);font-size:.78rem}
.kpi b{display:block;font-size:1.7rem;color:var(--txt);margin:2px 0}
.kpi small{color:var(--mut);font-size:.72rem}
.card{background:linear-gradient(160deg,var(--card),#072422);border:1px solid #14473d;border-radius:14px;padding:16px 18px;margin-bottom:14px;box-shadow:0 6px 24px rgba(0,0,0,.25)}
.card h4{margin:0 0 8px;color:var(--gold);font-family:'Cormorant Garamond',serif;font-size:1.3rem}
.card p{color:var(--mut);margin:4px 0;font-size:.9rem}
.sci{font-family:'Cormorant Garamond',serif;font-style:italic;font-size:1.5rem;color:var(--txt)}
.badge{display:inline-block;padding:2px 10px;border-radius:99px;font-size:.75rem;border:1px solid;margin-left:6px}
.low{color:#48D98D}.med{color:#E9C66C}.high{color:#E4694F}.na{color:#8FB5A3}
.bar{display:flex;align-items:center;gap:10px;margin:8px 0;font-size:.85rem;color:var(--txt)}
.bar>span{width:46%}.bar>div{flex:1;height:8px;background:#0a2f2a;border-radius:6px}
.bar i{display:block;height:100%;border-radius:6px}.bar>em{width:52px;text-align:right;font-style:normal}
.avatar{width:96px;height:96px;border-radius:50%;border:2px solid var(--em);display:flex;align-items:center;justify-content:center;font-family:'Cormorant Garamond',serif;font-size:2rem;color:var(--em);background:#06231D;object-fit:cover}
.row{display:flex;gap:18px;align-items:center;flex-wrap:wrap}.row>div:last-child{flex:1;min-width:220px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}
.rank{display:flex;justify-content:space-between;border-bottom:1px solid #14473d;padding:6px 0;color:var(--txt);font-size:.9rem}
.rank i{color:var(--mut)}.rank i.sp{color:var(--txt)}.rank small{color:var(--mut);font-size:.75rem}.auth{font-style:normal;font-size:1rem;color:var(--mut)}
.empty{border:1px dashed #1f6b58;border-radius:12px;padding:18px;color:var(--mut);text-align:center}
</style>"""


@functools.lru_cache(maxsize=32)  # photos are inlined as base64; encode once per process
def img_data(path):
    p = Path(path)
    if not p.exists():
        return None
    return f"data:image/{'png' if p.suffix == '.png' else 'jpeg'};base64," + base64.b64encode(p.read_bytes()).decode()


def hero(title, sub, tag, bg=None):
    style = f' style="background-image:linear-gradient(180deg,rgba(3,20,17,.25),rgba(3,20,17,.88)),url({bg});background-size:cover;background-position:center 18%"' if bg else ""
    return f'<div class="hero{"" if bg else " plain"}"{style}><span class="tag">{e(tag)}</span><h1>{e(title)}</h1><p>{e(sub)}</p></div>'


def card(title, body):
    return f'<div class="card"><h4>{e(title)}</h4>{body}</div>'


def kpis(items):
    return '<div class="kpis">' + "".join(
        f'<div class="kpi"><span>{e(l)}</span><b{" class=long" if len(str(v)) > 12 else ""}>{e(str(v))}</b><small>{e(n)}</small></div>' for l, v, n in items) + "</div>"


def bar(label, pct, text, color="var(--em)"):
    pct = 0 if pct != pct else max(0, min(100, pct))  # NaN-safe
    return f'<div class="bar"><span>{e(label)}</span><div><i style="width:{pct:.0f}%;background:{color}"></i></div><em>{e(text)}</em></div>'


def badge(cls):
    return f'<span class="badge {CLS[cls]}">{"No data" if cls == "n/a" else cls + " risk"}</span>'


def style(fig, h=320):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#E8F3EC"))
    return fig
