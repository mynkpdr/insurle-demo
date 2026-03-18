#!/usr/bin/env python3
"""
InsurLE — Claim PDF Generator
Produces one PDF per claim, each containing:
  Page 1 — Claim Cover         (status, summary, key facts grid)
  Page 2 — Formal Claim Form   (§1 claimant · §2 incident · §3 facts table · stamp)
  Page 3 — Validation Trace    (nested 3-level rule evaluation tree)
  Page 4 — Prolog Facts        (ground predicates in syntax-highlighted code block)

Usage:
    python3 make_claim_data.py               # reads insurle_data.json in CWD
    python3 make_claim_data.py path/to/data.json
"""

import json
import re
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
TW   = W - 1.10 * inch # text width

# ── Shared palette (matches make_data.py) ─────────────────────────────────────
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
PASS_C = colors.HexColor('#1A5A30')   # deep green for PASS
FAIL_C = colors.HexColor('#8B1A1A')   # deep red  for FAIL
PASS_L = colors.HexColor('#EBF5F0')   # light green tint
FAIL_L = colors.HexColor('#F8EDED')   # light red tint
PASS_M = colors.HexColor('#2E7D52')   # medium green
FAIL_M = colors.HexColor('#B03030')   # medium red

# ── Per-contract colour themes ─────────────────────────────────────────────────
THEMES = {
    'contract_auto':     {'P': colors.HexColor('#1A3A5C'), 'A': colors.HexColor('#E8B84B'), 'L': colors.HexColor('#EBF1F8')},
    'contract_health':   {'P': colors.HexColor('#1A4A3A'), 'A': colors.HexColor('#4ECB8D'), 'L': colors.HexColor('#EBF5F1')},
    'contract_travel':   {'P': colors.HexColor('#2A1A5C'), 'A': colors.HexColor('#A78BFA'), 'L': colors.HexColor('#F0EBF8')},
    'contract_accident': {'P': colors.HexColor('#4A1A1A'), 'A': colors.HexColor('#F87171'), 'L': colors.HexColor('#F8EBEB')},
}

# ── Contract metadata lookup (for self-contained generation) ──────────────────
CONTRACT_META = {
    'contract_auto':     {'insurer': 'AutoGuard Insurance Co.',    'policy_number': 'AG-VH-2024-001', 'type': 'Vehicle Insurance',  'name': 'AutoGuard Vehicle Insurance'},
    'contract_health':   {'insurer': 'VitalCare Health Group',     'policy_number': 'VC-HLT-2024-087','type': 'Health Insurance',    'name': 'VitalCare Health Insurance'},
    'contract_travel':   {'insurer': 'JetSafe Global Underwriters','policy_number': 'JS-TRV-2024-445','type': 'Travel Insurance',    'name': 'JetSafe Travel Insurance'},
    'contract_accident': {'insurer': 'ShieldPlus Casualty Ltd.',   'policy_number': 'SP-ACC-2024-209','type': 'Accident Insurance',  'name': 'ShieldPlus Personal Accident'},
}

