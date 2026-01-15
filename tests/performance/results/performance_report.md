# Retrieval System Performance Test Report

**Generated**: 2026-01-16 01:44:50

## BM25 Retriever Performance

| Document Count | Index Time (s) | Mean Latency (ms) | P95 Latency (ms) | Queries |
|----------------|----------------|-------------------|------------------|----------|
| 100 | 2.434 | 1.25 | 4.79 | 5 |
| 500 | 0.184 | 0.72 | 0.77 | 5 |
| 1,000 | 0.360 | 1.97 | 2.53 | 5 |
| 5,000 | 2.686 | 10.24 | 15.59 | 5 |

## Hybrid Retriever Performance

| Document Count | Index Time (s) | Mean Latency (ms) | P95 Latency (ms) | Queries |
|----------------|----------------|-------------------|------------------|----------|
| 100 | N/A | 2.33 | 3.75 | 5 |
| 500 | N/A | 4.84 | 7.27 | 5 |
| 1,000 | N/A | 5.59 | 6.01 | 5 |
| 5,000 | N/A | 24.12 | 30.94 | 5 |

### Hybrid Retriever Breakdown

| Document Count | Vector (ms) | BM25 (ms) | Fusion (ms) | Cache Hit Rate |
|----------------|-------------|-----------|-------------|----------------|
| 100 | 0.82 | 0.82 | 0.38 | 40.0% |
| 500 | 2.13 | 2.13 | 0.59 | 40.0% |
| 1,000 | 3.29 | 3.29 | 0.51 | 40.0% |
| 5,000 | 13.50 | 13.50 | 0.88 | 40.0% |

## Concurrent Query Performance

**Document Count**: 1,000

| Concurrent Users | Throughput (QPS) | Mean Latency (ms) | P95 Latency (ms) |
|------------------|------------------|-------------------|------------------|
| 1 | 260.95 | 3.50 | 3.50 |
| 5 | 378.76 | 9.79 | 12.76 |
| 10 | 558.41 | 7.91 | 17.25 |
| 20 | 16256.99 | 0.02 | 0.08 |

