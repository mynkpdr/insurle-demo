#!/usr/bin/env python3
"""
InsurLE — Claim PDF Generator
Produces one PDF per claim, each containing:
  Page 1 — Claim Cover         (status, summary, key facts grid)
  Page 2 — Formal Claim Form   (§1 claimant · §2 incident · §3 facts table · stamp)

Usage:
    python3 make_claim.py               # reads insurle_data.json in CWD
    python3 make_claim.py path/to/data.json
"""

import json
import sys
import textwrap
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors

# ── Page geometry ──────────────────────────────────────────────────────────────
W, H = letter          # 612 × 792 pts
LM   = 0.55 * inch    # left margin
TW   = W - 1.10 * inch  # text width

# ── Shared palette ─────────────────────────────────────────────────────────────
CREAM  = colors.HexColor('#F7F3EC')
CREAM2 = colors.HexColor('#EDE7D9')
INK    = colors.HexColor('#1A1510')
INK2   = colors.HexColor('#2A2520')
GREY   = colors.HexColor('#6A6050')
GREY2  = colors.HexColor('#9A8F7A')
RULE   = colors.HexColor('#C8BFA8')
WHITE  = colors.white
PASS_C = colors.HexColor('#1A5A30')
FAIL_C = colors.HexColor('#8B1A1A')
PASS_L = colors.HexColor('#EBF5F0')
FAIL_L = colors.HexColor('#F8EDED')
PASS_M = colors.HexColor('#2E7D52')
FAIL_M = colors.HexColor('#B03030')

# ── Per-contract colour themes ─────────────────────────────────────────────────
THEMES = {
    'contract_auto':     {'P': colors.HexColor('#1A3A5C'), 'A': colors.HexColor('#E8B84B'), 'L': colors.HexColor('#EBF1F8')},
    'contract_health':   {'P': colors.HexColor('#1A4A3A'), 'A': colors.HexColor('#4ECB8D'), 'L': colors.HexColor('#EBF5F1')},
    'contract_travel':   {'P': colors.HexColor('#2A1A5C'), 'A': colors.HexColor('#A78BFA'), 'L': colors.HexColor('#F0EBF8')},
    'contract_accident': {'P': colors.HexColor('#4A1A1A'), 'A': colors.HexColor('#F87171'), 'L': colors.HexColor('#F8EBEB')},
}

# ── Contract metadata lookup ──────────────────────────────────────────────────
CONTRACT_META = {
    'contract_auto':     {'insurer': 'AutoGuard Insurance Co.',    'policy_number': 'AG-VH-2024-001', 'type': 'Vehicle Insurance',  'name': 'AutoGuard Vehicle Insurance'},
    'contract_health':   {'insurer': 'VitalCare Health Group',     'policy_number': 'VC-HLT-2024-087', 'type': 'Health Insurance',   'name': 'VitalCare Health Insurance'},
    'contract_travel':   {'insurer': 'JetSafe Global Underwriters', 'policy_number': 'JS-TRV-2024-445', 'type': 'Travel Insurance',  'name': 'JetSafe Travel Insurance'},
    'contract_accident': {'insurer': 'ShieldPlus Casualty Ltd.',   'policy_number': 'SP-ACC-2024-209', 'type': 'Accident Insurance', 'name': 'ShieldPlus Personal Accident'},
}

# ── Helpers ────────────────────────────────────────────────────────────────────
def wrap(text, chars):
    return textwrap.wrap(str(text), max(18, int(chars))) or ['']


