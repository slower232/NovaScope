"""Reporte PDF de diagnóstico (ReportLab)."""
import io
from datetime import datetime
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ui.translations import t

COL = {"green": "#c8e6c9", "yellow": "#fff3b0", "red": "#ffcdd2", "gray": "#cfd8dc"}


def diagnosis_pdf(lang: str, farm: dict, crop_name: str, risks: list, overall: dict, sources: list[str],
                  notes: list[str]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
                            title="Field Shift")
    ss = getSampleStyleSheet()
    P = lambda s, st="BodyText": Paragraph(escape(s), ss[st])
    el = [P("Field Shift — " + t("rep.title", lang), "Title"),
          P(f"{farm['name']} · {crop_name} · {farm['lat']:.4f}, {farm['lon']:.4f}"),
          P(datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")), Spacer(1, 10),
          P(f"{t('overall', lang)}: {t('level.' + overall['level'], lang)}", "Heading2"),
          P(t("gray.note", lang, n=overall["n_gray"]) if overall["n_gray"] else ""), Spacer(1, 6)]
    rows = [[t("alert.what", lang), "", t("alert.src", lang)]]
    styles = [("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e7d32")),
              ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("VALIGN", (0, 0), (-1, -1), "TOP")]
    for i, r in enumerate(risks, start=1):
        what = (t(f"risk.{r.key}.what", lang, **r.params) if r.level in ("yellow", "red")
                else t(f"alert.{r.level}.what", lang))
        rows.append([Paragraph(escape(t(f"risk.{r.key}.name", lang)), ss["BodyText"]),
                     Paragraph(escape(t("level." + r.level, lang) + " — " + what), ss["BodyText"]),
                     Paragraph(escape(r.source), ss["BodyText"])])
        styles.append(("BACKGROUND", (1, i), (1, i), colors.HexColor(COL[r.level])))
    tb = Table(rows, colWidths=[4 * cm, 9 * cm, 4 * cm]); tb.setStyle(TableStyle(styles))
    el += [tb, Spacer(1, 10)]
    for r in risks:
        if r.level in ("yellow", "red"):
            el += [P(t(f"risk.{r.key}.name", lang), "Heading3"), P(t(f"risk.{r.key}.why", lang)),
                   P(t("alert.do", lang) + ": " + t(f"risk.{r.key}.{r.level}", lang))]
    el += [Spacer(1, 8), P(t("forecast.warn", lang), "Italic")]
    el += [P(t("source", lang) + ": " + "; ".join(sources))] + [P(n) for n in notes] + [P(t("limits", lang), "Italic")]
    doc.build(el)
    return buf.getvalue()
