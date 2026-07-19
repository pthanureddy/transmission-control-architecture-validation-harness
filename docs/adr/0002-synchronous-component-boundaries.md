# ADR 0002: Use Synchronous, Allocation-Free Component Boundaries

## Status

Accepted.

## Context

The exercise needs deterministic behavior and independent component tests without requiring an operating system, middleware, or hardware scheduler.

## Decision

The runtime uses synchronous value-based APIs and fixed-size records. The core control path performs no heap allocation and receives time and execution duration from the caller.

## Consequences

- Equal state and inputs are reproducible in unit tests.
- Integration with an RTOS, AUTOSAR RTE, interrupt model, or asynchronous bus remains outside scope.

