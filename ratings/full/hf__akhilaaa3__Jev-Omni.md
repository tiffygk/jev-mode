[← Summary](../hf__akhilaaa3__Jev-Omni.md)

# Jev-Omni: full rating

**Verdict 1, Replaces Jev, not yet rated** · jev replacement · rated 2026-09-30 at [`5addda8`](https://huggingface.co/akhilaaa3/Jev-Omni/tree/5addda86ddee) · read: full · rubric 2026-09-29 · claude-sonnet-5-5, medium effort

## Summary

Jev-Omni is an open 12B Gemma 4 fine-tune that returns a probability per option for a state, question and options, over text, image, audio and video. It publishes accuracy and calibration numbers on its own benchmark and states it is not affiliated with TypeSafe. It stands in for Jev, so it routes to 1r (placeholder, not a judgment) until a replacement track exists.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **no.** It loads its own Gemma 4 weights and head locally and posts to no TypeSafe endpoint ([`files/jev_omni.py:125`](https://huggingface.co/akhilaaa3/Jev-Omni/blob/5addda86ddee/files/jev_omni.py#L125)). https://docs.typesafe.ai/introduction.md |

## Why this verdict

Verdict 1, code 1r. Jev-Omni never calls hosted Jev: it runs its own Gemma 4 12B weights and a 256-slot head locally ([`files/jev_omni.py:125`](https://huggingface.co/akhilaaa3/Jev-Omni/blob/5addda86ddee/files/jev_omni.py#L125)), and offers others typed probabilities per option as a stand-in. Its README says it is not affiliated with or derived from TypeSafe and claims no Jev call, so 1a does not apply. No replacement track exists, so 1r is a placeholder and not a judgment of the model.

<details>
<summary><b>Files read (15)</b></summary>

- files/README.md -- read
- files/decision-bench__README.md -- read
- files/example.py -- read
- files/jev_omni.py -- read
- files/decision_config.json -- read
- files/verification.json -- read
- files/requirements.txt -- read
- files/generation_config.json -- read
- files/sha256.json -- read
- files/config.json -- read
- files/processor_config.json -- read
- files/chat_template.jinja -- read
- files/api.json -- read
- files/assets__medium-accuracy.svg -- read
- files/assets__medium-calibration.svg -- read

</details>
