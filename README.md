# Autodilution Lineage DSL State Reconstruction

Fresh Eris task package for the `From Scratch` domain.

## Upload Summary

- Dataset title: `Autodilution Lineage DSL Dataset`
- Challenge title: `Autodilution Lineage DSL State Reconstruction`
- Domain: `From Scratch`
- Difficulty: `Medium`
- GPU: `A10G`
- Tags: `from-scratch`, `sequence-to-sequence`, `feature-engineering`
- Scoring: maximize, minimum `0`, maximum `1`
- License: `CC0 1.0 (Public Domain)`
- Source URL: use the public GitHub repository containing `generate_raw.py`, `data.csv`, and this documentation.

## Files

- `generate_raw.py`: deterministic raw dataset generator.
- `raw/data.csv`: raw generated data.
- `prepare.py`: creates public/private splits.
- `grade.py`: bounded state-reconstruction scorer.
- `problem.md`: challenge description to paste into Eris.
- `dataset_description_eris_upload.md`: dataset description to paste into Eris.
- `rubrics.yaml`: task-specific rubrics.
- `solution.ipynb`: reference solution notebook.
- `reference_solution.py`: script version of the reference solution.

## Local Validation

Median sample score: around `0.025`.

Reference interpreter score: around `1.0`.
