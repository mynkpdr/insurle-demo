#!/usr/bin/env python3
"""InsurLE — Contract PDF Generator.
Produces one PDF per contract containing:
  Page 1 — Cover page (metadata, intro, seal, signature)
  Page 2+ — Terms & Conditions sections
"""
import json
import textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors

W, H = letter
CREAM  = colors.HexColor('#F7F3EC')
CREAM2 = colors.HexColor('#EDE7D9')
INK    = colors.HexColor('#1A1510')
INK2   = colors.HexColor('#2A2520')
GREY   = colors.HexColor('#6A6050')
GREY2  = colors.HexColor('#9A8F7A')
RULE   = colors.HexColor('#C8BFA8')
WHITE  = colors.white

THEMES = {
    'contract_auto':     {'P': colors.HexColor('#1A3A5C'), 'A': colors.HexColor('#E8B84B'), 'L': colors.HexColor('#EBF1F8')},
    'contract_health':   {'P': colors.HexColor('#1A4A3A'), 'A': colors.HexColor('#4ECB8D'), 'L': colors.HexColor('#EBF5F1')},
    'contract_travel':   {'P': colors.HexColor('#2A1A5C'), 'A': colors.HexColor('#A78BFA'), 'L': colors.HexColor('#F0EBF8')},
    'contract_accident': {'P': colors.HexColor('#4A1A1A'), 'A': colors.HexColor('#F87171'), 'L': colors.HexColor('#F8EBEB')},
}

LM = 0.55 * inch
TW = W - 1.1 * inch


def wrap(text, chars):
    return textwrap.wrap(str(text), max(20, int(chars))) or ['']


def page_header(c, contract, t, pg):
    P, A = t['P'], t['A']
    c.setFillColor(P);  c.rect(0, H - 0.72*inch, W, 0.72*inch, fill=1, stroke=0)
    c.setFillColor(A);  c.rect(0, H - 0.78*inch, W, 0.06*inch, fill=1, stroke=0)
    c.setFillColor(A);  c.rect(0, 0, 4, H, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 12); c.setFillColor(WHITE)
    c.drawString(LM, H - 0.46*inch, contract['insurer'])
    c.setFont('Courier-Bold', 8);    c.setFillColor(A)
    c.drawRightString(W - 0.5*inch, H - 0.46*inch, contract['policy_number'])
    c.setFont('Helvetica', 7);       c.setFillColor(colors.Color(1,1,1,alpha=0.5))
    c.drawRightString(W - 0.5*inch, H - 0.62*inch, contract['type'].upper())


def page_footer(c, contract, t, pg, total):
    c.setStrokeColor(RULE); c.setLineWidth(0.5)
    c.line(LM, 0.52*inch, W - LM, 0.52*inch)
    c.setFont('Helvetica', 7); c.setFillColor(GREY)
    c.drawString(LM, 0.35*inch, contract['name'])
    c.drawRightString(W - LM, 0.35*inch, 'Page %d of %d' % (pg, total))
    c.setFont('Helvetica', 6); c.setFillColor(GREY2)
    c.drawCentredString(W/2, 0.2*inch, 'CONFIDENTIAL — FOR POLICYHOLDER USE ONLY — InsurLE Logic Engine')


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
    c.drawCentredString(W/2, y, '%s  ·  %s – %s' % (contract['type'], contract['effective_date'], contract['expiry_date']))
    y -= 0.38*inch

    # Meta grid
    boxes = [
        ('INSURER',        contract['insurer']),
        ('POLICY NUMBER',  contract['policy_number']),
        ('ANNUAL PREMIUM', contract['premium']),
        ('COVERAGE LIMIT', contract['coverage']),
        ('EFFECTIVE DATE', contract['effective_date']),
        ('EXPIRY DATE',    contract['expiry_date']),
        ('POLICY TYPE',    contract['type']),
        ('JURISDICTION',   'InsurLE Standard'),
    ]
    bw = TW / 4; bh = 0.64*inch
    for i, (lbl, val) in enumerate(boxes):
        col, row = i % 4, i // 4
        bx = LM + col*bw; by = y - row*(bh + 0.05*inch)
        c.setFillColor(L); c.roundRect(bx, by - bh, bw - 0.04*inch, bh, 4, fill=1, stroke=0)
        c.setFillColor(P if row == 0 else A)
        c.rect(bx, by - 0.14*inch, bw - 0.04*inch, 0.14*inch, fill=1, stroke=0)
        c.setFont('Helvetica-Bold', 6); c.setFillColor(WHITE)
        c.drawString(bx + 7, by - 0.095*inch, lbl)
        c.setFont('Helvetica-Bold', 9); c.setFillColor(INK)
        c.drawString(bx + 7, by - bh + 0.14*inch, str(val)[:28])
        c.setStrokeColor(RULE); c.setLineWidth(0.3)
        c.roundRect(bx, by - bh, bw - 0.04*inch, bh, 4, fill=0, stroke=1)
    y -= 2*(bh + 0.05*inch) + 0.22*inch

    # Intro box
    intro = ('This Insurance Contract is issued by %s under policy %s. '
             'It constitutes a binding agreement governing the terms and scope of %s coverage. '
             'All eligibility rules are formally encoded and verified by the InsurLE automated '
             'insurance logic engine.' % (contract['insurer'], contract['policy_number'], contract['type']))
    lines = wrap(intro, (TW - 0.28*inch) / (8.5 * 0.52))
    bh2 = len(lines)*13 + 0.22*inch
    c.setFillColor(CREAM2); c.roundRect(LM, y - bh2, TW, bh2, 5, fill=1, stroke=0)
    c.setStrokeColor(A); c.setLineWidth(3)
    c.line(LM, y - bh2, LM, y)
    ty = y - 0.13*inch
    for line in lines:
        c.setFont('Times-Italic', 8.5); c.setFillColor(INK2)
        c.drawString(LM + 14, ty, line); ty -= 13
    y -= bh2 + 0.22*inch

    # Divider + seal
    c.setStrokeColor(RULE); c.setLineWidth(0.5)
    c.line(LM, y, W - LM, y); y -= 0.12*inch
    cx2, cy_s = W/2, y - 0.65*inch
    c.setStrokeColor(A); c.setLineWidth(2.5)
    c.circle(cx2, cy_s, 0.57*inch, stroke=1, fill=0)
    c.setLineWidth(0.8); c.circle(cx2, cy_s, 0.49*inch, stroke=1, fill=0)
    c.setFont('Helvetica-Bold', 11); c.setFillColor(P)
    c.drawCentredString(cx2, cy_s + 0.12*inch, 'InsurLE')
    c.setFont('Helvetica', 8); c.setFillColor(GREY)
    c.drawCentredString(cx2, cy_s - 0.02*inch, 'Logic Engine')
    c.setFont('Courier-Bold', 7); c.setFillColor(A)
    c.drawCentredString(cx2, cy_s - 0.20*inch, 'VERIFIED CONTRACT')
    y -= 1.45*inch

    # Signature block
    c.setFillColor(CREAM2); c.roundRect(LM, y - 0.68*inch, TW, 0.72*inch, 4, fill=1, stroke=0)
    c.setStrokeColor(RULE); c.setLineWidth(0.5)
    c.rect(LM, y - 0.68*inch, TW, 0.72*inch, fill=0, stroke=1)
    sw3 = (TW - 0.2*inch) / 3
    for i, lbl in enumerate(['POLICYHOLDER SIGNATURE', 'DATE', 'INSURER AUTHORISATION']):
        sx2 = LM + 0.12*inch + i*(sw3 + 0.04*inch)
        c.setStrokeColor(INK2); c.setLineWidth(0.7)
        c.line(sx2, y - 0.3*inch, sx2 + sw3 - 0.1*inch, y - 0.3*inch)
        c.setFont('Helvetica', 6); c.setFillColor(GREY)
        c.drawString(sx2, y - 0.52*inch, lbl)


