#!/usr/bin/env python3
"""InsurLE — clean canvas-based PDF generator. No Platypus, no layout issues."""
import json, re, textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors

W, H = letter  # 612 x 792 pts

# ── Palette ────────────────────────────────────
CREAM  = colors.HexColor('#F7F3EC')
CREAM2 = colors.HexColor('#EDE7D9')
INK    = colors.HexColor('#1A1510')
INK2   = colors.HexColor('#2A2520')
GREY   = colors.HexColor('#6A6050')
GREY2  = colors.HexColor('#9A8F7A')
RULE   = colors.HexColor('#C8BFA8')
CDARK  = colors.HexColor('#0D0F14')
CFG    = colors.HexColor('#ABB2BF')
CCM    = colors.HexColor('#5C6370')
CPR    = colors.HexColor('#61AFEF')
CAT    = colors.HexColor('#98C379')
COP    = colors.HexColor('#C678DD')
CNM    = colors.HexColor('#D19A66')
WHITE  = colors.white
GREEN  = colors.HexColor('#1A5A30')
RED    = colors.HexColor('#8B1A1A')

THEMES = {
    'contract_auto':     {'P': colors.HexColor('#1A3A5C'), 'A': colors.HexColor('#E8B84B'), 'L': colors.HexColor('#EBF1F8')},
    'contract_health':   {'P': colors.HexColor('#1A4A3A'), 'A': colors.HexColor('#4ECB8D'), 'L': colors.HexColor('#EBF5F1')},
    'contract_travel':   {'P': colors.HexColor('#2A1A5C'), 'A': colors.HexColor('#A78BFA'), 'L': colors.HexColor('#F0EBF8')},
    'contract_accident': {'P': colors.HexColor('#4A1A1A'), 'A': colors.HexColor('#F87171'), 'L': colors.HexColor('#F8EBEB')},
}

LM = 0.55 * inch  # left margin
TW = W - 1.1 * inch  # text width

def wrap(text, chars):
    return textwrap.wrap(str(text), max(20, int(chars))) or ['']

def page_header(c, contract, t, pg):
    P, A = t['P'], t['A']
    c.setFillColor(P);  c.rect(0, H - 0.72*inch, W, 0.72*inch, fill=1, stroke=0)
    c.setFillColor(A);  c.rect(0, H - 0.78*inch, W, 0.06*inch, fill=1, stroke=0)
    c.setFillColor(A);  c.rect(0, 0, 4, H, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 12); c.setFillColor(WHITE)
    c.drawString(LM, H - 0.46*inch, contract['insurer'])
    c.setFont('Courier-Bold', 8); c.setFillColor(A)
    c.drawRightString(W - 0.5*inch, H - 0.46*inch, contract['policy_number'])
    c.setFont('Helvetica', 7); c.setFillColor(colors.Color(1,1,1,alpha=0.5))
    c.drawRightString(W - 0.5*inch, H - 0.62*inch, contract['type'].upper())

def page_footer(c, contract, t, pg, total):
    c.setStrokeColor(RULE); c.setLineWidth(0.5)
    c.line(LM, 0.52*inch, W - LM, 0.52*inch)
    c.setFont('Helvetica', 7); c.setFillColor(GREY)
    c.drawString(LM, 0.35*inch, contract['name'])
    c.drawRightString(W - LM, 0.35*inch, 'Page %d of %d' % (pg, total))
    c.setFont('Helvetica', 6); c.setFillColor(GREY2)
    c.drawCentredString(W/2, 0.2*inch, 'CONFIDENTIAL \u2014 FOR POLICYHOLDER USE ONLY \u2014 InsurLE Logic Engine')

