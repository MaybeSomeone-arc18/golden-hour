"""The web demo re-implements the scorer in JS. Check it gives the same score as scorer.py on 2000 random hours.
needs node. usage: python eval/parity.py"""
import json, os, random, re, subprocess, sys
root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, root)
from golden_hour.scorer import Hour, comfort
random.seed(3)
hrs = [dict(t=random.uniform(-5, 42), r=random.choice([0, 5, 20, 50, 90, 100]), w=random.uniform(0, 45),
            uv=random.uniform(0, 11), day=random.random() < 0.7) for _ in range(2000)]
html = open(os.path.join(root, "demo", "standalone.html")).read()
js = html[html.index("function pen("):html.index("const NAMES")]
code = js + "\nconst H=" + json.dumps(hrs) + ";console.log(JSON.stringify(H.map(comfort)))"
out = json.loads(subprocess.run(["node", "-"], input=code, capture_output=True, text=True, check=True).stdout)
worst = max(abs(a - comfort(Hour("x", h["t"], h["r"], h["w"], h["uv"], h["day"]))) for a, h in zip(out, hrs))
print(f"max difference between JS and Python score over {len(hrs)} random hours: {worst:.2e}")
