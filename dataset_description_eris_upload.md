# Autodilution Lineage DSL Dataset

## Overview

This synthetic dataset contains deterministic liquid-handling protocol traces for a mini assay deck. Each row represents one protocol case. The goal is to reconstruct the final contents of a requested target well by executing the protocol language from left to right.

The dataset was generated locally using the included `generate_raw.py` script with a fixed random seed. It is intended for a from-scratch benchmark: participants should implement a protocol interpreter, not use external data or pretrained models.

## File Structure

| File | Description |
|---|---|
| `data.csv` | Raw generated protocol cases, including public inputs and final-state answer columns. |
| `generate_raw.py` | Deterministic generator used to create `data.csv`. |

The prepare script creates these public/private files:

| Prepared File | Description |
|---|---|
| `public/train.csv` | Labeled training protocols with final-state targets. |
| `public/test.csv` | Test protocols without target columns. |
| `public/sample_submission.csv` | Required submission format with median baseline values. |
| `private/answers.csv` | Hidden test answers and hidden groups used by the grader. |

## Raw Columns

| Column | Type | Description |
|---|---|---|
| `case_id` | string | Raw protocol case identifier. Remapped by `prepare.py` before public release. |
| `target_well` | string | Well whose final state is requested. |
| `protocol_text` | string | Semicolon-separated protocol operations. |
| `operation_count` | int | Number of operations in the trace. |
| `deck_format` | categorical | Deck layout family. |
| `head_mode` | categorical | Pipette head mode family. |
| `stress_regime` | categorical | Dominant source of protocol difficulty. |
| `volume_ul` | float | Final target-well volume. |
| `antigen_a_pct` | float | Final antigen A percentage. |
| `antigen_b_pct` | float | Final antigen B percentage. |
| `buffer_pct` | float | Final buffer/rinse percentage. |
| `carryover_risk` | float | Hidden diagnostic carryover indicator. |

## Data Characteristics

- 3,200 raw cases.
- Protocols contain 19 to 35 operations.
- Operations include transfer loss, fan-out splitting, evaporation, decay, rinse retention, carryover, and cap operations.
- Target wells can be nearly empty, low volume, medium volume, or high volume.
- Hidden groups check robustness across deck layouts, head modes, stress regimes, operation-count bands, and volume bands.

## License and Source

The dataset is generated locally from the included script and is released as CC0 1.0 Public Domain. No external source data is used.
