#!/usr/bin/env python3
"""
InsurLE Demo Data Generator
Produces insurle_data.json consumed by index.html via fetch().
Nothing is embedded in the HTML — all data lives here.

JSON structure:
  {
    "contracts": [ { ...contract fields + insurle_rules string + flowchart_nodes } ],
    "claims":    { "contract_id": [ ...claim objects ] }
  }
"""

import json

# ─────────────────────────────────────────────
#  INSURLE RULES  (Prolog source, per contract)
# ─────────────────────────────────────────────

INSURLE_RULES = {

"contract_auto": """\
%% AutoGuard Vehicle Insurance — InsurLE Contract Rules
%% Policy: AG-VH-2024-001  ·  4-Level Nested Predicate Hierarchy

valid_claim(C) :-
    driver_fully_eligible(C) :-
        age_eligible(C) :-
            age(C, A), A >= 21,
            driving_experience_months(C, E), E >= 12,
            age_class_verified(C, A, E) :-
                A >= 25, E >= 24.  %% Standard driver
            age_class_verified(C, A, E) :-
                A >= 21, A < 25, E >= 12,
                novice_endorsement(C, true). %% Young driver

        license_compliant(C) :-
            license_valid(C, true),
            license_expired(C, false),
            license_jurisdiction(C, Jur),
            recognized_jurisdiction(Jur) :-
                recognized_jurisdiction(us_state).
                recognized_jurisdiction(canada_province).
                recognized_jurisdiction(us_territory).
            license_class_valid(C) :-
                license_class(C, Class),
                member(Class, [class_a, class_b, class_c, class_d]).

        driving_history_acceptable(C) :-
            dui_history(C, N),
            fault_accidents_36mo(C, F),
            history_within_limits(C, N, F) :-
                history_within_limits(_, 0, F) :- F =< 2.
                history_within_limits(C, N, _) :-
                    N > 0,
                    months_since_last_dui(C, M), M >= 60,
                    high_risk_surcharge_paid(C, true),
                    defensive_course_completed(C, true).

    vehicle_authorization_valid(C) :-
        ownership_established(C) :-
            vehicle_ownership(C, own),
            title_on_file(C, true).
        ownership_established(C) :-
            vehicle_ownership(C, permitted),
            permission_chain_valid(C) :-
                written_permission(C, true),
                permission_notarized(C, true),
                owner_signature_verified(C, true).

        vehicle_type_covered(C) :-
            vehicle_class(C, passenger),
            vehicle_weight_kg(C, W), W =< 3500,
            not_race_modified(C) :-
                race_modification_flag(C, false).
            not_race_modified(C) :-
                race_modification_flag(C, true),
                sport_rider_attached(C, true).

        registration_current(C).

    incident_circumstances_covered(C) :-
        sobriety_confirmed(C) :-
            bac_within_limit(C) :-
                bac(C, B), B =< 0.08.
            narcotics_absent(C) :-
                under_influence_narcotics(C, false).

        geographic_scope_met(C) :-
            incident_location(C, Loc),
            location_covered(C, Loc) :-
                location_covered(_, continental_us).
                location_covered(C, hawaii) :-
                    pacific_extension_rider(C, true).
                location_covered(C, alaska) :-
                    pacific_extension_rider(C, true).

        activity_not_excluded(C) :-
            activity(C, A),
            activity_risk_class(A, Class) :-
                activity_risk_class(normal_driving, standard).
                activity_risk_class(highway_driving, standard).
                activity_risk_class(racing, prohibited).
                activity_risk_class(deliberate_damage, prohibited).
                activity_risk_class(illegal_transport, prohibited).
            class_permitted(C, Class) :-
                class_permitted(_, standard).

    claim_procedure_followed(C) :-
        reported_in_time(C) :-
            days_since_incident(C, D),
            reporting_deadline_met(C, D) :-
                reporting_deadline_met(_, D) :- D =< 30.

        evidence_complete(C) :-
            police_report_status(C) :-
                police_report(C, true).
            police_report_status(C) :-
                incident_value(C, V), V < 1000,
                police_report(C, not_required).

        fraud_cleared(C) :-
            fraud_indicator(C, false),
            siu_clearance(C) :-
                siu_flag(C, none).
            siu_clearance(C) :-
                siu_flag(C, reviewed),
                siu_result(C, cleared).""",

"contract_health": """\
%% VitalCare Health Insurance — InsurLE Contract Rules
%% Policy: VC-HLT-2024-087  ·  4-Level Nested Predicate Hierarchy

valid_claim(C) :-
    enrollment_requirements_met(C) :-
        continuous_enrollment_satisfied(C) :-
            continuous_enrollment_satisfied(C) :-
                is_emergency(C, true).
            continuous_enrollment_satisfied(C) :-
                days_enrolled(C, D), D >= 90,
                enrollment_lapse(C, false),
                enrollment_continuous_verified(C) :-
                    enrollment_continuous_verified(C) :-
                        payment_gaps(C, G), G =< 0.
                    enrollment_continuous_verified(C) :-
                        payment_gaps(C, G), G > 0, G =< 15,
                        late_payment_waiver(C, true).

        pre_existing_waiting_satisfied(C) :-
            pre_existing_waiting_satisfied(C) :-
                pre_existing_condition(C, false).
            pre_existing_waiting_satisfied(C) :-
                is_emergency(C, true).
            pre_existing_waiting_satisfied(C) :-
                pre_existing_condition(C, true),
                condition_type(C, standard),
                months_since_enrollment(C, M), M >= 12,
                clinical_stability_confirmed(C) :-
                    condition_stable_months(C, S), S >= 6.
            pre_existing_waiting_satisfied(C) :-
                pre_existing_condition(C, true),
                condition_type(C, genetic),
                months_since_enrollment(C, M), M >= 24,
                genetic_counselor_review(C, true) :-
                    counselor_assessment(C, approved).

        premium_lapse_reviewed(C) :-
            premium_lapse_reviewed(C) :-
                enrollment_lapse(C, false).
            premium_lapse_reviewed(C) :-
                enrollment_lapse(C, true),
                lapse_days(C, LD), LD =< 15,
                reinstatement_approved(C).

    coverage_applicable(C) :-
        provider_network_compliant(C) :-
            provider_network_compliant(C) :-
                is_emergency(C, true).
            provider_network_compliant(C) :-
                provider_network(C, in_network),
                provider_credentialed(C) :-
                    provider_license(C, valid),
                    board_certification(C, true).
            provider_network_compliant(C) :-
                provider_network(C, out_of_network),
                out_of_network_exception(C) :-
                    no_in_network_available(C, true),
                    referral_authorised(C, true).

        authorization_obtained_if_needed(C) :-
            authorization_obtained_if_needed(C) :-
                is_emergency(C, true).
            authorization_obtained_if_needed(C) :-
                claim_amount(C, A), A =< 5000,
                procedure_class(C, routine) :-
                    procedure_type(C, T),
                    member(T, [diagnostic, screening, preventive, minor_surgery]).
            authorization_obtained_if_needed(C) :-
                claim_amount(C, A), A > 5000,
                prior_authorization(C, true),
                mrb_review_completed(C) :-
                    mrb_decision(C, approved),
                    review_days_advance(C, D), D >= 10.

        not_cosmetic_only(C) :-
            not_cosmetic_only(C) :-
                cosmetic_only(C, false).
            not_cosmetic_only(C) :-
                cosmetic_only(C, true),
                medical_necessity(C, true),
                prior_authorization(C, true),
                reconstructive_qualification(C) :-
                    trauma_documented(C, true),
                    reconstructive_type(C, T),
                    member(T, [post_mastectomy, burn_repair, accident_reconstruction]).

    financial_limits_satisfied(C) :-
        deductible_status_ok(C) :-
            deductible_status_ok(C) :-
                is_emergency(C, true).
            deductible_status_ok(C) :-
                annual_deductible_met(C, true),
                deductible_year_match(C) :-
                    policy_year(C, Y),
                    service_year(C, Y).

        within_lifetime_max(C) :-
            cumulative_claims(C, Total),
            lifetime_headroom(C, Total, H) :-
                lifetime_headroom(_, Total, H) :-
                    H is 500000 - Total.
            H > 0.

        annual_out_of_pocket_ok(C) :-
            annual_oop(C, OOP), OOP =< 8000.

    timely_submission(C) :-
        days_since_service(C, D),
        submission_within_window(C, D) :-
            D =< 180,
            submission_channel_valid(C) :-
                submission_method(C, M),
                member(M, [portal, mail, fax, in_person]).""",

"contract_travel": """\
%% JetSafe Travel Insurance — InsurLE Contract Rules
%% Policy: JS-TRV-2024-445  ·  4-Level Nested Predicate Hierarchy

valid_claim(C) :-
    policy_validity_confirmed(C) :-
        purchased_within_window(C) :-
            purchased_within_window(C) :-
                days_after_deposit(C, D), D =< 21,
                purchase_channel_valid(C) :-
                    purchase_method(C, M),
                    member(M, [online, agent, broker, direct]).
            purchased_within_window(C) :-
                claim_type(C, T),
                \\+ member(T, [trip_cancellation]),
                non_cancellation_policy_valid(C) :-
                    policy_active_since(C, D), D >= 0.

        trip_not_already_commenced(C) :-
            trip_commenced_at_purchase(C, false),
            departure_date_check(C) :-
                purchase_before_departure(C, true).

        policy_status_active(C) :-
            policy_lapse(C, false),
            premium_paid(C, true),
            coverage_period_current(C) :-
                incident_within_trip_dates(C, true).

    covered_event_occurred(C) :-
        covered_event_occurred(C) :-
            claim_type(C, trip_cancellation),
            valid_cancellation_reason(C) :-
                cancellation_reason(C, R),
                covered_reason_class(R, Class) :-
                    covered_reason_class(illness, medical_class).
                    covered_reason_class(injury, medical_class).
                    covered_reason_class(death, bereavement_class).
                    covered_reason_class(natural_disaster, force_majeure).
                    covered_reason_class(airline_bankruptcy, carrier_failure).
                    covered_reason_class(job_loss, employment_class).
                    covered_reason_class(mandatory_evacuation, government_class).
                class_authorised(Class) :-
                    class_authorised(medical_class).
                    class_authorised(bereavement_class).
                    class_authorised(force_majeure).
                    class_authorised(carrier_failure).
                    class_authorised(employment_class).
                    class_authorised(government_class).

        covered_event_occurred(C) :-
            claim_type(C, medical),
            medical_event_covered(C) :-
                medical_event_covered(C) :-
                    medical_emergency(C, true),
                    medical_facility_attended(C) :-
                        facility_type(C, T),
                        member(T, [hospital, clinic, emergency_room, ambulance]).
                medical_event_covered(C) :-
                    medical_emergency(C, false),
                    treatment_required(C, true),
                    pre_existing_condition(C, false),
                    treating_physician_qualified(C) :-
                        physician_license(C, valid).

        covered_event_occurred(C) :-
            claim_type(C, baggage),
            baggage_loss_documented(C) :-
                police_report_filed(C, true),
                hours_to_report(C, H), H =< 24,
                baggage_value_within_limit(C) :-
                    baggage_value_within_limit(C) :-
                        baggage_claimed_amount(C, B), B =< 2500.
                    baggage_value_within_limit(C) :-
                        baggage_claimed_amount(C, B), B > 2500,
                        high_value_rider(C, true).

    risk_profile_eligible(C) :-
        fit_at_purchase(C, true).
    medically_fit_at_purchase(C) :-
        fit_at_purchase(C, false),
        pre_existing_waiver(C, true),
        condition_stable_60_days(C, true).

    destination_covered(C) :-
        destination_advisory_level(C, L), L < 4.

    activity_covered(C) :-
        activity_covered(C) :-
            activity(C, A), \\+ extreme_sport(A).
        activity_covered(C) :-
            activity(C, A), extreme_sport(A) :-
                extreme_sport(base_jumping). extreme_sport(skydiving).
                extreme_sport(free_solo_climbing). extreme_sport(cliff_diving).
            adventure_rider(C, true).

    documentation_complete(C) :-
        timely_notification(C) :-
            timely_notification(C) :-
                claim_type(C, baggage), hours_to_report(C, H), H =< 24.
            timely_notification(C) :-
                claim_type(C, T), T \\= baggage.
        documents_provided(C) :-
            documentation_provided(C, true).
        exclusions_clear(C) :-
            under_influence(C, false),
            war_related(C, false).""",

"contract_accident": """\
%% ShieldPlus Personal Accident — InsurLE Contract Rules
%% Policy: SP-ACC-2024-209  ·  4-Level Nested Predicate Hierarchy

valid_claim(C) :-
    accidental_origin_confirmed(C) :-
        cause_is_accidental(C) :-
            accident_type(C, T),
            accident_category(T, Cat) :-
                accident_category(fall, physical_trauma).
                accident_category(collision, physical_trauma).
                accident_category(burn, physical_trauma).
                accident_category(drowning, environmental).
                accident_category(electrocution, environmental).
                accident_category(workplace_accident, occupational).
                accident_category(road_accident, vehicular).
                accident_category(sports_accident, recreational).
            category_covered(Cat) :-
                category_covered(physical_trauma).
                category_covered(environmental).
                category_covered(occupational).
                category_covered(vehicular).
                category_covered(recreational).

        not_self_inflicted(C) :-
            not_self_inflicted(C) :-
                self_inflicted(C, false),
                psychological_assessment_required(C, false).
            not_self_inflicted(C) :-
                self_inflicted(C, false),
                psychological_assessment_required(C, true),
                psych_assessment_clear(C) :-
                    psych_report(C, no_intent).

        not_excluded_cause(C) :-
            cause(C, Cause),
            cause_exclusion_class(Cause, Class) :-
                cause_exclusion_class(workplace_accident,  occupational_class).
                cause_exclusion_class(road_accident,       vehicular_class).
                cause_exclusion_class(fall,                accidental_class).
                cause_exclusion_class(sports_accident,     recreational_class).
                cause_exclusion_class(self_inflicted,      excluded_class).
                cause_exclusion_class(criminal_activity,   excluded_class).
                cause_exclusion_class(war,                 excluded_class).
                cause_exclusion_class(professional_sports, excluded_class).
            class_not_excluded(Class) :-
                class_not_excluded(occupational_class).
                class_not_excluded(vehicular_class).
                class_not_excluded(accidental_class).
                class_not_excluded(recreational_class).

        sole_cause_verified(C) :-
            contributing_disease(C, false) :-
                comorbidity_flag(C, none).
            contributing_infirmity(C, false) :-
                pre_existing_infirmity(C, false).

    claimant_fully_eligible(C) :-
        age_in_range(C) :-
            age(C, A), A >= 18, A =< 70,
            age_band_confirmed(C, A) :-
                age_band_confirmed(_, A) :- A >= 18, A =< 65.
                age_band_confirmed(C, A) :-
                    A > 65, A =< 70,
                    senior_extension_policy(C, true).

        intoxication_negative(C) :-
            intoxicated(C, false),
            narcotics_influence(C, false),
            toxicology_report_status(C) :-
                toxicology_report_status(C) :-
                    toxicology_required(C, false).
                toxicology_report_status(C) :-
                    toxicology_required(C, true),
                    toxicology_result(C, negative).

        not_professional_sport(C) :-
            activity(C, A),
            sport_payment_status(C, A, Status) :-
                sport_payment_status(C, A, paid_athlete) :-
                    receives_remuneration(C, true),
                    member(A, [rugby, football, cricket, basketball, baseball]).
                sport_payment_status(C, _, amateur) :-
                    receives_remuneration(C, false).
            Status \\= paid_athlete.

        occupation_eligible(C) :-
            occupation_class(C, Class),
            hazardous_occupation_handled(C, Class) :-
                hazardous_occupation_handled(_, standard).
                hazardous_occupation_handled(C, hazardous) :-
                    hazardous_rider(C, true),
                    hazard_premium_paid(C, true).

    medical_criteria_met(C) :-
        medical_evidence_provided(C) :-
            medical_evidence(C, true),
            evidence_currency(C, Days) :-
                evidence_date_delta(C, Days).
            Days =< 30.

        licensed_provider_confirms(C) :-
            attending_physician_licensed(C, true),
            specialty_appropriate(C) :-
                physician_specialty(C, S),
                member(S, [general_practitioner, emergency_medicine, orthopaedics, neurology, cardiology, surgery]).

        injury_consistent_with_claim(C) :-
            injury_severity(C, Sev),
            claim_type(C, Type),
            severity_claim_alignment(Sev, Type) :-
                severity_claim_alignment(minor,    disability) :- !.
                severity_claim_alignment(moderate, disability).
                severity_claim_alignment(severe,   disability).
                severity_claim_alignment(severe,   accidental_death).
                severity_claim_alignment(fatal,    accidental_death).
                severity_claim_alignment(minor,    dismemberment) :- !.
                severity_claim_alignment(moderate, dismemberment).

    procedure_compliant(C) :-
        notification_in_time(C) :-
            notification_in_time(C) :-
                claim_type(C, accidental_death),
                days_to_notify(C, D), D =< 30.
            notification_in_time(C) :-
                claim_type(C, disability),
                days_to_notify(C, D), D =< 14.

        benefit_type_valid(C) :-
            claim_type(C, T),
            benefit_coverage_class(T, _) :-
                benefit_coverage_class(accidental_death, principal_benefit).
                benefit_coverage_class(dismemberment,    principal_benefit).
                benefit_coverage_class(disability,       periodic_benefit).

        within_benefit_limits(C) :-
            within_benefit_limits(C) :-
                claim_type(C, accidental_death),
                claim_amount_usd(C, A), A =< 250000.
            within_benefit_limits(C) :-
                claim_type(C, disability),
                claim_amount_usd(C, A), A =< 250000.""",

}