# ── Shared header / footer ─────────────────────────────────────────────────────
def page_header(c, contract, claim, t, pg):
    P, A = t['P'], t['A']
    c.setFillColor(P)
    c.rect(0, H - 0.72 * inch, W, 0.72 * inch, fill=1, stroke=0)
    c.setFillColor(A)
    c.rect(0, H - 0.78 * inch, W, 0.06 * inch, fill=1, stroke=0)
    c.setFillColor(A)
    c.rect(0, 0, 4, H, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 11)
    c.setFillColor(WHITE)
    c.drawString(LM, H - 0.44 * inch, contract['insurer'])
    c.setFont('Courier-Bold', 8)
    c.setFillColor(A)
    c.drawRightString(W - 0.5 * inch, H - 0.44 * inch, claim['id'].upper())
    c.setFont('Helvetica', 7)
    c.setFillColor(colors.Color(1, 1, 1, alpha=0.55))
    c.drawString(LM, H - 0.62 * inch, claim['claimant'])
    c.drawRightString(W - 0.5 * inch, H - 0.62 * inch,
                      contract['type'].upper() + '  ·  CLAIM DOCUMENT')


def page_footer(c, contract, claim, t, pg, total):
    c.setStrokeColor(RULE)
    c.setLineWidth(0.5)
    c.line(LM, 0.52 * inch, W - LM, 0.52 * inch)
    c.setFont('Helvetica', 7)
    c.setFillColor(GREY)
    c.drawString(LM, 0.35 * inch, '%s  ·  Claim %s' % (contract['name'], claim['id'].upper()))
    c.drawRightString(W - LM, 0.35 * inch, 'Page %d of %d' % (pg, total))
    c.setFont('Helvetica', 6)
    c.setFillColor(GREY2)
    c.drawCentredString(W / 2, 0.20 * inch,
                        'CONFIDENTIAL — FOR CLAIMS PROCESSING USE ONLY')


