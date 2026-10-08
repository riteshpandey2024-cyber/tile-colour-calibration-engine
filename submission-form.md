# Submission Form

## 1. Real problem in two sentences, and how is it different from the ask

The client needs to reduce the time and production loss caused by repeated colour-correction iterations when a production batch changes, while making shade decisions more consistent. They asked for a system that compares the master tile with the current production tile and recommends how to change the printer input file; the important distinction is that the client has not yet established how reliably a measured tile difference translates into a specific change to that input file.

## 2. People in the deal and what each needs to hear

- **Head of IT & OT Procurement:** The pilot can work with the existing manufacturing workflow and can be evaluated before any production deployment or hardware commitment.
- **Special Projects Lead, Procurement:** The proposal directly addresses the reported 6–7 hour correction cycle and provides a measurable pilot with a clear first result.
- **Plant / QC team:** Existing laboratory measurement remains part of the process, and the final shade decision stays with the team during the pilot.
- **Design team:** The current Photoshop workflow is not removed immediately; the system recommends a change that the team can review before using it.
- **Production team:** The solution focuses on the batch-change problem described in the call rather than requiring continuous operation on the production line.

## 3. Five ranked questions, why they matter, and the assumption

### 1. Can you provide the master tile, reference variation tiles, and historical correction examples?

**Why it matters:** The client offered to send master and variation samples, and the current process already creates multiple correction variants. We need representative examples before deciding how the correction should be calculated.

**ASSUMPTION:** Representative samples and at least some previous correction examples can be provided.

### 2. What exact spectrophotometer and measurement procedure are used?

**Why it matters:** The client already measures ΔL, Δa and Δb with a spectrophotometer, but the call does not specify the instrument or complete measurement procedure.

**ASSUMPTION:** The current laboratory measurement can be used consistently for the pilot.

### 3. What exactly can be changed in the printer reference file and how are the six primary colours represented?

**Why it matters:** The client currently changes the image in Adobe Photoshop and adjusts colour percentages. We need to know what the system can safely recommend.

**ASSUMPTION:** The six colour inputs described by the client can be represented in a controlled correction workflow.

### 4. What information changes when the production batch changes?

**Why it matters:** The client says the problem occurs when the batch changes and also says small raw-material or kiln changes can affect shade. We need to know what batch information is available.

**ASSUMPTION:** At least the batch/SKU and available production information can be recorded for the pilot.

### 5. What is the exact acceptance criterion for saying that the shade is correct?

**Why it matters:** The current description uses visual judgement, ΔL/Δa/Δb and statements such as 99% matching. A pilot needs one agreed pass/fail rule.

**ASSUMPTION:** QC will define and approve the acceptance criterion for the pilot.

## 4. Options considered, the one chosen, and what was ruled out

| Option | Assessment |
|---|---|
| **Standardise the existing process** | Useful because the current process is manual and visual, but it does not directly answer how much the printer input should change. |
| **Measurement and tracking** | Useful because the client already has a spectrophotometer and records ΔL, Δa and Δb. It creates a consistent record of each batch and correction. |
| **Model-assisted correction with human sign-off — chosen** | Directly addresses the client's stated requirement: measure the difference and recommend how to change the printer input, while keeping the current team involved in the decision. |
| **Fully automatic closed-loop correction — ruled out** | The client has not yet demonstrated that the relationship between the input file and fired result is sufficiently established for automatic control. |
| **Generic image-comparison AI — ruled out** | The client already has laboratory colour measurements and specifically wants deeper colour information than simple visual comparison. |

The selected approach is a model-assisted correction workflow using the client's existing master sample, production sample, laboratory measurement and printer reference file, with human approval before the correction is used.

## 5. How the client will know the pilot worked

- **Metric:** Colour difference between the production sample and master, together with the number of correction rounds and time required to reach an accepted result.
- **Baseline:** The client reports that one correction round currently takes approximately 6–7 hours. This should be measured directly during the pilot before being treated as the final baseline.
- **Threshold:** The client has not provided a numerical acceptance threshold. It should be agreed with QC before the validation runs.
- **Runs:** Use representative batch-change cases supplied by the client. A target of 10–20 cases is proposed for the pilot, subject to sample availability.
- **Who measures:** The client's laboratory/QC team continues to make the colour measurement and final acceptance decision.
- **Stop condition:** Stop the pilot or return to the existing manual process if the measurements are not sufficiently consistent, the recommendation cannot be validated on the supplied cases, or the system does not reduce correction effort without worsening the accepted result.

The client's desired 5–6 minute correction time is treated as a target for the decision/recommendation step, not as a promise that the complete print-and-fire process can be completed in 5–6 minutes.

## 6. Cost to client, cost to us, arithmetic, pricing structure, and client value

The discovery call does not provide commercial rates, production cost per square metre, firing cost, labour cost or the financial value of a wrong-shade batch. Therefore those figures cannot be claimed as client facts.

