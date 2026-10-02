[← All ratings](README.md)

> **Jev-Omni** at [`5addda8`](https://huggingface.co/akhilaaa3/Jev-Omni/tree/5addda86ddee) · jev replacement
> ### Not rated yet: replaces Jev
> Execution n.a. · Fit n.a. · Coverage n.a. · Evidence n.a.
>
> - Jev-Omni is an open 12B Gemma 4 fine-tune that returns a probability per option for a state, question and options, over text, image, audio and video.
> - It publishes accuracy and calibration numbers on its own benchmark and states it is not affiliated with TypeSafe.
> - It stands in for Jev, so it routes to 1r (placeholder, not a judgment) until a replacement track exists.

## What holds it back

- **Calls hosted Jev** (F0): It loads its own Gemma 4 weights and head locally and posts to no TypeSafe endpoint ([`files/jev_omni.py:125`](https://huggingface.co/akhilaaa3/Jev-Omni/blob/5addda86ddee/files/jev_omni.py#L125)). https://docs.typesafe.ai/introduction.md

[Full rating: every fact, its evidence and the files read →](full/hf__akhilaaa3__Jev-Omni.md)

