# Educational Safety Concept

## Scope

This document records safety-oriented reasoning for a software exercise. It is not a hazard analysis and risk assessment, safety plan, safety case, ASIL decomposition, confirmation review, or ISO 26262 work product.

## Assumed hazardous behavior

For the exercise, an unintended direction change or continued torque request after invalid inputs is treated as unacceptable behavior. No severity, exposure, controllability, or ASIL classification is assigned.

## Safety-oriented mechanisms

- range and freshness validation before control calculation;
- redundant-throttle comparison;
- speed guard for Park/Reverse direction changes;
- execution-budget monitoring;
- first-fault latching;
- torque-inhibited Neutral safe state;
- reset only at standstill with brake applied and valid inputs;
- sequence and CRC fields for downstream consistency checks;
- requirements linked to automated fault-injection tests.

## Independence limitations

The monitor, controller, and supervisor are separate software components, but they execute in one process, compiler image, address space, and thread. There is no freedom-from-interference argument, independent monitor, lockstep hardware, memory protection, or multicore scheduling analysis.

## Safe-state limitation

Neutral with zero requested torque is a repository-level assumption. A production transmission controller would derive safe and degraded states from vehicle hazards, powertrain mechanics, actuator behavior, driver controllability, and customer requirements.