# ─────────────────────────────────────────────
#  FLOWCHART NODE DATA  (used by buildFlowchartSVG in the HTML)
#  Each entry: { main: [line1, line2], tag: str, subs: [{label, items}] }
# ─────────────────────────────────────────────

FLOWCHART_NODES = {

    "contract_auto": [
        {
            "main": ["DRIVER", "ELIGIBLE?"],
            "tag": "L2: Age · Licence · History",
            "subs": [
                {"label": "age_eligible/1",                   "items": ["Age≥21", "Exp≥12mo", "age_class_verified"]},
                {"label": "license_compliant/1",              "items": ["valid", "not_expired", "jurisdiction", "class_valid"]},
                {"label": "driving_history_acceptable/1",     "items": ["DUI count", "history_within_limits"]}
            ]
        },
        {
            "main": ["VEHICLE", "AUTH?"],
            "tag": "L2: Ownership · Class · Weight",
            "subs": [
                {"label": "ownership_established/1",          "items": ["own: title_on_file", "permitted: permission_chain_valid"]},
                {"label": "vehicle_type_covered/1",           "items": ["passenger class", "weight≤3500kg", "not_race_modified"]},
                {"label": "registration_current/1",           "items": ["rego_valid", "rego_year_current"]}
            ]
        },
        {
            "main": ["INCIDENT", "COVERED?"],
            "tag": "L2: BAC · Location · Activity",
            "subs": [
                {"label": "sobriety_confirmed/1",             "items": ["bac_within_limit", "narcotics_absent"]},
                {"label": "geographic_scope_met/1",           "items": ["location_covered/4 zones"]},
                {"label": "activity_not_excluded/1",          "items": ["activity_risk_class", "class_permitted"]}
            ]
        },
        {
            "main": ["PROCEDURE", "FOLLOWED?"],
            "tag": "L2: Report · Evidence · Fraud",
            "subs": [
                {"label": "reported_in_time/1",               "items": ["days≤30", "reporting_deadline_met"]},
                {"label": "evidence_complete/1",              "items": ["police_report_status/2 rules"]},
                {"label": "fraud_cleared/1",                  "items": ["fraud_indicator=false", "siu_clearance"]}
            ]
        }
    ],

    "contract_health": [
        {
            "main": ["ENROLLMENT", "MET?"],
            "tag": "L2: 90-Day · Pre-Existing · Lapse",
            "subs": [
                {"label": "continuous_enrollment/1",          "items": ["emergency OR days≥90", "enrollment_continuous_verified"]},
                {"label": "pre_existing_wait/1",              "items": ["no_condition", "emergency override", "12mo standard", "24mo genetic"]},
                {"label": "premium_lapse_reviewed/1",         "items": ["no_lapse", "lapse≤15d+reinstatement"]}
            ]
        },
        {
            "main": ["COVERAGE", "APPLICABLE?"],
            "tag": "L2: Network · Auth · Cosmetic",
            "subs": [
                {"label": "provider_network_compliant/1",     "items": ["in_network: credentialed", "out_of_network: exception", "emergency override"]},
                {"label": "authorization_obtained/1",         "items": ["emergency", "≤$5k routine", "$5k+ MRB 10d prior"]},
                {"label": "not_cosmetic_only/1",              "items": ["cosmetic=false", "reconstructive_qualification"]}
            ]
        },
        {
            "main": ["FIN. LIMITS", "SATISFIED?"],
            "tag": "L2: Deductible · $500k · OOP",
            "subs": [
                {"label": "deductible_status_ok/1",           "items": ["emergency override", "annual_deductible_met + year_match"]},
                {"label": "within_lifetime_max/1",            "items": ["lifetime_headroom>0", "500000-cumulative"]},
                {"label": "annual_out_of_pocket_ok/1",        "items": ["OOP≤$8,000"]}
            ]
        },
        {
            "main": ["TIMELY", "SUBMISSION?"],
            "tag": "L2: ≤180 Days · Channel",
            "subs": [
                {"label": "submission_within_window/1",       "items": ["days≤180", "submission_channel_valid"]},
                {"label": "channel_valid/1",                  "items": ["portal", "mail", "fax", "in_person"]}
            ]
        }
    ],

    "contract_travel": [
        {
            "main": ["POLICY", "VALID?"],
            "tag": "L2: Window · Trip Status · Active",
            "subs": [
                {"label": "purchased_within_window/1",        "items": ["days≤21 + channel_valid", "non-cancellation exception"]},
                {"label": "trip_not_commenced/1",             "items": ["commenced=false", "departure_date_check"]},
                {"label": "policy_status_active/1",           "items": ["no_lapse", "premium paid", "coverage_period_current"]}
            ]
        },
        {
            "main": ["COVERED", "EVENT?"],
            "tag": "L2: Cancellation · Medical · Baggage",
            "subs": [
                {"label": "valid_cancellation_reason/1",      "items": ["reason class taxonomy", "7 recognised classes"]},
                {"label": "medical_event_covered/1",          "items": ["emergency: facility_attended", "non-emerg: physician_qualified"]},
                {"label": "baggage_loss_documented/1",        "items": ["police report 24h", "value≤$2500 or rider"]}
            ]
        },
        {
            "main": ["RISK", "ELIGIBLE?"],
            "tag": "L2: Fitness · Dest · Activity",
            "subs": [
                {"label": "medically_fit_at_purchase/1",      "items": ["fit=true: declaration", "waiver: stable 60d + signature"]},
                {"label": "destination_covered/1",            "items": ["advisory<4", "not_sanctions_listed"]},
                {"label": "activity_covered/1",               "items": ["sport_risk_level taxonomy", "extreme: adventure_rider required"]}
            ]
        },
        {
            "main": ["DOCS", "COMPLETE?"],
            "tag": "L2: Notification · Docs · Exclusions",
            "subs": [
                {"label": "timely_notification/1",            "items": ["baggage: 24h + channel", "other types: N/A"]},
                {"label": "documents_provided/1",             "items": ["documentation=true", "document_types_adequate"]},
                {"label": "exclusions_clear/1",               "items": ["under_influence=false", "war_related=false", "not_nuclear"]}
            ]
        }
    ],

    "contract_accident": [
        {
            "main": ["ACCIDENTAL", "ORIGIN?"],
            "tag": "L2: Type · Not-Self · Cause · Sole",
            "subs": [
                {"label": "cause_is_accidental/1",            "items": ["accident_category taxonomy", "8 categories covered"]},
                {"label": "not_self_inflicted/1",             "items": ["self_inflicted=false", "psych_assessment_clear"]},
                {"label": "not_excluded_cause/1",             "items": ["cause_exclusion_class", "4 permitted classes"]},
                {"label": "sole_cause_verified/1",            "items": ["contributing_disease=false", "contributing_infirmity=false"]}
            ]
        },
        {
            "main": ["CLAIMANT", "ELIGIBLE?"],
            "tag": "L2: Age · Sober · Sport · Occupation",
            "subs": [
                {"label": "age_in_range/1",                   "items": ["18≤age≤70", "age_band_confirmed: standard/senior"]},
                {"label": "intoxication_negative/1",          "items": ["intoxicated=false", "narcotics=false", "toxicology_status"]},
                {"label": "not_professional_sport/1",         "items": ["sport_payment_status", "paid_athlete=EXCLUDED"]},
                {"label": "occupation_eligible/1",            "items": ["standard OK", "hazardous: rider required"]}
            ]
        },
        {
            "main": ["MEDICAL", "CRITERIA?"],
            "tag": "L2: Evidence · Provider · Consistency",
            "subs": [
                {"label": "medical_evidence_provided/1",      "items": ["evidence=true", "currency≤30 days"]},
                {"label": "licensed_provider_confirms/1",     "items": ["physician licensed", "specialty_appropriate/2 types"]},
                {"label": "injury_consistent_with_claim/1",   "items": ["severity_claim_alignment matrix", "6 alignment rules"]}
            ]
        },
        {
            "main": ["PROCEDURE", "COMPLIANT?"],
            "tag": "L2: Notify · BenefitType · Limits",
            "subs": [
                {"label": "notification_in_time/1",           "items": ["death: 30d", "disability: 14d", "method_valid/5 channels"]},
                {"label": "benefit_type_valid/1",             "items": ["benefit_coverage_class", "3 benefit classes"]},
                {"label": "within_benefit_limits/1",          "items": ["policy_max lookup", "death=$250k", "disability=W×Wk"]}
            ]
        }
    ],
}

