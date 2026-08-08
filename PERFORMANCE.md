# Performance and evaluation

## Current state

No production load benchmark or formal ML evaluation report is included. The current matcher is deterministic and explainable; its percentage is a compatibility heuristic, not a probability of hiring.

## Metrics to establish before public launch

### Web application

- p50/p95 response latency for search, detail, dashboard, and recommendations;
- database query count per page;
- throughput under representative concurrent users;
- file extraction time by format and size;
- importer duration, failure rate, and records/second.

### Matching quality

- skill extraction precision, recall, and F1 on human-labelled resumes;
- top-k recommendation precision;
- human reviewer agreement;
- false-positive and false-negative gap detection;
- score stability across formatting changes;
- subgroup fairness analysis where lawful and appropriate;
- fabrication rate for generated documents: target zero unsupported factual claims.

## Suggested benchmark workflow

1. Create a consented, anonymized evaluation set.
2. Define labels before tuning.
3. Keep development and evaluation samples separate.
4. Publish scoring factors and limitations.
5. Track versions of synonym dictionaries and weights.
6. Require human review before application documents are used.

## Optimization priorities

Add database indexes for common filters, use pagination consistently, cache stable source metadata, move imports and document generation to background workers, and store private files in object storage.
