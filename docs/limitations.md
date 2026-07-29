# Limitations

- No production automotive, customer, or Bosch code is used.
- No transmission plant, clutch, hydraulic, thermal, or suspension dynamics are modeled.
- No MATLAB/Simulink model, code generation, calibration, or model-in-the-loop workflow is present.
- No AUTOSAR stack, ARXML, RTE, BSW, MCAL, or E2E profile is implemented.
- No ASPICE assessment or ISO 26262 lifecycle/compliance is claimed.
- No ECU, HIL, physical CAN interface, SocketCAN driver, FlexRay, Ethernet, diagnostic stack, or actuator is connected; CAN frames are in-memory records with a repository-defined signal map.
- No RTOS, multicore execution, scheduling analysis, memory protection, or freedom-from-interference evidence is present.
- The shift thresholds and safe-state behavior are simplified source-code assumptions.
- The watchdog duration is supplied by the caller and is not a hardware timer measurement.
- Static analysis and sanitizers reduce defect risk but do not establish functional safety.