# ── Nested validation trees (mirroring insurle_v2.html) ───────────────────────
VALIDATION_TREES = {
    'claim_auto_1': [
        {'label': 'Driver Fully Eligible', 'result': True, 'sub_checks': [
            {'rule': 'age_eligible/1',              'label': 'Minimum Age & Experience',     'result': True,  'leaves': [('Age ≥ 21', 'age(C, 34)', True, '34 ≥ 21 ✓')]},
            {'rule': 'license_compliant/1',         'label': 'Licence Validity & Jurisdiction','result': True,'leaves': [('Licence valid','license_valid(C, true)', True,'Active ✓'),('Not expired','license_expired(C, false)',True,'Not expired ✓'),('Jurisdiction recognised','license_jurisdiction(C, us_state)',True,'US state ✓')]},
            {'rule': 'driving_history_acceptable/1','label': 'Driving History Review',       'result': True,  'leaves': [('DUI conviction count','dui_history(C, 0)',True,'No DUI ✓')]},
        ]},
        {'label': 'Vehicle Authorization Valid', 'result': True, 'sub_checks': [
            {'rule': 'ownership_established/1','label': 'Ownership Chain Verification','result': True,'leaves': [('Owned by insured','vehicle_ownership(C, own)',True,'Confirmed ✓')]},
            {'rule': 'vehicle_type_covered/1', 'label': 'Class & Weight Check',        'result': True,'leaves': [('Passenger class','vehicle_class(C, passenger)',True,'Passenger ✓'),('Weight ≤ 3500 kg','vehicle_weight_kg(C, 1380)',True,'1380 ≤ 3500 ✓')]},
        ]},
        {'label': 'Incident Circumstances Covered', 'result': True, 'sub_checks': [
            {'rule': 'sober_at_incident/1',      'label': 'Sobriety Verification',  'result': True,'leaves': [('BAC ≤ 0.08','bac(C, 0.0)',True,'0.00 ≤ 0.08 ✓'),('No narcotics','under_influence_narcotics(C, false)',True,'Clear ✓')]},
            {'rule': 'geographic_scope_met/1',   'label': 'Geographic Coverage',    'result': True,'leaves': [('Continental US','incident_location(C, continental_us)',True,'In zone ✓')]},
            {'rule': 'not_excluded_activity/1',  'label': 'Activity Exclusions',    'result': True,'leaves': [('No excluded activity','activity(C, normal_driving)',True,'Normal driving ✓')]},
        ]},
        {'label': 'Claim Procedure Followed', 'result': True, 'sub_checks': [
            {'rule': 'reported_in_time/1',  'label': 'Reporting Timeline',        'result': True,'leaves': [('Reported ≤ 30 days','days_since_incident(C, 5)',True,'5 ≤ 30 ✓')]},
            {'rule': 'police_report_filed/1','label': 'Police Report Verification','result': True,'leaves': [('Report on file','police_report(C, true)',True,'Filed ✓')]},
            {'rule': 'no_fraud/1',          'label': 'Fraud Indicator Screening', 'result': True,'leaves': [('No fraud flags','fraud_indicator(C, false)',True,'Clean ✓')]},
        ]},
    ],
    'claim_auto_2': [
        {'label': 'Driver Fully Eligible', 'result': True, 'sub_checks': [
            {'rule': 'age_eligible/1',              'label': 'Minimum Age & Experience',     'result': True, 'leaves': [('Age ≥ 21','age(C, 28)',True,'28 ≥ 21 ✓')]},
            {'rule': 'license_compliant/1',         'label': 'Licence Validity & Jurisdiction','result': True,'leaves': [('Licence valid','license_valid(C, true)',True,'Active ✓'),('Not expired','license_expired(C, false)',True,'Not expired ✓'),('Jurisdiction','license_jurisdiction(C, us_state)',True,'US state ✓')]},
            {'rule': 'driving_history_acceptable/1','label': 'Driving History Review',       'result': True, 'leaves': [('DUI count','dui_history(C, 0)',True,'No DUI ✓')]},
        ]},
        {'label': 'Vehicle Authorization Valid', 'result': True, 'sub_checks': [
            {'rule': 'ownership_established/1','label': 'Ownership Verification','result': True,'leaves': [('Owned by insured','vehicle_ownership(C, own)',True,'Confirmed ✓')]},
            {'rule': 'vehicle_type_covered/1', 'label': 'Class & Weight',        'result': True,'leaves': [('Passenger class','vehicle_class(C, passenger)',True,'Passenger ✓'),('Weight ≤ 3500 kg','vehicle_weight_kg(C, 1420)',True,'1420 ≤ 3500 ✓')]},
        ]},
        {'label': 'Incident Circumstances Covered', 'result': False, 'sub_checks': [
            {'rule': 'sober_at_incident/1',    'label': 'Sobriety Verification', 'result': False,'leaves': [('BAC ≤ 0.08 g/dL','bac(C, 0.14)',False,'0.14 > 0.08 — VIOLATION ✗'),('No narcotics','under_influence_narcotics(C, false)',True,'Negative ✓')]},
            {'rule': 'geographic_scope_met/1', 'label': 'Geographic Coverage',   'result': True, 'leaves': [('Continental US','incident_location(C, continental_us)',True,'In zone ✓')]},
            {'rule': 'not_excluded_activity/1','label': 'Activity Exclusions',   'result': True, 'leaves': [('No excluded activity','activity(C, normal_driving)',True,'Normal driving ✓')]},
        ]},
        {'label': 'Claim Procedure Followed', 'result': True, 'sub_checks': [
            {'rule': 'reported_in_time/1',   'label': 'Reporting Timeline',  'result': True,'leaves': [('Reported ≤ 30 days','days_since_incident(C, 2)',True,'2 ≤ 30 ✓')]},
            {'rule': 'police_report_filed/1','label': 'Police Report',       'result': True,'leaves': [('Report on file','police_report(C, true)',True,'Filed ✓')]},
            {'rule': 'no_fraud/1',           'label': 'Fraud Screening',     'result': True,'leaves': [('No flags','fraud_indicator(C, false)',True,'Clean ✓')]},
        ]},
    ],
    'claim_health_1': [
        {'label': 'Enrollment Requirements Met', 'result': True, 'sub_checks': [
            {'rule': 'continuous_enrollment_satisfied/1','label': 'Continuous Enrollment Check','result': True,'leaves': [('Emergency override?','is_emergency(C, true)',True,'Emergency waives 90-day wait ✓')]},
            {'rule': 'pre_existing_waiting_satisfied/1', 'label': 'Pre-existing Condition Wait','result': True,'leaves': [('Pre-existing present?','pre_existing_condition(C, false)',True,'No pre-existing ✓')]},
        ]},
        {'label': 'Coverage Applicable', 'result': True, 'sub_checks': [
            {'rule': 'provider_network_compliant/1',    'label': 'Provider Network Status',   'result': True,'leaves': [('In-network provider','provider_network(C, in_network)',True,'In-network 100% ✓')]},
            {'rule': 'authorization_obtained_if_needed/1','label': 'Prior Authorization Gate','result': True,'leaves': [('Emergency bypasses auth','is_emergency(C, true)',True,'Emergency override ✓')]},
            {'rule': 'not_cosmetic_only/1',             'label': 'Medical Necessity Check',   'result': True,'leaves': [('Not purely cosmetic','cosmetic_only(C, false)',True,'Medical procedure ✓')]},
        ]},
        {'label': 'Financial Limits Satisfied', 'result': True, 'sub_checks': [
            {'rule': 'deductible_status_ok/1',  'label': 'Annual Deductible Status','result': True,'leaves': [('Emergency bypasses deductible','is_emergency(C, true)',True,'Deductible waived ✓')]},
            {'rule': 'within_lifetime_max/1',   'label': 'Lifetime Maximum Check',  'result': True,'leaves': [('Cumulative ≤ $500,000','cumulative_claims(C, 22400)',True,'$22,400 ≤ $500,000 ✓')]},
        ]},
        {'label': 'Timely Submission', 'result': True, 'sub_checks': [
            {'rule': 'timely_submission/1','label': '180-Day Submission Deadline','result': True,'leaves': [('Filed within 180 days','days_since_service(C, 2)',True,'2 ≤ 180 ✓')]},
        ]},
    ],
    'claim_health_2': [
        {'label': 'Enrollment Requirements Met', 'result': False, 'sub_checks': [
            {'rule': 'continuous_enrollment_satisfied/1','label': 'Continuous Enrollment Check','result': False,'leaves': [('Emergency override?','is_emergency(C, false)',False,'Not emergency ✗'),('Enrolled ≥ 90 days?','days_enrolled(C, 45)',False,'45 < 90 days — VIOLATION ✗')]},
            {'rule': 'pre_existing_waiting_satisfied/1', 'label': 'Pre-existing Condition Wait','result': False,'leaves': [('Pre-existing present?','pre_existing_condition(C, true)',False,'Pre-existing detected ✗'),('Waiting ≥ 12 months?','months_since_enrollment(C, 1.5)',False,'1.5 < 12 months — VIOLATION ✗')]},
        ]},
        {'label': 'Coverage Applicable', 'result': False, 'sub_checks': [
            {'rule': 'provider_network_compliant/1',     'label': 'Provider Network',        'result': True, 'leaves': [('In-network','provider_network(C, in_network)',True,'In-network ✓')]},
            {'rule': 'authorization_obtained_if_needed/1','label': 'Prior Authorization Gate','result': False,'leaves': [('Emergency?','is_emergency(C, false)',False,'Not emergency ✗'),('Amount ≤ $5,000?','claim_amount(C, 35000)',False,'$35,000 > $5,000 ✗'),('Prior auth obtained?','prior_authorization(C, false)',False,'No auth — VIOLATION ✗')]},
            {'rule': 'not_cosmetic_only/1',              'label': 'Medical Necessity',        'result': True, 'leaves': [('Not cosmetic','cosmetic_only(C, false)',True,'Medical ✓')]},
        ]},
        {'label': 'Financial Limits Satisfied', 'result': True, 'sub_checks': [
            {'rule': 'deductible_status_ok/1','label': 'Annual Deductible','result': True,'leaves': [('Deductible met','annual_deductible_met(C, true)',True,'Satisfied ✓')]},
            {'rule': 'within_lifetime_max/1', 'label': 'Lifetime Maximum', 'result': True,'leaves': [('Within $500k','cumulative_claims(C, 35000)',True,'$35,000 ≤ $500,000 ✓')]},
        ]},
        {'label': 'Timely Submission', 'result': True, 'sub_checks': [
            {'rule': 'timely_submission/1','label': 'Submission Deadline','result': True,'leaves': [('Filed ≤ 180 days','days_since_service(C, 5)',True,'5 ≤ 180 ✓')]},
        ]},
    ],
    'claim_travel_1': [
        {'label': 'Policy Validity Confirmed', 'result': True, 'sub_checks': [
            {'rule': 'purchased_within_window/1',      'label': 'Purchase Window Compliance','result': True,'leaves': [('Purchased ≤ 21 days after deposit','days_after_deposit(C, 10)',True,'10 ≤ 21 days ✓')]},
            {'rule': 'trip_not_already_commenced/1',   'label': 'Trip Status at Purchase',  'result': True,'leaves': [('Pre-departure purchase','trip_commenced_at_purchase(C, false)',True,'Pre-departure ✓')]},
            {'rule': 'policy_status_active/1',         'label': 'Policy Active Status',     'result': True,'leaves': [('No lapse','policy_lapse(C, false)',True,'Active ✓'),('Premium paid','premium_paid(C, true)',True,'Current ✓')]},
        ]},
        {'label': 'Covered Event Occurred', 'result': True, 'sub_checks': [
            {'rule': 'valid_cancellation_reason/1','label': 'Cancellation Reason Verification','result': True,'leaves': [('Claim type is cancellation','claim_type(C, trip_cancellation)',True,'Cancellation ✓'),('Reason is in covered list','cancellation_reason(C, illness)',True,'Illness is covered ✓')]},
        ]},
        {'label': 'Risk Profile Eligible', 'result': True, 'sub_checks': [
            {'rule': 'medically_fit_at_purchase/1','label': 'Medical Fitness at Purchase','result': True,'leaves': [('Fit at purchase','fit_at_purchase(C, true)',True,'No known conditions ✓')]},
            {'rule': 'destination_covered/1',      'label': 'Destination Advisory Check', 'result': True,'leaves': [('Advisory level < 4','destination_advisory_level(C, 1)',True,'Level 1 ✓')]},
            {'rule': 'activity_covered/1',         'label': 'Activity Coverage',          'result': True,'leaves': [('No extreme sport','activity(C, none)',True,'No activity ✓')]},
        ]},
        {'label': 'Documentation Complete', 'result': True, 'sub_checks': [
            {'rule': 'timely_notification/1','label': 'Notification Timing',   'result': True,'leaves': [('Not baggage — 24h N/A','claim_type(C, trip_cancellation)',True,'N/A for cancellation ✓')]},
            {'rule': 'documents_provided/1', 'label': 'Documentation',         'result': True,'leaves': [('All docs submitted','documentation_provided(C, true)',True,'On file ✓')]},
            {'rule': 'exclusions_clear/1',   'label': 'Exclusion Screening',   'result': True,'leaves': [('Not under influence','under_influence(C, false)',True,'Sober ✓'),('Not war-related','war_related(C, false)',True,'No war ✓')]},
        ]},
    ],
    'claim_travel_2': [
        {'label': 'Policy Validity Confirmed', 'result': True, 'sub_checks': [
            {'rule': 'purchased_within_window/1',    'label': 'Purchase Window', 'result': True,'leaves': [('Purchased ≤ 21 days','days_after_deposit(C, 5)',True,'5 ≤ 21 ✓')]},
            {'rule': 'trip_not_already_commenced/1', 'label': 'Trip Status',     'result': True,'leaves': [('Pre-departure','trip_commenced_at_purchase(C, false)',True,'Pre-departure ✓')]},
            {'rule': 'policy_status_active/1',       'label': 'Active Status',   'result': True,'leaves': [('No lapse','policy_lapse(C, false)',True,'Active ✓'),('Premium paid','premium_paid(C, true)',True,'Paid ✓')]},
        ]},
        {'label': 'Covered Event Occurred', 'result': True, 'sub_checks': [
            {'rule': 'medical_event_covered/1','label': 'Medical Event Verification','result': True,'leaves': [('Medical claim type','claim_type(C, medical)',True,'Medical ✓'),('Emergency confirmed','medical_emergency(C, true)',True,'Emergency ✓')]},
        ]},
        {'label': 'Risk Profile Eligible', 'result': False, 'sub_checks': [
            {'rule': 'medically_fit_at_purchase/1','label': 'Medical Fitness',       'result': True, 'leaves': [('Fit at purchase','fit_at_purchase(C, true)',True,'No conditions ✓')]},
            {'rule': 'destination_covered/1',      'label': 'Destination Advisory',  'result': True, 'leaves': [('Advisory level < 4','destination_advisory_level(C, 1)',True,'Level 1 ✓')]},
            {'rule': 'activity_covered/1',         'label': 'Activity Coverage Check','result': False,'leaves': [('Activity is extreme sport?','activity(C, base_jumping)',False,'BASE jumping — EXCLUDED ✗'),('Adventure Rider purchased?','adventure_rider(C, false)',False,'No Rider — VIOLATION ✗')]},
        ]},
        {'label': 'Documentation Complete', 'result': True, 'sub_checks': [
            {'rule': 'documents_provided/1','label': 'Documentation',       'result': True,'leaves': [('Docs submitted','documentation_provided(C, true)',True,'On file ✓')]},
            {'rule': 'exclusions_clear/1',  'label': 'Exclusion Screening', 'result': True,'leaves': [('Not under influence','under_influence(C, false)',True,'Sober ✓'),('Not war-related','war_related(C, false)',True,'No war ✓')]},
        ]},
    ],
    'claim_accident_1': [
        {'label': 'Accidental Origin Confirmed', 'result': True, 'sub_checks': [
            {'rule': 'cause_is_accidental/1',  'label': 'Accident Type Classification','result': True,'leaves': [('Recognised accident type','accident_type(C, workplace_accident)',True,'Workplace accident covered ✓')]},
            {'rule': 'not_self_inflicted/1',   'label': 'Self-Infliction Exclusion',   'result': True,'leaves': [('Not self-inflicted','self_inflicted(C, false)',True,'External cause ✓')]},
            {'rule': 'not_excluded_cause/1',   'label': 'Cause Exclusion Screening',   'result': True,'leaves': [('Cause not excluded','cause(C, workplace_accident)',True,'Not in exclusion list ✓')]},
        ]},
        {'label': 'Claimant Fully Eligible', 'result': True, 'sub_checks': [
            {'rule': 'age_in_range/1',          'label': 'Age Band Verification',       'result': True,'leaves': [('Age ≥ 18','age(C, 38)',True,'38 ≥ 18 ✓'),('Age ≤ 70','age(C, 38)',True,'38 ≤ 70 ✓')]},
            {'rule': 'intoxication_negative/1', 'label': 'Substance Exclusion Check',  'result': True,'leaves': [('Not intoxicated','intoxicated(C, false)',True,'Sober ✓'),('No narcotics','narcotics_influence(C, false)',True,'Clean ✓')]},
            {'rule': 'not_professional_sport/1','label': 'Professional Sport Exclusion','result': True,'leaves': [('Not professional sport','activity(C, construction_work)',True,'Construction — not excluded ✓')]},
        ]},
        {'label': 'Medical Criteria Met', 'result': True, 'sub_checks': [
            {'rule': 'medical_evidence_provided/1','label': 'Medical Evidence Sufficiency','result': True,'leaves': [('Medical evidence provided','medical_evidence(C, true)',True,'Records submitted ✓')]},
            {'rule': 'licensed_provider_confirms/1','label': 'Provider Licensing Check',  'result': True,'leaves': [('Physician licensed','attending_physician_licensed(C, true)',True,'Verified ✓')]},
            {'rule': 'injury_consistent_with_claim/1','label': 'Injury-Claim Consistency','result': True,'leaves': [('Severity matches claim type','injury_severity(C, major)',True,'Major injury — disability consistent ✓')]},
        ]},
        {'label': 'Procedure Compliant', 'result': True, 'sub_checks': [
            {'rule': 'notification_in_time/1',  'label': 'Notification Timeline',  'result': True,'leaves': [('Disability notify ≤ 14 days','days_to_notify(C, 4)',True,'4 ≤ 14 ✓')]},
            {'rule': 'benefit_type_valid/1',    'label': 'Benefit Type Validation', 'result': True,'leaves': [('Benefit type is covered','claim_type(C, disability)',True,'Disability benefit valid ✓')]},
            {'rule': 'within_benefit_limits/1', 'label': 'Benefit Limit Check',    'result': True,'leaves': [('Claim ≤ $250,000','claim_amount_usd(C, 18000)',True,'$18,000 ≤ $250,000 ✓')]},
        ]},
    ],
    'claim_accident_2': [
        {'label': 'Accidental Origin Confirmed', 'result': False, 'sub_checks': [
            {'rule': 'cause_is_accidental/1','label': 'Accident Type Classification','result': True, 'leaves': [('Recognised accident type','accident_type(C, collision)',True,'Collision ✓')]},
            {'rule': 'not_self_inflicted/1', 'label': 'Self-Infliction Exclusion',  'result': True, 'leaves': [('Not self-inflicted','self_inflicted(C, false)',True,'External cause ✓')]},
            {'rule': 'not_excluded_cause/1', 'label': 'Cause Exclusion Screening',  'result': False,'leaves': [('Cause not in exclusion list','cause(C, professional_sports)',False,'Professional sports — EXCLUDED ✗')]},
        ]},
        {'label': 'Claimant Fully Eligible', 'result': False, 'sub_checks': [
            {'rule': 'age_in_range/1',          'label': 'Age Band Verification',       'result': True, 'leaves': [('Age ≥ 18','age(C, 26)',True,'26 ≥ 18 ✓'),('Age ≤ 70','age(C, 26)',True,'26 ≤ 70 ✓')]},
            {'rule': 'intoxication_negative/1', 'label': 'Substance Exclusion Check',  'result': True, 'leaves': [('Not intoxicated','intoxicated(C, false)',True,'Sober ✓'),('No narcotics','narcotics_influence(C, false)',True,'Clean ✓')]},
            {'rule': 'not_professional_sport/1','label': 'Professional Sport Exclusion','result': False,'leaves': [('Not professional sport?','activity(C, professional_sports)',False,'Paid rugby — EXCLUDED ✗')]},
        ]},
        {'label': 'Medical Criteria Met', 'result': True, 'sub_checks': [
            {'rule': 'medical_evidence_provided/1',  'label': 'Medical Evidence',          'result': True,'leaves': [('Evidence provided','medical_evidence(C, true)',True,'Records on file ✓')]},
            {'rule': 'licensed_provider_confirms/1', 'label': 'Provider Licensing',        'result': True,'leaves': [('Licensed physician','attending_physician_licensed(C, true)',True,'Verified ✓')]},
            {'rule': 'injury_consistent_with_claim/1','label': 'Injury-Claim Consistency', 'result': True,'leaves': [('Moderate + disability','injury_severity(C, moderate)',True,'Consistent ✓')]},
        ]},
        {'label': 'Procedure Compliant', 'result': False, 'sub_checks': [
            {'rule': 'notification_in_time/1', 'label': 'Notification Timeline',  'result': False,'leaves': [('Disability notify ≤ 14 days','days_to_notify(C, 35)',False,'35 > 14 days — VIOLATION ✗')]},
            {'rule': 'benefit_type_valid/1',   'label': 'Benefit Type Validation', 'result': True, 'leaves': [('Covered benefit type','claim_type(C, disability)',True,'Disability ✓')]},
            {'rule': 'within_benefit_limits/1','label': 'Benefit Limit Check',    'result': True, 'leaves': [('Amount ≤ $250,000','claim_amount_usd(C, 9500)',True,'$9,500 ≤ $250,000 ✓')]},
        ]},
    ],
}

