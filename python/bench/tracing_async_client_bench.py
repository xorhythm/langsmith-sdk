import asyncio
import statistics
import time
from datetime import datetime
from typing import Dict
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from tracing_client_bench import create_run_data

from langsmith.async_client import AsyncClient


async def benchmark_run_creation(
    num_runs: int, json_size: int, samples: int = 1
) -> Dict:
    """
    Benchmark run creation with specified parameters.
    Returns timing statistics.
    """
    timings = []

    project_name = "__tracing_async_client_bench_python" + datetime.now().strftime(
        "%Y%m%dT%H%M%S"
    )

    for _ in range(samples):
        runs = [create_run_data(str(uuid4()), json_size) for i in range(num_runs)]

        mock_response = AsyncMock()
        mock_response.status_code = 202
        mock_response.text = "Accepted"
        mock_response.json.return_value = {"status": "success"}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch("httpx.AsyncClient", return_value=mock_client):
            client = AsyncClient(api_key="xxx", auto_batch_tracing=True)

            start = time.perf_counter()
            for run in runs:
                await client.create_run(**run, project_name=project_name)

            elapsed = time.perf_counter() - start

            timings.append(elapsed)
            await client.aclose()

    return {
        "mean": statistics.mean(timings),
        "median": statistics.median(timings),
        "stdev": statistics.stdev(timings) if len(timings) > 1 else 0,
        "min": min(timings),
        "max": max(timings),
    }


json_size = 3_000
num_runs = 1000


async def main(json_size: int, num_runs: int):
    """
    Run benchmarks with different combinations of parameters and report results.
    """

    results = await benchmark_run_creation(num_runs=num_runs, json_size=json_size)

    print(f"\nBenchmark Results for {num_runs} runs with JSON size {json_size}:")
    print(f"Mean time: {results['mean']:.4f} seconds")
    print(f"Median time: {results['median']:.4f} seconds")
    print(f"Std Dev: {results['stdev']:.4f} seconds")
    print(f"Min time: {results['min']:.4f} seconds")
    print(f"Max time: {results['max']:.4f} seconds")
    print(f"Throughput: {num_runs / results['mean']:.2f} runs/second")


if __name__ == "__main__":
    asyncio.run(main(json_size, num_runs))
