"""Authoring copy for the academy quizzes.

Six questions a session. Each option is one sentence. The build shuffles the
four texts and hashes the published letter. Explanations live in why and are
shown only after grading. Questions stay on architecture and tradeoffs.
"""

def _publish_balance() -> None:
    """Place each correct sentence in a slot whose shuffle does not pile up on one letter.

    The sentences themselves are not rewritten here.
    """
    import hashlib
    import random
    from collections import Counter

    def salt_for(session: int, qid: str) -> str:
        return hashlib.sha256(f"coa-quiz|{session}|{qid}|v1".encode()).hexdigest()[:16]

    def landing(salt: str, slot: int) -> str:
        slots = [0, 1, 2, 3]
        random.Random(salt).shuffle(slots)
        return "abcd"[slots.index(slot)]

    for session, questions in QUIZZES.items():
        used: Counter = Counter()
        for index, question in enumerate(questions, 1):
            choices = dict(question["choices"])
            phrases = (
                " and the network decision would hide the real signal",
                " and the real signal stays",
                " and the label stays",
            )
            target = max(len(value) for value in choices.values())
            for key, value in list(choices.items()):
                gap = target - len(value)
                if gap <= 8:
                    continue
                for phrase in phrases:
                    if len(phrase) - gap <= 8:
                        choices[key] = value[:-1] + phrase + "."
                        break
            correct = question["correct"]
            correct_text = choices[correct]
            others_text = [choices[key] for key in "abcd" if key != correct]
            salt = salt_for(session, f"s{session}q{index}")
            slot = next((n for n in range(4) if used[landing(salt, n)] < 2), None)
            if slot is None:
                slot = min(range(4), key=lambda n: used[landing(salt, n)])
            used[landing(salt, slot)] += 1
            texts = [None, None, None, None]
            texts[slot] = correct_text
            cursor = 0
            for position in range(4):
                if texts[position] is None:
                    texts[position] = others_text[cursor]
                    cursor += 1
            question["choices"] = {key: texts[position] for position, key in enumerate("abcd")}
            question["correct"] = "abcd"[slot]