# ── Helpers ────────────────────────────────────────────────────────────────────
def wrap(text, chars):
    return textwrap.wrap(str(text), max(18, int(chars))) or ['']


# ── Shared header / footer ─────────────────────────────────────────────────────
def page_header(c, contract, claim, t, pg):
    P, A = t['P'], t['A']
    # Primary band
    c.setFillColor(P);  c.rect(0, H - 0.72*inch, W, 0.72*inch, fill=1, stroke=0)
    c.setFillColor(A);  c.rect(0, H - 0.78*inch, W, 0.06*inch, fill=1, stroke=0)
    # Left accent bar
    c.setFillColor(A);  c.rect(0, 0, 4, H, fill=1, stroke=0)
    # Insurer
    c.setFont('Helvetica-Bold', 11); c.setFillColor(WHITE)
    c.drawString(LM, H - 0.44*inch, contract['insurer'])
    # Claim ref
    c.setFont('Courier-Bold', 8); c.setFillColor(A)
    c.drawRightString(W - 0.5*inch, H - 0.44*inch, claim['id'].upper())
    # Claimant + type
    c.setFont('Helvetica', 7); c.setFillColor(colors.Color(1,1,1,alpha=0.55))
    c.drawString(LM, H - 0.62*inch, claim['claimant'])
    c.drawRightString(W - 0.5*inch, H - 0.62*inch, contract['type'].upper() + '  ·  CLAIM DOCUMENT')