# ─── Cover page ──────────────────────────────────────────────────────────────
def draw_cover(c, contract, t):
    P, A, L = t['P'], t['A'], t['L']
    y = H - 1.05*inch

    # Title
    c.setFont('Helvetica-Bold', 24); c.setFillColor(P)
    c.drawCentredString(W/2, y, contract['name'])
    y -= 0.28*inch
    c.setStrokeColor(A); c.setLineWidth(2)
    c.line(W/2 - 2.2*inch, y, W/2 + 2.2*inch, y)
    y -= 0.18*inch
    c.setFont('Helvetica', 10); c.setFillColor(GREY)
    c.drawCentredString(W/2, y, '%s  \u00b7  %s \u2013 %s' % (contract['type'], contract['effective_date'], contract['expiry_date']))
    y -= 0.38*inch

    # Meta grid 4 cols x 2 rows
    boxes = [
        ('INSURER', contract['insurer']),
        ('POLICY NUMBER', contract['policy_number']),
        ('ANNUAL PREMIUM', contract['premium']),
        ('COVERAGE LIMIT', contract['coverage']),
        ('EFFECTIVE DATE', contract['effective_date']),
        ('EXPIRY DATE', contract['expiry_date']),
        ('POLICY TYPE', contract['type']),
        ('JURISDICTION', 'InsurLE Standard'),
    ]
    bw = TW / 4; bh = 0.64*inch
    for i, (lbl, val) in enumerate(boxes):
        col, row = i % 4, i // 4
        bx = LM + col * bw; by = y - row * (bh + 0.05*inch)
        c.setFillColor(L); c.roundRect(bx, by - bh, bw - 0.04*inch, bh, 4, fill=1, stroke=0)
        bar_c = P if row == 0 else A
        c.setFillColor(bar_c); c.rect(bx, by - 0.14*inch, bw - 0.04*inch, 0.14*inch, fill=1, stroke=0)
        c.setFont('Helvetica-Bold', 6); c.setFillColor(WHITE)
        c.drawString(bx + 7, by - 0.095*inch, lbl)
        c.setFont('Helvetica-Bold', 9); c.setFillColor(INK)
        c.drawString(bx + 7, by - bh + 0.14*inch, str(val)[:28])
        c.setStrokeColor(RULE); c.setLineWidth(0.3)
        c.roundRect(bx, by - bh, bw - 0.04*inch, bh, 4, fill=0, stroke=1)
    y -= 2 * (bh + 0.05*inch) + 0.22*inch

    # Intro box
    intro = ('This Insurance Contract is issued by %s under policy %s. '
             'It constitutes a binding agreement governing the terms and scope of %s coverage. '
             'All eligibility rules are formally encoded as nested Prolog predicates within the '
             'InsurLE automated verification engine.' % (contract['insurer'], contract['policy_number'], contract['type']))
    lines = wrap(intro, (TW - 0.28*inch) / (8.5 * 0.52))
    bh2 = len(lines) * 13 + 0.22*inch
    c.setFillColor(CREAM2); c.roundRect(LM, y - bh2, TW, bh2, 5, fill=1, stroke=0)
    c.setStrokeColor(A); c.setLineWidth(3); c.line(LM, y - bh2, LM, y)
    ty = y - 0.13*inch
    for line in lines:
        c.setFont('Times-Italic', 8.5); c.setFillColor(INK2); c.drawString(LM + 14, ty, line); ty -= 13
    y -= bh2 + 0.22*inch

    # Divider + seal
    c.setStrokeColor(RULE); c.setLineWidth(0.5); c.line(LM, y, W - LM, y); y -= 0.12*inch
    cx2, cy_s = W/2, y - 0.65*inch
    c.setStrokeColor(A); c.setLineWidth(2.5); c.circle(cx2, cy_s, 0.57*inch, stroke=1, fill=0)
    c.setStrokeColor(A); c.setLineWidth(0.8); c.circle(cx2, cy_s, 0.49*inch, stroke=1, fill=0)
    c.setFont('Helvetica-Bold', 11); c.setFillColor(P); c.drawCentredString(cx2, cy_s + 0.12*inch, 'InsurLE')
    c.setFont('Helvetica', 8); c.setFillColor(GREY); c.drawCentredString(cx2, cy_s - 0.02*inch, 'Logic Engine')
    c.setFont('Courier-Bold', 7); c.setFillColor(A); c.drawCentredString(cx2, cy_s - 0.2*inch, 'VERIFIED CONTRACT')
    y -= 1.45*inch

    # Signature block
    c.setFillColor(CREAM2); c.roundRect(LM, y - 0.68*inch, TW, 0.72*inch, 4, fill=1, stroke=0)
    c.setStrokeColor(RULE); c.setLineWidth(0.5); c.rect(LM, y - 0.68*inch, TW, 0.72*inch, fill=0, stroke=1)
    sw3 = (TW - 0.2*inch) / 3
    for i, lbl in enumerate(['POLICYHOLDER SIGNATURE', 'DATE', 'INSURER AUTHORISATION']):
        sx2 = LM + 0.12*inch + i * (sw3 + 0.04*inch)
        c.setStrokeColor(INK2); c.setLineWidth(0.7)
        c.line(sx2, y - 0.3*inch, sx2 + sw3 - 0.1*inch, y - 0.3*inch)
        c.setFont('Helvetica', 6); c.setFillColor(GREY); c.drawString(sx2, y - 0.52*inch, lbl)

