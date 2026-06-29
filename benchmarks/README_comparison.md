# GentisAI Benchmark Notes

The benchmark assets in this directory compare GentisAI's low orchestration overhead with manager-loop agent frameworks for interactive chat.

Use the offline benchmark for CI-friendly checks:

```bash
gentis bench
```

Use the provider benchmark only when you have the required provider keys and benchmark dependencies installed:

```bash
pip install "gentis-ai[bench]"
python benchmarks/benchmark.py
```

Keep benchmark claims tied to committed artifacts in `benchmarks/`.
