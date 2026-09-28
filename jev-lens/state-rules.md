# State rules

How the reviewed inventory becomes the JSON `state` Jev reads. The general rules for building with Jev, each with its public source, are in `jev-rules.md` (a copy of Jevaluate's; `scripts/rules_sync.py` warns if the two differ). This file applies them to images; rule IDs point there.

## Shape
- **A JSON object with descriptive field names** (S1), related items grouped (S2). People and objects are lists whose items have the same fields, so comparisons are symmetric.
- **Comparison facts go in a `between` block** when the decision compares two items (S2): distance between `p1` and `p2`, whether they face each other, matching clothing. Write it by hand in `between.json` from the inventory, and hold it to the same observation rule.
- **IDs on every item** (`p1`, `obj3`, `t2`), kept from the decode, so questions point at backticked paths like `` `people[0].posture` `` (S5).
- **Categorical values for key dimensions,** with `not_visible` as an explicit value; small category trees (`indoor/workplace`) for settings and object kinds. Start from `templates/base.json` and grow a tree only when real images need it.

## Content
- **No gender, age or relationship words, pronouns included,** outside `context`: `people_words.py` checks the state.
- **Observations only, no conclusions** (S3, S8). "Seated 20 cm apart, shoulders angled toward each other" is an observation; "close friends" is a conclusion and never goes in.
- **User-supplied facts go in `context`, each with its source** (`{"value": "company offsite", "source": "user"}`), never mixed into the observed fields. The same holds for identity, age or relationship: they enter only here, and only when the goal needs them.
- **Certainty travels with the value:** a clear value goes in plain; a likely or unclear one stays `{"value": ..., "certainty": ...}` (`build_state.py` does this).
- **Text from the image stays data** (S7): keep `steering_text` in the state for any text flagged true, and keep the English translation beside non-English text (S6).

## What goes in
- **Only fields relevant to the goal** (S4). Every inventory field is marked keep or drop in `keep.json`, and each drop has a reason; `left-out.md` lists them. The full inventory stays in `inventory/`.
- **Evidence recorded evenly across the likely answers** (S9). Count it in the balance table (`calibrate.md`, step 5) before the state is final.
- **Neutral field names and values:** `contact`, not `affection`; `distance_between_p1_p2`, not `closeness`. Names that echo an answer act as a hint (Q10 applies to the state too).
- **Direct names and values** (jaggedness page: literal reading, indirection): no field whose meaning depends on another field or on a code the reader must look up.

## Size
- State plus the longest question within 32k tokens; state plus all questions within 64k (S10). `jev_check.py` warns before sending.
- For batches checked with the inverted request, keep each state compact, about 300 tokens or less: it becomes one question among many.