# ─── Sections pages ───────────────────────────────────────────────────────────
def draw_sections(c, contract, t, pg_start, total):
    P, A, L = t['P'], t['A'], t['L']
    pg = pg_start
    y = H - 1.02*inch
    c.setFont('Helvetica-Bold', 15); c.setFillColor(P)
    c.drawString(LM, y, 'Terms & Conditions')
    y -= 0.1*inch; c.setStrokeColor(A); c.setLineWidth(2)
    c.line(LM, y, LM + 3.0*inch, y); y -= 0.22*inch

    for sec_text in contract['contract_text']:
        m = re.match(r'^(SECTION \d+\s*[\u2013\-]\s*[^:]+):\s*([\s\S]*)', sec_text)
        sec_title = m.group(1).strip() if m else ''
        body = m.group(2).strip() if m else sec_text

        chars = (TW - 0.22*inch) / (8.5 * 0.52)
        body_lines = wrap(body, chars)
        needed = 0.24*inch + len(body_lines) * 12.5 + 0.14*inch

        if y - needed < 0.82*inch:
            page_footer(c, contract, t, pg, total)
            c.showPage(); pg += 1
            page_header(c, contract, t, pg)
            y = H - 1.02*inch

        # Heading band
        c.setFillColor(P); c.rect(LM, y - 0.22*inch, TW, 0.22*inch, fill=1, stroke=0)
        c.setFillColor(A); c.rect(LM, y - 0.22*inch, 4, 0.22*inch, fill=1, stroke=0)
        c.setFont('Helvetica-Bold', 8); c.setFillColor(WHITE)
        c.drawString(LM + 10, y - 0.143*inch, sec_title)
        y -= 0.22*inch

        # Body
        bh = len(body_lines) * 12.5 + 0.18*inch
        c.setFillColor(L); c.rect(LM, y - bh, TW, bh, fill=1, stroke=0)
        c.setFillColor(A); c.rect(LM, y - bh, 3, bh, fill=1, stroke=0)
        c.setStrokeColor(RULE); c.setLineWidth(0.35); c.rect(LM, y - bh, TW, bh, fill=0, stroke=1)
        ty = y - 0.1*inch
        for line in body_lines:
            c.setFont('Times-Roman', 8.5); c.setFillColor(INK2)
            c.drawString(LM + 12, ty, line); ty -= 12.5
        y -= bh + 0.08*inch
    return pg

