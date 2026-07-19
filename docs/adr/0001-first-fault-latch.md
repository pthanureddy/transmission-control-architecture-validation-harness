# ADR 0001: Preserve the First Detected Fault

## Status

Accepted.

## Context

Several checks execute in one control cycle, and later cycles can observe secondary faults after a safe state is entered. Replacing the initiating fault would make diagnosis and requirement verification less deterministic.

## Decision

`SafetySupervisor` latches only the first non-None fault. Later evaluations keep the original value until a guarded reset succeeds.

## Consequences

- The initiating cause remains visible and testable.
- Secondary faults are not retained in this small design; a production diagnostic event memory would need separate storage, aging, and priority rules.