# ─────────────────────────────────────────────
#  CONTRACT DEFINITIONS
# ─────────────────────────────────────────────

CONTRACTS = [
    {
        "id": "contract_auto",
        "name": "AutoGuard Vehicle Insurance",
        "type": "Vehicle Insurance",
        "insurer": "AutoGuard Insurance Co.",
        "policy_number": "AG-VH-2024-001",
        "effective_date": "2024-01-01",
        "expiry_date": "2024-12-31",
        "premium": "$1,200/year",
        "coverage": "$50,000",
        "icon": "🚗",
        "color": "#1a3a5c",
        "accent": "#e8b84b",
        "pdf_url": "contract_pdfs/contract_auto.pdf",
        "contract_sections": [
            {"num": "SEC. 1", "title": "Driver Eligibility",
             "text": "The insured driver must be at least 21 years of age at the time of the incident. Drivers with fewer than 12 months of licensed experience require a Novice Endorsement. The driver must hold a valid, unexpired licence issued by a recognised authority and must not have accumulated more than two at-fault accidents in the preceding 36 months."},
            {"num": "SEC. 2", "title": "Vehicle Ownership & Authorisation",
             "text": "Coverage applies only when the insured is operating (a) a vehicle they legally own, or (b) a vehicle for which they hold a current notarised written-permission letter countersigned by the registered owner. The vehicle must carry current registration. Loaned vehicles require a co-insured endorsement."},
            {"num": "SEC. 3", "title": "Sobriety & Intoxication Exclusion",
             "text": "Any claim arising where the driver's BAC exceeded 0.08 g/dL at the time of the incident, or where the driver was under the influence of unprescribed narcotics, is void regardless of whether the substance was the proximate cause. This exclusion survives any legal challenge."},
            {"num": "SEC. 4", "title": "Vehicle Classification & Weight",
             "text": "Coverage is limited to personal passenger vehicles with GVWR not exceeding 3,500 kg. Commercial vehicles, motorcycles, off-road vehicles, and race-modified vehicles are excluded unless a Commercial or Sport Rider is explicitly attached to the policy prior to the incident."},
            {"num": "SEC. 5", "title": "Geographic Scope",
             "text": "Coverage is limited to incidents occurring within the continental United States. Hawaii and Alaska are covered only under the Pacific Extension Rider. International incidents require a Foreign Territory Endorsement. Incidents in active conflict zones are excluded without exception."},
            {"num": "SEC. 6", "title": "Incident Reporting Obligation",
             "text": "Claims must be reported within 30 calendar days of the incident date. For incidents with bodily injury or property damage exceeding $1,000, a police report filed at the scene must accompany the claim. Failure to meet reporting deadlines constitutes grounds for denial."},
            {"num": "SEC. 7", "title": "Driving History Requirements",
             "text": "Claims are excluded when the driver has a DUI or DWI conviction within the preceding 60 months. Drivers with a single conviction older than 60 months may qualify subject to payment of a high-risk surcharge and completion of an approved defensive-driving course within 90 days."},
            {"num": "SEC. 8", "title": "Fraud & Misrepresentation",
             "text": "Any deliberate misrepresentation, concealment of material fact, or attempted fraud in connection with any claim will result in immediate policy cancellation, denial of all pending claims, and referral to the Special Investigations Unit for potential civil and criminal action."}
        ]
    },
    {
        "id": "contract_health",
        "name": "VitalCare Health Insurance",
        "type": "Health Insurance",
        "insurer": "VitalCare Health Group",
        "policy_number": "VC-HLT-2024-087",
        "effective_date": "2024-01-01",
        "expiry_date": "2024-12-31",
        "premium": "$450/month",
        "coverage": "$500,000 lifetime",
        "icon": "🏥",
        "color": "#1a4a3a",
        "accent": "#4ecb8d",
        "pdf_url": "contract_pdfs/contract_health.pdf",
        "contract_sections": [
            {"num": "SEC. 1", "title": "Continuous Enrollment",
             "text": "The policyholder must be continuously enrolled for a minimum of 90 days before filing any non-emergency claim. Emergency services are covered from day one. Any premium payment lapse exceeding 15 days resets the continuous-enrollment counter to zero."},
            {"num": "SEC. 2", "title": "Pre-Existing Conditions",
             "text": "Conditions diagnosed prior to enrollment are subject to a 12-month waiting period from the enrollment date. Genetic conditions and congenital disorders carry a 24-month waiting period. Emergency treatment of pre-existing conditions is covered from day one regardless of waiting periods."},
            {"num": "SEC. 3", "title": "Provider Network & Coverage Tiers",
             "text": "In-network providers are reimbursed at 100% after the annual deductible. Out-of-network providers are reimbursed at 60%. Emergency services at any facility are covered at 100% irrespective of network status. The insured must designate a primary care physician within 30 days of enrollment."},
            {"num": "SEC. 4", "title": "Prior Authorization",
             "text": "Non-emergency procedures, hospitalisations, or specialist referrals exceeding $5,000 require written prior authorisation from VitalCare's Medical Review Board. Requests must be submitted at least 10 business days before the scheduled procedure. Retroactive authorisation is not permitted."},
            {"num": "SEC. 5", "title": "Annual Deductible",
             "text": "An annual deductible of $1,500 per individual must be satisfied before non-emergency reimbursements are processed. Emergency claims bypass the deductible entirely. The deductible resets on the policy anniversary date."},
            {"num": "SEC. 6", "title": "Lifetime Maximum Benefit",
             "text": "Total lifetime benefits shall not exceed $500,000 per individual policyholder. VitalCare will provide written notification when cumulative claims reach 80% of the lifetime maximum. Benefits beyond the maximum are the sole responsibility of the insured."},
            {"num": "SEC. 7", "title": "Cosmetic Procedure Exclusions",
             "text": "Purely cosmetic procedures with no documented medical necessity are excluded. Procedures that are cosmetically performed but medically necessary (e.g. reconstructive surgery following trauma) are covered subject to prior authorisation and medical necessity confirmation from the Review Board."},
            {"num": "SEC. 8", "title": "Claim Submission Deadline",
             "text": "All claims must be submitted within 180 calendar days of the date of service. Claims submitted after this deadline are denied regardless of medical validity. Electronic portal submissions are accepted as timely if submitted by 11:59 PM on the 180th day."}
        ]
    },
    {
        "id": "contract_travel",
        "name": "JetSafe Travel Insurance",
        "type": "Travel Insurance",
        "insurer": "JetSafe Global Underwriters",
        "policy_number": "JS-TRV-2024-445",
        "effective_date": "2024-01-01",
        "expiry_date": "2024-12-31",
        "premium": "$85/trip",
        "coverage": "$100,000 per trip",
        "icon": "✈️",
        "color": "#2a1a5c",
        "accent": "#a78bfa",
        "pdf_url": "contract_pdfs/contract_travel.pdf",
        "contract_sections": [
            {"num": "SEC. 1", "title": "Policy Purchase Window",
             "text": "The policy must be purchased within 21 calendar days of the initial trip deposit to activate pre-departure cancellation coverage. Medical and emergency benefits are active from the policy purchase date through trip completion. Policies purchased after the 21-day window have reduced benefits and exclude cancellation coverage."},
            {"num": "SEC. 2", "title": "Trip Cancellation Covered Reasons",
             "text": "Cancellation benefits are payable only for: (a) sudden illness or injury of the insured or immediate family member; (b) death of insured or immediate family member; (c) natural disaster rendering the destination uninhabitable; (d) airline bankruptcy; (e) job loss following 3+ years continuous employment; (f) mandatory government evacuation order."},
            {"num": "SEC. 3", "title": "Medical Fitness at Purchase",
             "text": "The insured must be medically fit to travel at the time of policy purchase. Claims arising from conditions known, diagnosed, or symptomatic at purchase are excluded unless a Pre-Existing Condition Waiver is attached. The waiver requires a stable condition for at least 60 days preceding the purchase date."},
            {"num": "SEC. 4", "title": "Adventure & Extreme Sports",
             "text": "Injuries sustained during extreme sports including BASE jumping, skydiving, free solo climbing, and cliff diving are excluded unless the Adventure Rider supplement has been purchased simultaneously with the base policy. Retrospective Adventure Rider additions after policy issuance are not permitted."},
            {"num": "SEC. 5", "title": "Destination Exclusions",
             "text": "Claims arising from travel to destinations under Level 4 Travel Advisory (Do Not Travel) as issued by the U.S. Department of State at time of departure are excluded. Active conflict zones, sanctioned countries, and territories under pandemic quarantine are also excluded."},
            {"num": "SEC. 6", "title": "Baggage & Personal Effects",
             "text": "Lost or stolen baggage requires a police report filed within 24 hours of discovery of loss. Maximum single-item value is $500 unless a High-Value Item Rider is attached. Electronics require proof of purchase. The aggregate baggage limit is $2,500 per trip."},
            {"num": "SEC. 7", "title": "Documentation Requirements",
             "text": "All claims must be accompanied by original receipts, invoices, medical records, police reports, or other official documentation as applicable. Undocumented claims will be suspended for up to 60 days pending receipt of required documentation, after which they may be denied."},
            {"num": "SEC. 8", "title": "Substance Use & War Exclusions",
             "text": "Claims arising from incidents where the insured was under the influence of alcohol (BAC > 0.08) or unprescribed substances are excluded without exception. Claims arising from war, terrorism, civil insurrection, military action, or nuclear incidents are also excluded."}
        ]
    },
    {
        "id": "contract_accident",
        "name": "ShieldPlus Personal Accident",
        "type": "Accident Insurance",
        "insurer": "ShieldPlus Casualty Ltd.",
        "policy_number": "SP-ACC-2024-209",
        "effective_date": "2024-01-01",
        "expiry_date": "2024-12-31",
        "premium": "$180/year",
        "coverage": "$250,000",
        "icon": "🛡️",
        "color": "#4a1a1a",
        "accent": "#f87171",
        "pdf_url": "contract_pdfs/contract_accident.pdf",
        "contract_sections": [
            {"num": "SEC. 1", "title": "Accidental Death & Dismemberment",
             "text": "Full principal benefit is payable upon accidental death, or loss of both hands, both feet, sight in both eyes, or any combination thereof. Fifty percent of the principal benefit is payable for loss of one hand, one foot, or sight in one eye. Benefits are paid in addition to any disability benefit, subject to the aggregate policy maximum."},
            {"num": "SEC. 2", "title": "Temporary Total Disability",
             "text": "Weekly disability benefit of $500 is payable for up to 52 consecutive weeks when the insured is wholly unable to engage in any gainful occupation due to a covered accident. A 7-day elimination period applies from date of accident. The insured must remain under continuous care of a licensed physician."},
            {"num": "SEC. 3", "title": "Age Requirements",
             "text": "Coverage applies to individuals aged 18 to 70 at the time of the accident. Policyholders reaching age 71 during the policy period retain coverage until the next policy anniversary date, after which the policy must be converted or allowed to lapse. No coverage for minors under 18."},
            {"num": "SEC. 4", "title": "Accidental Origin Requirement",
             "text": "Benefits are payable only for injuries caused by a sudden, unexpected, external, and accidental event. The accident must be the direct and independent cause of the covered loss with no contributing disease, bodily infirmity, or mental disorder. Injuries from illness, gradual onset, or natural aging are excluded."},
            {"num": "SEC. 5", "title": "Cause Exclusions",
             "text": "No benefit is payable for accidents resulting from: (a) self-inflicted injury or suicide attempt; (b) participation in criminal activity; (c) acts of war or military operations; (d) professional sports or organised athletic competitions where the claimant receives remuneration; (e) hazardous occupational activities without a Hazardous Occupation Rider."},
            {"num": "SEC. 6", "title": "Substance Exclusion",
             "text": "No benefit is payable if the accident occurred while the insured was intoxicated (BAC > 0.08 g/dL) or under the influence of unprescribed narcotics, hallucinogens, or stimulants. This exclusion applies regardless of causal relationship between the substance and the accident."},
            {"num": "SEC. 7", "title": "Claim Notification Deadlines",
             "text": "Accidental death claims must be notified within 30 calendar days of death. Disability claims must be notified within 14 days of the commencement of disability. Late notification will only be accepted where the insured demonstrates notification was impossible due to circumstances wholly beyond their control."},
            {"num": "SEC. 8", "title": "Medical Evidence Required",
             "text": "All claims require a completed attending physician statement from a licensed medical practitioner. For disability claims, monthly ongoing physician statements are required throughout the disability period. Self-reported injuries without corroborating medical documentation are excluded from coverage entirely."}
        ]
    }
]

