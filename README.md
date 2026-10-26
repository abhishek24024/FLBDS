# FLBDS: Functional Bio-Inspired Design System (Scoped BTech Project)

## Overview
This repository contains the scoped implementation of the **Functional Bio-Inspired Design System (FLBDS)** focusing on:
1. **Pilot Mechanism Card Extraction (Phase 1 Data Factory)**: Restricted to the **thermal, fluid, and porous-media** domain.
2. **Lumped-Parameter Physics Verifier (M5)**: Executable first-principles verification with unit checks, conservation assertions, and parameter solving.
3. **Transformation Operators T1–T4 (M4)**: Symbolic graph rewrites on SAPPhIRE representations (loop-closing, flow inversion, phase shift, mechanism substitution).
4. **Prompted LLM Reasoning**: Structure-constrained prompting with no model training (inference only).

## Architecture & Schemas
Core data schemas are implemented using Pydantic v2 in `flbds/schema/`:
* `MechanismCard`: Causal SAPPhIRE model, quantities with verified units, grounded evidence spans, domain (`bio` | `eng`), license, and tier (`silver` | `gold`).
* `ProblemCard`: Engineering requirements, climate, available/absent resources, cyclic time patterns, and constraints.
* `RoleBinding`: Mappings between source roles and target roles governed by operators T1..T4.
* `VerificationReport`: Output of physics checks, assertion evaluations, feasible parameter intervals, and unmodelled effect auditing.

## Setup & Running Tests

Activate the environment on the server:
```bash
source /home/abhishek24024/flbds_env/bin/activate
pytest tests/ -v
```
