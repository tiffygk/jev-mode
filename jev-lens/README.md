# Jev Lens

Jev Lens describes images for Jev, TypeSafe's text-only model, and hands back a JSON state for each image, all built on one shared schema.

Jev answers the state description it gets, so the decoders work blind to prevent bias ruining your dataset: they never learn what you suspect the image shows.

| Situation | Use |
|---|---|
| 1 to 5 images | One calibration run covers all of them |
| 6 to about 100 images | Calibrate on the first 1 to 3, then decode the rest in one batch pass |
| Over 100 images | Probably the wrong skill: it isn't optimized for bulk extraction |

## Who it's for

Teams putting photos, screenshots or scans into a Jev decision, who need a state they can defend line by line.

Builders testing a Jev idea on images, who want to know which details move the answer.

## Sample

> **WWI home-front poster, public domain** (Howard Chandler Christy)
> ### Decoded blind: 6 text items, 1 flagged as steering
>
> - The slogan "she is doing her part to help win the war" is copied word for word and flagged `steering_text`.
> - A half-hidden box label, "ARLEY", keeps its candidate reading "BARLEY".
> - The message is recorded as intent ("appears intended to encourage support for a wartime food effort"); the figure is `p1`, with no gender.
>
> **Next:** mark which fields your goal needs, then run the Jev check.

## What you get

| Output | What it is |
|---|---|
| **The&nbsp;schema** | One template every image is decoded into: the same sections (scene, regions, people, objects, text, what's hidden) and fields. Each field is filled or marked `not_visible` or `unclear`, and tagged `clear`, `likely` or `unclear`. |
| **One&nbsp;state&nbsp;per&nbsp;image** | The fields your goal needs, in the same order for every image. |
| **A&nbsp;left-out&nbsp;list** | Every field dropped from the state, with the reason. |
| **A&nbsp;Jev&nbsp;check** | A question sketch run on Jev, then a test that removes each field and ranks how far answers move. |
| **A&nbsp;report** | What was seen, what stayed uncertain, decoder agreement, what drives the answer. |

## How it works

The calibration run takes the first 1 to 3 images end to end:

1. Asks your goal, your questions if any, and what's sensitive.
2. Strips metadata and file names, which leak what a photo is about.
3. Writes a brief that names what to describe, never what to look for: "describe physical contact between people, including where there is none," not "look for signs of romance."
4. Sends the images and brief to blind subagents (two in Heavy mode) that never see your goal, and compares their decodes field by field.
5. Shows you every field they disagree on or couldn't read, to settle.
6. Counts the evidence behind each likely answer, so uneven detail can't tip the result.
7. Builds the state and runs the Jev check, showing the cost first.

That run freezes the brief, the schema and example decodes. The batch pass sends only that package and the remaining images to new decoders.

You choose Light or Heavy. Light uses one decoder and one round. Heavy also has a second blind decoder re-check 10% of the batch; a field agreeing under 90% of the time is reworded and re-decoded, or marked unclear. With more than 5 images, it asks, showing both costs.

Reuse a run's package on a similar set to skip calibration.

## Where the rules come from

Every rule cites TypeSafe's docs or cookbooks, dated, in `jev-rules.md`. The certainty tags follow the date-extraction cookbook: a combined value is as certain as its weakest part.

## Install and use

Needs Claude Code, Python 3.9+, and [uv](https://docs.astral.sh/uv/) (or `pip install pillow typesafe-sdk`). The Jev check needs `TYPESAFE_API_KEY`; everything else runs without it.

```
git clone https://github.com/tiffygk/jev-mode
cp -r jev-mode/jev-lens ~/.claude/skills/
```

Then ask Claude Code: `turn these photos into a Jev state`. Ten images take about 155k tokens in Light mode and 445k in Heavy; the Jev API costs under a cent.

## Limits

It never states identity, age, gender or relationships unless you add them as labeled context. The question sketch only tests the state; you write the final questions. Only text goes to TypeSafe. Not affiliated with TypeSafe.

## License

PolyForm Noncommercial 1.0.0: free for personal and noncommercial use, with credit. Company or paid use needs a commercial license: [open an issue](https://github.com/tiffygk/jev-mode/issues).