# ─────────────────────────────────────────────
#  CLAIMS  (keyed by contract id)
# ─────────────────────────────────────────────

CLAIMS = {

"contract_auto": [
    {
        "id": "claim_auto_1",
        "claimant": "James Ellison",
        "date": "2024-03-15",
        "incident_date": "2024-03-10",
        "description": "Rear-end collision on I-95. Insured's vehicle struck by an uninsured motorist at a red light. Police report filed at scene. Insured is 34, has 10 years of driving experience, no DUI history, and owns the vehicle outright.",
        "amount": "$8,500",
        "expected": "VALID",
        "facts_prolog": [
            "age(claim_auto_1, 34).",
            "driving_experience_months(claim_auto_1, 120).",
            "license_valid(claim_auto_1, true).",
            "license_expired(claim_auto_1, false).",
            "license_jurisdiction(claim_auto_1, us_state).",
            "dui_history(claim_auto_1, 0).",
            "vehicle_ownership(claim_auto_1, own).",
            "vehicle_class(claim_auto_1, passenger).",
            "vehicle_weight_kg(claim_auto_1, 1580).",
            "bac(claim_auto_1, 0.00).",
            "under_influence_narcotics(claim_auto_1, false).",
            "incident_location(claim_auto_1, continental_us).",
            "activity(claim_auto_1, normal_driving).",
            "days_since_incident(claim_auto_1, 5).",
            "police_report(claim_auto_1, true).",
            "fraud_indicator(claim_auto_1, false)."
        ],
        "validation_tree": [
            {"id": "b1", "label": "Driver Fully Eligible", "icon": "👤", "result": True,
             "sub_checks": [
                 {"rule": "age_eligible/1", "label": "Minimum Age & Experience", "result": True,
                  "sub_sub_checks": [
                      {"label": "Age & experience checks", "result": True, "leaf_checks": [
                          {"check": "Age ≥ 21", "fact": "age(C, 34)", "result": True, "reason": "34 ≥ 21 ✓"},
                          {"check": "Experience ≥ 12 mo", "fact": "driving_experience_months(C, 120)", "result": True, "reason": "120 ≥ 12 ✓"}
                      ]}
                  ]},
                 {"rule": "license_compliant/1", "label": "Licence Validity", "result": True,
                  "sub_sub_checks": [
                      {"label": "Licence checks", "result": True, "leaf_checks": [
                          {"check": "Licence valid", "fact": "license_valid(C, true)", "result": True, "reason": "Active ✓"},
                          {"check": "Not expired", "fact": "license_expired(C, false)", "result": True, "reason": "Current ✓"},
                          {"check": "Jurisdiction recognised", "fact": "license_jurisdiction(C, us_state)", "result": True, "reason": "US state ✓"}
                      ]}
                  ]},
                 {"rule": "driving_history_acceptable/1", "label": "Driving History", "result": True,
                  "sub_sub_checks": [
                      {"label": "History checks", "result": True, "leaf_checks": [
                          {"check": "No DUI", "fact": "dui_history(C, 0)", "result": True, "reason": "Clean record ✓"}
                      ]}
                  ]}
             ]},
            {"id": "b2", "label": "Vehicle Authorization Valid", "icon": "🚗", "result": True,
             "sub_checks": [
                 {"rule": "ownership_established/1", "label": "Ownership Verification", "result": True,
                  "sub_sub_checks": [
                      {"label": "Ownership check", "result": True, "leaf_checks": [
                          {"check": "Owned by insured", "fact": "vehicle_ownership(C, own)", "result": True, "reason": "Confirmed ✓"}
                      ]}
                  ]},
                 {"rule": "vehicle_type_covered/1", "label": "Class & Weight", "result": True,
                  "sub_sub_checks": [
                      {"label": "Type checks", "result": True, "leaf_checks": [
                          {"check": "Passenger class", "fact": "vehicle_class(C, passenger)", "result": True, "reason": "Passenger ✓"},
                          {"check": "Weight ≤ 3,500 kg", "fact": "vehicle_weight_kg(C, 1580)", "result": True, "reason": "1,580 ≤ 3,500 ✓"}
                      ]}
                  ]}
             ]},
            {"id": "b3", "label": "Incident Circumstances Covered", "icon": "🔍", "result": True,
             "sub_checks": [
                 {"rule": "sobriety_confirmed/1", "label": "Sobriety Verification", "result": True,
                  "sub_sub_checks": [
                      {"label": "Sobriety checks", "result": True, "leaf_checks": [
                          {"check": "BAC ≤ 0.08", "fact": "bac(C, 0.00)", "result": True, "reason": "0.00 ≤ 0.08 ✓"},
                          {"check": "No narcotics", "fact": "under_influence_narcotics(C, false)", "result": True, "reason": "Clear ✓"}
                      ]}
                  ]},
                 {"rule": "geographic_scope_met/1", "label": "Geographic Coverage", "result": True,
                  "sub_sub_checks": [
                      {"label": "Location check", "result": True, "leaf_checks": [
                          {"check": "Continental US", "fact": "incident_location(C, continental_us)", "result": True, "reason": "In zone ✓"}
                      ]}
                  ]},
                 {"rule": "activity_not_excluded/1", "label": "Activity Exclusions", "result": True,
                  "sub_sub_checks": [
                      {"label": "Activity check", "result": True, "leaf_checks": [
                          {"check": "Normal driving", "fact": "activity(C, normal_driving)", "result": True, "reason": "Permitted ✓"}
                      ]}
                  ]}
             ]},
            {"id": "b4", "label": "Claim Procedure Followed", "icon": "📋", "result": True,
             "sub_checks": [
                 {"rule": "reported_in_time/1", "label": "Reporting Timeline", "result": True,
                  "sub_sub_checks": [
                      {"label": "Deadline check", "result": True, "leaf_checks": [
                          {"check": "Reported ≤ 30 days", "fact": "days_since_incident(C, 5)", "result": True, "reason": "5 ≤ 30 ✓"}
                      ]}
                  ]},
                 {"rule": "evidence_complete/1", "label": "Police Report Verification", "result": True,
                  "sub_sub_checks": [
                      {"label": "Report check", "result": True, "leaf_checks": [
                          {"check": "Police report on file", "fact": "police_report(C, true)", "result": True, "reason": "Report filed ✓"}
                      ]}
                  ]},
                 {"rule": "fraud_cleared/1", "label": "Fraud Indicator Screening", "result": True,
                  "sub_sub_checks": [
                      {"label": "Fraud check", "result": True, "leaf_checks": [
                          {"check": "No fraud flags", "fact": "fraud_indicator(C, false)", "result": True, "reason": "Clean ✓"}
                      ]}
                  ]}
             ]}
        ]
    },
    {
        "id": "claim_auto_2",
        "claimant": "Marcia Delgado",
        "date": "2024-06-22",
        "incident_date": "2024-06-20",
        "description": "Single vehicle accident on Highway 101. Vehicle drifted off the road and struck a guardrail at 65 mph. Responding officers administered a breathalyzer recording BAC of 0.14% — nearly double the legal limit of 0.08%.",
        "amount": "$12,000",
        "expected": "INVALID",
        "facts_prolog": [
            "age(claim_auto_2, 28).",
            "driving_experience_months(claim_auto_2, 84).",
            "license_valid(claim_auto_2, true).",
            "license_expired(claim_auto_2, false).",
            "license_jurisdiction(claim_auto_2, us_state).",
            "dui_history(claim_auto_2, 0).",
            "vehicle_ownership(claim_auto_2, own).",
            "vehicle_class(claim_auto_2, passenger).",
            "vehicle_weight_kg(claim_auto_2, 1420).",
            "bac(claim_auto_2, 0.14).",
            "under_influence_narcotics(claim_auto_2, false).",
            "incident_location(claim_auto_2, continental_us).",
            "activity(claim_auto_2, normal_driving).",
            "days_since_incident(claim_auto_2, 2).",
            "police_report(claim_auto_2, true).",
            "fraud_indicator(claim_auto_2, false)."
        ],
        "validation_tree": [
            {"id": "b1", "label": "Driver Fully Eligible", "icon": "👤", "result": True,
             "sub_checks": [
                 {"rule": "age_eligible/1", "label": "Minimum Age & Experience", "result": True,
                  "sub_sub_checks": [
                      {"label": "Age checks", "result": True, "leaf_checks": [
                          {"check": "Age ≥ 21", "fact": "age(C, 28)", "result": True, "reason": "28 ≥ 21 ✓"}
                      ]}
                  ]},
                 {"rule": "license_compliant/1", "label": "Licence Validity", "result": True,
                  "sub_sub_checks": [
                      {"label": "Licence checks", "result": True, "leaf_checks": [
                          {"check": "Licence valid", "fact": "license_valid(C, true)", "result": True, "reason": "Active ✓"},
                          {"check": "Not expired", "fact": "license_expired(C, false)", "result": True, "reason": "Not expired ✓"},
                          {"check": "Jurisdiction recognised", "fact": "license_jurisdiction(C, us_state)", "result": True, "reason": "US state ✓"}
                      ]}
                  ]},
                 {"rule": "driving_history_acceptable/1", "label": "Driving History", "result": True,
                  "sub_sub_checks": [
                      {"label": "History checks", "result": True, "leaf_checks": [
                          {"check": "DUI count", "fact": "dui_history(C, 0)", "result": True, "reason": "No DUI ✓"}
                      ]}
                  ]}
             ]},
            {"id": "b2", "label": "Vehicle Authorization Valid", "icon": "🚗", "result": True,
             "sub_checks": [
                 {"rule": "ownership_established/1", "label": "Ownership Verification", "result": True,
                  "sub_sub_checks": [
                      {"label": "Ownership check", "result": True, "leaf_checks": [
                          {"check": "Owned by insured", "fact": "vehicle_ownership(C, own)", "result": True, "reason": "Confirmed ✓"}
                      ]}
                  ]},
                 {"rule": "vehicle_type_covered/1", "label": "Class & Weight", "result": True,
                  "sub_sub_checks": [
                      {"label": "Type checks", "result": True, "leaf_checks": [
                          {"check": "Passenger class", "fact": "vehicle_class(C, passenger)", "result": True, "reason": "Passenger ✓"},
                          {"check": "Weight ≤ 3,500 kg", "fact": "vehicle_weight_kg(C, 1420)", "result": True, "reason": "1,420 ≤ 3,500 ✓"}
                      ]}
                  ]}
             ]},
            {"id": "b3", "label": "Incident Circumstances Covered", "icon": "🔍", "result": False,
             "sub_checks": [
                 {"rule": "sobriety_confirmed/1", "label": "Sobriety Verification", "result": False,
                  "sub_sub_checks": [
                      {"label": "Sobriety checks", "result": False, "leaf_checks": [
                          {"check": "BAC ≤ 0.08 g/dL", "fact": "bac(C, 0.14)", "result": False, "reason": "0.14 > 0.08 — DUI VIOLATION ✗"},
                          {"check": "No narcotics", "fact": "under_influence_narcotics(C, false)", "result": True, "reason": "Clear ✓"}
                      ]}
                  ]},
                 {"rule": "geographic_scope_met/1", "label": "Geographic Coverage", "result": True,
                  "sub_sub_checks": [
                      {"label": "Location check", "result": True, "leaf_checks": [
                          {"check": "Continental US", "fact": "incident_location(C, continental_us)", "result": True, "reason": "In zone ✓"}
                      ]}
                  ]},
                 {"rule": "activity_not_excluded/1", "label": "Activity Exclusions", "result": True,
                  "sub_sub_checks": [
                      {"label": "Activity check", "result": True, "leaf_checks": [
                          {"check": "No excluded activity", "fact": "activity(C, normal_driving)", "result": True, "reason": "Normal driving ✓"}
                      ]}
                  ]}
             ]},
            {"id": "b4", "label": "Claim Procedure Followed", "icon": "📋", "result": True,
             "sub_checks": [
                 {"rule": "reported_in_time/1", "label": "Reporting Timeline", "result": True,
                  "sub_sub_checks": [
                      {"label": "Deadline check", "result": True, "leaf_checks": [
                          {"check": "Reported ≤ 30 days", "fact": "days_since_incident(C, 2)", "result": True, "reason": "2 ≤ 30 ✓"}
                      ]}
                  ]},
                 {"rule": "evidence_complete/1", "label": "Police Report", "result": True,
                  "sub_sub_checks": [
                      {"label": "Report check", "result": True, "leaf_checks": [
                          {"check": "Report filed", "fact": "police_report(C, true)", "result": True, "reason": "On file ✓"}
                      ]}
                  ]},
                 {"rule": "fraud_cleared/1", "label": "Fraud Screening", "result": True,
                  "sub_sub_checks": [
                      {"label": "Fraud check", "result": True, "leaf_checks": [
                          {"check": "No fraud flags", "fact": "fraud_indicator(C, false)", "result": True, "reason": "Clean ✓"}
                      ]}
                  ]}
             ]}
        ]
    }
],

"contract_health": [
    {
        "id": "claim_health_1",
        "claimant": "Priya Sharma",
        "date": "2024-05-20",
        "incident_date": "2024-05-18",
        "description": "Emergency appendectomy at St. Mary's Medical Center (in-network). Sudden acute appendicitis requiring immediate surgical intervention. No pre-existing condition. Policy active for 210 continuous days.",
        "amount": "$22,400",
        "expected": "VALID",
        "facts_prolog": [
            "is_emergency(claim_health_1, true).",
            "days_enrolled(claim_health_1, 210).",
            "enrollment_lapse(claim_health_1, false).",
            "pre_existing_condition(claim_health_1, false).",
            "provider_network(claim_health_1, in_network).",
            "claim_amount(claim_health_1, 22400).",
            "prior_authorization(claim_health_1, false).",
            "cosmetic_only(claim_health_1, false).",
            "annual_deductible_met(claim_health_1, true).",
            "cumulative_claims(claim_health_1, 22400).",
            "days_since_service(claim_health_1, 2)."
        ],
        "validation_tree": [
            {"id": "b1", "label": "Enrollment Requirements Met", "icon": "📅", "result": True,
             "sub_checks": [
                 {"rule": "continuous_enrollment_satisfied/1", "label": "Continuous Enrollment Check", "result": True,
                  "sub_sub_checks": [
                      {"label": "Enrollment checks", "result": True, "leaf_checks": [
                          {"check": "Emergency override?", "fact": "is_emergency(C, true)", "result": True, "reason": "Emergency waives 90-day wait ✓"}
                      ]}
                  ]},
                 {"rule": "pre_existing_waiting_satisfied/1", "label": "Pre-existing Condition Wait", "result": True,
                  "sub_sub_checks": [
                      {"label": "Pre-existing check", "result": True, "leaf_checks": [
                          {"check": "Pre-existing present?", "fact": "pre_existing_condition(C, false)", "result": True, "reason": "No pre-existing ✓"}
                      ]}
                  ]}
             ]},
            {"id": "b2", "label": "Coverage Applicable", "icon": "🏥", "result": True,
             "sub_checks": [
                 {"rule": "provider_network_compliant/1", "label": "Provider Network Status", "result": True,
                  "sub_sub_checks": [
                      {"label": "Network check", "result": True, "leaf_checks": [
                          {"check": "In-network provider", "fact": "provider_network(C, in_network)", "result": True, "reason": "In-network 100% ✓"}
                      ]}
                  ]},
                 {"rule": "authorization_obtained_if_needed/1", "label": "Prior Authorization Gate", "result": True,
                  "sub_sub_checks": [
                      {"label": "Auth check", "result": True, "leaf_checks": [
                          {"check": "Emergency bypasses auth", "fact": "is_emergency(C, true)", "result": True, "reason": "Emergency override ✓"}
                      ]}
                  ]},
                 {"rule": "not_cosmetic_only/1", "label": "Medical Necessity Check", "result": True,
                  "sub_sub_checks": [
                      {"label": "Cosmetic check", "result": True, "leaf_checks": [
                          {"check": "Not purely cosmetic", "fact": "cosmetic_only(C, false)", "result": True, "reason": "Medical procedure ✓"}
                      ]}
                  ]}
             ]},
            {"id": "b3", "label": "Financial Limits Satisfied", "icon": "💰", "result": True,
             "sub_checks": [
                 {"rule": "deductible_status_ok/1", "label": "Annual Deductible Status", "result": True,
                  "sub_sub_checks": [
                      {"label": "Deductible check", "result": True, "leaf_checks": [
                          {"check": "Emergency bypasses deductible", "fact": "is_emergency(C, true)", "result": True, "reason": "Deductible waived ✓"}
                      ]}
                  ]},
                 {"rule": "within_lifetime_max/1", "label": "Lifetime Maximum Check", "result": True,
                  "sub_sub_checks": [
                      {"label": "Lifetime max check", "result": True, "leaf_checks": [
                          {"check": "Cumulative ≤ $500,000", "fact": "cumulative_claims(C, 22400)", "result": True, "reason": "$22,400 ≤ $500,000 ✓"}
                      ]}
                  ]}
             ]},
            {"id": "b4", "label": "Timely Submission", "icon": "🕒", "result": True,
             "sub_checks": [
                 {"rule": "timely_submission/1", "label": "180-Day Submission Deadline", "result": True,
                  "sub_sub_checks": [
                      {"label": "Deadline check", "result": True, "leaf_checks": [
                          {"check": "Filed within 180 days", "fact": "days_since_service(C, 2)", "result": True, "reason": "2 ≤ 180 ✓"}
                      ]}
                  ]}
             ]}
        ]
    },
    {
        "id": "claim_health_2",
        "claimant": "George Whitfield",
        "date": "2024-07-10",
        "incident_date": "2024-07-05",
        "description": "Elective knee replacement for osteoarthritis diagnosed 3 years prior. Patient enrolled only 45 days ago, no prior authorisation obtained for $35,000 procedure. Three distinct violations: enrollment, waiting period, and prior auth.",
        "amount": "$35,000",
        "expected": "INVALID",
        "facts_prolog": [
            "is_emergency(claim_health_2, false).",
            "days_enrolled(claim_health_2, 45).",
            "enrollment_lapse(claim_health_2, false).",
            "pre_existing_condition(claim_health_2, true).",
            "condition_type(claim_health_2, standard).",
            "months_since_enrollment(claim_health_2, 1.5).",
            "provider_network(claim_health_2, in_network).",
            "claim_amount(claim_health_2, 35000).",
            "prior_authorization(claim_health_2, false).",
            "cosmetic_only(claim_health_2, false).",
            "annual_deductible_met(claim_health_2, true).",
            "cumulative_claims(claim_health_2, 35000).",
            "days_since_service(claim_health_2, 5)."
        ],
        "validation_tree": [
            {"id": "b1", "label": "Enrollment Requirements Met", "icon": "📅", "result": False,
             "sub_checks": [
                 {"rule": "continuous_enrollment_satisfied/1", "label": "Continuous Enrollment Check", "result": False,
                  "sub_sub_checks": [
                      {"label": "Enrollment checks", "result": False, "leaf_checks": [
                          {"check": "Emergency override?", "fact": "is_emergency(C, false)", "result": False, "reason": "Not emergency ✗"},
                          {"check": "Enrolled ≥ 90 days?", "fact": "days_enrolled(C, 45)", "result": False, "reason": "45 < 90 days — VIOLATION ✗"}
                      ]}
                  ]},
                 {"rule": "pre_existing_waiting_satisfied/1", "label": "Pre-existing Condition Wait", "result": False,
                  "sub_sub_checks": [
                      {"label": "Pre-existing checks", "result": False, "leaf_checks": [
                          {"check": "Pre-existing present?", "fact": "pre_existing_condition(C, true)", "result": False, "reason": "Pre-existing detected ✗"},
                          {"check": "Waiting ≥ 12 months?", "fact": "months_since_enrollment(C, 1.5)", "result": False, "reason": "1.5 < 12 months — VIOLATION ✗"}
                      ]}
                  ]}
             ]},
            {"id": "b2", "label": "Coverage Applicable", "icon": "🏥", "result": False,
             "sub_checks": [
                 {"rule": "provider_network_compliant/1", "label": "Provider Network", "result": True,
                  "sub_sub_checks": [
                      {"label": "Network check", "result": True, "leaf_checks": [
                          {"check": "In-network", "fact": "provider_network(C, in_network)", "result": True, "reason": "In-network ✓"}
                      ]}
                  ]},
                 {"rule": "authorization_obtained_if_needed/1", "label": "Prior Authorization Gate", "result": False,
                  "sub_sub_checks": [
                      {"label": "Auth checks", "result": False, "leaf_checks": [
                          {"check": "Emergency?", "fact": "is_emergency(C, false)", "result": False, "reason": "Not emergency ✗"},
                          {"check": "Amount ≤ $5,000?", "fact": "claim_amount(C, 35000)", "result": False, "reason": "$35,000 > $5,000 ✗"},
                          {"check": "Prior auth obtained?", "fact": "prior_authorization(C, false)", "result": False, "reason": "No auth — VIOLATION ✗"}
                      ]}
                  ]},
                 {"rule": "not_cosmetic_only/1", "label": "Medical Necessity", "result": True,
                  "sub_sub_checks": [
                      {"label": "Cosmetic check", "result": True, "leaf_checks": [
                          {"check": "Not cosmetic", "fact": "cosmetic_only(C, false)", "result": True, "reason": "Medical need ✓"}
                      ]}
                  ]}
             ]},
            {"id": "b3", "label": "Financial Limits Satisfied", "icon": "💰", "result": True,
             "sub_checks": [
                 {"rule": "deductible_status_ok/1", "label": "Annual Deductible", "result": True,
                  "sub_sub_checks": [
                      {"label": "Deductible check", "result": True, "leaf_checks": [
                          {"check": "Deductible met", "fact": "annual_deductible_met(C, true)", "result": True, "reason": "Satisfied ✓"}
                      ]}
                  ]},
                 {"rule": "within_lifetime_max/1", "label": "Lifetime Maximum", "result": True,
                  "sub_sub_checks": [
                      {"label": "Lifetime max check", "result": True, "leaf_checks": [
                          {"check": "Within $500k limit", "fact": "cumulative_claims(C, 35000)", "result": True, "reason": "$35,000 ≤ $500,000 ✓"}
                      ]}
                  ]}
             ]},
            {"id": "b4", "label": "Timely Submission", "icon": "🕒", "result": True,
             "sub_checks": [
                 {"rule": "timely_submission/1", "label": "Submission Deadline", "result": True,
                  "sub_sub_checks": [
                      {"label": "Deadline check", "result": True, "leaf_checks": [
                          {"check": "Filed ≤ 180 days", "fact": "days_since_service(C, 5)", "result": True, "reason": "5 ≤ 180 ✓"}
                      ]}
                  ]}
             ]}
        ]
    }
],

"contract_travel": [
    {
        "id": "claim_travel_1",
        "claimant": "Hana Kobayashi",
        "date": "2024-04-10",
        "incident_date": "2024-04-08",
        "description": "Trip cancellation due to sudden hospitalisation of insured's mother with a cardiac event. Policy purchased 10 days after booking deposit. Full documentation provided including hospital admission letter and attending physician statement.",
        "amount": "$3,200",
        "expected": "VALID",
        "facts_prolog": [
            "days_after_deposit(claim_travel_1, 10).",
            "trip_commenced_at_purchase(claim_travel_1, false).",
            "policy_lapse(claim_travel_1, false).",
            "premium_paid(claim_travel_1, true).",
            "claim_type(claim_travel_1, trip_cancellation).",
            "cancellation_reason(claim_travel_1, illness).",
            "fit_at_purchase(claim_travel_1, true).",
            "destination_advisory_level(claim_travel_1, 1).",
            "activity(claim_travel_1, none).",
            "adventure_rider(claim_travel_1, false).",
            "documentation_provided(claim_travel_1, true).",
            "under_influence(claim_travel_1, false).",
            "war_related(claim_travel_1, false)."
        ],
        "validation_tree": [
            {"id": "b1", "label": "Policy Validity Confirmed", "icon": "📜", "result": True,
             "sub_checks": [
                 {"rule": "purchased_within_window/1", "label": "Purchase Window Compliance", "result": True,
                  "sub_sub_checks": [
                      {"label": "Window check", "result": True, "leaf_checks": [
                          {"check": "Purchased ≤ 21 days after deposit", "fact": "days_after_deposit(C, 10)", "result": True, "reason": "10 ≤ 21 days ✓"}
                      ]}
                  ]},
                 {"rule": "trip_not_already_commenced/1", "label": "Trip Status at Purchase", "result": True,
                  "sub_sub_checks": [
                      {"label": "Trip status check", "result": True, "leaf_checks": [
                          {"check": "Pre-departure purchase", "fact": "trip_commenced_at_purchase(C, false)", "result": True, "reason": "Pre-departure ✓"}
                      ]}
                  ]},
                 {"rule": "policy_status_active/1", "label": "Policy Active Status", "result": True,
                  "sub_sub_checks": [
                      {"label": "Active status checks", "result": True, "leaf_checks": [
                          {"check": "No lapse", "fact": "policy_lapse(C, false)", "result": True, "reason": "Active ✓"},
                          {"check": "Premium paid", "fact": "premium_paid(C, true)", "result": True, "reason": "Current ✓"}
                      ]}
                  ]}
             ]},
            {"id": "b2", "label": "Covered Event Occurred", "icon": "🎯", "result": True,
             "sub_checks": [
                 {"rule": "valid_cancellation_reason/1", "label": "Cancellation Reason Verification", "result": True,
                  "sub_sub_checks": [
                      {"label": "Reason checks", "result": True, "leaf_checks": [
                          {"check": "Claim type is cancellation", "fact": "claim_type(C, trip_cancellation)", "result": True, "reason": "Cancellation ✓"},
                          {"check": "Reason is in covered list", "fact": "cancellation_reason(C, illness)", "result": True, "reason": "Illness is covered ✓"}
                      ]}
                  ]}
             ]},
            {"id": "b3", "label": "Risk Profile Eligible", "icon": "⚠️", "result": True,
             "sub_checks": [
                 {"rule": "medically_fit_at_purchase/1", "label": "Medical Fitness at Purchase", "result": True,
                  "sub_sub_checks": [
                      {"label": "Fitness check", "result": True, "leaf_checks": [
                          {"check": "Fit at purchase", "fact": "fit_at_purchase(C, true)", "result": True, "reason": "No known conditions ✓"}
                      ]}
                  ]},
                 {"rule": "destination_covered/1", "label": "Destination Advisory Check", "result": True,
                  "sub_sub_checks": [
                      {"label": "Advisory check", "result": True, "leaf_checks": [
                          {"check": "Advisory level < 4", "fact": "destination_advisory_level(C, 1)", "result": True, "reason": "Level 1 ✓"}
                      ]}
                  ]},
                 {"rule": "activity_covered/1", "label": "Activity Coverage", "result": True,
                  "sub_sub_checks": [
                      {"label": "Activity check", "result": True, "leaf_checks": [
                          {"check": "No extreme sport", "fact": "activity(C, none)", "result": True, "reason": "No activity ✓"}
                      ]}
                  ]}
             ]},
            {"id": "b4", "label": "Documentation Complete", "icon": "📁", "result": True,
             "sub_checks": [
                 {"rule": "timely_notification/1", "label": "Notification Timing", "result": True,
                  "sub_sub_checks": [
                      {"label": "Notification check", "result": True, "leaf_checks": [
                          {"check": "Not baggage — 24h N/A", "fact": "claim_type(C, trip_cancellation)", "result": True, "reason": "N/A for cancellation ✓"}
                      ]}
                  ]},
                 {"rule": "documents_provided/1", "label": "Documentation", "result": True,
                  "sub_sub_checks": [
                      {"label": "Documentation check", "result": True, "leaf_checks": [
                          {"check": "All docs submitted", "fact": "documentation_provided(C, true)", "result": True, "reason": "On file ✓"}
                      ]}
                  ]},
                 {"rule": "exclusions_clear/1", "label": "Exclusion Screening", "result": True,
                  "sub_sub_checks": [
                      {"label": "Exclusion checks", "result": True, "leaf_checks": [
                          {"check": "Not under influence", "fact": "under_influence(C, false)", "result": True, "reason": "Sober ✓"},
                          {"check": "Not war-related", "fact": "war_related(C, false)", "result": True, "reason": "No war ✓"}
                      ]}
                  ]}
             ]}
        ]
    },
    {
        "id": "claim_travel_2",
        "claimant": "Dmitri Volkov",
        "date": "2024-08-30",
        "incident_date": "2024-08-25",
        "description": "Medical claim for injuries during a BASE jumping excursion in the Swiss Alps. Policy purchased 5 days after deposit but does NOT include the Adventure Rider supplement. Claims $15,000 for emergency evacuation and treatment.",
        "amount": "$15,000",
        "expected": "INVALID",
        "facts_prolog": [
            "days_after_deposit(claim_travel_2, 5).",
            "trip_commenced_at_purchase(claim_travel_2, false).",
            "policy_lapse(claim_travel_2, false).",
            "premium_paid(claim_travel_2, true).",
            "claim_type(claim_travel_2, medical).",
            "medical_emergency(claim_travel_2, true).",
            "fit_at_purchase(claim_travel_2, true).",
            "destination_advisory_level(claim_travel_2, 1).",
            "activity(claim_travel_2, base_jumping).",
            "adventure_rider(claim_travel_2, false).",
            "documentation_provided(claim_travel_2, true).",
            "under_influence(claim_travel_2, false).",
            "war_related(claim_travel_2, false)."
        ],
        "validation_tree": [
            {"id": "b1", "label": "Policy Validity Confirmed", "icon": "📜", "result": True,
             "sub_checks": [
                 {"rule": "purchased_within_window/1", "label": "Purchase Window", "result": True,
                  "sub_sub_checks": [
                      {"label": "Window check", "result": True, "leaf_checks": [
                          {"check": "Purchased ≤ 21 days", "fact": "days_after_deposit(C, 5)", "result": True, "reason": "5 ≤ 21 ✓"}
                      ]}
                  ]},
                 {"rule": "trip_not_already_commenced/1", "label": "Trip Status", "result": True,
                  "sub_sub_checks": [
                      {"label": "Trip status check", "result": True, "leaf_checks": [
                          {"check": "Pre-departure", "fact": "trip_commenced_at_purchase(C, false)", "result": True, "reason": "Pre-departure ✓"}
                      ]}
                  ]},
                 {"rule": "policy_status_active/1", "label": "Active Status", "result": True,
                  "sub_sub_checks": [
                      {"label": "Active status checks", "result": True, "leaf_checks": [
                          {"check": "No lapse", "fact": "policy_lapse(C, false)", "result": True, "reason": "Active ✓"},
                          {"check": "Premium paid", "fact": "premium_paid(C, true)", "result": True, "reason": "Paid ✓"}
                      ]}
                  ]}
             ]},
            {"id": "b2", "label": "Covered Event Occurred", "icon": "🎯", "result": True,
             "sub_checks": [
                 {"rule": "medical_event_covered/1", "label": "Medical Event Verification", "result": True,
                  "sub_sub_checks": [
                      {"label": "Medical event checks", "result": True, "leaf_checks": [
                          {"check": "Medical claim type", "fact": "claim_type(C, medical)", "result": True, "reason": "Medical ✓"},
                          {"check": "Emergency confirmed", "fact": "medical_emergency(C, true)", "result": True, "reason": "Emergency ✓"}
                      ]}
                  ]}
             ]},
            {"id": "b3", "label": "Risk Profile Eligible", "icon": "⚠️", "result": False,
             "sub_checks": [
                 {"rule": "medically_fit_at_purchase/1", "label": "Medical Fitness", "result": True,
                  "sub_sub_checks": [
                      {"label": "Fitness check", "result": True, "leaf_checks": [
                          {"check": "Fit at purchase", "fact": "fit_at_purchase(C, true)", "result": True, "reason": "No known conditions ✓"}
                      ]}
                  ]},
                 {"rule": "destination_covered/1", "label": "Destination Advisory", "result": True,
                  "sub_sub_checks": [
                      {"label": "Advisory check", "result": True, "leaf_checks": [
                          {"check": "Advisory level < 4", "fact": "destination_advisory_level(C, 1)", "result": True, "reason": "Level 1 ✓"}
                      ]}
                  ]},
                 {"rule": "activity_covered/1", "label": "Activity Coverage Check", "result": False,
                  "sub_sub_checks": [
                      {"label": "Activity checks", "result": False, "leaf_checks": [
                          {"check": "Activity is extreme sport?", "fact": "activity(C, base_jumping)", "result": False, "reason": "BASE jumping — EXCLUDED ✗"},
                          {"check": "Adventure Rider purchased?", "fact": "adventure_rider(C, false)", "result": False, "reason": "No Rider — VIOLATION ✗"}
                      ]}
                  ]}
             ]},
            {"id": "b4", "label": "Documentation Complete", "icon": "📁", "result": True,
             "sub_checks": [
                 {"rule": "documents_provided/1", "label": "Documentation", "result": True,
                  "sub_sub_checks": [
                      {"label": "Documentation check", "result": True, "leaf_checks": [
                          {"check": "Docs submitted", "fact": "documentation_provided(C, true)", "result": True, "reason": "On file ✓"}
                      ]}
                  ]},
                 {"rule": "exclusions_clear/1", "label": "Exclusion Screening", "result": True,
                  "sub_sub_checks": [
                      {"label": "Exclusion checks", "result": True, "leaf_checks": [
                          {"check": "Not under influence", "fact": "under_influence(C, false)", "result": True, "reason": "Sober ✓"},
                          {"check": "Not war-related", "fact": "war_related(C, false)", "result": True, "reason": "No war ✓"}
                      ]}
                  ]}
             ]}
        ]
    }
],

"contract_accident": [
    {
        "id": "claim_accident_1",
        "claimant": "Samuel Okonkwo",
        "date": "2024-02-14",
        "incident_date": "2024-02-10",
        "description": "Workplace fall from scaffolding at a construction site, resulting in a fractured left arm and two broken ribs. Incident occurred during regular working hours. Police and medical reports filed. Insurer notified within 4 days.",
        "amount": "$18,000",
        "expected": "VALID",
        "facts_prolog": [
            "accident_type(claim_accident_1, fall).",
            "self_inflicted(claim_accident_1, false).",
            "cause(claim_accident_1, workplace_accident).",
            "age(claim_accident_1, 42).",
            "intoxicated(claim_accident_1, false).",
            "narcotics_influence(claim_accident_1, false).",
            "activity(claim_accident_1, occupational).",
            "medical_evidence(claim_accident_1, true).",
            "attending_physician_licensed(claim_accident_1, true).",
            "injury_severity(claim_accident_1, moderate).",
            "claim_type(claim_accident_1, disability).",
            "days_to_notify(claim_accident_1, 4).",
            "claim_amount_usd(claim_accident_1, 18000)."
        ],
        "validation_tree": [
            {"id": "b1", "label": "Accidental Origin Confirmed", "icon": "⚡", "result": True,
             "sub_checks": [
                 {"rule": "cause_is_accidental/1", "label": "Accident Type Classification", "result": True,
                  "sub_sub_checks": [
                      {"label": "Accident type checks", "result": True, "leaf_checks": [
                          {"check": "Cause is a fall", "fact": "accident_type(C, fall)", "result": True, "reason": "Physical trauma ✓"},
                          {"check": "Category covered", "fact": "accident_category(fall, physical_trauma)", "result": True, "reason": "physical_trauma ✓"}
                      ]}
                  ]},
                 {"rule": "not_self_inflicted/1", "label": "Self-Infliction Exclusion", "result": True,
                  "sub_sub_checks": [
                      {"label": "Self-infliction check", "result": True, "leaf_checks": [
                          {"check": "Not self-inflicted", "fact": "self_inflicted(C, false)", "result": True, "reason": "External event ✓"}
                      ]}
                  ]},
                 {"rule": "not_excluded_cause/1", "label": "Cause Exclusion Screening", "result": True,
                  "sub_sub_checks": [
                      {"label": "Cause exclusion checks", "result": True, "leaf_checks": [
                          {"check": "Cause class permitted?", "fact": "cause(C, workplace_accident)", "result": True, "reason": "occupational_class — permitted ✓"}
                      ]}
                  ]},
                 {"rule": "sole_cause_verified/1", "label": "Sole Cause Verification", "result": True,
                  "sub_sub_checks": [
                      {"label": "Sole cause checks", "result": True, "leaf_checks": [
                          {"check": "No contributing disease", "fact": "comorbidity_flag(C, none)", "result": True, "reason": "No comorbidity ✓"}
                      ]}
                  ]}
             ]},
            {"id": "b2", "label": "Claimant Fully Eligible", "icon": "👤", "result": True,
             "sub_checks": [
                 {"rule": "age_in_range/1", "label": "Age Band Verification", "result": True,
                  "sub_sub_checks": [
                      {"label": "Age checks", "result": True, "leaf_checks": [
                          {"check": "Age ≥ 18", "fact": "age(C, 42)", "result": True, "reason": "42 ≥ 18 ✓"},
                          {"check": "Age ≤ 70", "fact": "age(C, 42)", "result": True, "reason": "42 ≤ 70 ✓"}
                      ]}
                  ]},
                 {"rule": "intoxication_negative/1", "label": "Substance Check", "result": True,
                  "sub_sub_checks": [
                      {"label": "Substance checks", "result": True, "leaf_checks": [
                          {"check": "Not intoxicated", "fact": "intoxicated(C, false)", "result": True, "reason": "Sober ✓"},
                          {"check": "No narcotics", "fact": "narcotics_influence(C, false)", "result": True, "reason": "Clear ✓"}
                      ]}
                  ]},
                 {"rule": "not_professional_sport/1", "label": "Professional Sport Check", "result": True,
                  "sub_sub_checks": [
                      {"label": "Sport check", "result": True, "leaf_checks": [
                          {"check": "Not paid athlete", "fact": "activity(C, occupational)", "result": True, "reason": "Not sport ✓"}
                      ]}
                  ]}
             ]},
            {"id": "b3", "label": "Medical Criteria Met", "icon": "🩺", "result": True,
             "sub_checks": [
                 {"rule": "medical_evidence_provided/1", "label": "Medical Documentation", "result": True,
                  "sub_sub_checks": [
                      {"label": "Documentation checks", "result": True, "leaf_checks": [
                          {"check": "Medical evidence", "fact": "medical_evidence(C, true)", "result": True, "reason": "On file ✓"},
                          {"check": "Physician licensed", "fact": "attending_physician_licensed(C, true)", "result": True, "reason": "Licensed ✓"}
                      ]}
                  ]},
                 {"rule": "injury_consistent_with_claim/1", "label": "Injury-Claim Compatibility", "result": True,
                  "sub_sub_checks": [
                      {"label": "Compatibility checks", "result": True, "leaf_checks": [
                          {"check": "Moderate severity + disability", "fact": "injury_severity(C, moderate)", "result": True, "reason": "Compatible ✓"},
                          {"check": "Amount ≤ $250,000", "fact": "claim_amount_usd(C, 18000)", "result": True, "reason": "$18,000 ≤ $250,000 ✓"}
                      ]}
                  ]}
             ]},
            {"id": "b4", "label": "Procedure Compliant", "icon": "📋", "result": True,
             "sub_checks": [
                 {"rule": "notification_in_time/1", "label": "Notification Deadline", "result": True,
                  "sub_sub_checks": [
                      {"label": "Deadline check", "result": True, "leaf_checks": [
                          {"check": "Disability notify ≤ 14 days", "fact": "days_to_notify(C, 4)", "result": True, "reason": "4 ≤ 14 ✓"}
                      ]}
                  ]},
                 {"rule": "benefit_type_valid/1", "label": "Benefit Type Validation", "result": True,
                  "sub_sub_checks": [
                      {"label": "Benefit type checks", "result": True, "leaf_checks": [
                          {"check": "Benefit type is covered", "fact": "claim_type(C, disability)", "result": True, "reason": "Disability benefit valid ✓"}
                      ]}
                  ]},
                 {"rule": "within_benefit_limits/1", "label": "Benefit Limit Check", "result": True,
                  "sub_sub_checks": [
                      {"label": "Limit check", "result": True, "leaf_checks": [
                          {"check": "Claim ≤ $250,000", "fact": "claim_amount_usd(C, 18000)", "result": True, "reason": "$18,000 ≤ $250,000 ✓"}
                      ]}
                  ]}
             ]}
        ]
    },
    {
        "id": "claim_accident_2",
        "claimant": "Fiona MacAllister",
        "date": "2024-11-05",
        "incident_date": "2024-10-01",
        "description": "Fractured collarbone sustained during a semi-professional rugby match. Claimant is a paid player for a local club team. Notification filed 35 days after the incident — 21 days beyond the 14-day disability window. Two violations identified.",
        "amount": "$9,500",
        "expected": "INVALID",
        "facts_prolog": [
            "accident_type(claim_accident_2, collision).",
            "self_inflicted(claim_accident_2, false).",
            "cause(claim_accident_2, professional_sports).",
            "age(claim_accident_2, 26).",
            "intoxicated(claim_accident_2, false).",
            "narcotics_influence(claim_accident_2, false).",
            "activity(claim_accident_2, professional_sports).",
            "medical_evidence(claim_accident_2, true).",
            "attending_physician_licensed(claim_accident_2, true).",
            "injury_severity(claim_accident_2, moderate).",
            "claim_type(claim_accident_2, disability).",
            "days_to_notify(claim_accident_2, 35).",
            "claim_amount_usd(claim_accident_2, 9500)."
        ],
        "validation_tree": [
            {"id": "b1", "label": "Accidental Origin Confirmed", "icon": "⚡", "result": False,
             "sub_checks": [
                 {"rule": "cause_is_accidental/1", "label": "Accident Type Classification", "result": True,
                  "sub_sub_checks": [
                      {"label": "Accident type checks", "result": True, "leaf_checks": [
                          {"check": "Cause recognisable as accident", "fact": "accident_type(C, collision)", "result": True, "reason": "Collision type ✓"}
                      ]}
                  ]},
                 {"rule": "not_self_inflicted/1", "label": "Self-Infliction Exclusion", "result": True,
                  "sub_sub_checks": [
                      {"label": "Self-infliction check", "result": True, "leaf_checks": [
                          {"check": "Not self-inflicted", "fact": "self_inflicted(C, false)", "result": True, "reason": "External ✓"}
                      ]}
                  ]},
                 {"rule": "not_excluded_cause/1", "label": "Cause Exclusion Screening", "result": False,
                  "sub_sub_checks": [
                      {"label": "Cause exclusion checks", "result": False, "leaf_checks": [
                          {"check": "Cause not in exclusion list", "fact": "cause(C, professional_sports)", "result": False, "reason": "Professional sports is EXCLUDED ✗"}
                      ]}
                  ]}
             ]},
            {"id": "b2", "label": "Claimant Fully Eligible", "icon": "👤", "result": False,
             "sub_checks": [
                 {"rule": "age_in_range/1", "label": "Age Band", "result": True,
                  "sub_sub_checks": [
                      {"label": "Age checks", "result": True, "leaf_checks": [
                          {"check": "Age ≥ 18", "fact": "age(C, 26)", "result": True, "reason": "26 ≥ 18 ✓"},
                          {"check": "Age ≤ 70", "fact": "age(C, 26)", "result": True, "reason": "26 ≤ 70 ✓"}
                      ]}
                  ]},
                 {"rule": "intoxication_negative/1", "label": "Substance Check", "result": True,
                  "sub_sub_checks": [
                      {"label": "Substance checks", "result": True, "leaf_checks": [
                          {"check": "Not intoxicated", "fact": "intoxicated(C, false)", "result": True, "reason": "Sober ✓"},
                          {"check": "No narcotics", "fact": "narcotics_influence(C, false)", "result": True, "reason": "Clean ✓"}
                      ]}
                  ]},
                 {"rule": "not_professional_sport/1", "label": "Professional Sport Exclusion", "result": False,
                  "sub_sub_checks": [
                      {"label": "Substance & activity checks", "result": False, "leaf_checks": [
                          {"check": "Not intoxicated", "fact": "intoxicated(C, false)", "result": True, "reason": "Sober ✓"},
                          {"check": "No narcotics", "fact": "narcotics_influence(C, false)", "result": True, "reason": "Clear ✓"},
                          {"check": "Not professional sport?", "fact": "activity(C, professional_sports)", "result": False, "reason": "Paid sport — VIOLATION ✗"}
                      ]}
                  ]}
             ]},
            {"id": "b3", "label": "Medical Criteria Met", "icon": "🩺", "result": True,
             "sub_checks": [
                 {"rule": "medical_evidence_provided/1", "label": "Medical Documentation", "result": True,
                  "sub_sub_checks": [
                      {"label": "Documentation checks", "result": True, "leaf_checks": [
                          {"check": "Medical evidence", "fact": "medical_evidence(C, true)", "result": True, "reason": "On file ✓"},
                          {"check": "Physician licensed", "fact": "attending_physician_licensed(C, true)", "result": True, "reason": "Licensed ✓"}
                      ]}
                  ]},
                 {"rule": "injury_consistent_with_claim/1", "label": "Injury-Claim Compatibility", "result": True,
                  "sub_sub_checks": [
                      {"label": "Compatibility checks", "result": True, "leaf_checks": [
                          {"check": "Moderate severity + disability", "fact": "injury_severity(C, moderate)", "result": True, "reason": "Compatible ✓"},
                          {"check": "Amount ≤ $250,000", "fact": "claim_amount_usd(C, 9500)", "result": True, "reason": "$9,500 ≤ $250,000 ✓"}
                      ]}
                  ]}
             ]},
            {"id": "b4", "label": "Procedure Compliant", "icon": "📋", "result": False,
             "sub_checks": [
                 {"rule": "notification_in_time/1", "label": "Notification Deadline (OR gate)", "result": False,
                  "sub_sub_checks": [
                      {"label": "Deadline check", "result": False, "leaf_checks": [
                          {"check": "Death ≤ 30 days?", "fact": "claim_type(C, disability) — N/A", "result": False, "reason": "Not an accidental death claim ✗"},
                          {"check": "Disability ≤ 14 days?", "fact": "days_to_notify(C, 35)", "result": False, "reason": "35 > 14 — LATE NOTIFICATION ✗"}
                      ]}
                  ]},
                 {"rule": "benefit_type_valid/1", "label": "Benefit Type Valid", "result": True,
                  "sub_sub_checks": [
                      {"label": "Benefit checks", "result": True, "leaf_checks": [
                          {"check": "Recognised benefit type", "fact": "claim_type(C, disability)", "result": True, "reason": "Disability ✓"}
                      ]}
                  ]}
             ]}
        ]
    }
]

}


