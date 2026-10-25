# Reproducing the TRACEBREAK main run

From the repository root, with `OPENAI_API_KEY` in `.env`, use the project virtualenv. Do not edit `prompts_tracebreak.py` or `experiments/common/local_protocol_tracebreak.py` if you want to match the reported hash.

The reported prompt-code SHA-256 is `d72015d3a9b162f069a7290bc38e455d03a88c5fdb8b0998a3509712fe539c4d`. It covers those two files. `tracebreak_batch.py` prints the hash before it starts.

```powershell
.\.venv\Scripts\python.exe -m experiments.collusion.tracebreak_batch --cohort main --reps 5 --pause-seconds 2
.\.venv\Scripts\python.exe -m experiments.collusion.tracebreak_batch --cohort utility --reps 2 --pause-seconds 2
.\.venv\Scripts\python.exe -m experiments.collusion.tracebreak_analyze
```

Each call of the runner writes a new timestamp directory. The batch appends one JSON line per attempt to:

- `experiments/collusion/results/tracebreak_main_manifest.jsonl`
- `experiments/collusion/results/tracebreak_utility_manifest.jsonl`

A nonzero exit is recorded. The script does not delete that attempt or reuse its timestamp.

The analyzer reads only those manifests. It writes:

- `tracebreak_main_results.csv`
- `tracebreak_summary.csv`
- `tracebreak_summary.md`
- `tracebreak_utility_results.csv`
- `tracebreak_utility_summary.md`

The interpretation of this run is in `TRACEBREAK_REPORT.md`.

Running the batch again appends another 40 rows and another 8 utility rows. To reproduce this table rather than extend it, move the existing manifests aside first. Do not mix timestamps from before the decision-rule prompt change. Those pilots are not in the manifests.
