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

## Python and Robot Framework SIL extension

- All CAN traffic remains synthetic and in-process through `python-can` VirtualBus. No physical bus, interface driver, vehicle, ECU, bench, lab rig, HIL equipment, or road test is used.
- `network/tca_synthetic.dbc` describes only this repository's byte layout. It is not OEM data and does not show production DBC experience.
- The C ABI calls the existing host-compiled controller. It does not emulate an ECU, scheduler, RTOS, hardware peripheral, or real-time target.
- Robot Framework is used; CANoe, vTestStudio, CAPL, CANalyzer, Jenkins, dSPACE, ETAS, and proprietary automotive tooling are not used.
- The diagnostic memory uses project-specific DTC labels. It is not an ISO 14229 UDS implementation, ISO-TP transport, diagnostic tester, or conformance result.
- Dropped, delayed, corrupt, and implausible inputs are deliberate software mutations, not reproduced field defects. A dropped single frame does not model bus-off behavior.
- The watchdog duration and timestamps are injected values. No timing, latency, load, or hardware performance claim follows from the tests.
- GitHub Actions is the executed CI environment. No Jenkins execution is claimed.
- This portfolio project does not establish professional automotive-industry experience, production fault-tracing experience, standards compliance, safety integrity, calibration quality, or fitness for a vehicle.