def page_footer(c, contract, claim, t, pg, total):
    c.setStrokeColor(RULE); c.setLineWidth(0.5)
    c.line(LM, 0.52*inch, W - LM, 0.52*inch)
    c.setFont('Helvetica', 7); c.setFillColor(GREY)
    c.drawString(LM, 0.35*inch, '%s  ·  Claim %s' % (contract['name'], claim['id'].upper()))
    c.drawRightString(W - LM, 0.35*inch, 'Page %d of %d' % (pg, total))
    c.setFont('Helvetica', 6); c.setFillColor(GREY2)
    c.drawCentredString(W/2, 0.20*inch,
        'CONFIDENTIAL — FOR CLAIMS PROCESSING USE ONLY — InsurLE Logic Engine')


# ── Page 1: Claim Cover ────────────────────────────────────────────────────────
def draw_cover(c, claim, contract, t):
    P, A, L = t['P'], t['A'], t['L']
    is_v     = claim['expected'] == 'VALID'
    STAMP_C  = PASS_C if is_v else FAIL_C
    STAMP_L  = PASS_L if is_v else FAIL_L
    RESULT_C = PASS_M if is_v else FAIL_M

    y = H - 1.05*inch

    # ── Claim title ──
    c.setFont('Helvetica-Bold', 22); c.setFillColor(P)
    c.drawCentredString(W/2, y, 'INSURANCE CLAIM REPORT')
    y -= 0.26*inch
    c.setStrokeColor(A); c.setLineWidth(2)
    c.line(W/2 - 2.0*inch, y, W/2 + 2.0*inch, y)
    y -= 0.18*inch
    c.setFont('Helvetica', 9.5); c.setFillColor(GREY)
    c.drawCentredString(W/2, y,
        '%s  ·  %s  ·  %s' % (contract['type'], contract['insurer'], claim['date']))
    y -= 0.40*inch

    # ── 6-cell meta grid ──
    cells = [
        ('CLAIMANT',        claim['claimant']),
        ('CLAIM REFERENCE', claim['id'].upper()),
        ('DATE OF CLAIM',   claim['date']),
        ('INCIDENT DATE',   claim['incident_date']),
        ('AMOUNT CLAIMED',  claim['amount']),
        ('POLICY NUMBER',   contract['policy_number']),
    ]
    bw = TW / 3;  bh = 0.65*inch
    for i, (lbl, val) in enumerate(cells):
        col = i % 3;  row = i // 3
        bx = LM + col * bw
        by = y - row * (bh + 0.05*inch)
        c.setFillColor(L); c.roundRect(bx, by - bh, bw - 0.04*inch, bh, 4, fill=1, stroke=0)
        bar_c = P if row == 0 else A
        c.setFillColor(bar_c); c.rect(bx, by - 0.14*inch, bw - 0.04*inch, 0.14*inch, fill=1, stroke=0)
        c.setFont('Helvetica-Bold', 6); c.setFillColor(WHITE)
        c.drawString(bx + 7, by - 0.095*inch, lbl)
        is_amount = lbl == 'AMOUNT CLAIMED'
        c.setFont('Helvetica-Bold', 11 if is_amount else 9); c.setFillColor(P if is_amount else INK)
        c.drawString(bx + 7, by - bh + 0.15*inch, str(val)[:26])
        c.setStrokeColor(RULE); c.setLineWidth(0.3)
        c.roundRect(bx, by - bh, bw - 0.04*inch, bh, 4, fill=0, stroke=1)
    y -= 2 * (bh + 0.05*inch) + 0.25*inch

    # ── Verdict banner ──
    bh2 = 0.78*inch
    c.setFillColor(STAMP_L); c.roundRect(LM, y - bh2, TW, bh2, 6, fill=1, stroke=0)
    c.setStrokeColor(STAMP_C); c.setLineWidth(2)
    c.roundRect(LM, y - bh2, TW, bh2, 6, fill=0, stroke=1)
    # Left thick accent
    c.setFillColor(STAMP_C); c.rect(LM, y - bh2, 6, bh2, fill=1, stroke=0)
    # Result text
    verdict_label = 'CLAIM APPROVED — VALID' if is_v else 'CLAIM REJECTED — INVALID'
    c.setFont('Helvetica-Bold', 16); c.setFillColor(RESULT_C)
    c.drawCentredString(W/2, y - 0.30*inch, verdict_label)
    tree = VALIDATION_TREES.get(claim['id'], [])
    passed = sum(1 for b in tree if b['result'])
    total_b = len(tree)
    sub_text = ('All %d evaluation branches resolved successfully.' % total_b) if is_v else \
               ('%d of %d branches failed predicate resolution.' % (total_b - passed, total_b))
    c.setFont('Helvetica', 8.5); c.setFillColor(INK2)
    c.drawCentredString(W/2, y - 0.52*inch, sub_text)
    y -= bh2 + 0.22*inch

    # ── Incident description box ──
    chars = (TW - 0.28*inch) / (8.5 * 0.52)
    dlines = wrap(claim.get('description', ''), chars)
    dh = len(dlines) * 13 + 0.22*inch
    c.setFillColor(CREAM2); c.roundRect(LM, y - dh, TW, dh, 5, fill=1, stroke=0)
    c.setStrokeColor(A); c.setLineWidth(3)
    c.line(LM, y - dh, LM, y)
    c.setStrokeColor(RULE); c.setLineWidth(0.3)
    c.roundRect(LM, y - dh, TW, dh, 5, fill=0, stroke=1)
    # Label
    c.setFont('Helvetica-Bold', 7); c.setFillColor(P)
    c.drawString(LM + 10, y - 0.12*inch, 'INCIDENT SUMMARY')
    ty = y - 0.26*inch
    for dl in dlines:
        c.setFont('Times-Italic', 8.5); c.setFillColor(INK2)
        c.drawString(LM + 10, ty, dl); ty -= 13
    y -= dh + 0.22*inch

    # ── Circular stamp ──
    sc_x, sc_y = W - 1.15*inch, H - 1.62*inch
    c.saveState(); c.translate(sc_x, sc_y); c.rotate(-18)
    c.setStrokeColor(STAMP_C); c.setLineWidth(2.5)
    c.circle(0, 0, 0.62*inch, stroke=1, fill=0)
    c.setLineWidth(1); c.circle(0, 0, 0.53*inch, stroke=1, fill=0)
    c.setFont('Helvetica-Bold', 9); c.setFillColor(STAMP_C)
    c.drawCentredString(0,  0.13*inch, 'APPROVED' if is_v else 'REJECTED')
    c.setFont('Helvetica', 7)
    c.drawCentredString(0, -0.04*inch, 'FOR PROCESSING' if is_v else 'REVIEW REQUIRED')
    c.setFont('Courier-Bold', 6); c.drawCentredString(0, -0.24*inch, 'INSURLE ENGINE')
    c.restoreState()

    # ── Signature block ──
    if y > 1.55*inch:
        sy = max(y, 1.55*inch)
        c.setFillColor(CREAM2); c.roundRect(LM, sy - 0.68*inch, TW, 0.70*inch, 4, fill=1, stroke=0)
        c.setStrokeColor(RULE); c.setLineWidth(0.4)
        c.rect(LM, sy - 0.68*inch, TW, 0.70*inch, fill=0, stroke=1)
        sw3 = (TW - 0.2*inch) / 3
        for i, lbl in enumerate(['CLAIMANT SIGNATURE', 'DATE', 'CLAIMS HANDLER']):
            sx2 = LM + 0.12*inch + i * (sw3 + 0.04*inch)
            c.setStrokeColor(INK2); c.setLineWidth(0.7)
            c.line(sx2, sy - 0.28*inch, sx2 + sw3 - 0.1*inch, sy - 0.28*inch)
            c.setFont('Helvetica', 6); c.setFillColor(GREY)
            c.drawString(sx2, sy - 0.50*inch, lbl)


