# golden-hour

**live demo:** https://maybesomeone-arc18.github.io/golden-hour/demo/standalone.html

**write-up:** https://dev.to/sansk_ya/golden-hour-a-go-outside-planner-where-a-small-local-gemma-cannot-invent-numbers-3ol5

a tiny offline-friendly "go outside" planner. it looks at a free forecast, picks the best hour for a walk with plain rules, and a small local Gemma writes one friendly sentence about it.

```
python -m golden_hour --lat 12.97 --lon 77.59 --place Bengaluru --minutes 45
```

## how it works
1. forecast from Open-Meteo (no key, no account)
2. `scorer.py` ranks the next 24 hours with simple penalties (`docs/scoring.md`)
3. `nudge.py` asks a local Gemma 3 1B (GGUF via llama.cpp) for one sentence
4. the sentence is accepted only if its numbers carry the right unit and value, the day word is right, and it makes no weather claim the forecast does not support. otherwise a template sentence is used. the model never picks the time, only words it.

## measured
all runs on one 2-CPU, ~2 GB RAM box, Gemma 3 1B Q4_K_M.

**sentences** (`eval/run_eval.py`): 20 cities x 3 walk lengths (30, 60, 120 min) = 60 runs, one run each.
- 3 runs had no good window (Nairobi, 92% rain). the model is skipped and the app says so
- of the 57 where Gemma wrote a sentence: **56 passed validation (98%)**, 1 was rejected and replaced by the template line
- time per sentence: median 2.9 s, range 2.1 to 4.1 s, including generation
- Gemma 3 270M was tried and ignored the task, so it is not used

**validator** (`eval/mutation.py`): I corrupted correct sentences in six known ways, 400 each, and counted how many were flagged. my first version only checked that each number appeared somewhere in the facts, with no units. it caught a wrong number 95% of the time and the other five kinds 0%. now: 99 to 100% of all six. correct sentences are still accepted (100%). these corruptions are the ones i thought of, so this is a floor on what i tested, not proof of what it can't miss.

**weights** (`eval/sensitivity.py`): scaling every scorer weight randomly by 0.7x to 1.3x, 3000 re-picks: same hour 92%, within 1 hour 95%, moved more than 2 hours 3%.

**demo vs python** (`eval/parity.py`): the JS scorer in the web demo matches `scorer.py` to 2e-14 over 2000 random hours.

## limits, honestly
- it is Gemma 3, not Gemma 4
- the sentences are bland. the 1B model is a writer of one line, nothing more. the template line is just as useful
- weights in the scorer are my judgment, not tuned on user data (the sensitivity run shows the pick is stable against small changes, not that it matches your taste)
- not field tested: nobody has used it on a real walk yet, so no claims about that
- the validator checks facts (numbers with units, day word, a short list of weather words), not tone or any claim outside that list
- forecast quality is whatever Open-Meteo gives
- 20 cities, one run each, is a sanity check and not a benchmark

tests: `python -m pytest tests`