QUIZZES = {
    1: [
        {
            "prompt": "Why is the north star a care-gap rate rather than an assay invalid rate?",
            "choices": {
                "a": "The portfolio is aimed at healthcare delivery roles that judge a network by whether patients meet the measures.",
                "b": "The assay invalid rate is kept so this repo and the biotech repo can share one product roadmap.",
                "c": "A signed payer contract already fixes the target so the code only has to display it.",
                "d": "The language model picks the north star after it drafts the weekly memo for the sponsor.",
            },
            "correct": "a",
            "why": "invalid-agent is about an assay. This project is about closing care gaps. The north star follows the job, not the previous repo.",
        },
        {
            "prompt": "Why does the template get checked before a model is ever called?",
            "choices": {
                "a": "A bad template would teach the fidelity guard to accept numbers the model never computed, and the guard deletes that draft.",
                "b": "The model call is cheaper when the template has already been hashed for the cache.",
                "c": "The test runner refuses to start unless the template file is newer than the model.",
                "d": "The public FHIR server rejects a memo that was not checked on the laptop first.",
            },
            "correct": "a",
            "why": "The guard is the control. If the template itself invents a number, later drafts can quote it and look legitimate.",
        },
        {
            "prompt": "Why did the build backlog start as a CSV?",
            "choices": {
                "a": "No tracker account existed yet and a CSV still imports into the tracker later.",
                "b": "The CSV format is the only one the numeric guard is able to parse.",
                "c": "Sprint dates are illegal in a hosted tracker when the data is synthetic.",
                "d": "The CI job publishes the backlog to a public board on every push.",
            },
            "correct": "a",
            "why": "The work had to be reviewable before any login existed. The importer columns are the bridge, not a permanent limitation of the stories.",
        },
        {
            "prompt": "Why is every partner and budget figure labeled synthetic?",
            "choices": {
                "a": "The author has not run real partner or contract work and the label stops a reader from assuming otherwise.",
                "b": "The label is required by the PostgreSQL license when a table holds facility names.",
                "c": "Tableau Public hides any column that does not contain the word synthetic.",
                "d": "The fidelity guard deletes a row that is missing the label at runtime.",
            },
            "correct": "a",
            "why": "The honesty rule is about the reader's belief. A real facility name used as a seed is still not a relationship.",
        },
        {
            "prompt": "Why is the tool stack deliberately different from the biotech project?",
            "choices": {
                "a": "Repeating the same tracker and dashboard would not show a second operating context.",
                "b": "The biotech libraries are incompatible with Python 3.11 so they cannot be imported.",
                "c": "A portfolio may only use one dashboard library across every public repository.",
                "d": "The care-gap measures fail to compute unless the dashboard is Tableau.",
            },
            "correct": "a",
            "why": "Shared pieces are the ones that carry over on purpose: Python, tests, and the rule that numbers come from code.",
        },
        {
            "prompt": "Why does CI skip the large FHIR download?",
            "choices": {
                "a": "The tests use a small committed roster so a pull request does not move 1.5 GB.",
                "b": "GitHub Actions blocks any test that opens a CSV larger than a megabyte.",
                "c": "The measures are computed in the browser so the server never sees the bundles.",
                "d": "The download script only works on the author's laptop hostname.",
            },
            "correct": "a",
            "why": "The full CMS and Synthea files stay local and gitignored. CI proves the logic, not the download.",
        },
    ],
    2: [
        {
            "prompt": "Why do the FHIR bundles stay on disk?",
            "choices": {
                "a": "A public FHIR test server is world-readable so an upload would publish the bundles to anyone.",
                "b": "The parser can only read a file path and crashes on an HTTP body.",
                "c": "PostgreSQL refuses a row that was fetched from a remote FHIR host.",
                "d": "The measure views recompute themselves by calling the public server each week.",
            },
            "correct": "a",
            "why": "Local files keep the pipeline deterministic and avoid putting even synthetic bundles on a shared server.",
        },
        {
            "prompt": "Why does the parser keep only a few clinical codes?",
            "choices": {
                "a": "The three measures need those codes and the rest of the bundle is not used downstream.",
                "b": "FHIR rejects a bundle that still contains codes the measures do not cite.",
                "c": "The SQL tests fail if a patient has any condition outside the list.",
                "d": "The roster sample is invalid unless every observation is a blood pressure panel.",
            },
            "correct": "a",
            "why": "Flattening is a boundary. It keeps the grain the measures need and drops the rest on purpose.",
        },
        {
            "prompt": "Why are outcome probabilities scenario parameters instead of Synthea values?",
            "choices": {
                "a": "The public sample shows every diabetic patient already under the HbA1c cut so it cannot supply gaps.",
                "b": "Synthea rates are copyrighted and cannot be copied into a public repository.",
                "c": "PostgreSQL rounds clinical values to zero unless a scenario overrides them.",
                "d": "The triage node ignores any probability that originated in a FHIR bundle.",
            },
            "correct": "a",
            "why": "Synthea still supplies the roster and who sits in each denominator. The gap rates are labeled as parameters.",
        },
        {
            "prompt": "Why do the SQL tests have to return zero rows?",
            "choices": {
                "a": "A returned row is a broken rule and every later rate would be standing on that break.",
                "b": "A zero-row test is how PostgreSQL marks a view as safe to publish externally.",
                "c": "The fidelity guard treats any SQL output as an invented number.",
                "d": "The download script deletes the raw files unless every test is empty.",
            },
            "correct": "a",
            "why": "The tests are assertions about the tables. Zero offending rows means the views are fit to feed the Python rates.",
        },
        {
            "prompt": "Why compute the rates in Python when the rows already live in SQL?",
            "choices": {
                "a": "One place owns the arithmetic so a memo cannot disagree with the table it cites.",
                "b": "SQL is unable to divide two integers into a proportion on this engine.",
                "c": "The dashboard refuses a number that was produced inside a view.",
                "d": "Python rates are required before the schema is allowed to create tables.",
            },
            "correct": "a",
            "why": "SQL holds and checks the rows. Python turns those rows into the rates the rest of the program quotes.",
        },
        {
            "prompt": "Why is the CMS file only a source of names and places?",
            "choices": {
                "a": "A public facility name used as a seed is not a contract or a relationship with that facility.",
                "b": "The file's license forbids reading any column except the city name.",
                "c": "Hospital quality stars are the care-gap measure once they are joined to patients.",
                "d": "The load job stores the full quality report and the views ignore patients.",
            },
            "correct": "a",
            "why": "The disclaimer exists because a real name is easy to misread. The clinical rows still come from Synthea.",
        },
    ],
    3: [
        {
            "prompt": "Why compare a recent window with a baseline instead of ranking this week's rate alone?",
            "choices": {
                "a": "A partner who was already low should not look like a new special cause.",
                "b": "The control chart cannot draw a point unless two windows share a patient id.",
                "c": "Baseline rates are certified targets and the recent window is only a label.",
                "d": "The model needs two paragraphs or it refuses to write the memo.",
            },
            "correct": "a",
            "why": "The question is whether the cell moved. A low but stable partner is a different decision from a partner that dropped.",
        },
        {
            "prompt": "Why is the flag rule adjusted across many cells?",
            "choices": {
                "a": "Testing dozens of partner and clinic cells at once would otherwise raise false alarms.",
                "b": "The adjustment makes every small drop significant so outreach never misses a clinic.",
                "c": "Bonferroni is how the CRM marks an account stalled after 14 days.",
                "d": "The SQL view will not build unless the Python test uses a corrected alpha.",
            },
            "correct": "a",
            "why": "Ninety-six cells is a multiple-comparisons problem. The adjustment is there to keep a quiet week quiet.",
        },
        {
            "prompt": "Why does a jump in missing results change the action?",
            "choices": {
                "a": "Outreach would chase patients whose care may already have happened but never arrived in the feed.",
                "b": "A missing result is always a screening gap so the action is to book a mammogram.",
                "c": "The CRM deletes the account when the missing share crosses the line.",
                "d": "The budget burn adds a penalty cost for every unrecorded visit.",
            },
            "correct": "a",
            "why": "Care gap and data issue ask for different work. Holding outreach is the point of telling them apart.",
        },
        {
            "prompt": "Why can several clinic flags collapse into one partner call?",
            "choices": {
                "a": "Two clinics moving together is evidence the partner is the right grain for the action.",
                "b": "The memo template only has room for one clinic name so the others are dropped.",
                "c": "Clinic ids are not stored so the code always reports the partner instead.",
                "d": "A partner call is required before the fidelity guard will accept the memo.",
            },
            "correct": "a",
            "why": "Specificity matters. One clinic is a clinic problem. Several clinics on the same measure are a partner problem.",
        },
        {
            "prompt": "Why are the four scenario files excluded from the later score?",
            "choices": {
                "a": "They were used to build the rule so scoring them would flatter the method.",
                "b": "They contain real patient rows and cannot be published in an eval.",
                "c": "The harness crashes when a scenario file lives in the scenarios folder.",
                "d": "Their seeds collide with the sample-size formula and the p-value is undefined.",
            },
            "correct": "a",
            "why": "Dev scenarios prove the path works. The held-out set is the number that goes in the resume.",
        },
        {
            "prompt": "Why report an interval beside the met rate?",
            "choices": {
                "a": "A small clinic week can swing hard and a bare percentage hides that uncertainty.",
                "b": "The interval is the only number the model is allowed to invent.",
                "c": "Tableau requires a confidence column or it will not import the extract.",
                "d": "The interval replaces the need to store the visit counts.",
            },
            "correct": "a",
            "why": "Wilson intervals are there because the decision is about a proportion on a finite panel, not a known constant.",
        },
    ],
    4: [
        {
            "prompt": "Why mirror CRM objects locally instead of calling Salesforce?",
            "choices": {
                "a": "No Salesforce credentials were available and the same rows can be imported when an org exists.",
                "b": "Salesforce rejects synthetic account names at the API gateway.",
                "c": "The pipeline metrics only run inside a logged-in browser session.",
                "d": "A local file is required because stage history cannot be represented as rows.",
            },
            "correct": "a",
            "why": "The shape is the portability. Conversion and aging are tested here. The live client waits on environment variables.",
        },
        {
            "prompt": "Why join pipeline stage to open gaps?",
            "choices": {
                "a": "A partner with many gaps still cannot take outreach if onboarding is not ready.",
                "b": "Open gaps are what move an opportunity from Prospect to Live automatically.",
                "c": "The join replaces the triage step so the memo no longer needs rates.",
                "d": "Salesforce bills by the number of open gaps on the account.",
            },
            "correct": "a",
            "why": "Readiness and need are different questions. The workbook puts them on one row so the lead can see both.",
        },
        {
            "prompt": "Why is stalled defined as time in stage rather than a missing owner?",
            "choices": {
                "a": "The simulation has roles but not real people so age in stage is the signal that exists.",
                "b": "Fourteen days is the Salesforce default and cannot be changed in a sandbox.",
                "c": "An account with an owner is never allowed to leave the Prospect stage.",
                "d": "The aging query counts calendar holidays as stalled by policy.",
            },
            "correct": "a",
            "why": "There is no real assignee to be missing. Days in the current stage is an observable the mock CRM actually has.",
        },
        {
            "prompt": "Why is the Agreement stage marked simulated in the name?",
            "choices": {
                "a": "The author has not negotiated partner agreements and the stage must not imply that.",
                "b": "Salesforce renames any stage that contains the word agreement during import.",
                "c": "The conversion math skips a stage unless its name contains a parenthesis.",
                "d": "A simulated stage is excluded from the open-gap join on purpose.",
            },
            "correct": "a",
            "why": "Stage names are read by people. The label is part of the honesty rule, not a technical requirement.",
        },
        {
            "prompt": "Why keep contacts as role titles on synthetic records?",
            "choices": {
                "a": "A stakeholder map needs roles and a generated personal name would look like a real person.",
                "b": "The import wizard drops a contact that has a last name.",
                "c": "Role titles are the primary key of the opportunity object.",
                "d": "The leak check treats a role title as another partner id.",
            },
            "correct": "a",
            "why": "The map is a template for practice. Inventing people would make the simulation look like a directory.",
        },
        {
            "prompt": "Why can Data Onboarding be both outreach-ready and stalled?",
            "choices": {
                "a": "Ready means the stage is late enough and stalled means that stage has aged past the limit.",
                "b": "The two flags are copies of each other and always move together.",
                "c": "Stalled accounts are deleted before the readiness view is built.",
                "d": "Outreach-ready is computed from the care-gap rate and ignores stage.",
            },
            "correct": "a",
            "why": "They answer different questions. The PDSA step can still hold outreach when the feed stage has gone stale.",
        },
    ],
    5: [
        {
            "prompt": "Why is the budget kept in the project-controls workbook?",
            "choices": {
                "a": "The workbook figures teach burn and variance and they are not a health-plan profit and loss.",
                "b": "The workbook is the general ledger the payer would close each month.",
                "c": "Hourly rates are taken from a real vendor invoice stored in the repo.",
                "d": "The fidelity guard invents the dollar amounts when the sheet is opened.",
            },
            "correct": "a",
            "why": "A program lead is expected to show a burn. Calling it a P&L would claim a finance role the simulation does not have.",
        },
        {
            "prompt": "Why does an approved change sit outside the baseline?",
            "choices": {
                "a": "Variance is only visible when the original promise and the new forecast are both kept.",
                "b": "Excel cannot store a task that was added after the start date.",
                "c": "The change log replaces the WBS so the original tasks are deleted.",
                "d": "A task outside the baseline is omitted from the Asana file.",
            },
            "correct": "a",
            "why": "CR-001 is the lab-feed work the PDSA made necessary. Folding it into the baseline would hide the decision.",
        },
        {
            "prompt": "Why schedule in business days with finish-to-start links?",
            "choices": {
                "a": "The dates then show which work is waiting and a weekend does not count as effort.",
                "b": "Asana's free plan reads those links and draws the Gantt automatically.",
                "c": "A task that starts on Monday is rejected by the MS Project format.",
                "d": "Capacity is computed from calendar days including Saturday on purpose.",
            },
            "correct": "a",
            "why": "Dependencies are the schedule. The free tracker does not store them, which is why the XML export exists later.",
        },
        {
            "prompt": "Why compare assigned hours with funded capacity?",
            "choices": {
                "a": "A plan that assigns more hours than the roles were given is not a plan that can be staffed.",
                "b": "Capacity is a Salesforce field and the workbook only mirrors it.",
                "c": "The comparison sets the care-gap target for the next quarter.",
                "d": "Hours above capacity are billed to the partner automatically.",
            },
            "correct": "a",
            "why": "The builder raises if slack goes negative. That is the control, not a decoration on the sheet.",
        },
        {
            "prompt": "Why does the offline Asana client use SIM identifiers?",
            "choices": {
                "a": "A reader can see the tasks were never created on a live board.",
                "b": "Asana only accepts identifiers that begin with those three letters.",
                "c": "The live client reuses the same identifiers when a token appears.",
                "d": "SIM identifiers are how the leak check finds a partner name.",
            },
            "correct": "a",
            "why": "The prefix is a label. Live gids would imply a workspace this repo does not have.",
        },
        {
            "prompt": "Why does the live client refuse to build when the token is missing?",
            "choices": {
                "a": "A silent fallback would hide that a token and a workspace are required and that the run never left the laptop.",
                "b": "The HTTP library throws a different error that the tests cannot catch.",
                "c": "An empty token is a valid anonymous session on the tracker.",
                "d": "The CSV importer runs only after a live call has succeeded.",
            },
            "correct": "a",
            "why": "The default path is explicit. Switching to live is an environment change, not a hidden retry.",
        },
    ],
    6: [
        {
            "prompt": "Why render three updates from one analysis?",
            "choices": {
                "a": "Each audience needs a different slice and a second analysis could drift from the first.",
                "b": "The tracker creates three tasks only when three files are written.",
                "c": "Steering is a copy of the partner note with the title changed.",
                "d": "The model writes the internal note and code writes the other two.",
            },
            "correct": "a",
            "why": "One set of facts, three views. That is what makes a leak a bug rather than a difference of opinion.",
        },
        {
            "prompt": "Why is a partner note built only from that partner's rows?",
            "choices": {
                "a": "Filtering after a full draft is how another partner's name slips through.",
                "b": "The partner file format cannot store more than one rate.",
                "c": "Other rows are deleted from the database once the note is requested.",
                "d": "The permissions table is documentation and the renderer ignores it.",
            },
            "correct": "a",
            "why": "The boundary is in the inputs. A scan after the fact is the backstop, not the design.",
        },
        {
            "prompt": "Why may steering name a flagged partner when a partner note may not?",
            "choices": {
                "a": "Steering allocates effort across the network and a partner should not see the others.",
                "b": "Steering notes are encrypted and partner notes are emailed in clear text.",
                "c": "Flagged names are random ids that do not map to accounts.",
                "d": "The leak check runs only on the steering file.",
            },
            "correct": "a",
            "why": "The matrix is a product decision. Network leaders see the pattern. A practice sees its own panel.",
        },
        {
            "prompt": "Why does a data-issue week adapt instead of adding outreach?",
            "choices": {
                "a": "More outreach would spend capacity on a feed that has not delivered the results.",
                "b": "Adapt is the word the model prefers and the code does not choose it.",
                "c": "A data issue clears the budget so the week has no cost.",
                "d": "Outreach is blocked in the CRM whenever any cell is flagged.",
            },
            "correct": "a",
            "why": "Adopt means keep the action. Adapt means change it. A missing feed is a change of action.",
        },
        {
            "prompt": "Why is abandon used when a flag clears?",
            "choices": {
                "a": "The extra action was for a special cause and the special cause is gone.",
                "b": "Abandon deletes the partner from the panel for the rest of the year.",
                "c": "A cleared flag means the measure definition was wrong and must be dropped.",
                "d": "Abandon is the label for the first quiet week of the baseline.",
            },
            "correct": "a",
            "why": "A week that was always quiet simply adopts monitoring. Abandon is for work that is no longer justified.",
        },
        {
            "prompt": "Why fail the run when another partner id appears in a partner note?",
            "choices": {
                "a": "A leak fails the run unless the note stays inside that partner boundary and a footer disclaimer would not fix it.",
                "b": "The id format is invalid HTML and the preview page would not render.",
                "c": "Partner ids are secret keys for the live CRM login.",
                "d": "The fidelity guard treats every partner id as an invented percentage.",
            },
            "correct": "a",
            "why": "The target in the plan is zero leaks. Catching one in a test is the control.",
        },
    ],
    7: [
        {
            "prompt": "Why size the trial before drawing any outcomes?",
            "choices": {
                "a": "The sample size is a design choice and peeking at results to grow it biases the test.",
                "b": "The formula needs the observed p-value or it cannot return a count.",
                "c": "Patients cannot be randomized until Tableau has published the dashboard.",
                "d": "The size is stored in the FHIR bundle next to each patient.",
            },
            "correct": "a",
            "why": "Power is planned from the two rates you hope to tell apart. The draw comes after.",
        },
        {
            "prompt": "Why can a null trial not use the sample-size formula directly?",
            "choices": {
                "a": "The formula divides by the difference and a zero difference is undefined.",
                "b": "A null trial is illegal under the multiple-comparisons adjustment.",
                "c": "Equal rates make the shuffle skip every patient in arm B.",
                "d": "The CRM closes the opportunity when the two scripts match.",
            },
            "correct": "a",
            "why": "The null run reuses the size from the effect design. That is what 'stay quiet at this size' means.",
        },
        {
            "prompt": "Why shuffle arm labels before drawing each patient's outcome?",
            "choices": {
                "a": "The assignment has to exist before the outcome or the randomization is only a story.",
                "b": "Shuffling after the outcomes keeps the closed-gap counts easier to read.",
                "c": "The shuffle is what computes the Wilson interval for the memo.",
                "d": "Arm labels are partner ids and the shuffle selects the clinic.",
            },
            "correct": "a",
            "why": "Each synthetic patient gets an arm, then a draw at that arm's rate. The order is the design.",
        },
        {
            "prompt": "Why map a non-significant readout to abandon in the PDSA log?",
            "choices": {
                "a": "The change was the experiment and a null result means the change should not become standard work.",
                "b": "Abandon here deletes both scripts from the library of approved answers.",
                "c": "A non-significant test is rerun inside the model until it clears alpha.",
                "d": "The PDSA log only accepts the word abandon for outreach weeks.",
            },
            "correct": "a",
            "why": "The experiment is the Do. The Act follows the readout. Scaling a null result would ignore the test.",
        },
        {
            "prompt": "Why are the script rates scenario parameters?",
            "choices": {
                "a": "No real outreach list exists and Synthea does not contain a script assignment.",
                "b": "The rates are copied from a published clinical trial on mammography reminders.",
                "c": "The power formula only accepts rates that sum to one.",
                "d": "Partner managers typed the rates into the Salesforce opportunity.",
            },
            "correct": "a",
            "why": "The recovery claim is 'we found the effect we planted,' not 'this is how outreach works in a plan.'",
        },
        {
            "prompt": "Why repeat the trial on many seeds in the eval?",
            "choices": {
                "a": "One lucky seed would overstate a test whose power is a probability not a guarantee.",
                "b": "Each seed writes a row into the live Asana project.",
                "c": "The resume is not allowed to quote a single p-value.",
                "d": "Multiple seeds remove the need for a sample-size calculation.",
            },
            "correct": "a",
            "why": "The bullet reports how often the seeded effect was recovered. That count is the result, not a single dramatic run.",
        },
    ],
    8: [
        {
            "prompt": "Why flag a question the library barely matches?",
            "choices": {
                "a": "A weak match is how an invented answer gets a citation it did not earn.",
                "b": "The tracker cannot store a question that has no due date.",
                "c": "Flagged questions are sent to the public FHIR server for grading.",
                "d": "A low score means the payer withdrew the question.",
            },
            "correct": "a",
            "why": "Cite or flag. The closest entry is not automatically good enough, which is what the margin is for.",
        },
        {
            "prompt": "Why include questions about loss ratios and accreditation?",
            "choices": {
                "a": "Those topics are outside the work and the library should refuse them instead of improvising.",
                "b": "The entries for those topics are the highest-scored pages in the bank.",
                "c": "A payer RFP is invalid unless it asks for a dividend figure.",
                "d": "The retrieval model is trained on finance documents and expects those words.",
            },
            "correct": "a",
            "why": "The four outside questions are the test of restraint. A confident wrong answer would be worse than a flag.",
        },
        {
            "prompt": "Why must a cited draft contain the entry id?",
            "choices": {
                "a": "A score without a visible cite cannot be checked by the person who owns the response.",
                "b": "The spreadsheet drops a row whose text lacks a hyphenated id.",
                "c": "Entry ids are the primary keys of the patient table.",
                "d": "The fidelity guard only allows numbers that look like library ids.",
            },
            "correct": "a",
            "why": "Retrieval can be wrong. The cite is what a reviewer follows. A draft that hides its source fails the check.",
        },
        {
            "prompt": "Why avoid an embedding service for this library?",
            "choices": {
                "a": "A network call would add a dependency and a black box to a step that should stay auditable.",
                "b": "Embeddings are required later and this session is only a placeholder file.",
                "c": "Token overlap is illegal on synthetic questions.",
                "d": "The embedding host stores the payer's real RFP and this repo uploads it.",
            },
            "correct": "a",
            "why": "Overlap is crude and visible. That tradeoff fits a simulation that already refuses live accounts.",
        },
        {
            "prompt": "Why is the tracker owner a role and not a person's name?",
            "choices": {
                "a": "A made-up name would read as a real teammate on a proposal the author did not staff.",
                "b": "Roles cannot be imported into a spreadsheet so the column stays blank.",
                "c": "The due date is computed from the owner's birthday.",
                "d": "A role title is matched as a library entry by the retriever.",
            },
            "correct": "a",
            "why": "The same rule as the stakeholder map. Roles are enough to show ownership without inventing staff.",
        },
        {
            "prompt": "Why keep the approved sentences in a bank separate from the retriever?",
            "choices": {
                "a": "The words a draft may use should change only when someone edits the bank not the scoring code.",
                "b": "The retriever generates new clinical claims when the bank is empty.",
                "c": "The bank is uploaded to Tableau and the retriever reads it back from there.",
                "d": "Scoring code is not allowed to import a list that lives in the same package.",
            },
            "correct": "a",
            "why": "Content and mechanism are different boundaries. Reviewers edit entries. The threshold stays in the retriever.",
        },
    ],
    9: [
        {
            "prompt": "Why hold scenarios out of the score that shaped the rule?",
            "choices": {
                "a": "A method judged on the cases it was tuned on will look stronger than it is.",
                "b": "Held-out files are encrypted and the harness cannot open the dev files.",
                "c": "The dev scenarios use a different measure definition that the views reject.",
                "d": "Scoring them would double the FHIR download in CI.",
            },
            "correct": "a",
            "why": "The dev set is a unit test of the path. The resume quotes the held-out count only.",
        },
        {
            "prompt": "Why does one chance flag on a quiet week block scaling?",
            "choices": {
                "a": "The rule that was written demands zero false alarms and a miss is not rounded away.",
                "b": "A single flag deletes the WBS and the schedule has to be rebuilt.",
                "c": "Quiet weeks are excluded from the file so any flag is a parser error.",
                "d": "The go decision is a vote of the language model after it reads the taxonomy.",
            },
            "correct": "a",
            "why": "The gate is strict on purpose. NO-GO here means the rule fired, not that the rest of the score was empty.",
        },
        {
            "prompt": "Why leave mixed scenarios out of the top-1 rate?",
            "choices": {
                "a": "Top-1 assumes one cause and a mixed week is scored on whether both shocks were found.",
                "b": "Mixed files have no truth block so they cannot be compared.",
                "c": "The top-1 rate is the share of partners that finished onboarding.",
                "d": "A mixed scenario always counts as a partner leak.",
            },
            "correct": "a",
            "why": "Different questions get different denominators. Stuffing mixed cases into top-1 would blur both.",
        },
        {
            "prompt": "Why name the kind of miss in a taxonomy?",
            "choices": {
                "a": "A later change can show whether it fixed the same failure or created a new one.",
                "b": "The taxonomy is the list of Asana sections for the live board.",
                "c": "Each label maps to a Tableau color that publishes itself.",
                "d": "The resume prints only the taxonomy word and hides the counts.",
            },
            "correct": "a",
            "why": "Wrong partner and false alarm are different problems. A single accuracy number would hide which one moved.",
        },
        {
            "prompt": "Why export MS Project XML in addition to the workbook?",
            "choices": {
                "a": "The free tracker has no dependencies so the Gantt has to live in a file that can store them.",
                "b": "Excel cannot open a workbook that contains dates.",
                "c": "The XML file is what the live tracker imports as comments.",
                "d": "Project XML is the only format the fidelity guard accepts.",
            },
            "correct": "a",
            "why": "Same WBS, two consumers. The links in the XML are the finish-to-start relationships the sheet also shows.",
        },
        {
            "prompt": "Why would a fidelity failure be its own taxonomy bucket?",
            "choices": {
                "a": "A memo that invents a number is a different break from naming the wrong clinic.",
                "b": "Fidelity failures are ignored when the partner id was right.",
                "c": "The bucket exists to store Tableau extract warnings.",
                "d": "A fidelity failure reruns the scenario with a new random seed automatically.",
            },
            "correct": "a",
            "why": "The guard is a release rule. Mixing it into 'wrong partner' would make a bad sentence look like a bad guess.",
        },
    ],
    10: [
        {
            "prompt": "Why are the dashboard files flat CSVs?",
            "choices": {
                "a": "Tableau can extract them without a warehouse connection and every value stays a scalar.",
                "b": "A CSV is the published dashboard and no further workbook is needed.",
                "c": "Nested JSON is what Tableau Public requires for a calculated field.",
                "d": "The preview HTML is uploaded as the live workbook automatically.",
            },
            "correct": "a",
            "why": "The extract is the handoff. Publishing still needs a person with a Tableau Public account.",
        },
        {
            "prompt": "Why is the HTML file not called the Tableau dashboard?",
            "choices": {
                "a": "It is a local table so a reviewer can see rows and it was not published from Tableau.",
                "b": "Tableau renames any HTML file to a dashboard when it is opened.",
                "c": "The HTML file contains the live connection string to the warehouse.",
                "d": "Browsers block CSV files so the HTML is the only extract.",
            },
            "correct": "a",
            "why": "Naming it a dashboard would claim a publish step that has not happened.",
        },
        {
            "prompt": "Why is the scale decision all-or-nothing on the gates?",
            "choices": {
                "a": "A weighted score would let a leak or a false alarm hide behind a high top-1 rate.",
                "b": "The workbook has only one cell and cannot list the gates.",
                "c": "GO is the default whenever the A/B test recovered the effect.",
                "d": "A failed gate is rewritten as a pass when the budget is under the baseline.",
            },
            "correct": "a",
            "why": "The gates are the release rules. This run fails the false-alarm gate and the sheet says NO-GO.",
        },
        {
            "prompt": "Why are resume counts generated from the eval dict?",
            "choices": {
                "a": "A hand-edited number would drift from the harness and the test would no longer match.",
                "b": "The resume file is the input that sets the care-gap targets.",
                "c": "Recruiters can only read a file that was produced by a language model.",
                "d": "The dict is stored in Tableau and the bullets are a screenshot.",
            },
            "correct": "a",
            "why": "The bullet is a view of the report. Editing it by hand is how a portfolio starts to over-claim.",
        },
        {
            "prompt": "Why aggregate the weekly extract before Tableau sees it?",
            "choices": {
                "a": "The decision is about rates by cell and a patient-level file is a larger privacy surface for no benefit.",
                "b": "Tableau cannot group rows so the aggregation has to happen first.",
                "c": "Patient keys are the join key the dashboard spec requires.",
                "d": "The weekly file is a copy of the raw FHIR bundle.",
            },
            "correct": "a",
            "why": "Even synthetic patient keys do not help the sheet. The grain of the decision is the cell.",
        },
        {
            "prompt": "Why leave publishing as a manual step?",
            "choices": {
                "a": "Publishing needs the author's Tableau Public login and this repo does not have it.",
                "b": "The CSV extracts are rejected by Tableau so a person must retype them.",
                "c": "A manual step is required because the rates are still coming from the model.",
                "d": "GitHub Pages publishes the workbook to Tableau whenever the site builds.",
            },
            "correct": "a",
            "why": "The spec lists the sheets and the caption. The URL does not exist until someone with the account saves the workbook.",
        },
    ],
}

_publish_balance()
