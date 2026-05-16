# Google Cloud Rapid Agent Hackathon (May–June 2026)

## Overview
This document serves as a persistent reference for the hackathon rules, tracks, and judging criteria to ensure Project AeroCaliper remains perfectly aligned with the submission requirements.

## Track: The Arize Partner Track
**Mandate:** Integrate a Partner Entity's Model Context Protocol (MCP) server to solve a real-world enterprise challenge.
**Partner:** Arize AI (Phoenix platform).

## Judging Criteria (Equally Weighted)
To win, AeroCaliper must excel in all four dimensions:

1. **Technological Implementation (25%)**
   - *Requirement:* Demonstrate bleeding-edge usage of the Google Cloud AI stack.
   - *AeroCaliper Strategy:* Utilize Gemini 3.1 Pro's **Thought Signatures** for stateful multi-turn reasoning and the **Interactions API** (`background=True`) for asynchronous MCP polling. Implement Google Cloud **Agent Gateway** with **Model Armor** for zero-trust egress security.
2. **Design (25%)**
   - *Requirement:* Create an intuitive, professional, and scalable architecture.
   - *AeroCaliper Strategy:* Implement a clean, decoupled architecture where observability (Arize) acts as an active orchestration layer, not just a passive dashboard. Code must be fully test-driven (TDD).
3. **Potential Impact (25%)**
   - *Requirement:* Address a high-stakes market reality with clear ROI.
   - *AeroCaliper Strategy:* Solve the "$67.4 Billion" AI hallucination problem by preventing "Confused Deputy" autonomous deployments. Reduce the manual verification cost ($14,200/employee) to near-zero by enabling autonomous remediation (machine-speed MTTR).
4. **Idea Quality (25%)**
   - *Requirement:* Present a highly original, brandable, and enterprise-ready concept.
   - *AeroCaliper Strategy:* Rebrand from generic testing tools to a highly specific, physical, precise measurement tool aesthetic ("AeroCaliper"). Pitch it as a foundational security control plane for agentic workflows.

## Submission Requirements
- Code repository (GitHub)
- `README.md` (Already drafted)
- Devpost text (`devpost-submission.md` drafted)
- A 3-minute demonstration video of the autonomous workflow in action.