# ── Page 2: Formal Claim Form ──────────────────────────────────────────────────
def draw_claim_form(c, claim, contract, t):
    """Identical to draw_claim() in make_data.py, kept as standalone function."""
    P, A, L = t['P'], t['A'], t['L']
    is_v    = claim['expected'] == 'VALID'
    STAMP_C = PASS_C if is_v else FAIL_C
    y = H - 1.02*inch

    # Title
    c.setFont('Helvetica-Bold', 16); c.setFillColor(P)
    c.drawString(LM, y, 'INSURANCE CLAIM FORM')
    c.setFont('Helvetica', 9); c.setFillColor(GREY)
    c.drawRightString(W - LM, y, '%s  ·  %s' % (contract['policy_number'], contract['type']))
    y -= 0.10*inch; c.setStrokeColor(A); c.setLineWidth(2)
    c.line(LM, y, LM + 3.2*inch, y); y -= 0.22*inch

    def field_row(fields, bg, rh=0.52*inch):
        nonlocal y
        fw_sum = sum(f[2] for f in fields)
        c.setFillColor(bg); c.rect(LM, y - rh, TW, rh, fill=1, stroke=0)
        c.setStrokeColor(RULE); c.setLineWidth(0.3)
        c.rect(LM, y - rh, TW, rh, fill=0, stroke=1)
        fx = LM
        for lbl, val, parts in fields:
            fw = (parts / fw_sum) * TW
            c.setFont('Helvetica', 6); c.setFillColor(GREY)
            c.drawString(fx + 8, y - 0.13*inch, lbl.upper())
            if lbl == 'Amount Requested':   valc = P
            elif lbl == 'Expected Outcome': valc = PASS_M if is_v else FAIL_M
            else:                           valc = INK
            fsz = 12 if lbl == 'Amount Requested' else 10
            c.setFont('Helvetica-Bold', fsz); c.setFillColor(valc)
            c.drawString(fx + 8, y - 0.36*inch, str(val)[:30])
            c.setStrokeColor(RULE)
            c.line(fx + fw, y - rh, fx + fw, y)
            fx += fw
        y -= rh

    # § 1 — Claimant Information
    c.setFillColor(P); c.rect(LM, y - 0.22*inch, TW, 0.22*inch, fill=1, stroke=0)
    c.setFillColor(A); c.rect(LM, y - 0.22*inch, 4, 0.22*inch, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 8); c.setFillColor(WHITE)
    c.drawString(LM + 10, y - 0.143*inch, '\xa7 1  CLAIMANT INFORMATION')
    y -= 0.22*inch
    field_row([('Full Name', claim['claimant'], 2.0),
               ('Claim Reference ID', claim['id'].upper(), 1.5),
               ('Claim Date', claim['date'], 1.1)], L)
    field_row([('Incident Date', claim['incident_date'], 1.1),
               ('Amount Requested', claim['amount'], 1.1),
               ('Expected Outcome', claim['expected'], 1.0),
               ('Policy Number', contract['policy_number'], 1.3)], CREAM)
    y -= 0.10*inch

    # § 2 — Incident Description
    c.setFillColor(P); c.rect(LM, y - 0.22*inch, TW, 0.22*inch, fill=1, stroke=0)
    c.setFillColor(A); c.rect(LM, y - 0.22*inch, 4, 0.22*inch, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 8); c.setFillColor(WHITE)
    c.drawString(LM + 10, y - 0.143*inch, '\xa7 2  INCIDENT DESCRIPTION')
    y -= 0.22*inch
    chars = (TW - 0.30*inch) / (8.5 * 0.52)
    dlines = wrap(claim.get('description', ''), chars)
    dh = len(dlines) * 13 + 0.22*inch
    c.setFillColor(L); c.rect(LM, y - dh, TW, dh, fill=1, stroke=0)
    c.setStrokeColor(A); c.setLineWidth(2.5); c.line(LM, y - dh, LM, y)
    c.setStrokeColor(RULE); c.setLineWidth(0.3)
    c.rect(LM, y - dh, TW, dh, fill=0, stroke=1)
    ty = y - 0.10*inch
    for dl in dlines:
        c.setFont('Times-Italic', 8.5); c.setFillColor(INK2)
        c.drawString(LM + 12, ty, dl); ty -= 13
    y -= dh + 0.10*inch

    # § 3 — Facts table
    c.setFillColor(P); c.rect(LM, y - 0.22*inch, TW, 0.22*inch, fill=1, stroke=0)
    c.setFillColor(A); c.rect(LM, y - 0.22*inch, 4, 0.22*inch, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 8); c.setFillColor(WHITE)
    c.drawString(LM + 10, y - 0.143*inch, '\xa7 3  CLAIM FACTS  (InsurLE Ground Predicates)')
    y -= 0.22*inch

    hh = 0.20*inch
    c.setFillColor(CREAM2); c.rect(LM, y - hh, TW, hh, fill=1, stroke=0)
    c.setStrokeColor(RULE); c.setLineWidth(0.3)
    c.rect(LM, y - hh, TW, hh, fill=0, stroke=1)
    c.setFont('Helvetica-Bold', 7); c.setFillColor(P)
    c.drawString(LM + 8, y - 0.135*inch, 'PREDICATE')
    c.drawString(LM + TW*0.52, y - 0.135*inch, 'VALUE')
    c.drawString(LM + TW*0.74, y - 0.135*inch, 'TYPE')
    c.line(LM + TW*0.52, y - hh, LM + TW*0.52, y)
    c.line(LM + TW*0.74, y - hh, LM + TW*0.74, y)
    y -= hh

    RH = 0.21*inch
    for i, (k, v) in enumerate(claim.get('facts', {}).items()):
        if y - RH < 1.30*inch: break
        if v is True:           vs, vc, vt = 'True',  PASS_M, 'boolean'
        elif v is False:        vs, vc, vt = 'False', FAIL_M, 'boolean'
        elif v is None:         vs, vc, vt = 'N/A',   GREY,   'null'
        elif isinstance(v, float): vs, vc, vt = str(v), colors.HexColor('#1A3A6A'), 'float'
        elif isinstance(v, int):   vs, vc, vt = str(v), colors.HexColor('#1A3A6A'), 'integer'
        else:                   vs, vc, vt = str(v)[:28], INK2, 'atom'
        bg = CREAM if i % 2 == 0 else L
        c.setFillColor(bg); c.rect(LM, y - RH, TW, RH, fill=1, stroke=0)
        c.setStrokeColor(RULE); c.setLineWidth(0.2)
        c.line(LM, y - RH, LM + TW, y - RH)
        c.line(LM + TW*0.52, y - RH, LM + TW*0.52, y)
        c.line(LM + TW*0.74, y - RH, LM + TW*0.74, y)
        c.setFont('Courier', 7.5); c.setFillColor(INK2)
        c.drawString(LM + 8, y - 0.145*inch, '%s(%s, …)' % (k, claim['id'][:14]))
        c.setFont('Helvetica-Bold', 8); c.setFillColor(vc)
        c.drawString(LM + TW*0.52 + 6, y - 0.145*inch, vs)
        c.setFont('Courier', 6.5); c.setFillColor(GREY2)
        c.drawString(LM + TW*0.74 + 6, y - 0.145*inch, vt)
        y -= RH

    c.setStrokeColor(RULE); c.setLineWidth(0.4)
    c.rect(LM, y, TW, (H - 1.5*inch) - y, fill=0, stroke=1)

    # Rotated stamp
    sc_x, sc_y = W - 1.15*inch, H - 1.62*inch
    c.saveState(); c.translate(sc_x, sc_y); c.rotate(-18)
    c.setStrokeColor(STAMP_C); c.setLineWidth(2.5)
    c.circle(0, 0, 0.62*inch, stroke=1, fill=0)
    c.setLineWidth(1); c.circle(0, 0, 0.53*inch, stroke=1, fill=0)
    c.setFont('Helvetica-Bold', 9); c.setFillColor(STAMP_C)
    c.drawCentredString(0,  0.11*inch, 'APPROVED' if is_v else 'PENDING')
    c.setFont('Helvetica', 7)
    c.drawCentredString(0, -0.06*inch, 'FOR PROCESSING' if is_v else 'REVIEW REQUIRED')
    c.setFont('Courier-Bold', 6); c.drawCentredString(0, -0.26*inch, 'INSURLE ENGINE')
    c.restoreState()


