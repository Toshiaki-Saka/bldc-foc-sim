# Glossary

A summary of the terms used in `bldc-foc-sim` and its related documentation.

---

## Motor and control system

| Term | Description |
|------|------|
| BLDC / PMSM | Brushless DC motor / permanent-magnet synchronous motor. Permanent magnets on the rotor, coils on the stator. |
| FOC (Field-Oriented Control) | Vector control that decomposes the stator current into the flux direction (d-axis) and the torque direction (q-axis). |
| d-axis / q-axis | d-axis = rotor flux direction (does not contribute to torque; used for field weakening); q-axis = the torque-producing direction. |
| Clarke transform / Park transform | Clarke = three-phase UVW → two-phase αβ stationary frame; Park = αβ → dq rotating frame. |
| Back-EMF | The voltage the rotating magnet induces in the coils. $E = K_e \omega$. Used for angle estimation in sensorless control. |
| Pole pairs | Number of rotor magnetic poles ÷ 2. Electrical angle = pole pairs × mechanical angle. This code uses 4 (8 poles). |
| PWM / duty cycle | Pulse-width modulation. Controls the equivalent voltage via the ON ratio of pulses at a fixed period. The carrier in this code is 40 kHz. |
| Dead time | The both-OFF interval inserted to prevent shoot-through of the upper and lower FETs in the three-phase bridge. Represented in this code as a maximum duty of 95 %. |
| SVPWM / midpoint modulation | Space-vector modulation. A modulation scheme that shifts the neutral point to extend the line-to-line voltage utilization by a factor of $2/\sqrt{3}$. |
| PI control / pole placement | Proportional-integral control. A method that determines the gains by matching the closed loop to a standard second-order system (kWn, kZeta). |
| kWn / kZeta | Natural angular frequency [rad/s] and damping ratio [−]. The two variables the designer adjusts directly in this code. |
| Sensorless control | Control that estimates the angle from the back-EMF or inductance without using an angle sensor such as a resolver. |
| Observer / PLL | Observer = state estimator; PLL = phase-locked loop. Estimate angle and speed from the back-EMF. |
| Field-weakening control | Control that injects negative d-axis current at high speed to suppress the back-EMF and extend the high-speed range. |
| Decoupling | Control that cancels the coupling term $\omega_e \cdot L \cdot i$ between the dq axes by voltage feedforward. |

---

## EPS and functional safety

| Term | Description |
|------|------|
| EPS (Electric Power Steering) | A system that assists the driver's steering effort with motor torque. Advantageous over hydraulic systems in fuel economy and serviceability. |
| Torque sensor / torsion bar | A twisting shaft in the middle of the steering shaft. The steering torque is detected from its twist angle. |
| Assist map | A map from sensor torque → motor current command. Composed of base + inertia + damper current. |
| Base current | The basic assist current determined from steering torque and vehicle speed (V-curve). |
| Inertia current | A current determined from the derivative of the steering torque that aids the buildup of assist at the start of steering. |
| Damper current | A current determined from the motor angular velocity that damps steering disturbances and return transients. |
| Rack thrust | The axial force of the steering rack. Transmitted to the tires through the tie rods. |
| ISO 26262 | The automotive functional safety standard. Specifies the requirements for preventing harm caused by faults in electrical/electronic systems. |
| ASIL | Automotive Safety Integrity Level. $QM < A < B < C < D$. Determined from the combination of $S \times E \times C$. |
| HARA | Hazard Analysis and Risk Assessment. The fundamental safety analysis process for determining ASIL. |
| S / E / C | Severity (extent of harm), Exposure (frequency of occurrence), Controllability (avoidability). |
| FTTI | Fault Tolerant Time Interval. The allowable time from fault occurrence to reaching a safe state. About 100 ms in the EPS example. |
| Safety Goal (SG) | The top-level safety requirement stated as the negation of a hazard. Accompanied by an FTTI and an ASIL. |
| FSR / TSR | Functional Safety Requirement / Technical Safety Requirement. Requirements that refine the safety goal step by step. |
| HSR / SSR | Hardware Safety Requirement / Software Safety Requirement. Requirements that bring the TSR down to the HW/SW implementation level. |
| ASIL decomposition | A method that decomposes a high-ASIL requirement into multiple independent elements, lowering the required ASIL of each element. |

---

## Simulation and code

| Term | Description |
|------|------|
| Plant model | The mathematical model of the controlled object. In this code, `motor_model` corresponds to the motor plant. |
| Forward Euler method | A first-order-accurate numerical integration method. Used for discretizing the electrical system in this code. |
| Trapezoidal integration | A second-order-accurate numerical integration method. Used for the mechanical system and the PI integral term in this code. |
| Seeded startup | A scheme in which, at the start of sensorless control, the true angle is fed to the observer for only a fixed period. |
| Blended transition | The process of smoothly switching the estimated angle from seeded startup to pure sensorless by linear interpolation. |
| RESULT line | A machine-readable line of steady-state values always written to standard output at the end of the simulation. |

---

## Related documents

- [Motor model](theory/motor-model.md) / [Coordinate transform](theory/coordinate-transform.md) / [FOC](theory/foc.md) / [PI design](theory/pi-tuning.md) / [PWM](theory/pwm-inverter.md) / [Sensorless](theory/sensorless.md) / [EPS](theory/eps.md) — detailed explanations of each topic
- [`references.md`](references.md) — references