# ── Page 1: Claim Cover ────────────────────────────────────────────────────────
def draw_cover(c, claim, contract, t):
    P, A, L = t['P'], t['A'], t['L']
    is_v    = claim['expected'] == 'VALID'
    STAMP_C = PASS_C if is_v else FAIL_C
    STAMP_L = PASS_L if is_v else FAIL_L
    RESULT_C = PASS_M if is_v else FAIL_M

    y = H - 1.05 * inch

    # Title
    c.setFont('Helvetica-Bold', 22)
    c.setFillColor(P)
    c.drawCentredString(W / 2, y, 'INSURANCE CLAIM REPORT')
    y -= 0.26 * inch
    c.setStrokeColor(A)
    c.setLineWidth(2)
    c.line(W / 2 - 2.0 * inch, y, W / 2 + 2.0 * inch, y)
    y -= 0.18 * inch
    c.setFont('Helvetica', 9.5)
    c.setFillColor(GREY)
    c.drawCentredString(W / 2, y,
                        '%s  ·  %s  ·  %s' % (contract['type'], contract['insurer'], claim['date']))
    y -= 0.40 * inch

    # 6-cell meta grid
    cells = [
        ('CLAIMANT',        claim['claimant']),
        ('CLAIM REFERENCE', claim['id'].upper()),
        ('DATE OF CLAIM',   claim['date']),
        ('INCIDENT DATE',   claim['incident_date']),
        ('AMOUNT CLAIMED',  claim['amount']),
        ('POLICY NUMBER',   contract['policy_number']),
    ]
    bw = TW / 3
    bh = 0.65 * inch
    for i, (lbl, val) in enumerate(cells):
        col = i % 3
        row = i // 3
        bx = LM + col * bw
        by = y - row * (bh + 0.05 * inch)
        c.setFillColor(L)
        c.roundRect(bx, by - bh, bw - 0.04 * inch, bh, 4, fill=1, stroke=0)
        bar_c = P if row == 0 else A
        c.setFillColor(bar_c)
        c.rect(bx, by - 0.14 * inch, bw - 0.04 * inch, 0.14 * inch, fill=1, stroke=0)
        c.setFont('Helvetica-Bold', 6)
        c.setFillColor(WHITE)
        c.drawString(bx + 7, by - 0.095 * inch, lbl)
        is_amount = lbl == 'AMOUNT CLAIMED'
        c.setFont('Helvetica-Bold', 11 if is_amount else 9)
        c.setFillColor(P if is_amount else INK)
        c.drawString(bx + 7, by - bh + 0.15 * inch, str(val)[:26])
        c.setStrokeColor(RULE)
        c.setLineWidth(0.3)
        c.roundRect(bx, by - bh, bw - 0.04 * inch, bh, 4, fill=0, stroke=1)
    y -= 2 * (bh + 0.05 * inch) + 0.25 * inch

    # Verdict banner
    bh2 = 0.78 * inch
    c.setFillColor(STAMP_L)
    c.roundRect(LM, y - bh2, TW, bh2, 6, fill=1, stroke=0)
    c.setStrokeColor(STAMP_C)
    c.setLineWidth(2)
    c.roundRect(LM, y - bh2, TW, bh2, 6, fill=0, stroke=1)
    c.setFillColor(STAMP_C)
    c.rect(LM, y - bh2, 6, bh2, fill=1, stroke=0)
    verdict_label = 'CLAIM APPROVED — VALID' if is_v else 'CLAIM REJECTED — INVALID'
    c.setFont('Helvetica-Bold', 16)
    c.setFillColor(RESULT_C)
    c.drawCentredString(W / 2, y - 0.30 * inch, verdict_label)
    c.setFont('Helvetica', 8.5)
    c.setFillColor(INK2)
    sub_text = ('Claim meets all policy requirements.' if is_v else
                'One or more policy requirements were not satisfied.')
    c.drawCentredString(W / 2, y - 0.52 * inch, sub_text)
    y -= bh2 + 0.22 * inch

    # Incident description box
    chars = (TW - 0.28 * inch) / (8.5 * 0.52)
    dlines = wrap(claim.get('description', ''), chars)
    dh = len(dlines) * 13 + 0.22 * inch
    c.setFillColor(CREAM2)
    c.roundRect(LM, y - dh, TW, dh, 5, fill=1, stroke=0)
    c.setStrokeColor(A)
    c.setLineWidth(3)
    c.line(LM, y - dh, LM, y)
    c.setStrokeColor(RULE)
    c.setLineWidth(0.3)
    c.roundRect(LM, y - dh, TW, dh, 5, fill=0, stroke=1)
    c.setFont('Helvetica-Bold', 7)
    c.setFillColor(P)
    c.drawString(LM + 10, y - 0.12 * inch, 'INCIDENT SUMMARY')
    ty = y - 0.26 * inch
    for dl in dlines:
        c.setFont('Times-Italic', 8.5)
        c.setFillColor(INK2)
        c.drawString(LM + 10, ty, dl)
        ty -= 13
    y -= dh + 0.22 * inch

    # Circular stamp
    sc_x, sc_y = W - 1.15 * inch, H - 1.62 * inch
    c.saveState()
    c.translate(sc_x, sc_y)
    c.rotate(-18)
    c.setStrokeColor(STAMP_C)
    c.setLineWidth(2.5)
    c.circle(0, 0, 0.62 * inch, stroke=1, fill=0)
    c.setLineWidth(1)
    c.circle(0, 0, 0.53 * inch, stroke=1, fill=0)
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(STAMP_C)
    c.drawCentredString(0, 0.13 * inch, 'APPROVED' if is_v else 'REJECTED')
    c.setFont('Helvetica', 7)
    c.drawCentredString(0, -0.04 * inch, 'FOR PROCESSING' if is_v else 'REVIEW REQUIRED')
    c.setFont('Courier-Bold', 6)
    c.drawCentredString(0, -0.24 * inch, 'INSURLE ENGINE')
    c.restoreState()

    # Signature block
    if y > 1.55 * inch:
        sy = max(y, 1.55 * inch)
        c.setFillColor(CREAM2)
        c.roundRect(LM, sy - 0.68 * inch, TW, 0.70 * inch, 4, fill=1, stroke=0)
        c.setStrokeColor(RULE)
        c.setLineWidth(0.4)
        c.rect(LM, sy - 0.68 * inch, TW, 0.70 * inch, fill=0, stroke=1)
        sw3 = (TW - 0.2 * inch) / 3
        for i, lbl in enumerate(['CLAIMANT SIGNATURE', 'DATE', 'CLAIMS HANDLER']):
            sx2 = LM + 0.12 * inch + i * (sw3 + 0.04 * inch)
            c.setStrokeColor(INK2)
            c.setLineWidth(0.7)
            c.line(sx2, sy - 0.28 * inch, sx2 + sw3 - 0.1 * inch, sy - 0.28 * inch)
            c.setFont('Helvetica', 6)
            c.setFillColor(GREY)
            c.drawString(sx2, sy - 0.50 * inch, lbl)


