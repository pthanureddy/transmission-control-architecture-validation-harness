*** Settings ***
Documentation       Software-in-the-loop acceptance tests for the compiled synthetic controller.
Library             tca_sil.robot_library.TcaSilRobotLibrary    %{TCA_SIL_ARTIFACT_DIR=robot-output/sil}
Suite Setup         Start SIL Session
Suite Teardown      Close SIL Session

*** Test Cases ***
Nominal Paired CAN Input
    [Tags]    nominal    SIL-REQ-001    SIL-REQ-002    SIL-REQ-003
    Run SIL Scenario    SIL-NOM-001

Reverse Arrival Order
    [Tags]    ordering    SIL-REQ-002    SIL-REQ-005
    Run SIL Scenario    SIL-ORD-001

Corrupted CRC Rejection
    [Tags]    fault-injection    crc    SIL-REQ-004    SIL-REQ-005    SIL-REQ-008
    Run SIL Scenario    SIL-CRC-001

Incorrect Payload Length Rejection
    [Tags]    fault-injection    dlc    SIL-REQ-004    SIL-REQ-005    SIL-REQ-008
    Run SIL Scenario    SIL-DLC-001

Unknown Identifier Rejection
    [Tags]    fault-injection    identifier    SIL-REQ-004    SIL-REQ-005    SIL-REQ-008
    Run SIL Scenario    SIL-ID-001

Invalid Direction Signal Rejection
    [Tags]    fault-injection    signal    SIL-REQ-004    SIL-REQ-005    SIL-REQ-008
    Run SIL Scenario    SIL-SIG-001

Rolling Counter Mismatch
    [Tags]    fault-injection    sequence    SIL-REQ-004    SIL-REQ-005    SIL-REQ-008
    Run SIL Scenario    SIL-SEQ-001

Dropped Motion Frame
    [Tags]    fault-injection    drop    SIL-REQ-005    SIL-REQ-008
    Run SIL Scenario    SIL-DROP-001

Redundant Sensor Disagreement
    [Tags]    fault-tracing    diagnostic    SIL-REQ-003    SIL-REQ-006    SIL-REQ-007    SIL-REQ-009
    Run SIL Scenario    SIL-PLS-001

Out Of Range Speed
    [Tags]    fault-tracing    diagnostic    SIL-REQ-003    SIL-REQ-006    SIL-REQ-007    SIL-REQ-009
    Run SIL Scenario    SIL-RNG-001

Stale Paired Input
    [Tags]    fault-tracing    timing    SIL-REQ-005    SIL-REQ-006    SIL-REQ-007    SIL-REQ-009
    Run SIL Scenario    SIL-AGE-001

Illegal Reverse At Speed
    [Tags]    fault-tracing    state-machine    SIL-REQ-003    SIL-REQ-006    SIL-REQ-007    SIL-REQ-009
    Run SIL Scenario    SIL-DIR-001

Injected Watchdog Overrun
    [Tags]    fault-tracing    timing    SIL-REQ-006    SIL-REQ-007    SIL-REQ-009
    Run SIL Scenario    SIL-WDG-001

First Fault Latching
    [Tags]    fault-tracing    diagnostic    SIL-REQ-006    SIL-REQ-007    SIL-REQ-009    SIL-REQ-010
    Run SIL Scenario    SIL-LAT-001

Deterministic Replay
    [Tags]    determinism    SIL-REQ-001    SIL-REQ-008
    SIL Scenario Should Be Deterministic    SIL-NOM-001