# ─────────────────────────────────────────────
#  BUILD OUTPUT
# ─────────────────────────────────────────────

def propagate_validation_results(validation_tree):
    """Force result propagation from deepest leaf to top-level branch."""

    def derive_leaf_result(leaf):
        return bool(leaf.get("result", False))

    def derive_sub_sub_result(sub_sub):
        leaves = sub_sub.get("leaf_checks") or []
        if leaves:
            sub_sub["result"] = all(derive_leaf_result(leaf) for leaf in leaves)
        else:
            sub_sub["result"] = bool(sub_sub.get("result", False))
        return sub_sub["result"]

    def derive_sub_result(sub):
        sub_sub_checks = sub.get("sub_sub_checks") or []
        leaves = sub.get("leaf_checks") or []

        if sub_sub_checks:
            sub["result"] = all(derive_sub_sub_result(sub_sub) for sub_sub in sub_sub_checks)
        elif leaves:
            sub["result"] = all(derive_leaf_result(leaf) for leaf in leaves)
        else:
            sub["result"] = bool(sub.get("result", False))
        return sub["result"]

    for branch in validation_tree:
        sub_checks = branch.get("sub_checks") or []
        if sub_checks:
            branch["result"] = all(derive_sub_result(sub) for sub in sub_checks)
        else:
            branch["result"] = bool(branch.get("result", False))

    overall_result = all(bool(branch.get("result", False)) for branch in validation_tree)
    return validation_tree, overall_result