# ─── InsurLE code page ────────────────────────────────────────────────────────
def draw_code(c, contract, t, pg):
    P, A, L = t['P'], t['A'], t['L']
    y = H - 1.02*inch
    c.setFont('Helvetica-Bold', 15); c.setFillColor(P)
    c.drawString(LM, y, 'InsurLE Logic Rules')
    y -= 0.1*inch; c.setStrokeColor(A); c.setLineWidth(2)
    c.line(LM, y, LM + 2.8*inch, y); y -= 0.18*inch
    c.setFont('Helvetica', 8.5); c.setFillColor(GREY)
    c.drawString(LM, y, 'Prolog encoding  \u00b7  %s  \u00b7  3-level nested hierarchy' % contract['policy_number'])
    y -= 0.22*inch

    rules = contract['insurle_rules']
    LINE_H = 11
    avail = int((y - 0.78*inch) / LINE_H)
    code_h = min(avail, len(rules)) * LINE_H + 0.24*inch

    c.setFillColor(CDARK); c.roundRect(LM, y - code_h, TW, code_h + 0.08*inch, 6, fill=1, stroke=0)
    c.setStrokeColor(A); c.setLineWidth(3)
    c.line(LM + TW, y - code_h, LM + TW, y + 0.08*inch)

    # Mac dots
    for di, dc in enumerate(['#FF5F57','#FEBC2E','#28C840']):
        c.setFillColor(colors.HexColor(dc)); c.circle(LM + 0.2*inch + di*0.17*inch, y + 0.03*inch, 0.044*inch, fill=1, stroke=0)
    c.setFont('Courier', 7); c.setFillColor(CCM)
    c.drawString(LM + 0.75*inch, y + 0.005*inch, '%s.pl  \u2014  InsurLE rules (3-level nesting)' % contract['id'])

    CW2 = 4.22  # char width at 7.5pt Courier
    cy = y - 0.04*inch
    for i, raw in enumerate(rules[:avail]):
        cy -= LINE_H
        xc = LM + 0.18*inch
        s = raw.strip()
        if not s: continue
        if s.startswith('%'):
            c.setFont('Courier-Oblique', 7.5); c.setFillColor(CCM)
            c.drawString(xc, cy, raw[:90])
            continue
        c.setFont('Courier', 7.5); c.setFillColor(CFG)
        c.drawString(xc, cy, raw[:90])
        for mt in re.finditer(r'\b([a-z][a-z_0-9]*)(?=\()', raw):
            c.setFont('Courier-Bold', 7.5); c.setFillColor(CPR)
            c.drawString(xc + mt.start() * CW2, cy, mt.group(0))
        for mt in re.finditer(r'\b(true|false|own|permitted|continental_us|canada|passenger|commercial|'
                              r'illness|injury|death|natural_disaster|airline_bankruptcy|medical|baggage|'
                              r'disability|workplace_accident|professional_sports|criminal_activity|war|'
                              r'self_inflicted|base_jumping|skydiving|free_solo_climbing|'
                              r'category_[abcd]|tier[123]|ptd|ppd|ttd)\b', raw):
            c.setFont('Courier', 7.5); c.setFillColor(CAT)
            c.drawString(xc + mt.start() * CW2, cy, mt.group(0))
        for mt in re.finditer(r'\b(\d+\.?\d*)\b', raw):
            c.setFont('Courier', 7.5); c.setFillColor(CNM)
            c.drawString(xc + mt.start() * CW2, cy, mt.group(0))
        for mt in re.finditer(r'(:-)', raw):
            c.setFont('Courier-Bold', 7.5); c.setFillColor(COP)
            c.drawString(xc + mt.start() * CW2, cy, mt.group(0))

