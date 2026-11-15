CSS = """
<style>
:root { color-scheme: light; }
.stApp { background: #f7f3e8; color: #223127; font-size: 16px; }
.block-container { padding-top: .5rem; padding-bottom: 1.5rem; max-width: 1420px; }
[data-testid="stHeader"] { background: transparent; height: 2.4rem; }

/* Tarjetas y contenedores */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #fffdf7;
    border: 1px solid #e2d7be;
    border-radius: 16px;
    box-shadow: 0 3px 12px rgba(62, 52, 33, .06);
    padding: 8px;
}
[data-testid="stForm"] {
    background: #fffdf7;
    border: 1px solid #e2d7be;
    border-radius: 18px;
    padding: 1.25rem;
    box-shadow: 0 4px 14px rgba(62, 52, 33, .05);
}
[data-testid="stAlert"] { border-radius: 14px; border: 1px solid #e0d3b6; }
div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] { color: #2b3a2e; font-size: .98rem; }
div[data-testid="stMetric"] {
    background: #fffdf7;
    border: 1px solid #e0d3b6;
    border-radius: 16px;
    padding: 14px 16px;
    box-shadow: 0 2px 8px rgba(62, 52, 33, .04);
}
details[data-testid="stExpander"] {
    background: #fffdf7;
    border: 1px solid #dfd3b8;
    border-radius: 14px;
}
div[data-baseweb="select"] > div {
    background: #fffdf7;
    border-color: #c8b894;
    border-radius: 12px;
    min-height: 44px;
}

/* Botones amigables y grandes */
button[kind="secondary"] {
    background: #efe7d4;
    border: 1px solid #d3c3a0;
    color: #2f3e31;
    border-radius: 12px;
    font-weight: 600;
    min-height: 42px;
}
button[kind="secondary"]:hover { background: #e5dac0; border-color: #bfa97e; }
button[kind="primary"] {
    background: #2e6f40;
    border: 1px solid #2e6f40;
    color: #ffffff;
    border-radius: 12px;
    font-weight: 700;
    min-height: 42px;
}
button[kind="primary"]:hover { background: #245832; border-color: #245832; }
button:focus-visible { outline: 3px solid #5c946e !important; }

/* Header y marca */
.fs-brand { font-size: 1.32rem; font-weight: 800; line-height: 1.1; white-space: nowrap; color: #213827; letter-spacing: -.01em; }
.fs-tagline { font-size: .9rem; color: #566858; margin-top: 2px; }

/* Barra de flujo paso a paso */
.fs-flow-wrap {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: .5rem;
    background: #efe8d5;
    border: 1px solid #dfd2b5;
    border-radius: 14px;
    padding: .5rem .85rem;
    margin: .35rem 0 .85rem 0;
    flex-wrap: wrap;
}
.fs-step {
    display: inline-flex;
    align-items: center;
    gap: .45rem;
    padding: .32rem .75rem;
    border-radius: 999px;
    font-size: .86rem;
    font-weight: 650;
    color: #556657;
    background: transparent;
}
.fs-step-active {
    background: #2e6f40;
    color: #ffffff;
    box-shadow: 0 2px 6px rgba(46, 111, 64, .25);
}
.fs-step-done {
    background: #dcead9;
    color: #255232;
}
.fs-step-arrow { color: #9aa396; font-weight: 700; }

/* Hero Banner agrícola con paisaje ilustrado SVG */
.fs-hero-banner {
    background-color: #e7efe0;
    background-image:
        linear-gradient(105deg, rgba(255, 253, 247, 0.94) 0%, rgba(255, 253, 247, 0.86) 58%, rgba(235, 244, 228, 0.65) 100%),
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 260'%3E%3Cdefs%3E%3ClinearGradient id='sky' x1='0' y1='0' x2='0' y2='1'%3E%3Cstop offset='0%25' stop-color='%23f6edd6'/%3E%3Cstop offset='100%25' stop-color='%23e3eed9'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='1200' height='260' fill='url(%23sky)'/%3E%3Ccircle cx='1040' cy='62' r='34' fill='%23f3c86b' opacity='0.65'/%3E%3Cpath d='M0 165 Q 260 115, 560 160 T 1200 140 L 1200 260 L 0 260 Z' fill='%23b8d4a3' opacity='0.6'/%3E%3Cpath d='M0 195 Q 340 150, 720 190 T 1200 175 L 1200 260 L 0 260 Z' fill='%238ab573' opacity='0.65'/%3E%3Cpath d='M0 225 Q 420 195, 860 220 T 1200 210 L 1200 260 L 0 260 Z' fill='%235d8f4c' opacity='0.55'/%3E%3C/svg%3E");
    background-size: cover;
    background-position: center;
    border: 1px solid #cde0c1;
    border-radius: 18px;
    padding: 1.15rem 1.4rem;
    margin-bottom: .9rem;
    box-shadow: 0 4px 14px rgba(46, 85, 52, .07);
}
.fs-verdict-badge {
    display: inline-flex;
    align-items: center;
    gap: .45rem;
    padding: .45rem .95rem;
    border-radius: 999px;
    font-weight: 750;
    font-size: .95rem;
    margin-top: .45rem;
}
.fs-verdict-green { background: #d6ebd4; color: #1f542d; border: 1px solid #96c493; }
.fs-verdict-yellow { background: #fdf0c2; color: #6e500e; border: 1px solid #dfc068; }
.fs-verdict-red { background: #fadbd5; color: #82271e; border: 1px solid #dc8f86; }

/* Tarjetas de alertas en lenguaje simple */
.fs-card-title { font-weight: 750; font-size: 1.08rem; color: #2c4430; }
.fs-alert-panel { border-radius: 14px; padding: 14px 16px; margin: 8px 0; color: #223127; font-size: .96rem; line-height: 1.45; }
.fs-alert-red { background: #fae0da; border-left: 7px solid #c84b31; }
.fs-alert-yellow { background: #fbf0cc; border-left: 7px solid #cfa028; }
.fs-alert-green { background: #e1eedc; border-left: 7px solid #49824b; }
.fs-alert-gray { background: #ebe8de; border-left: 7px solid #8a887a; }

/* Tanque de agua */
.fs-water-tank {
    height: 180px;
    width: 72px;
    border: 4px solid #5f7872;
    border-radius: 18px 18px 24px 24px;
    position: relative;
    overflow: hidden;
    background: #f5efe0;
    margin: 6px auto;
}
.fs-water-fill {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(0deg, #3b8ea8, #8fd0d2);
    transition: height .4s ease;
}

/* Cultivos y visuales */
.fs-crop-img { object-fit: cover; border-radius: 14px; border: 1px solid #dfd3b8; background: #f3ecda; vertical-align: middle; }
.fs-crop-fallback { display: inline-flex; align-items: center; justify-content: center; border-radius: 14px; background: #f4e8c4; border: 1px dashed #c8b273; vertical-align: middle; flex: 0 0 auto; }
.fs-crop-row { display: flex; align-items: center; gap: .9rem; }
.fs-crop-title { font-weight: 800; font-size: 1.15rem; color: #243927; }
.fs-crop-pill { display: inline-flex; align-items: center; gap: .35rem; margin: .2rem .75rem .2rem 0; font-size: .88rem; color: #485b4c; font-weight: 600; }
.fs-crop-preview-card {
    display: flex;
    align-items: center;
    gap: .9rem;
    background: #f2ecdc;
    border: 1px solid #d9cbb0;
    border-radius: 14px;
    padding: .75rem 1rem;
    margin: .4rem 0 .8rem 0;
}

/* Badges de fuente de datos (ocultos en modo simple, visibles en modo técnico) */
.fs-kind { display: inline-block; padding: .08rem .55rem; border-radius: 999px; font-size: .74rem; font-weight: 700; border: 1px solid transparent; margin: .1rem .2rem .1rem 0; white-space: nowrap; }
.fs-kind-observation { background: #dfeaf5; color: #2d5577; border-color: #a9c4dd; }
.fs-kind-estimate { background: #e1eeee; color: #36625f; border-color: #a8cac7; }
.fs-kind-forecast { background: #ece3f3; color: #5b3f77; border-color: #c5b0d8; }
.fs-kind-model { background: #f3e8d2; color: #6b4d1f; border-color: #d8c294; }
.fs-kind-user { background: #efefd9; color: #5a5d2a; border-color: #c9cc93; border-style: dashed; }

/* Notificación flotante y tarjetas de recomendación/clima */
.fs-toast { position: fixed; z-index: 99999; top: 4.4rem; right: 1.25rem; padding: .85rem 1.25rem; border-radius: 14px; background: #d6ebd4; color: #1f4726; border: 1px solid #96c493; box-shadow: 0 8px 24px rgba(45, 65, 40, .2); font-weight: 700; animation: fs-toast-out 5s ease forwards; pointer-events: none; }
@keyframes fs-toast-out { 0%, 82% { opacity: 1; visibility: visible; transform: translateY(0); } 100% { opacity: 0; visibility: hidden; transform: translateY(-8px); } }
.fs-compat { display: inline-block; padding: .55rem .8rem; border-radius: 999px; text-align: center; font-weight: 750; width: 100%; box-sizing: border-box; }
.fs-compat-green { background: #dcebd7; color: #2f6735; border: 1px solid #8bb17e; }
.fs-compat-yellow { background: #fff0bf; color: #775b13; border: 1px solid #d8b85f; }
.fs-compat-red { background: #f6ddd8; color: #8b342b; border: 1px solid #d48c81; }
.fs-rec-fact, .fs-rec-requirements, .fs-rec-missing { padding: .75rem .9rem; border-radius: 12px; margin: .45rem 0; }
.fs-rec-fact { background: #edf2e5; color: #394d35; }
.fs-rec-requirements { background: #e5f0ef; color: #355653; }
.fs-rec-missing { background: #fff0c7; color: #6e5418; }
.fs-rec-good, .fs-rec-limits { min-height: 100%; box-sizing: border-box; padding: .9rem; border-radius: 12px; line-height: 1.55; }
.fs-rec-good { background: #e6efdf; border: 1px solid #c4d7b8; color: #365032; }
.fs-rec-limits { background: #f7e8df; border: 1px solid #e6c9b8; color: #5c4236; }
.fs-weather-card { height: 100%; min-height: 185px; padding: .85rem; border-radius: 14px; border: 1px solid #d7cfb7; text-align: center; color: #2f3e32; box-sizing: border-box; }
.fs-weather-green { background: #e3eedb; border-color: #aec598; }
.fs-weather-yellow { background: #fff0c4; border-color: #dfc370; }
.fs-weather-red { background: #f7ddd7; border-color: #dda098; }
.fs-weather-day { font-size: .84rem; color: #5f695c; }
.fs-weather-icon { font-size: 2rem; margin: .25rem 0; }
.fs-weather-temp { font-weight: 750; margin: .25rem 0; }
.fs-weather-status { font-size: .78rem; font-weight: 750; text-transform: uppercase; letter-spacing: .04em; margin-top: .35rem; }
.fs-map-caption { font-size: .88rem; color: #4d5f52; margin-top: .4rem; }
.fs-small { font-size: .84rem; color: #566454; }
.st-key-footer_reports button, .st-key-footer_sources button { font-size: .84rem; padding: .3rem .75rem; min-height: 2.2rem; }
</style>
"""
ICON = {"green": "🟢", "yellow": "🟡", "red": "🔴", "gray": "⚪"}