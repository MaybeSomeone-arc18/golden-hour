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
4. the sentence is accepted only if every number in it matches the facts. otherwise a template sentence is used. the model never picks the time, only words it.

## measured (eval/run_eval.py, 20 cities, one run each)
- Gemma 3 1B Q4_K_M, 2 CPUs, ~2 GB RAM box
- sentence passed validation: 19/20, template fallback: 1/20
- median 3.0 s per sentence including generation
- Gemma 3 270M was tried and ignored the task, so it is not used

## limits, honestly
- it is Gemma 3, not Gemma 4
- the sentences are bland. the 1B model is a writer of one line, nothing more
- weights in the scorer are my judgment, not tuned on user data
- not field tested: nobody has used it on a real walk yet, so no claims about that
- validation checks numbers, not tone or truth beyond the facts it was given
- forecast quality is whatever Open-Meteo gives

tests: `python -m pytest tests`