def build_validation_hierarchy(claim_id, validation_tree):
    """Create nested, box-friendly validation tree for UI rendering."""

    def leaf_node(leaf):
        return {
            "kind": "leaf",
            "label": leaf.get("check", "Leaf check"),
            "fact": leaf.get("fact", ""),
            "reason": leaf.get("reason", ""),
            "result": bool(leaf.get("result", False)),
            "children": []
        }

    def sub_sub_node(sub_sub):
        leaves = [leaf_node(leaf) for leaf in (sub_sub.get("leaf_checks") or [])]
        node_result = bool(sub_sub.get("result", False)) if leaves else bool(sub_sub.get("result", False))
        if leaves:
            node_result = all(child["result"] for child in leaves)
        return {
            "kind": "sub_sub_check",
            "label": sub_sub.get("label", "Nested check"),
            "result": node_result,
            "children": leaves
        }

    def sub_node(sub):
        sub_sub_checks = sub.get("sub_sub_checks") or []
        leaves = sub.get("leaf_checks") or []

        if sub_sub_checks:
            children = [sub_sub_node(sub_sub) for sub_sub in sub_sub_checks]
            node_result = all(child["result"] for child in children)
        elif leaves:
            children = [leaf_node(leaf) for leaf in leaves]
            node_result = all(child["result"] for child in children)
        else:
            children = []
            node_result = bool(sub.get("result", False))

        return {
            "kind": "sub_check",
            "rule": sub.get("rule", "unknown_rule/1"),
            "label": sub.get("label", "Sub-check"),
            "result": node_result,
            "children": children
        }

    branches = []
    for branch in validation_tree:
        children = [sub_node(sub) for sub in (branch.get("sub_checks") or [])]
        branch_result = all(child["result"] for child in children) if children else bool(branch.get("result", False))
        branches.append({
            "kind": "branch",
            "id": branch.get("id", "branch"),
            "label": branch.get("label", "Branch"),
            "icon": branch.get("icon", ""),
            "result": branch_result,
            "children": children
        })

    overall_result = all(branch["result"] for branch in branches)
    return {
        "kind": "root",
        "label": f"valid_claim({claim_id})",
        "result": overall_result,
        "children": branches
    }


