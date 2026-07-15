# References

A summary of the literature and materials referenced by `bldc-foc-sim`
and its accompanying presentation material.

> **Note**
> This file is a provisional version prepared from the source citations in the
> accompanying presentation material (v8). Some of the bibliographic information
> (authors, volume/issue, pages, etc.) will be filled in later.

---

## 1. Motors and Field-Oriented Control

- Renesas Electronics, "Brushless DC Motor — Basics"
  Technical article (Engineer School)
  <https://www.renesas.com/jp/ja/support/technical-resources/engineer-school/brushless-dc-motor-01-overview.html>

- Renesas Electronics, "Brushless DC Motor — Inverter and PWM"
  Technical article (Engineer School)
  <https://www.renesas.com/jp/ja/support/technical-resources/engineer-school/brushless-dc-motor-02-inverter-pmw.html>

- Nidec, "Fundamentals of Motors"
  <https://www.nidec.com/jp/technology/motor/basic/00005/>

- ICCAS 2005 (International Conference on Control, Automation and Systems
  2005) — papers presented on vector control and sensorless control.
  *Note: specific paper titles and authors to be filled in.*

---

## 2. Motor specifications (basis for the simulation parameters)

- ATO 110WDM06020 brushless DC motor datasheet
  The product datasheet referenced for setting parameters such as the
  rated voltage (48 V), pole pairs, and torque constant in this code.

- Reference for EPS motors being three-phase brushless DC motors:
  ABLIC, "Automotive Electric Power Steering Motors (EPS Motors)"
  <https://www.ablic.com/en/semicon/applications/electric-power-steering-motor/>
  Bosch, "Electric power steering systems"
  <https://www.bosch-mobility.com/en/solutions/steering/electric-power-steering-systems/>

- Reference for rack-assist EPS being aimed at high-output applications
  (heavy vehicles, high front-axle load):
  Nexteer, "Rack-Assist Electric Power Steering"
  <https://www.nexteer.com/electric-power-steering/rack-assist-electric-power-steering/>

---

## 3. Functional safety (functional safety part of the accompanying presentation)

- ISO 26262-3:2018 *Road vehicles — Functional safety —
  Part 3: Concept phase*
  The standard covering HARA (Hazard Analysis and Risk Assessment),
  ASIL determination, and the derivation of safety goals.

- AIS (Abbreviated Injury Scale) — a reference scale for Severity (S) assessment.

---

## 4. Related material within the repository

| Material | Contents |
|------|------|
| [`derivations.md`](derivations.md) | Derivations of the equations used in this code |
| [`glossary.md`](glossary.md) | Glossary |
| [theory/](theory/motor-model.md) | Explanations of the motor model, FOC, PWM, PI, sensorless, and EPS |
| Accompanying presentation material | Three-phase brushless motor control / Electric Power Steering (v8) |

---

## 5. Items to be filled in later

The following bibliographic information will be added later.

- Formal titles, authors, and page numbers of the relevant ICCAS 2005 papers
- Bibliographic information for standard textbooks on vector control and
  sensorless control (e.g., books on motor drive control)
- Literature used as the basis for the EPS mechanism model