# ── Page 2: Formal Claim Form ──────────────────────────────────────────────────
def draw_claim_form(c, claim, contract, t):
    P, A, L = t['P'], t['A'], t['L']
    is_v    = claim['expected'] == 'VALID'
    STAMP_C = PASS_C if is_v else FAIL_C
    y = H - 1.02 * inch

    # Title
    c.setFont('Helvetica-Bold', 16)
    c.setFillColor(P)
    c.drawString(LM, y, 'INSURANCE CLAIM FORM')
    c.setFont('Helvetica', 9)
    c.setFillColor(GREY)
    c.drawRightString(W - LM, y, '%s  ·  %s' % (contract['policy_number'], contract['type']))
    y -= 0.10 * inch
    c.setStrokeColor(A)
    c.setLineWidth(2)
    c.line(LM, y, LM + 3.2 * inch, y)
    y -= 0.22 * inch

    def field_row(fields, bg, rh=0.52 * inch):
        nonlocal y
        fw_sum = sum(f[2] for f in fields)
        c.setFillColor(bg)
        c.rect(LM, y - rh, TW, rh, fill=1, stroke=0)
        c.setStrokeColor(RULE)
        c.setLineWidth(0.3)
        c.rect(LM, y - rh, TW, rh, fill=0, stroke=1)
        fx = LM
        for lbl, val, parts in fields:
            fw = (parts / fw_sum) * TW
            c.setFont('Helvetica', 6)
            c.setFillColor(GREY)
            c.drawString(fx + 8, y - 0.13 * inch, lbl.upper())
            if lbl == 'Amount Requested':
                valc = P
            elif lbl == 'Expected Outcome':
                valc = PASS_M if is_v else FAIL_M
            else:
                valc = INK
            fsz = 12 if lbl == 'Amount Requested' else 10
            c.setFont('Helvetica-Bold', fsz)
            c.setFillColor(valc)
            c.drawString(fx + 8, y - 0.36 * inch, str(val)[:30])
            c.setStrokeColor(RULE)
            c.line(fx + fw, y - rh, fx + fw, y)
            fx += fw
        y -= rh

    # § 1 — Claimant Information
    c.setFillColor(P)
    c.rect(LM, y - 0.22 * inch, TW, 0.22 * inch, fill=1, stroke=0)
    c.setFillColor(A)
    c.rect(LM, y - 0.22 * inch, 4, 0.22 * inch, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 8)
    c.setFillColor(WHITE)
    c.drawString(LM + 10, y - 0.143 * inch, '\xa7 1  CLAIMANT INFORMATION')
    y -= 0.22 * inch
    field_row([('Full Name', claim['claimant'], 2.0),
               ('Claim Reference ID', claim['id'].upper(), 1.5),
               ('Claim Date', claim['date'], 1.1)], L)
    field_row([('Incident Date', claim['incident_date'], 1.1),
               ('Amount Requested', claim['amount'], 1.1),
               ('Expected Outcome', claim['expected'], 1.0),
               ('Policy Number', contract['policy_number'], 1.3)], CREAM)
    y -= 0.10 * inch

    # § 2 — Incident Description
    c.setFillColor(P)
    c.rect(LM, y - 0.22 * inch, TW, 0.22 * inch, fill=1, stroke=0)
    c.setFillColor(A)
    c.rect(LM, y - 0.22 * inch, 4, 0.22 * inch, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 8)
    c.setFillColor(WHITE)
    c.drawString(LM + 10, y - 0.143 * inch, '\xa7 2  INCIDENT DESCRIPTION')
    y -= 0.22 * inch
    chars = (TW - 0.30 * inch) / (8.5 * 0.52)
    dlines = wrap(claim.get('description', ''), chars)
    dh = len(dlines) * 13 + 0.22 * inch
    c.setFillColor(L)
    c.rect(LM, y - dh, TW, dh, fill=1, stroke=0)
    c.setStrokeColor(A)
    c.setLineWidth(2.5)
    c.line(LM, y - dh, LM, y)
    c.setStrokeColor(RULE)
    c.setLineWidth(0.3)
    c.rect(LM, y - dh, TW, dh, fill=0, stroke=1)
    ty = y - 0.10 * inch
    for dl in dlines:
        c.setFont('Times-Italic', 8.5)
        c.setFillColor(INK2)
        c.drawString(LM + 12, ty, dl)
        ty -= 13
    y -= dh + 0.10 * inch

    # § 3 — Facts table
    c.setFillColor(P)
    c.rect(LM, y - 0.22 * inch, TW, 0.22 * inch, fill=1, stroke=0)
    c.setFillColor(A)
    c.rect(LM, y - 0.22 * inch, 4, 0.22 * inch, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 8)
    c.setFillColor(WHITE)
    c.drawString(LM + 10, y - 0.143 * inch, '\xa7 3  CLAIM FACTS')
    y -= 0.22 * inch

    hh = 0.20 * inch
    c.setFillColor(CREAM2)
    c.rect(LM, y - hh, TW, hh, fill=1, stroke=0)
    c.setStrokeColor(RULE)
    c.setLineWidth(0.3)
    c.rect(LM, y - hh, TW, hh, fill=0, stroke=1)
    c.setFont('Helvetica-Bold', 7)
    c.setFillColor(P)
    c.drawString(LM + 8, y - 0.135 * inch, 'FACT')
    c.drawString(LM + TW * 0.52, y - 0.135 * inch, 'VALUE')
    c.drawString(LM + TW * 0.74, y - 0.135 * inch, 'TYPE')
    c.line(LM + TW * 0.52, y - hh, LM + TW * 0.52, y)
    c.line(LM + TW * 0.74, y - hh, LM + TW * 0.74, y)
    y -= hh

    RH = 0.21 * inch
    for i, (k, v) in enumerate(claim.get('facts', {}).items()):
        if y - RH < 1.30 * inch:
            break
        if v is True:
            vs, vc, vt = 'True', PASS_M, 'boolean'
        elif v is False:
            vs, vc, vt = 'False', FAIL_M, 'boolean'
        elif v is None:
            vs, vc, vt = 'N/A', GREY, 'null'
        elif isinstance(v, float):
            vs, vc, vt = str(v), colors.HexColor('#1A3A6A'), 'float'
        elif isinstance(v, int):
            vs, vc, vt = str(v), colors.HexColor('#1A3A6A'), 'integer'
        else:
            vs, vc, vt = str(v)[:28], INK2, 'atom'
        bg = CREAM if i % 2 == 0 else L
        c.setFillColor(bg)
        c.rect(LM, y - RH, TW, RH, fill=1, stroke=0)
        c.setStrokeColor(RULE)
        c.setLineWidth(0.2)
        c.line(LM, y - RH, LM + TW, y - RH)
        c.line(LM + TW * 0.52, y - RH, LM + TW * 0.52, y)
        c.line(LM + TW * 0.74, y - RH, LM + TW * 0.74, y)
        c.setFont('Courier', 7.5)
        c.setFillColor(INK2)
        c.drawString(LM + 8, y - 0.145 * inch, str(k).replace('_', ' '))
        c.setFont('Helvetica-Bold', 8)
        c.setFillColor(vc)
        c.drawString(LM + TW * 0.52 + 6, y - 0.145 * inch, vs)
        c.setFont('Courier', 6.5)
        c.setFillColor(GREY2)
        c.drawString(LM + TW * 0.74 + 6, y - 0.145 * inch, vt)
        y -= RH

    c.setStrokeColor(RULE)
    c.setLineWidth(0.4)
    c.rect(LM, y, TW, (H - 1.5 * inch) - y, fill=0, stroke=1)

    # Rotated stamp
    sc_x, sc_y = W - 1.15 * inch, H - 1.62 * inch
    c.saveState()
    c.translate(sc_x, sc_y)
    c.rotate(-18)
    c.setStrokeColor(STAMP_C)
    c.setLineWidth(2.5)
    c.circle(0, 0, 0.62 * inch, stroke=1, fill=0)
    c.setLineWidth(1)
    c.circle(0, 0, 0.53 * inch, stroke=1, fill=0)
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(STAMP_C)
    c.drawCentredString(0, 0.11 * inch, 'APPROVED' if is_v else 'PENDING')
    c.setFont('Helvetica', 7)
    c.drawCentredString(0, -0.06 * inch, 'FOR PROCESSING' if is_v else 'REVIEW REQUIRED')
    c.setFont('Courier-Bold', 6)
    c.drawCentredString(0, -0.26 * inch, 'INSURLE ENGINE')
    c.restoreState()

    # Signature block
    if y > 1.5 * inch:
        sy2 = max(y, 1.5 * inch)
        c.setFillColor(CREAM2)
        c.roundRect(LM, sy2 - 0.65 * inch, TW, 0.68 * inch, 4, fill=1, stroke=0)
        c.setStrokeColor(RULE)
        c.setLineWidth(0.4)
        c.rect(LM, sy2 - 0.65 * inch, TW, 0.68 * inch, fill=0, stroke=1)
        sw3 = (TW - 0.2 * inch) / 3
        for i, lbl in enumerate(['CLAIMANT SIGNATURE', 'DATE', 'CLAIMS HANDLER']):
            sx3 = LM + 0.12 * inch + i * (sw3 + 0.04 * inch)
            c.setStrokeColor(INK2)
            c.setLineWidth(0.7)
            c.line(sx3, sy2 - 0.27 * inch, sx3 + sw3 - 0.1 * inch, sy2 - 0.27 * inch)
            c.setFont('Helvetica', 6)
            c.setFillColor(GREY)
            c.drawString(sx3, sy2 - 0.47 * inch, lbl)