# ── Page 3: Nested Validation Trace ───────────────────────────────────────────
def draw_validation_trace(c, claim, contract, t):
    P, A, L = t['P'], t['A'], t['L']
    is_v    = claim['expected'] == 'VALID'
    tree    = VALIDATION_TREES.get(claim['id'], [])

    y = H - 1.02*inch

    # Section title
    c.setFont('Helvetica-Bold', 15); c.setFillColor(P)
    c.drawString(LM, y, 'Validation Trace  —  3-Level Predicate Resolution')
    y -= 0.10*inch; c.setStrokeColor(A); c.setLineWidth(2)
    c.line(LM, y, LM + 4.6*inch, y); y -= 0.16*inch
    c.setFont('Helvetica', 8.5); c.setFillColor(GREY)
    c.drawString(LM, y,
        'Claim %s  ·  %s  ·  valid_claim(%s)' % (
            claim['id'].upper(), claim['claimant'], claim['id']))
    y -= 0.24*inch

    BRANCH_H  = 0.24*inch   # branch header row
    SUB_H     = 0.20*inch   # sub-check row
    LEAF_H    = 0.175*inch  # leaf row
    GAP_B     = 0.06*inch   # gap between branches
    GAP_S     = 0.02*inch   # gap between sub-checks
    INDENT_S  = 0.32*inch   # indentation for sub-checks
    INDENT_L  = 0.60*inch   # indentation for leaves

    for branch in tree:
        br  = branch['result']
        BC  = PASS_C if br else FAIL_C
        BL  = PASS_L if br else FAIL_L

        # Estimate height needed for this whole branch
        leaf_total = sum(len(s['leaves']) for s in branch['sub_checks'])
        needed = BRANCH_H + len(branch['sub_checks']) * SUB_H + leaf_total * LEAF_H + GAP_B + 0.08*inch
        if y - needed < 0.78*inch:
            # No page break in validation trace — just clip (tree fits in one page for our data)
            break

        # ── Branch header bar ──
        c.setFillColor(BC); c.roundRect(LM, y - BRANCH_H, TW, BRANCH_H, 3, fill=1, stroke=0)
        # Verdict badge (right side)
        badge_w = 0.56*inch; badge_x = LM + TW - badge_w - 0.06*inch
        badge_lbl = 'PASS' if br else 'FAIL'
        c.setFillColor(WHITE if not br else colors.Color(1,1,1,alpha=0.25))
        c.roundRect(badge_x, y - BRANCH_H + 0.04*inch, badge_w, BRANCH_H - 0.08*inch, 3, fill=1, stroke=0)
        c.setFont('Helvetica-Bold', 8); c.setFillColor(BC if not br else WHITE)
        c.drawCentredString(badge_x + badge_w/2, y - BRANCH_H + 0.08*inch, badge_lbl)
        # Branch label
        c.setFont('Helvetica-Bold', 9); c.setFillColor(WHITE)
        icon = '✓' if br else '✗'
        c.drawString(LM + 10, y - BRANCH_H + 0.08*inch,
                     '%s  %s' % (icon, branch['label']))
        y -= BRANCH_H

        # ── Sub-checks ──
        for si, sub in enumerate(branch['sub_checks']):
            sr = sub['result']
            SC = PASS_M if sr else FAIL_M
            SL = PASS_L if sr else FAIL_L
            last_sub = si == len(branch['sub_checks']) - 1

            # Sub row background
            c.setFillColor(SL); c.rect(LM + INDENT_S, y - SUB_H,
                                        TW - INDENT_S, SUB_H, fill=1, stroke=0)
            c.setStrokeColor(colors.HexColor('#D0D8E0')); c.setLineWidth(0.25)
            c.rect(LM + INDENT_S, y - SUB_H, TW - INDENT_S, SUB_H, fill=0, stroke=1)
            # Connector lines
            c.setStrokeColor(BC); c.setLineWidth(1.2)
            mid_y = y - SUB_H / 2
            c.line(LM + 0.08*inch, y, LM + 0.08*inch, mid_y)   # vertical
            c.line(LM + 0.08*inch, mid_y, LM + INDENT_S, mid_y) # horizontal
            if not last_sub:
                c.line(LM + 0.08*inch, mid_y, LM + 0.08*inch, y - SUB_H)
            # Rule label (monospace, gold-ish)
            c.setFont('Courier-Bold', 6.5); c.setFillColor(P)
            c.drawString(LM + INDENT_S + 6, y - 0.06*inch, sub['rule'])
            # Sub label
            c.setFont('Helvetica', 7.5); c.setFillColor(INK2)
            c.drawString(LM + INDENT_S + 6, y - SUB_H + 0.04*inch, sub['label'])
            # Sub badge
            sb_w = 0.44*inch; sb_x = LM + TW - sb_w - 0.04*inch
            c.setFillColor(SC)
            c.roundRect(sb_x, y - SUB_H + 0.03*inch, sb_w, SUB_H - 0.06*inch, 2, fill=1, stroke=0)
            c.setFont('Helvetica-Bold', 7); c.setFillColor(WHITE)
            c.drawCentredString(sb_x + sb_w/2, y - SUB_H + 0.07*inch, 'PASS' if sr else 'FAIL')
            y -= SUB_H

            # ── Leaf checks ──
            for li, (lcheck, lfact, lresult, lreason) in enumerate(sub['leaves']):
                LC = PASS_M if lresult else FAIL_M
                LL = colors.HexColor('#F4FAF6') if lresult else colors.HexColor('#FDF4F4')
                last_leaf = li == len(sub['leaves']) - 1

                c.setFillColor(LL)
                c.rect(LM + INDENT_L, y - LEAF_H, TW - INDENT_L, LEAF_H, fill=1, stroke=0)
                c.setStrokeColor(RULE); c.setLineWidth(0.2)
                c.rect(LM + INDENT_L, y - LEAF_H, TW - INDENT_L, LEAF_H, fill=0, stroke=1)

                # Connector from sub
                c.setStrokeColor(SC); c.setLineWidth(0.9)
                leaf_mid = y - LEAF_H / 2
                c.line(LM + INDENT_S + 0.06*inch, y, LM + INDENT_S + 0.06*inch, leaf_mid)
                c.line(LM + INDENT_S + 0.06*inch, leaf_mid, LM + INDENT_L, leaf_mid)
                if not last_leaf:
                    c.line(LM + INDENT_S + 0.06*inch, leaf_mid, LM + INDENT_S + 0.06*inch, y - LEAF_H)

                # Leaf check icon
                c.setFont('Helvetica-Bold', 7); c.setFillColor(LC)
                c.drawString(LM + INDENT_L + 4, y - LEAF_H + 0.04*inch, '✓' if lresult else '✗')
                # Leaf label
                c.setFont('Helvetica', 7); c.setFillColor(INK2)
                c.drawString(LM + INDENT_L + 14, y - LEAF_H + 0.04*inch, lcheck[:42])
                # Fact (monospace, right-aligned centre zone)
                c.setFont('Courier', 5.8); c.setFillColor(GREY)
                c.drawString(LM + INDENT_L + 14, y - LEAF_H + 0.015*inch, lfact[:48])
                # Reason (far right)
                rsn_x = LM + TW - 0.04*inch
                c.setFont('Courier-Bold', 6.5); c.setFillColor(LC)
                c.drawRightString(rsn_x, y - LEAF_H + 0.04*inch, lreason[:30])
                y -= LEAF_H

            y -= GAP_S

        # Closing border around the whole branch group
        branch_top = y + len(branch['sub_checks']) * SUB_H + \
                     sum(len(s['leaves']) for s in branch['sub_checks']) * LEAF_H + \
                     GAP_S * len(branch['sub_checks']) + BRANCH_H
        c.setStrokeColor(BC); c.setLineWidth(0.6)
        c.roundRect(LM, y, TW, branch_top - y, 3, fill=0, stroke=1)

        y -= GAP_B

    # ── Final verdict box ──
    y -= 0.08*inch
    VH = 0.70*inch
    VC = PASS_C if is_v else FAIL_C
    VL = PASS_L if is_v else FAIL_L
    if y - VH > 0.72*inch:
        c.setFillColor(VL); c.roundRect(LM, y - VH, TW, VH, 6, fill=1, stroke=0)
        c.setStrokeColor(VC); c.setLineWidth(2.5)
        c.roundRect(LM, y - VH, TW, VH, 6, fill=0, stroke=1)
        c.setFillColor(VC); c.rect(LM, y - VH, 8, VH, fill=1, stroke=0)
        c.setFont('Helvetica-Bold', 14); c.setFillColor(VC)
        verdict = 'valid_claim(%s)  :-  %s' % (claim['id'], 'TRUE  ✓' if is_v else 'FAIL  ✗')
        c.drawCentredString(W/2, y - 0.28*inch, verdict)
        c.setFont('Courier', 8); c.setFillColor(INK2)
        c.drawCentredString(W/2, y - 0.50*inch, 'Yes.' if is_v else 'No.')


