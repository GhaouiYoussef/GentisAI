from __future__ import annotations

import statistics
from dataclasses import dataclass, field


@dataclass
class LatencyMetrics:
    samples_ms: list[float] = field(default_factory=list)

    def observe(self, latency_ms: float) -> None:
        self.samples_ms.append(latency_ms)

    def summary(self) -> dict[str, float]:
        if not self.samples_ms:
            return {"count": 0.0, "p50_ms": 0.0, "p95_ms": 0.0}

        sorted_samples = sorted(self.samples_ms)
        p95_index = min(len(sorted_samples) - 1, int(len(sorted_samples) * 0.95))
        return {
            "count": float(len(sorted_samples)),
            "p50_ms": float(statistics.median(sorted_samples)),
            "p95_ms": float(sorted_samples[p95_index]),
        }