# ── Assemble one claim PDF (2 pages) ──────────────────────────────────────────
def build_claim_pdf(claim, contract_meta, out_path):
    cid = None
    for k in THEMES:
        if claim['id'].startswith(k.replace('contract_', 'claim_')):
            cid = k
            break
    if cid is None:
        # fallback: guess from claim id prefix
        prefix = claim['id'].split('_')[1]  # e.g. 'auto' from 'claim_auto_1'
        cid = 'contract_' + prefix

    t = THEMES.get(cid, THEMES['contract_auto'])
    total = 2

    cv = canvas.Canvas(str(out_path), pagesize=letter)
    cv.setTitle('Claim: ' + claim['id'])
    cv.setAuthor(contract_meta['insurer'])

    # Page 1 — Cover
    page_header(cv, contract_meta, claim, t, 1)
    draw_cover(cv, claim, contract_meta, t)
    page_footer(cv, contract_meta, claim, t, 1, total)
    cv.showPage()

    # Page 2 — Claim Form
    page_header(cv, contract_meta, claim, t, 2)
    draw_claim_form(cv, claim, contract_meta, t)
    page_footer(cv, contract_meta, claim, t, 2, total)
    cv.showPage()

    cv.save()
    print('  ✓  %s  (%d pages)' % (out_path.name, total))


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    data_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('insurle_data.json')
    data = json.loads(data_path.read_text())

    out_dir = Path('claim_pdfs')
    out_dir.mkdir(exist_ok=True)

    print('🖨  Generating claim PDFs…')
    count = 0
    for cid, claims in data['claims'].items():
        contract_meta = CONTRACT_META.get(cid)
        if contract_meta is None:
            continue
        for claim in claims:
            out_path = out_dir / ('%s.pdf' % claim['id'])
            build_claim_pdf(claim, contract_meta, out_path)
            count += 1

    print('\n✅  %d claim PDFs generated in %s/' % (count, out_dir))


if __name__ == '__main__':
    main()