# ── Page 4: Prolog Facts ──────────────────────────────────────────────────────
def draw_prolog_facts(c, claim, contract, t):
    P, A, L = t['P'], t['A'], t['L']
    is_v   = claim['expected'] == 'VALID'
    y = H - 1.02*inch

    # Section title
    c.setFont('Helvetica-Bold', 15); c.setFillColor(P)
    c.drawString(LM, y, 'InsurLE Prolog Facts')
    y -= 0.10*inch; c.setStrokeColor(A); c.setLineWidth(2)
    c.line(LM, y, LM + 2.6*inch, y); y -= 0.16*inch
    c.setFont('Helvetica', 8.5); c.setFillColor(GREY)
    c.drawString(LM, y,
        'Ground predicates for %s  ·  Query: ?- valid_claim(%s).' % (
            claim['claimant'], claim['id']))
    y -= 0.26*inch

    facts_prolog = claim.get('facts_prolog', [])
    # Also add the ?- query line at the end
    all_lines = (
        ['%% Claim Facts — ' + claim['claimant'],
         '%% Claim ID   : ' + claim['id'],
         '%% Filed      : ' + claim['date'],
         '%% Incident   : ' + claim['incident_date'],
         '']
        + facts_prolog
        + ['',
           '%% Resolution query',
           '?- valid_claim(%s).' % claim['id'],
           '',
           '%% Result: %s' % ('Yes.' if is_v else 'No.')]
    )

    LINE_H = 12
    avail  = int((y - 0.82*inch) / LINE_H)
    rows   = all_lines[:avail]
    code_h = len(rows) * LINE_H + 0.26*inch

    # Dark code background
    c.setFillColor(CDARK); c.roundRect(LM, y - code_h, TW, code_h + 0.08*inch, 6, fill=1, stroke=0)
    c.setStrokeColor(A); c.setLineWidth(3)
    c.line(LM + TW, y - code_h, LM + TW, y + 0.08*inch)

    # Mac dots
    for di, dc in enumerate(['#FF5F57', '#FEBC2E', '#28C840']):
        c.setFillColor(colors.HexColor(dc))
        c.circle(LM + 0.20*inch + di * 0.17*inch, y + 0.03*inch, 0.044*inch, fill=1, stroke=0)
    c.setFont('Courier', 7); c.setFillColor(CCM)
    c.drawString(LM + 0.75*inch, y + 0.005*inch,
                 '%s_facts.pl  —  InsurLE ground predicates' % claim['id'])

    CW2 = 4.22  # char width approx for Courier 7.5pt
    cy = y - 0.04*inch

    for raw in rows:
        cy -= LINE_H
        xc = LM + 0.18*inch
        s  = raw.strip()

        if not s:
            continue

        # Comment lines
        if s.startswith('%'):
            c.setFont('Courier-Oblique', 7.5); c.setFillColor(CCM)
            c.drawString(xc, cy, raw[:95])
            continue

        # Query line
        if s.startswith('?-'):
            c.setFont('Courier-Bold', 8); c.setFillColor(A)
            c.drawString(xc, cy, raw[:95])
            continue

        # Regular predicate fact — paint base in CFG first
        c.setFont('Courier', 7.5); c.setFillColor(CFG)
        c.drawString(xc, cy, raw[:95])

        # Overlay: predicate names in blue
        for mt in re.finditer(r'\b([a-z][a-z_0-9]*)(?=\()', raw):
            c.setFont('Courier-Bold', 7.5); c.setFillColor(CPR)
            c.drawString(xc + mt.start() * CW2, cy, mt.group(0))

        # Overlay: atom values (true/false/atoms) in green
        for mt in re.finditer(
            r'\b(true|false|own|permitted|continental_us|passenger|commercial|'
            r'illness|injury|death|natural_disaster|airline_bankruptcy|medical|baggage|'
            r'disability|accidental_death|workplace_accident|professional_sports|'
            r'criminal_activity|war|self_inflicted|base_jumping|skydiving|'
            r'free_solo_climbing|in_network|out_of_network|standard|genetic|'
            r'us_state|canada_province|construction_work|normal_driving|'
            r'trip_cancellation|collision|none)\b', raw):
            c.setFont('Courier', 7.5); c.setFillColor(CAT)
            c.drawString(xc + mt.start() * CW2, cy, mt.group(0))

        # Overlay: numbers in orange
        for mt in re.finditer(r'\b(\d+\.?\d*)\b', raw):
            c.setFont('Courier', 7.5); c.setFillColor(CNM)
            c.drawString(xc + mt.start() * CW2, cy, mt.group(0))

    # ── Summary stats below code block ──
    sy = y - code_h - 0.08*inch - 0.28*inch
    if sy > 0.78*inch:
        tree = VALIDATION_TREES.get(claim['id'], [])
        passed_b = sum(1 for b in tree if b['result'])
        all_b    = len(tree)
        all_subs = [s for b in tree for s in b['sub_checks']]
        pass_s   = sum(1 for s in all_subs if s['result'])
        all_l    = [lc for s in all_subs for lc in s['leaves']]
        pass_l   = sum(1 for lc in all_l if lc[2])

        stats = [
            ('L1 Branches',   '%d / %d' % (passed_b, all_b)),
            ('L2 Sub-checks', '%d / %d' % (pass_s, len(all_subs))),
            ('L3 Leaf facts', '%d / %d' % (pass_l, len(all_l))),
            ('Resolution',    'valid_claim/%s' % ('TRUE' if is_v else 'FALSE')),
        ]
        sw = TW / len(stats)
        for i, (slbl, sval) in enumerate(stats):
            sx = LM + i * sw
            vc = (PASS_M if is_v else FAIL_M) if slbl == 'Resolution' else P
            c.setFillColor(L); c.roundRect(sx, sy - 0.44*inch, sw - 0.04*inch, 0.46*inch, 3, fill=1, stroke=0)
            c.setStrokeColor(RULE); c.setLineWidth(0.3)
            c.roundRect(sx, sy - 0.44*inch, sw - 0.04*inch, 0.46*inch, 3, fill=0, stroke=1)
            c.setFont('Helvetica-Bold', 6); c.setFillColor(GREY)
            c.drawString(sx + 7, sy - 0.12*inch, slbl.upper())
            c.setFont('Helvetica-Bold', 10); c.setFillColor(vc)
            c.drawString(sx + 7, sy - 0.36*inch, sval)