# ─── Claim form page ──────────────────────────────────────────────────────────
def draw_claim(c, claim, contract, t):
    P, A, L = t['P'], t['A'], t['L']
    is_v = claim['expected'] == 'VALID'
    STAMP_C = GREEN if is_v else RED
    y = H - 1.02*inch

    # Title
    c.setFont('Helvetica-Bold', 16); c.setFillColor(P)
    c.drawString(LM, y, 'INSURANCE CLAIM FORM')
    c.setFont('Helvetica', 9); c.setFillColor(GREY)
    c.drawRightString(W - LM, y, '%s  \u00b7  %s' % (contract['policy_number'], contract['type']))
    y -= 0.1*inch; c.setStrokeColor(A); c.setLineWidth(2)
    c.line(LM, y, LM + 3.2*inch, y); y -= 0.22*inch

    def field_row(fields, bg, rh=0.52*inch):
        nonlocal y
        fw_sum = sum(f[2] for f in fields)
        c.setFillColor(bg); c.rect(LM, y - rh, TW, rh, fill=1, stroke=0)
        c.setStrokeColor(RULE); c.setLineWidth(0.3); c.rect(LM, y - rh, TW, rh, fill=0, stroke=1)
        fx = LM
        for lbl, val, parts in fields:
            fw = (parts / fw_sum) * TW
            c.setFont('Helvetica', 6); c.setFillColor(GREY); c.drawString(fx + 8, y - 0.13*inch, lbl.upper())
            valc = P if lbl == 'Amount Requested' else (GREEN if (lbl=='Expected Outcome' and is_v) else (RED if lbl=='Expected Outcome' else INK))
            c.setFont('Helvetica-Bold', 10 if lbl!='Amount Requested' else 12); c.setFillColor(valc)
            c.drawString(fx + 8, y - 0.35*inch, str(val)[:30])
            c.setStrokeColor(RULE); c.line(fx + fw, y - rh, fx + fw, y)
            fx += fw
        y -= rh

    # Section 1
    c.setFillColor(P); c.rect(LM, y - 0.22*inch, TW, 0.22*inch, fill=1, stroke=0)
    c.setFillColor(A); c.rect(LM, y - 0.22*inch, 4, 0.22*inch, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 8); c.setFillColor(WHITE); c.drawString(LM + 10, y - 0.143*inch, '\u00a7 1  CLAIMANT INFORMATION')
    y -= 0.22*inch
    field_row([('Full Name', claim['claimant'], 2.0), ('Claim Reference ID', claim['id'], 1.5), ('Claim Date', claim['date'], 1.1)], L)
    field_row([('Incident Date', claim['incident_date'], 1.1), ('Amount Requested', claim['amount'], 1.1), ('Expected Outcome', claim['expected'], 1.0), ('Policy Number', contract['policy_number'], 1.3)], CREAM)
    y -= 0.1*inch

    # Section 2
    c.setFillColor(P); c.rect(LM, y - 0.22*inch, TW, 0.22*inch, fill=1, stroke=0)
    c.setFillColor(A); c.rect(LM, y - 0.22*inch, 4, 0.22*inch, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 8); c.setFillColor(WHITE); c.drawString(LM + 10, y - 0.143*inch, '\u00a7 2  INCIDENT DESCRIPTION')
    y -= 0.22*inch
    chars = (TW - 0.3*inch) / (8.5 * 0.52)
    dlines = wrap(claim['description'], chars)
    dh = len(dlines) * 13 + 0.2*inch
    c.setFillColor(L); c.rect(LM, y - dh, TW, dh, fill=1, stroke=0)
    c.setStrokeColor(A); c.setLineWidth(2.5); c.line(LM, y - dh, LM, y)
    c.setStrokeColor(RULE); c.setLineWidth(0.3); c.rect(LM, y - dh, TW, dh, fill=0, stroke=1)
    ty = y - 0.1*inch
    for dl in dlines:
        c.setFont('Times-Italic', 8.5); c.setFillColor(INK2); c.drawString(LM + 12, ty, dl); ty -= 13
    y -= dh + 0.1*inch

    # Section 3 — facts table
    c.setFillColor(P); c.rect(LM, y - 0.22*inch, TW, 0.22*inch, fill=1, stroke=0)
    c.setFillColor(A); c.rect(LM, y - 0.22*inch, 4, 0.22*inch, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 8); c.setFillColor(WHITE); c.drawString(LM + 10, y - 0.143*inch, '\u00a7 3  CLAIM FACTS  (InsurLE Ground Predicates)')
    y -= 0.22*inch
    # Header row
    hh = 0.2*inch
    c.setFillColor(CREAM2); c.rect(LM, y - hh, TW, hh, fill=1, stroke=0)
    c.setStrokeColor(RULE); c.setLineWidth(0.3); c.rect(LM, y - hh, TW, hh, fill=0, stroke=1)
    c.setFont('Helvetica-Bold', 7); c.setFillColor(P)
    c.drawString(LM + 8, y - 0.135*inch, 'PREDICATE')
    c.drawString(LM + TW*0.52, y - 0.135*inch, 'VALUE')
    c.drawString(LM + TW*0.74, y - 0.135*inch, 'TYPE')
    c.setStrokeColor(RULE)
    c.line(LM + TW*0.52, y - hh, LM + TW*0.52, y)
    c.line(LM + TW*0.74, y - hh, LM + TW*0.74, y)
    y -= hh

    RH = 0.21*inch
    for i, (k, v) in enumerate(claim.get('facts', {}).items()):
        if y - RH < 1.3*inch: break
        if v is True:     vs, vc, vt = 'True',  GREEN, 'boolean'
        elif v is False:  vs, vc, vt = 'False', RED, 'boolean'
        elif v is None:   vs, vc, vt = 'N/A',   GREY, 'null'
        elif isinstance(v, float): vs, vc, vt = str(v), colors.HexColor('#1A3A6A'), 'float'
        elif isinstance(v, int):   vs, vc, vt = str(v), colors.HexColor('#1A3A6A'), 'integer'
        else:             vs, vc, vt = str(v)[:28], INK2, 'atom'
        bg = CREAM if i % 2 == 0 else L
        c.setFillColor(bg); c.rect(LM, y - RH, TW, RH, fill=1, stroke=0)
        c.setStrokeColor(RULE); c.setLineWidth(0.2)
        c.line(LM, y - RH, LM + TW, y - RH)
        c.line(LM + TW*0.52, y - RH, LM + TW*0.52, y)
        c.line(LM + TW*0.74, y - RH, LM + TW*0.74, y)
        c.setFont('Courier', 7.5); c.setFillColor(INK2)
        c.drawString(LM + 8, y - 0.145*inch, '%s(%s, \u2026)' % (k, claim['id'][:14]))
        c.setFont('Helvetica-Bold', 8); c.setFillColor(vc); c.drawString(LM + TW*0.52 + 6, y - 0.145*inch, vs)
        c.setFont('Courier', 6.5); c.setFillColor(GREY2); c.drawString(LM + TW*0.74 + 6, y - 0.145*inch, vt)
        y -= RH

    c.setStrokeColor(RULE); c.setLineWidth(0.4)
    c.rect(LM, y, TW, (H - 1.5*inch) - y, fill=0, stroke=1)
    y -= 0.18*inch

    # Rotated stamp
    sc_x, sc_y = W - 1.15*inch, H - 1.65*inch
    c.saveState(); c.translate(sc_x, sc_y); c.rotate(-18)
    c.setStrokeColor(STAMP_C); c.setLineWidth(2.5); c.circle(0, 0, 0.62*inch, stroke=1, fill=0)
    c.setLineWidth(1); c.circle(0, 0, 0.53*inch, stroke=1, fill=0)
    c.setFont('Helvetica-Bold', 9); c.setFillColor(STAMP_C)
    c.drawCentredString(0, 0.11*inch, 'APPROVED' if is_v else 'PENDING')
    c.setFont('Helvetica', 7)
    c.drawCentredString(0, -0.06*inch, 'FOR PROCESSING' if is_v else 'REVIEW REQUIRED')
    c.setFont('Courier-Bold', 6); c.drawCentredString(0, -0.26*inch, 'INSURLE ENGINE')
    c.restoreState()

    # Signature block
    if y > 1.5*inch:
        sy2 = max(y, 1.5*inch)
        c.setFillColor(CREAM2); c.roundRect(LM, sy2 - 0.65*inch, TW, 0.68*inch, 4, fill=1, stroke=0)
        c.setStrokeColor(RULE); c.setLineWidth(0.4); c.rect(LM, sy2 - 0.65*inch, TW, 0.68*inch, fill=0, stroke=1)
        sw3 = (TW - 0.2*inch) / 3
        for i, lbl in enumerate(['CLAIMANT SIGNATURE', 'DATE', 'CLAIMS HANDLER']):
            sx3 = LM + 0.12*inch + i * (sw3 + 0.04*inch)
            c.setStrokeColor(INK2); c.setLineWidth(0.7)
            c.line(sx3, sy2 - 0.27*inch, sx3 + sw3 - 0.1*inch, sy2 - 0.27*inch)
            c.setFont('Helvetica', 6); c.setFillColor(GREY); c.drawString(sx3, sy2 - 0.47*inch, lbl)