def build_output():
    output = {
        "contracts": [],
        "claims": {}
    }

    for contract in CONTRACTS:
        cid = contract["id"]
        contract_claims = CLAIMS.get(cid, [])
        output["claims"][cid] = []
        valid_count = 0
        invalid_count = 0

        for claim in contract_claims:
            validation_tree = json.loads(json.dumps(claim["validation_tree"]))
            validation_tree, propagated_result = propagate_validation_results(validation_tree)
            validation_hierarchy = build_validation_hierarchy(claim["id"], validation_tree)
            expected_status = "VALID" if propagated_result else "INVALID"

            if expected_status == "VALID":
                valid_count += 1
            else:
                invalid_count += 1

            output["claims"][cid].append({
                "id":             claim["id"],
                "claimant":       claim["claimant"],
                "date":           claim["date"],
                "incident_date":  claim["incident_date"],
                "description":    claim["description"],
                "amount":         claim["amount"],
                "expected":       expected_status,
                "facts_prolog":   claim["facts_prolog"],
                "validation_tree": validation_tree,
                "validation_hierarchy": validation_hierarchy,
            })

        output["contracts"].append({
            # ── Identity & display ──────────────────────
            "id":             cid,
            "name":           contract["name"],
            "type":           contract["type"],
            "insurer":        contract["insurer"],
            "policy_number":  contract["policy_number"],
            "effective_date": contract["effective_date"],
            "expiry_date":    contract["expiry_date"],
            "premium":        contract["premium"],
            "coverage":       contract["coverage"],
            "icon":           contract["icon"],
            "color":          contract["color"],
            "accent":         contract["accent"],
            "pdf_url":        contract["pdf_url"],
            # ── Derived counts ──────────────────────────
            "claim_count":    len(contract_claims),
            "valid_count":    valid_count,
            "invalid_count":  invalid_count,
            # ── Rich content ────────────────────────────
            "contract_sections":  contract["contract_sections"],
            "insurle_rules":      INSURLE_RULES[cid],
            "flowchart_nodes":    FLOWCHART_NODES[cid],
        })

    return output


if __name__ == "__main__":
    data = build_output()
    with open("insurle_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    total_contracts = len(data["contracts"])
    total_claims    = sum(len(v) for v in data["claims"].values())
    print(f"✅  Generated insurle_data.json")
    print(f"    Contracts   : {total_contracts}")
    print(f"    Claims      : {total_claims}")
    print(f"    Fields/contract: id · name · type · insurer · policy_number · effective_date ·")
    print(f"                     expiry_date · premium · coverage · icon · color · accent ·")
    print(f"                     pdf_url · claim_count · valid_count · invalid_count ·")
    print(f"                     contract_sections · insurle_rules · flowchart_nodes")
    print(f"    Fields/claim   : id · claimant · date · incident_date · description · amount ·")
    print(f"                     expected · facts_prolog · validation_tree")