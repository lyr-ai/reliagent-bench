"""Hand-normalised state writes for LongMemEval knowledge-update questions.

Track E-B (plan §9): the benchmark's ``has_answer`` flags identify WHICH turns
carry the writes; the SLOT and VALUE were read off each flagged turn by hand,
before any variant was run, and frozen here. Every variant receives exactly
these writes. Nothing below was changed after seeing a result.

Conventions
- ``writes``: (session_date, value) in session order; observed_at = session
  date; no validity dates (the benchmark carries none); no authority or
  confidence (the benchmark carries none).
- ``queries``: ("current", expected) → as_of = question_date;
  ("after", k, expected) → as_of = writes[k].date + 1 day, i.e. before the
  next write; ("direction", expected) → the adapter compares the last two
  values numerically ("up" / "down").
- values are canonical strings; gold was normalised to the same form.
- ``norm``: how the value was obtained — "explicit" (stated verbatim) or
  "derived" (e.g. "half of 10" → 5, "added a new coin" to 37 → 38).
"""

T = {
 # ── current_state ────────────────────────────────────────────────────────
 "01493427": dict(slot="postcards_added", writes=[("2023-08-11", "17"), ("2023-11-30", "25")], queries=[("current", "25")]),
 "06db6396": dict(slot="painting_projects", writes=[("2023-08-16", "4"), ("2023-10-09", "5")], queries=[("current", "5")]),
 "07741c45": dict(slot="old_sneakers_location", writes=[("2023-05-20", "under my bed"), ("2023-05-26", "in a shoe rack in my closet")], queries=[("current", "in a shoe rack in my closet")], norm="derived: second write is phrased as a plan"),
 "08e075c7": dict(slot="fitbit_months", writes=[("2023-06-18", "6 months"), ("2023-09-02", "9 months")], queries=[("current", "9 months")]),
 "0e4e4c46": dict(slot="ticket_to_ride_high_score", writes=[("2023-05-25", "124"), ("2023-05-30", "132")], queries=[("current", "132")]),
 "0f05491a": dict(slot="starbucks_gold_stars", writes=[("2023-07-11", "125"), ("2023-07-30", "120")], queries=[("current", "120")]),
 "184da446": dict(slot="short_history_page", writes=[("2023-05-20", "200"), ("2023-05-29", "220")], queries=[("current", "220")]),
 "18bc8abd": dict(slot="favourite_bbq_sauce", writes=[("2023-04-16", "sweet baby ray's"), ("2023-06-30", "kansas city masterpiece")], queries=[("current", "kansas city masterpiece")], state_type="preference"),
 "1cea1afa": dict(slot="instagram_followers", writes=[("2023-05-21", "500"), ("2023-05-25", "600")], queries=[("current", "600")]),
 "2133c1b5": dict(slot="harajuku_months", writes=[("2023-04-11", "1 month"), ("2023-10-15", "3 months")], queries=[("current", "3 months")]),
 "2698e78f": dict(slot="therapist_frequency", writes=[("2023-04-03", "every two weeks"), ("2023-11-03", "every week")], queries=[("current", "every week")]),
 "26bdc477": dict(slot="camera_trips", writes=[("2023-03-16", "3"), ("2023-05-30", "5")], queries=[("current", "5")]),
 "3ba21379": dict(slot="current_model_project", writes=[("2023-05-27", "ford mustang shelby gt350r"), ("2023-05-30", "ford f-150 pickup truck")], queries=[("current", "ford f-150 pickup truck")]),
 "41698283": dict(slot="most_recent_lens", writes=[("2023-03-11", "50mm prime lens"), ("2023-08-30", "70-200mm zoom lens")], queries=[("current", "70-200mm zoom lens")]),
 "42ec0761": dict(slot="has_spare_screwdriver", writes=[("2023-08-11", "no"), ("2023-08-15", "yes")], queries=[("current", "yes")], norm="derived: 'misplaced' → no; 'have a spare' → yes"),
 "45dc21b6": dict(slot="emma_recipes_tried", writes=[("2023-05-24", "2"), ("2023-05-28", "3")], queries=[("current", "3")]),
 "4b24c848": dict(slot="hm_tops", writes=[("2023-08-11", "3"), ("2023-09-30", "5")], queries=[("current", "5")]),
 "4d6b87c8": dict(slot="to_watch_titles", writes=[("2023-05-22", "20"), ("2023-05-28", "25")], queries=[("current", "25")]),
 "5831f84d": dict(slot="crash_course_videos", writes=[("2023-08-11", "10"), ("2023-09-30", "15")], queries=[("current", "15")]),
 "59524333": dict(slot="gym_time", writes=[("2023-02-11", "7:00 pm"), ("2023-05-30", "6:00 pm")], queries=[("current", "6:00 pm")]),
 "603deb26": dict(slot="negroni_attempts", writes=[("2023-08-11", "5"), ("2023-11-30", "10")], queries=[("current", "10")]),
 "618f13b2": dict(slot="converse_wears", writes=[("2023-05-24", "4"), ("2023-05-24", "6")], queries=[("current", "6")], norm="same-day writes; file order preserved by a sequence tiebreak"),
 "6a1eabeb": dict(slot="charity_5k_pb", writes=[("2023-05-25", "27:12"), ("2023-05-27", "25:50")], queries=[("current", "25:50")]),
 "6a27ffc2": dict(slot="corey_schafer_videos", writes=[("2023-05-21", "20"), ("2023-05-24", "30")], queries=[("current", "30")]),
 "6aeb4375": dict(slot="korean_restaurants", writes=[("2023-08-11", "3"), ("2023-09-30", "4")], queries=[("current", "4")]),
 "71315a70": dict(slot="sculpture_hours", writes=[("2023-06-11", "5-6 hours"), ("2023-06-17", "10-12 hours")], queries=[("current", "10-12 hours")]),
 "72e3ee87": dict(slot="crash_course_science_episodes", writes=[("2023-05-20", "10"), ("2023-05-24", "50")], queries=[("current", "50")]),
 "7401057b": dict(slot="hilton_free_nights", writes=[("2023-05-20", "1"), ("2023-05-28", "2")], queries=[("current", "2")]),
 "7a87bd0c": dict(slot="tidying_routine_weeks", writes=[("2023-06-11", "3 weeks"), ("2023-09-30", "4 weeks")], queries=[("current", "4 weeks")]),
 "7e974930": dict(slot="downtown_market_last_earnings", writes=[("2023-04-11", "$350"), ("2023-09-30", "$420")], queries=[("current", "$420")], norm="derived: first write is the latest Downtown Farmers Market entry in a listed series"),
 "830ce83f": dict(slot="rachel_location", writes=[("2023-05-21", "the city"), ("2023-05-21", "chicago"), ("2023-05-26", "the suburbs")], queries=[("current", "the suburbs")]),
 "852ce960": dict(slot="wells_fargo_preapproval", writes=[("2023-08-11", "$350,000"), ("2023-11-30", "$400,000")], queries=[("current", "$400,000")], norm="two reports of one event; gold takes the later"),
 "89941a93": dict(slot="bikes_owned", writes=[("2023-02-22", "3"), ("2023-10-10", "4")], queries=[("current", "4")]),
 "8fb83627": dict(slot="natgeo_issues_finished", writes=[("2023-04-20", "3"), ("2023-04-20", "3"), ("2023-07-15", "5")], queries=[("current", "5")]),
 "945e3d21": dict(slot="yoga_frequency", writes=[("2023-08-11", "twice a week"), ("2023-11-30", "three times a week")], queries=[("current", "three times a week")]),
 "9ea5eabc": dict(slot="most_recent_family_trip", writes=[("2023-05-29", "hawaii"), ("2023-05-30", "paris")], queries=[("current", "paris")]),
 "a1eacc2a": dict(slot="short_stories_written", writes=[("2023-05-21", "4"), ("2023-05-30", "7")], queries=[("current", "7")]),
 "a2f3aa27": dict(slot="instagram_followers", writes=[("2023-05-28", "1250"), ("2023-05-28", "1300")], queries=[("current", "1300")], norm="hedged 'close to 1300' taken as 1300, as gold does"),
 "affe2881": dict(slot="bird_species_seen", writes=[("2023-05-25", "27"), ("2023-05-29", "32")], queries=[("current", "32")]),
 "b01defab": dict(slot="finished_the_nightingale", writes=[("2023-01-21", "no"), ("2023-03-30", "yes")], queries=[("current", "yes")], norm="derived: 'put down temporarily' → no"),
 "b6019101": dict(slot="mcu_films_3_months", writes=[("2023-05-20", "4"), ("2023-05-25", "5")], queries=[("current", "5")]),
 "ba61f0b9": dict(slot="women_on_rachels_team", writes=[("2023-01-18", "5"), ("2023-07-20", "6")], queries=[("current", "6")], norm="derived: 'half of 10' → 5"),
 "c7dc5443": dict(slot="volleyball_record", writes=[("2023-06-16", "3-2"), ("2023-06-30", "5-2")], queries=[("current", "5-2")]),
 "cc5ded98": dict(slot="daily_coding_hours", writes=[("2023-05-25", "about an hour"), ("2023-05-27", "about two hours")], queries=[("current", "about two hours")]),
 "ce6d2d27": dict(slot="cocktail_class_day", writes=[("2023-06-16", "thursday"), ("2023-06-30", "friday")], queries=[("current", "friday")]),
 "cf22b7bf": dict(slot="weight_lost", writes=[("2023-05-21", "5 pounds"), ("2023-06-21", "10 pounds")], queries=[("current", "10 pounds")]),
 "d7c942c3": dict(slot="mom_uses_same_list_method", writes=[("2023-03-11", "no"), ("2023-04-30", "yes")], queries=[("current", "yes")], norm="derived"),
 "dad224aa": dict(slot="saturday_wake_time", writes=[("2023-05-24", "8:30 am"), ("2023-05-28", "7:30 am")], queries=[("current", "7:30 am")]),
 "db467c8c": dict(slot="parents_stay_months", writes=[("2023-07-16", "six months"), ("2023-10-20", "nine months")], queries=[("current", "nine months")]),
 "e493bb7c": dict(slot="ethereal_dreams_location", writes=[("2023-07-11", "above my living room sofa"), ("2023-10-30", "in my bedroom")], queries=[("current", "in my bedroom")], norm="derived: 'above my bed' → in my bedroom, as gold does"),
 "e61a7584": dict(slot="luna_months", writes=[("2023-08-11", "6 months"), ("2023-11-30", "9 months")], queries=[("current", "9 months")]),
 "ed4ddc30": dict(slot="eggs_dozen_stocked", writes=[("2023-01-11", "30"), ("2023-03-15", "20")], queries=[("current", "20")]),
 "f9e8c073": dict(slot="bereavement_sessions", writes=[("2023-05-11", "3"), ("2023-10-30", "5")], queries=[("current", "5")]),
 # ── historical_state ─────────────────────────────────────────────────────
 "07741c44": dict(slot="old_sneakers_location", writes=[("2023-08-11", "under my bed"), ("2023-11-30", "in a shoe rack in my closet")], queries=[("after", 0, "under my bed")]),
 "50635ada": dict(slot="united_status", writes=[("2022-09-16", "premier silver"), ("2023-05-30", "premier gold")], queries=[("after", 0, "premier silver")]),
 "89941a94": dict(slot="has_road_bike_besides_mountain_and_commuter", writes=[("2023-05-26", "yes"), ("2023-05-29", "yes")], queries=[("after", 0, "yes")], norm="derived: boolean about the state before the gravel bike; both writes say yes"),
 "9bbe84a2": dict(slot="apex_level_goal", writes=[("2023-06-16", "level 100"), ("2023-09-30", "level 150")], queries=[("after", 0, "level 100")], state_type="goal"),
 "dfde3500": dict(slot="language_tutor_day", writes=[("2023-05-26", "wednesday"), ("2023-05-26", "thursday")], queries=[("after", 0, "wednesday")], norm="derived: Juan (Wed) superseded by Maria (Thu), same session"),
 "e66b632c": dict(slot="charity_5k_pb", writes=[("2023-04-11", "27:45"), ("2023-07-30", "26:30")], queries=[("after", 0, "27:45")]),
 # ── both_states ──────────────────────────────────────────────────────────
 "031748ae": dict(slot="engineers_led", writes=[("2023-05-11", "4"), ("2023-10-24", "5")], queries=[("after", 0, "4"), ("current", "5")]),
 "f685340e": dict(slot="tennis_frequency", writes=[("2023-03-11", "every week"), ("2023-07-30", "every other week")], queries=[("after", 0, "every week"), ("current", "every other week")]),
 # ── delta_direction ──────────────────────────────────────────────────────
 "6071bd76": dict(slot="french_press_oz_per_tbsp", writes=[("2023-02-11", "6"), ("2023-06-30", "5")], queries=[("direction", "down")]),
 "c4ea545c": dict(slot="gym_days_per_week", writes=[("2023-06-01", "3"), ("2023-08-15", "4")], queries=[("direction", "up")]),
 "c6853660": dict(slot="morning_coffee_cups", writes=[("2023-05-28", "1"), ("2023-05-29", "2")], queries=[("direction", "up")], norm="derived: second write is 'thinking of changing to two'"),
 # ── accumulation (normaliser resolved the delta) ─────────────────────────
 "69fee5aa": dict(slot="pre1920_coins", writes=[("2023-05-20", "37"), ("2023-05-24", "38")], queries=[("current", "38")], norm="derived: 'added a new coin' → 38 — the delta was folded by the normaliser; reported separately"),
 # ── abstention: the asked-about slot has no writes ───────────────────────
 "031748ae_abs": dict(slot="engineers_led_as_manager", writes=[], queries=[("current", None)]),
 "0ddfec37_abs": dict(slot="autographed_footballs", writes=[], queries=[("current", None)]),
 "2133c1b5_abs": dict(slot="shinjuku_months", writes=[], queries=[("current", None)]),
 "2698e78f_abs": dict(slot="dr_johnson_frequency", writes=[], queries=[("current", None)]),
 "6aeb4375_abs": dict(slot="italian_restaurants", writes=[], queries=[("current", None)]),
 "f685340e_abs": dict(slot="table_tennis_frequency", writes=[], queries=[("current", None)]),
}