# ─── Assemble one contract PDF ────────────────────────────────────────────────
def build_pdf(contract, claims, out):
    c = canvas.Canvas(out, pagesize=letter)
    c.setTitle(contract['name']); c.setAuthor(contract['insurer'])
    t = THEMES.get(contract['id'], THEMES['contract_auto'])
    total = 3 + len(claims)

    # P1 cover
    page_header(c, contract, t, 1)
    draw_cover(c, contract, t)
    page_footer(c, contract, t, 1, total)
    c.showPage()

    # P2+ sections
    page_header(c, contract, t, 2)
    pg = draw_sections(c, contract, t, 2, total)
    page_footer(c, contract, t, pg, total)
    c.showPage(); pg += 1

    # Code page
    page_header(c, contract, t, pg)
    draw_code(c, contract, t, pg)
    page_footer(c, contract, t, pg, total)
    c.showPage(); pg += 1

    # Claim pages
    for cl in claims:
        page_header(c, contract, t, pg)
        draw_claim(c, cl, contract, t)
        page_footer(c, contract, t, pg, total)
        c.showPage(); pg += 1

    c.save()
    print('  \u2713  %s  (%d pages)' % (out, pg - 1))

def main():
    data = json.load(open('insurle_data.json'))
    print('\U0001f5a8  Generating PDFs\u2026')
    for contract in data['contracts']:
        cid = contract['id']
        claims = data['claims'].get(cid, [])
        out = 'contract_%s.pdf' % cid.replace('contract_', '')
        build_pdf(contract, claims, out)
    print('\n\u2705  %d PDFs generated' % len(data['contracts']))

if __name__ == '__main__':
    main()