def draw_sections(c, contract, t, pg_start, total):
    P, A, L = t['P'], t['A'], t['L']
    pg = pg_start
    y  = H - 1.02*inch

    c.setFont('Helvetica-Bold', 15); c.setFillColor(P)
    c.drawString(LM, y, 'Terms & Conditions')
    y -= 0.1*inch
    c.setStrokeColor(A); c.setLineWidth(2)
    c.line(LM, y, LM + 3.0*inch, y); y -= 0.22*inch

    for sec in contract.get('contract_sections', []):
        sec_title = '%s — %s' % (sec.get('num', ''), sec.get('title', ''))
        body      = sec.get('text', '')
        chars     = (TW - 0.22*inch) / (8.5 * 0.52)
        body_lines = wrap(body, chars)
        needed    = 0.24*inch + len(body_lines)*12.5 + 0.14*inch

        if y - needed < 0.82*inch:
            page_footer(c, contract, t, pg, total)
            c.showPage(); pg += 1
            page_header(c, contract, t, pg)
            y = H - 1.02*inch

        c.setFillColor(P); c.rect(LM, y - 0.22*inch, TW, 0.22*inch, fill=1, stroke=0)
        c.setFillColor(A); c.rect(LM, y - 0.22*inch, 4, 0.22*inch, fill=1, stroke=0)
        c.setFont('Helvetica-Bold', 8); c.setFillColor(WHITE)
        c.drawString(LM + 10, y - 0.143*inch, sec_title[:85])
        y -= 0.22*inch

        bh = len(body_lines)*12.5 + 0.18*inch
        c.setFillColor(L); c.rect(LM, y - bh, TW, bh, fill=1, stroke=0)
        c.setFillColor(A); c.rect(LM, y - bh, 3, bh, fill=1, stroke=0)
        c.setStrokeColor(RULE); c.setLineWidth(0.35)
        c.rect(LM, y - bh, TW, bh, fill=0, stroke=1)
        ty = y - 0.1*inch
        for line in body_lines:
            c.setFont('Times-Roman', 8.5); c.setFillColor(INK2)
            c.drawString(LM + 12, ty, line); ty -= 12.5
        y -= bh + 0.08*inch

    return pg


def build_pdf(contract, out):
    c = canvas.Canvas(out, pagesize=letter)
    c.setTitle(contract['name'])
    c.setAuthor(contract['insurer'])
    t     = THEMES.get(contract['id'], THEMES['contract_auto'])
    total = 3

    page_header(c, contract, t, 1)
    draw_cover(c, contract, t)
    page_footer(c, contract, t, 1, total)
    c.showPage()

    page_header(c, contract, t, 2)
    pg = draw_sections(c, contract, t, 2, total)
    page_footer(c, contract, t, pg, total)
    c.showPage()

    c.save()
    print('  ✓  %s  (%d pages)' % (out, pg))


def main():
    data = json.load(open('insurle_data.json'))
    print('🖨  Generating contract PDFs…')
    import os; os.makedirs('contract_pdfs', exist_ok=True)
    for contract in data['contracts']:
        out = 'contract_pdfs/contract_%s.pdf' % contract['id'].replace('contract_', '')
        build_pdf(contract, out)
    print('\n✅  %d contract PDFs generated' % len(data['contracts']))


if __name__ == '__main__':
    main()