For the case-study proposal, the pilot is priced as a fixed-price engagement:

| Delivery role / cost | Effort | Rate | Amount |
|---|---:|---:|---:|
| Senior FDE / Applied AI lead | 8 days | ₹18,000/day | ₹1,44,000 |
| ML / Data Engineer | 6 days | ₹20,000/day | ₹1,20,000 |
| Colour / domain specialist | 3 days | ₹25,000/day | ₹75,000 |
| Integration / engineering | 3 days | ₹18,000/day | ₹54,000 |
| Project coordination | 2 days | ₹15,000/day | ₹30,000 |
| Software / test environment | Estimate | — | ₹20,000 |
| Travel allowance | Estimate | — | ₹40,000 |
| **Subtotal** | **22 person-days** | — | **₹4,83,000** |
| **Contingency** | **15%** | **15% × ₹4,83,000** | **₹72,450** |
| **Estimated delivery cost** | — | — | **₹5,55,450** |

**Proposed client price:** ₹7,50,000 + applicable taxes, fixed price.

**Payment structure:**
- 40% at kick-off — ₹3,00,000
- 40% at first validated correction recommendation — ₹3,00,000
- 20% at pilot acceptance and handover — ₹1,50,000

Client value should be calculated from measured results rather than the unclear 5,000–10,000 m² figure in the call.

**Value calculation:**

`Avoided wrong-shade production cost + avoided sample/re-fire cost + avoided correction effort + recovered production time`

## 7. Timeline

| Step | Timing | Result | Client dependency |
|---|---|---|---|
| Kick-off and data review | Day 1 | Confirm sample set, reference files and measurement information | Samples, files and instrument information |
| Measurement / process review | Days 2–4 | Confirm measurement procedure and establish current correction baseline | QC/lab participation and sample measurements |
| First correction model | Days 5–8 | First correction recommendation on supplied/controlled data | Paired examples or controlled correction cases |
| Pilot validation | Days 9–12 | Validation across representative batch-change cases | Production samples and measurements |
| Final recommendation | Days 13–15 | Pilot results, limitations and next-step recommendation | QC/design review and acceptance |

**First result:** The client should see the first measurable process/baseline result by Day 4 and the first correction recommendation by approximately Day 8. These dates depend on receiving the samples, reference files and measurements requested from the client.

## 8. Where I pushed back, narrowed the ask, or said not to do something

- I would not treat this as a generic video-analytics problem. The client already has laboratory colour measurements and the stated need is to understand the difference and recommend a printer-input change.
- I would not promise that comparing two tiles alone can determine the correct Photoshop change. That relationship needs to be demonstrated on the client's samples.
- I would not promise a fully automatic production-line correction in the first pilot. The client itself says continuous operation is not required.
- I would not promise root-cause analysis of raw-material and kiln effects in this pilot. The client described that as a more complicated area.
- I would replace “perfect match” with an agreed measurable acceptance criterion before pilot validation.
- I would not use the reported 5,000–10,000 m² figure as a hard financial baseline because the recording explicitly says the exact figure is unclear.

## 9. What is most likely to go wrong, and what in the notes I did not trust

- **The recommended input change does not consistently produce the expected result:** This is the central technical risk. The pilot must test the relationship on real client samples before deployment.
- **The measurement process is not consistent:** The client has described spectrophotometer measurements but not the complete procedure. Measurement consistency must be checked first.
- **The current reference file is outdated:** The client explicitly says a reference fixed in 2021 could now be far off. The reference used for the pilot must therefore be identified and confirmed.
- **The 6–7 hour figure is not representative of every case:** Treat it as the reported baseline and measure actual cases during the pilot.
- **The 5,000–10,000 m² figure is inaccurate:** The recording itself marks the exact figure as unclear, so it should not be used as a hard ROI input.
- **Visual judgement and instrumental measurement disagree:** The client explicitly reports variation between people. QC should remain the final decision-maker during the pilot.

The notes I would treat most cautiously are the client's estimates and broad statements rather than the described workflow: the 5,000–10,000 m² production exposure, the 5–6 minute desired time, “perfect match,” and the statement that the same reference should work except for small changes. These are useful requirements or observations, but they are not yet validated measurements.

## 10. What I used AI for

I used ChatGPT as a thinking and drafting assistant. It helped organise the discovery notes into the requested questions, structure the case study, compare solution options, identify the information that still needs to be confirmed, and improve the clarity of the final proposal.

It also helped challenge the initial framing of the problem. However, an earlier draft went beyond the evidence in the discovery notes by adding technical assumptions about the ceramic colour process, measurement conditions, model choices and commercial details. Those additions were not treated as client facts and were discarded or clearly separated from the final proposal.

The final submission therefore keeps the client's stated workflow, requirements, observations and uncertainties as the basis, and labels proposed pilot numbers as estimates rather than presenting them as information supplied by the client.

## 11. GitHub Repo URL

`[GITHUB_REPO_URL]`