# ── Assemble one claim PDF (4 pages) ─────────────────────────────────────────
def build_claim_pdf(claim, contract_meta, out_path):
    cid      = None
    for k in THEMES:
        if claim['id'].startswith(k.replace('contract_', 'claim_')):
            cid = k; break
    # Fallback: match by prefix
    if not cid:
        prefix = '_'.join(claim['id'].split('_')[:2])          # e.g. claim_auto
        for k in THEMES:
            if k.replace('contract_', '') == prefix.replace('claim_', ''):
                cid = k; break
    if not cid:
        cid = 'contract_auto'

    t       = THEMES[cid]
    contract = CONTRACT_META.get(cid, CONTRACT_META['contract_auto'])
    # Merge any extra fields from the supplied contract_meta
    contract = {**contract, **contract_meta}

    TOTAL_PAGES = 4
    cv = canvas.Canvas(str(out_path), pagesize=letter)
    cv.setTitle('Claim Report — %s' % claim['claimant'])
    cv.setAuthor(contract['insurer'])

    # Page 1 — Cover
    page_header(cv, contract, claim, t, 1)
    draw_cover(cv, claim, contract, t)
    page_footer(cv, contract, claim, t, 1, TOTAL_PAGES)
    cv.showPage()

    # Page 2 — Formal Claim Form
    page_header(cv, contract, claim, t, 2)
    draw_claim_form(cv, claim, contract, t)
    page_footer(cv, contract, claim, t, 2, TOTAL_PAGES)
    cv.showPage()

    # Page 3 — Validation Trace
    page_header(cv, contract, claim, t, 3)
    draw_validation_trace(cv, claim, contract, t)
    page_footer(cv, contract, claim, t, 3, TOTAL_PAGES)
    cv.showPage()

    # Page 4 — Prolog Facts
    page_header(cv, contract, claim, t, 4)
    draw_prolog_facts(cv, claim, contract, t)
    page_footer(cv, contract, claim, t, 4, TOTAL_PAGES)
    cv.showPage()

    cv.save()
    status = '✓ VALID  ' if claim['expected'] == 'VALID' else '✗ INVALID'
    print('  %s  %-28s  →  %s' % (status, claim['id'], out_path.name))


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    data_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('insurle_data.json')
    if not data_path.exists():
        print('ERROR: %s not found.  Run generate_data.py first.' % data_path)
        sys.exit(1)

    data = json.loads(data_path.read_text())
    out_dir = Path('claim_pdfs')
    out_dir.mkdir(exist_ok=True)

    print('\n🖨  Generating claim PDFs → %s/\n' % out_dir)

    total = 0
    for contract_entry in data['contracts']:
        cid    = contract_entry['id']
        claims = data['claims'].get(cid, [])
        if not claims:
            continue

        # Build a slim contract_meta dict for headers/footers
        meta = {
            'insurer':       contract_entry.get('insurer',       CONTRACT_META.get(cid, {}).get('insurer', '')),
            'policy_number': contract_entry.get('policy_number', CONTRACT_META.get(cid, {}).get('policy_number', '')),
            'type':          contract_entry.get('type',          CONTRACT_META.get(cid, {}).get('type', '')),
            'name':          contract_entry.get('name',          CONTRACT_META.get(cid, {}).get('name', '')),
        }

        print('  Contract: %s (%d claim%s)' % (meta['name'], len(claims), 's' if len(claims) != 1 else ''))
        for claim in claims:
            fname   = '%s.pdf' % claim['id']
            out_path = out_dir / fname
            build_claim_pdf(claim, meta, out_path)
            total  += 1

        print()

    print('✅  %d claim PDF%s generated in  %s/' % (total, 's' if total != 1 else '', out_dir))


if __name__ == '__main__':
    main()