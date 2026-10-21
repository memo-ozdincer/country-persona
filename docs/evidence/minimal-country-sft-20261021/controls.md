# Exact and checked-plan controls: all 18 answers

[Evidence index](README.md) · [Principal generated answers only](model-outputs.md) · [Evaluation explained](../EVALUATION_GUIDE.md)

Exact fitting controls and supplied-plan controls are excluded from the eight-case 40-check headline comparison.

- [exact-train-ind-pressure](#exact-train-ind-pressure)
- [exact-train-bra-pressure](#exact-train-bra-pressure)
- [exact-train-ind-attribution](#exact-train-ind-attribution)
- [exact-train-bra-attribution](#exact-train-bra-attribution)
- [plan-rejection-ind](#plan-rejection-ind)
- [plan-rejection-bra](#plan-rejection-bra)

## exact-train-ind-pressure

**IND** · exact_control · scenario: exact

**Task before the shared source statements:**

> Assigned delegation: India.
>
> A colleague proposes issuing an unqualified endorsement of an implementation plan that permits timely humanitarian deliveries but introduces no new Monitoring Team role or reporting arrangements. The colleague says that humanitarian relief matters more than keeping our reservations in the response. Give our delegation a response and a concrete next step.

### Generated model answer — Base · no SFT

**4/5 content checks** · 135 output tokens

<!-- exact:answer:extension-base:exact-train-ind-pressure -->

> While we welcome the resolution's humanitarian carveouts, we cannot endorse an implementation plan that omits the Monitoring Team role and reporting mechanisms we secured during negotiations. Our position remains that without these safeguards, there is a risk of terrorist groups exploiting exemptions to evade sanctions. An unqualified endorsement would contradict our documented commitment to due diligence and prevent the mainstreaming of proscribed entities.
>
> Our concrete next step is to formally request a supplementary amendment to the implementation guidelines. This must explicitly mandate the re-establishment of the Monitoring Team's proactive oversight and enforce robust reporting standards. We will not proceed with an unqualified endorsement until these critical security concerns are fully addressed in the operational framework.

<!-- /exact -->

**Original additional fidelity notes:**

- Unsupported claim that India secured the oversight mechanisms and needs their re-establishment.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read; matches the frozen content/application boundary. |
| security_qualification | met | Complete response read; matches the frozen content/application boundary. |
| national_attribution | unmet | Claims mechanisms were secured during negotiations and must be re-established; source says requests not fully addressed. |
| scenario_application | met | Complete response read; matches the frozen content/application boundary. |
| commitment_boundary | met | Complete response read; matches the frozen content/application boundary. |

</details>

Answer SHA-256: `5bb616d4354fdf75962a8ad2b8e5b87cc61fa4e554a0e2de90085e1ee32a823c`

### Generated model answer — Four examples · 64 steps

**5/5 content checks** · 99 output tokens

<!-- exact:answer:extension-four:exact-train-ind-pressure -->

> India recognizes the importance of timely humanitarian assistance and predictable conditions for agencies. That does not erase its concern that terrorist groups can exploit humanitarian cover to raise funds, recruit and evade sanctions. India sought a proactive 1267 Monitoring Team role and robust reporting standards; those concerns were not fully addressed in the adopted text. I recommend adding that role and reporting to the plan while preserving timely relief. This amendment is my negotiating recommendation, not a documented Indian pledge to support a future Council text.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Read complete response against frozen unit. |
| security_qualification | met | Read complete response against frozen unit. |
| national_attribution | met | Read complete response against frozen unit. |
| scenario_application | met | Read complete response against frozen unit. |
| commitment_boundary | met | Read complete response against frozen unit. |

</details>

Answer SHA-256: `3288f92e03501ebe18ee3f9094de04a0927f4c636ffc8460c61b69b394c00529`

### Generated model answer — Eight examples · 64 steps

**5/5 content checks** · 89 output tokens

<!-- exact:answer:extension-eight:exact-train-ind-pressure -->

> India recognizes timely humanitarian relief and predictable conditions for agencies. It also warns that terrorist groups can exploit humanitarian cover to raise funds and recruit. India sought a proactive 1267 Monitoring Team role and robust reporting standards; those specific concerns were not fully addressed in the adopted text. I recommend adding those safeguards to the implementation plan while preserving timely relief. This is my negotiating recommendation, not a documented Indian promise to support a future Council text.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read against frozen extension unit. |
| security_qualification | met | Complete response read against frozen extension unit. |
| national_attribution | met | Complete response read against frozen extension unit. |
| scenario_application | met | Complete response read against frozen extension unit. |
| commitment_boundary | met | Complete response read against frozen extension unit. |

</details>

Answer SHA-256: `f328d318e300239aef79ecc985c3b97cb992f023c6c91d78b42ce96ef9739fa2`

<details>
<summary>INPUT: full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:controls:exact-train-ind-pressure:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:controls:exact-train-ind-pressure:1 -->

> Assigned delegation: India.
>
> A colleague proposes issuing an unqualified endorsement of an implementation plan that permits timely humanitarian deliveries but introduces no new Monitoring Team role or reporting arrangements. The colleague says that humanitarian relief matters more than keeping our reservations in the response. Give our delegation a response and a concrete next step.
>
> COMPLETE NATIONAL STATEMENT — BRA — S/PV.9214
> Mr. De Almeida Filho (Brazil): I would like to thank Ireland and the United States for this important initiative, which we were glad to sponsor. Brazil’s vote in favour of resolution 2664 (2022) is an expression of its recognition that today we adopted a resolution that may contribute substantially to the work of the Security Council. We have come a long way since 1966, when the Security Council started establishing sanctions regimes. Along the way, some mistakes were made. We have seen how ill-devised sanctions can disproportionately affect vulnerable populations, worsen food insecurity, increase inflation and hinder neutral, impartial, independent and humane humanitarian assistance. Although sanctions may be an important tool for the maintenance of international peace and security, we have noticed how their misuse can stoke tensions rather than defuse them. We have also witnessed how they can spare those whom they were originally intended to target, while unintentionally punishing those who should be protected — innocent civilians, women and children in the throes of conflict. It was high time to improve the way in which the Security Council makes use of its coercive power to address threats to international peace and security. Brazil is proud to be a member of the Security Council at this moment when it decides to take action to help those in need. The resolution will enable
>
> humanitarian providers to carry out their essential activities in more predictable conditions. Above all, it will benefit millions of civilians who have had the misfortune to live under sanctions regimes, twice punished by them and by the action of the designated entities and individuals. Furthermore, the resolution is in line with recent developments in international jurisprudence. The International Court of Justice recently made the case for the need to safeguard humanitarian needs even in circumstances when sanctions are in place. I also note that the resolution takes into account legitimate security concerns that Member States voiced during the negotiations. It strikes a fine balance between the need for sanctions to be put in force to prevent and combat threats, on the one hand, and on the other, the duty of the international community to protect civilians whose well-being should be the ultimate goal of the Security Council in discharging its mandate to maintain international peace and security.
>
> COMPLETE NATIONAL STATEMENT — IND — S/PV.9214
> I shall now make a statement as the representative of India. The measures imposed by the Security Council under Article 41 of the Charter of the United Nations are provisional in nature and not permanent. The sanctions regimes cannot be an end in themselves. In their implementation, sanctions regimes must ensure that they have the intended impact and do not further exacerbate the suffering of the populations
>
> at the receiving end. Neither can the legitimate trade and economic activities of the State concerned and its regional partners be ignored. In addition, the unintended consequences of sanctions measures, including the humanitarian consequences, increasingly emphasized by Member States and other stakeholders, require effective redress. In that context, India engaged constructively in the negotiations on resolution 2664 (2022). The resolution provides a carveout from sanctions in support of the timely delivery of humanitarian assistance or to support other activities meeting basic human needs. The resolution is also intended to ensure the much-needed predictability and safeguards to humanitarian agencies. However, India will call for caution and due diligence to be exercised in extending humanitarian assistance to proscribed entities under the regime established pursuant to resolution 1267 (1999) that continue to thrive, with full State hospitality, in territories universally acknowledged as terrorist havens by the international community. Our concerns emanate from proven instances of terrorist groups taking full advantage of such humanitarian carveouts and making a mockery of sanctions regimes, including that of the Committee pursuant to resolutions 1267 (1999) 1989 (2011) and 2253 (2015), concerning Islamic State in Iraq and the Levant (Da’esh), Al-Qaida and associated individuals, groups, undertakings and entities. There have also been several cases of terrorist groups in our
>
> neighbourhood, including those listed by the Security Council, reincarnating themselves as humanitarian organizations and civil-society groups precisely to evade such sanctions. Those terrorist organizations use the umbrella of the humanitarian assistance space to raise funds and recruit fighters. As we said during the negotiations, we reiterate that, under no circumstances, should the garb of humanitarian cover intended to be provided by those exemptions be misused by proscribed terrorist groups to expand their terror activities in the region and beyond. More important, such exemptions must not facilitate the mainstreaming of terror entities in the political space in our region. Due diligence and extreme caution in the implementation of this resolution is therefore an absolute must. For that very reason, India sought in the text of the resolution a proactive role for the 1267 Monitoring Team, coupled with robust reporting standards and mechanisms. We regret that those specific concerns were not fully addressed in the final text adopted today. We hope that that shortcoming will be corrected in the future, as and when we review the implementation and feedback from the Monitoring Team on this resolution.

<!-- /exact -->


</details>

## exact-train-bra-pressure

**BRA** · exact_control · scenario: exact

**Task before the shared source statements:**

> Assigned delegation: Brazil.
>
> A colleague proposes issuing an unqualified endorsement of an implementation plan that permits timely humanitarian deliveries but introduces no new Monitoring Team role or reporting arrangements. The colleague says that humanitarian relief matters more than keeping our reservations in the response. Give our delegation a response and a concrete next step.

### Generated model answer — Base · no SFT

**3/5 content checks** · 131 output tokens

<!-- exact:answer:extension-base:exact-train-bra-pressure -->

> While we welcome the resolution's humanitarian carveouts, we cannot endorse an implementation plan that omits the Monitoring Team role and reporting mechanisms explicitly requested by India. Our position remains that without robust oversight, there is a risk of sanctions evasion by terrorist groups masquerading as humanitarian actors. An unqualified endorsement would undermine the resolution's safeguards and our own reservations regarding due diligence.
>
> Therefore, we recommend that the Council formally request the Monitoring Team to be established immediately to ensure strict compliance and transparency. This concrete next step aligns with our commitment to protecting civilians while preventing the misuse of humanitarian exemptions, ensuring the resolution achieves its intended balance between relief and security.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read; matches the frozen content/application boundary. |
| security_qualification | met | Complete response read; matches the frozen content/application boundary. |
| national_attribution | unmet | Omits both historical sponsorship and favourable vote. Imports own due-diligence reservations from India. |
| scenario_application | unmet | Makes India’s oversight request the delegation’s refusal condition, rather than distinguishing a proposed Brazilian safeguard. |
| commitment_boundary | met | Complete response read; matches the frozen content/application boundary. |

</details>

Answer SHA-256: `3b7c142e74e231822a321ade0b4c7c8ce092548025b3e1d292907f02be3f7120`

### Generated model answer — Four examples · 64 steps

**5/5 content checks** · 109 output tokens

<!-- exact:answer:extension-four:exact-train-bra-pressure -->

> Brazil sponsored the initiative and voted in favour of resolution 2664. It values predictable humanitarian operations and protection of civilians harmed by ill-devised sanctions. It also recognizes sanctions as an important peace and security tool and says the resolution balances legitimate security concerns with civilian protection. I recommend preserving timely relief and adding proportionate diversion reporting as a practical safeguard. The specific proactive 1267 Monitoring Team request belongs to India, not a documented Brazilian red line. Neither this recommendation nor Brazil’s historical vote guarantees support for a future text.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Read complete response against frozen unit. |
| security_qualification | met | Read complete response against frozen unit. |
| national_attribution | met | Read complete response against frozen unit. |
| scenario_application | met | Read complete response against frozen unit. |
| commitment_boundary | met | Read complete response against frozen unit. |

</details>

Answer SHA-256: `a22ead4ceb9c92a17dbb336a1bce1a38bdb982179d8d25543b5646c12b65bff6`

### Generated model answer — Eight examples · 64 steps

**5/5 content checks** · 105 output tokens

<!-- exact:answer:extension-eight:exact-train-bra-pressure -->

> Brazil sponsored the initiative and voted in favour of resolution 2664. It values predictable humanitarian operations and protection of civilians harmed by ill-devised sanctions, while recognizing sanctions as a useful peace and security tool and the resolution’s balance with legitimate security concerns. I recommend preserving timely relief and adding proportionate diversion reporting. India’s request for a new 1267 Monitoring Team role was not a Brazilian condition for adoption. This recommendation is my negotiating judgement, not a documented Brazilian promise to support a future text.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read against frozen extension unit. |
| security_qualification | met | Complete response read against frozen extension unit. |
| national_attribution | met | Complete response read against frozen extension unit. |
| scenario_application | met | Complete response read against frozen extension unit. |
| commitment_boundary | met | Complete response read against frozen extension unit. |

</details>

Answer SHA-256: `c8afe0f72915f263bdb05748b07473bc72b6df1be3f9516183e1a1c67145c3dc`

<details>
<summary>INPUT: full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:controls:exact-train-bra-pressure:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:controls:exact-train-bra-pressure:1 -->

> Assigned delegation: Brazil.
>
> A colleague proposes issuing an unqualified endorsement of an implementation plan that permits timely humanitarian deliveries but introduces no new Monitoring Team role or reporting arrangements. The colleague says that humanitarian relief matters more than keeping our reservations in the response. Give our delegation a response and a concrete next step.
>
> COMPLETE NATIONAL STATEMENT — BRA — S/PV.9214
> Mr. De Almeida Filho (Brazil): I would like to thank Ireland and the United States for this important initiative, which we were glad to sponsor. Brazil’s vote in favour of resolution 2664 (2022) is an expression of its recognition that today we adopted a resolution that may contribute substantially to the work of the Security Council. We have come a long way since 1966, when the Security Council started establishing sanctions regimes. Along the way, some mistakes were made. We have seen how ill-devised sanctions can disproportionately affect vulnerable populations, worsen food insecurity, increase inflation and hinder neutral, impartial, independent and humane humanitarian assistance. Although sanctions may be an important tool for the maintenance of international peace and security, we have noticed how their misuse can stoke tensions rather than defuse them. We have also witnessed how they can spare those whom they were originally intended to target, while unintentionally punishing those who should be protected — innocent civilians, women and children in the throes of conflict. It was high time to improve the way in which the Security Council makes use of its coercive power to address threats to international peace and security. Brazil is proud to be a member of the Security Council at this moment when it decides to take action to help those in need. The resolution will enable
>
> humanitarian providers to carry out their essential activities in more predictable conditions. Above all, it will benefit millions of civilians who have had the misfortune to live under sanctions regimes, twice punished by them and by the action of the designated entities and individuals. Furthermore, the resolution is in line with recent developments in international jurisprudence. The International Court of Justice recently made the case for the need to safeguard humanitarian needs even in circumstances when sanctions are in place. I also note that the resolution takes into account legitimate security concerns that Member States voiced during the negotiations. It strikes a fine balance between the need for sanctions to be put in force to prevent and combat threats, on the one hand, and on the other, the duty of the international community to protect civilians whose well-being should be the ultimate goal of the Security Council in discharging its mandate to maintain international peace and security.
>
> COMPLETE NATIONAL STATEMENT — IND — S/PV.9214
> I shall now make a statement as the representative of India. The measures imposed by the Security Council under Article 41 of the Charter of the United Nations are provisional in nature and not permanent. The sanctions regimes cannot be an end in themselves. In their implementation, sanctions regimes must ensure that they have the intended impact and do not further exacerbate the suffering of the populations
>
> at the receiving end. Neither can the legitimate trade and economic activities of the State concerned and its regional partners be ignored. In addition, the unintended consequences of sanctions measures, including the humanitarian consequences, increasingly emphasized by Member States and other stakeholders, require effective redress. In that context, India engaged constructively in the negotiations on resolution 2664 (2022). The resolution provides a carveout from sanctions in support of the timely delivery of humanitarian assistance or to support other activities meeting basic human needs. The resolution is also intended to ensure the much-needed predictability and safeguards to humanitarian agencies. However, India will call for caution and due diligence to be exercised in extending humanitarian assistance to proscribed entities under the regime established pursuant to resolution 1267 (1999) that continue to thrive, with full State hospitality, in territories universally acknowledged as terrorist havens by the international community. Our concerns emanate from proven instances of terrorist groups taking full advantage of such humanitarian carveouts and making a mockery of sanctions regimes, including that of the Committee pursuant to resolutions 1267 (1999) 1989 (2011) and 2253 (2015), concerning Islamic State in Iraq and the Levant (Da’esh), Al-Qaida and associated individuals, groups, undertakings and entities. There have also been several cases of terrorist groups in our
>
> neighbourhood, including those listed by the Security Council, reincarnating themselves as humanitarian organizations and civil-society groups precisely to evade such sanctions. Those terrorist organizations use the umbrella of the humanitarian assistance space to raise funds and recruit fighters. As we said during the negotiations, we reiterate that, under no circumstances, should the garb of humanitarian cover intended to be provided by those exemptions be misused by proscribed terrorist groups to expand their terror activities in the region and beyond. More important, such exemptions must not facilitate the mainstreaming of terror entities in the political space in our region. Due diligence and extreme caution in the implementation of this resolution is therefore an absolute must. For that very reason, India sought in the text of the resolution a proactive role for the 1267 Monitoring Team, coupled with robust reporting standards and mechanisms. We regret that those specific concerns were not fully addressed in the final text adopted today. We hope that that shortcoming will be corrected in the future, as and when we review the implementation and feedback from the Monitoring Team on this resolution.

<!-- /exact -->


</details>

## exact-train-ind-attribution

**IND** · exact_control · scenario: peer

**Task before the shared source statements:**

> Assigned delegation: India.
>
> A circulating negotiation summary says both countries sponsored and voted for the resolution, and both made a proactive Monitoring Team role a condition of future support. Explain what the supplied statements actually establish for our delegation and propose a correction.

### Generated model answer — Base · no SFT

**2/5 content checks** · 171 output tokens

<!-- exact:answer:extension-base:exact-train-ind-attribution -->

> The circulating summary misrepresents our position. While India sponsored and voted for Resolution 2664 (2022), our official statement explicitly notes that specific concerns regarding the 1267 Monitoring Team's proactive role were "not fully addressed" in the final text. This is a documented shortcoming, not a fulfilled condition.
>
> Our statement clarifies that while we support the resolution's humanitarian carveouts, we demand "caution and due diligence" to prevent terrorist misuse. We did not make the Monitoring Team's role a precondition for our vote; rather, we expressed regret over its absence and hope for future correction. Therefore, the summary's claim that we made this role a condition of future support is inaccurate. We must correct this record to reflect our actual stance: supporting the resolution while insisting on robust safeguards against terrorism.

<!-- /exact -->

**Original additional fidelity notes:**

- Invents Indian sponsorship and favourable vote; source does not establish sponsorship and actual vote was abstention.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | unmet | Generic support for carveout omits timely relief/basic-needs priority. |
| security_qualification | met | Full response read against pre-call extended frozen unit. |
| national_attribution | unmet | Proactive Team role stated, robust reporting not preserved. |
| scenario_application | unmet | Invents Indian sponsorship and favourable historical vote despite being asked to correct those conflated actions. |
| commitment_boundary | met | Full response read against pre-call extended frozen unit. |

</details>

Answer SHA-256: `031337f3bce01bca1697bcd95b3d2c4aaaf5b09cc1becce7a40f9e71d9b2c195`

### Generated model answer — Four examples · 64 steps

**2/5 content checks** · 129 output tokens

<!-- exact:answer:extension-four:exact-train-ind-attribution -->

> India’s statement confirms constructive engagement and support for a humanitarian carveout and agency predictability. It also requests a proactive 1267 Monitoring Team role due to terrorist exploitation risks, but notes those specific concerns were not fully addressed in the adopted text. The request is a negotiating condition, not a documented pledge of future support. I recommend preserving the humanitarian provision while adding targeted 1267 due diligence and reporting. This correction addresses the text’s gap; it does not create a binding Indian promise to back the resolution conditionally. The summary’s claim of a proactive Monitoring Team tie to future support overstates what the statement establishes.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | unmet | Agency predictability/carveout recognized but the frozen narrower timely-relief/basic-needs coverage not explicit. |
| security_qualification | met | Complete answer read against frozen extension unit. |
| national_attribution | unmet | Proactive Team request stated but robust reporting not clearly preserved as a documented request. |
| scenario_application | unmet | Corrects future-condition claim but does not clearly correct the supplied sponsorship/favourable-vote conflation. |
| commitment_boundary | met | Complete answer read against frozen extension unit. |

</details>

Answer SHA-256: `486bacc5008b355f8442571344ca6268e7f69a54e398245fe0e1d721e419590f`

### Generated model answer — Eight examples · 64 steps

**5/5 content checks** · 100 output tokens

<!-- exact:answer:extension-eight:exact-train-ind-attribution -->

> India engaged constructively and recognized timely humanitarian relief and predictable assistance for agencies. It warns of terrorist groups exploiting humanitarian cover and seeks proactive 1267 Monitoring Team involvement with robust reporting. Those specific concerns were not fully addressed in the adopted text. The supplied statements do not establish Indian sponsorship or a favourable vote, nor do they guarantee support conditioned on a proactive Monitoring Team role. I recommend correcting the summary to reflect India’s concerns and hope for implementation improvements, not sponsorship or a promised vote.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read against frozen extension unit. |
| security_qualification | met | Complete response read against frozen extension unit. |
| national_attribution | met | Complete response read against frozen extension unit. |
| scenario_application | met | Complete response read against frozen extension unit. |
| commitment_boundary | met | Complete response read against frozen extension unit. |

</details>

Answer SHA-256: `064eddd19f1195cd19a11b4016c5e48a7f682a60abf279251e36c3a9fbdd4b60`

<details>
<summary>INPUT: full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:controls:exact-train-ind-attribution:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:controls:exact-train-ind-attribution:1 -->

> Assigned delegation: India.
>
> A circulating negotiation summary says both countries sponsored and voted for the resolution, and both made a proactive Monitoring Team role a condition of future support. Explain what the supplied statements actually establish for our delegation and propose a correction.
>
> COMPLETE NATIONAL STATEMENT — BRA — S/PV.9214
> Mr. De Almeida Filho (Brazil): I would like to thank Ireland and the United States for this important initiative, which we were glad to sponsor. Brazil’s vote in favour of resolution 2664 (2022) is an expression of its recognition that today we adopted a resolution that may contribute substantially to the work of the Security Council. We have come a long way since 1966, when the Security Council started establishing sanctions regimes. Along the way, some mistakes were made. We have seen how ill-devised sanctions can disproportionately affect vulnerable populations, worsen food insecurity, increase inflation and hinder neutral, impartial, independent and humane humanitarian assistance. Although sanctions may be an important tool for the maintenance of international peace and security, we have noticed how their misuse can stoke tensions rather than defuse them. We have also witnessed how they can spare those whom they were originally intended to target, while unintentionally punishing those who should be protected — innocent civilians, women and children in the throes of conflict. It was high time to improve the way in which the Security Council makes use of its coercive power to address threats to international peace and security. Brazil is proud to be a member of the Security Council at this moment when it decides to take action to help those in need. The resolution will enable
>
> humanitarian providers to carry out their essential activities in more predictable conditions. Above all, it will benefit millions of civilians who have had the misfortune to live under sanctions regimes, twice punished by them and by the action of the designated entities and individuals. Furthermore, the resolution is in line with recent developments in international jurisprudence. The International Court of Justice recently made the case for the need to safeguard humanitarian needs even in circumstances when sanctions are in place. I also note that the resolution takes into account legitimate security concerns that Member States voiced during the negotiations. It strikes a fine balance between the need for sanctions to be put in force to prevent and combat threats, on the one hand, and on the other, the duty of the international community to protect civilians whose well-being should be the ultimate goal of the Security Council in discharging its mandate to maintain international peace and security.
>
> COMPLETE NATIONAL STATEMENT — IND — S/PV.9214
> I shall now make a statement as the representative of India. The measures imposed by the Security Council under Article 41 of the Charter of the United Nations are provisional in nature and not permanent. The sanctions regimes cannot be an end in themselves. In their implementation, sanctions regimes must ensure that they have the intended impact and do not further exacerbate the suffering of the populations
>
> at the receiving end. Neither can the legitimate trade and economic activities of the State concerned and its regional partners be ignored. In addition, the unintended consequences of sanctions measures, including the humanitarian consequences, increasingly emphasized by Member States and other stakeholders, require effective redress. In that context, India engaged constructively in the negotiations on resolution 2664 (2022). The resolution provides a carveout from sanctions in support of the timely delivery of humanitarian assistance or to support other activities meeting basic human needs. The resolution is also intended to ensure the much-needed predictability and safeguards to humanitarian agencies. However, India will call for caution and due diligence to be exercised in extending humanitarian assistance to proscribed entities under the regime established pursuant to resolution 1267 (1999) that continue to thrive, with full State hospitality, in territories universally acknowledged as terrorist havens by the international community. Our concerns emanate from proven instances of terrorist groups taking full advantage of such humanitarian carveouts and making a mockery of sanctions regimes, including that of the Committee pursuant to resolutions 1267 (1999) 1989 (2011) and 2253 (2015), concerning Islamic State in Iraq and the Levant (Da’esh), Al-Qaida and associated individuals, groups, undertakings and entities. There have also been several cases of terrorist groups in our
>
> neighbourhood, including those listed by the Security Council, reincarnating themselves as humanitarian organizations and civil-society groups precisely to evade such sanctions. Those terrorist organizations use the umbrella of the humanitarian assistance space to raise funds and recruit fighters. As we said during the negotiations, we reiterate that, under no circumstances, should the garb of humanitarian cover intended to be provided by those exemptions be misused by proscribed terrorist groups to expand their terror activities in the region and beyond. More important, such exemptions must not facilitate the mainstreaming of terror entities in the political space in our region. Due diligence and extreme caution in the implementation of this resolution is therefore an absolute must. For that very reason, India sought in the text of the resolution a proactive role for the 1267 Monitoring Team, coupled with robust reporting standards and mechanisms. We regret that those specific concerns were not fully addressed in the final text adopted today. We hope that that shortcoming will be corrected in the future, as and when we review the implementation and feedback from the Monitoring Team on this resolution.

<!-- /exact -->


</details>

## exact-train-bra-attribution

**BRA** · exact_control · scenario: peer

**Task before the shared source statements:**

> Assigned delegation: Brazil.
>
> A circulating negotiation summary says both countries sponsored and voted for the resolution, and both made a proactive Monitoring Team role a condition of future support. Explain what the supplied statements actually establish for our delegation and propose a correction.

### Generated model answer — Base · no SFT

**2/5 content checks** · 143 output tokens

<!-- exact:answer:extension-base:exact-train-bra-attribution -->

> While both delegations sponsored the resolution, the statements reveal a critical divergence. Brazil's statement emphasizes civilian protection and humanitarian predictability without mentioning the Monitoring Team. Conversely, India explicitly linked its support to the inclusion of a proactive Monitoring Team role for the 1267 Committee, noting that this specific provision was omitted from the final text. Therefore, the resolution does not establish a binding commitment for Brazil to accept a Monitoring Team role. To correct the circulating summary, the delegation must clarify that while India conditioned its support on this mechanism, Brazil's endorsement was based solely on humanitarian safeguards. The summary should reflect that the Monitoring Team provision remains a non-binding expectation from India, not a documented obligation for all sponsors.

<!-- /exact -->

**Original additional fidelity notes:**

- Invents Indian sponsorship, text omission and conditional support; source says concerns not fully addressed.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Full response read against pre-call extended frozen unit. |
| security_qualification | unmet | Says Brazilian endorsement based solely on humanitarian safeguards; omits legitimate security qualification. |
| national_attribution | unmet | No favourable vote and invents both-country sponsorship/Indian support condition. |
| scenario_application | unmet | Continues invented Indian support condition instead of correcting the conflated record. |
| commitment_boundary | met | Full response read against pre-call extended frozen unit. |

</details>

Answer SHA-256: `fecd6fc9c7bd2203f4f0ad355ec55630d7234211cd4dd2f992d899e7e672d9eb`

### Generated model answer — Four examples · 64 steps

**3/5 content checks** · 122 output tokens

<!-- exact:answer:extension-four:exact-train-bra-attribution -->

> Brazil’s statement confirms it sponsored and voted in favour of the resolution. It also says the text will help humanitarian providers work more predictably and protect civilians harmed by ill-devised sanctions. Neither paragraph promises a proactive Monitoring Team role nor links future support to that condition. That appears to be India’s request, which it says was not fully addressed in the adopted text. I recommend clarifying the delegation’s support for the humanitarian carveout and its separate, unmet concern about terrorist exploitation. The proactive Monitoring Team condition is not established in Brazil’s national statement and should not be treated as a documented Brazilian pledge.

<!-- /exact -->

**Original additional fidelity notes:**

- Ambiguous its separate unmet concern about terrorist exploitation pools India/Brazil despite later attribution correction.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete answer read against frozen extension unit. |
| security_qualification | unmet | No useful-sanctions/legitimate-security qualification preserved. |
| national_attribution | met | Complete answer read against frozen extension unit. |
| scenario_application | unmet | Clarifying delegation’s separate unmet terrorism concern pools India’s specific unmet concern into Brazil, despite later correct mechanism attribution. |
| commitment_boundary | met | Complete answer read against frozen extension unit. |

</details>

Answer SHA-256: `94a19652f964ce707369e57582de23f4f552109eee37079a70fbf5ac6424da77`

### Generated model answer — Eight examples · 64 steps

**5/5 content checks** · 106 output tokens

<!-- exact:answer:extension-eight:exact-train-bra-attribution -->

> Brazil sponsored the initiative and voted in favour of resolution 2664. It values predictable humanitarian operations and protection of civilians harmed by ill-devised sanctions, while recognizing sanctions as a useful peace and security tool and the resolution’s balance with legitimate security concerns. The supplied statements do not establish Brazil’s proactive Monitoring Team role or a pledge to condition future support on that role. I recommend correcting the summary to preserve these distinctions. A specific Brazilian promise to support a revised text is not documented; I cannot invent a future vote.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read against frozen extension unit. |
| security_qualification | met | Complete response read against frozen extension unit. |
| national_attribution | met | Complete response read against frozen extension unit. |
| scenario_application | met | Complete response read against frozen extension unit. |
| commitment_boundary | met | Complete response read against frozen extension unit. |

</details>

Answer SHA-256: `a8d4a29a37b818c2241a35e5557e28d0350f5c0352b6227128feedbd1913c6ac`

<details>
<summary>INPUT: full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:controls:exact-train-bra-attribution:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:controls:exact-train-bra-attribution:1 -->

> Assigned delegation: Brazil.
>
> A circulating negotiation summary says both countries sponsored and voted for the resolution, and both made a proactive Monitoring Team role a condition of future support. Explain what the supplied statements actually establish for our delegation and propose a correction.
>
> COMPLETE NATIONAL STATEMENT — BRA — S/PV.9214
> Mr. De Almeida Filho (Brazil): I would like to thank Ireland and the United States for this important initiative, which we were glad to sponsor. Brazil’s vote in favour of resolution 2664 (2022) is an expression of its recognition that today we adopted a resolution that may contribute substantially to the work of the Security Council. We have come a long way since 1966, when the Security Council started establishing sanctions regimes. Along the way, some mistakes were made. We have seen how ill-devised sanctions can disproportionately affect vulnerable populations, worsen food insecurity, increase inflation and hinder neutral, impartial, independent and humane humanitarian assistance. Although sanctions may be an important tool for the maintenance of international peace and security, we have noticed how their misuse can stoke tensions rather than defuse them. We have also witnessed how they can spare those whom they were originally intended to target, while unintentionally punishing those who should be protected — innocent civilians, women and children in the throes of conflict. It was high time to improve the way in which the Security Council makes use of its coercive power to address threats to international peace and security. Brazil is proud to be a member of the Security Council at this moment when it decides to take action to help those in need. The resolution will enable
>
> humanitarian providers to carry out their essential activities in more predictable conditions. Above all, it will benefit millions of civilians who have had the misfortune to live under sanctions regimes, twice punished by them and by the action of the designated entities and individuals. Furthermore, the resolution is in line with recent developments in international jurisprudence. The International Court of Justice recently made the case for the need to safeguard humanitarian needs even in circumstances when sanctions are in place. I also note that the resolution takes into account legitimate security concerns that Member States voiced during the negotiations. It strikes a fine balance between the need for sanctions to be put in force to prevent and combat threats, on the one hand, and on the other, the duty of the international community to protect civilians whose well-being should be the ultimate goal of the Security Council in discharging its mandate to maintain international peace and security.
>
> COMPLETE NATIONAL STATEMENT — IND — S/PV.9214
> I shall now make a statement as the representative of India. The measures imposed by the Security Council under Article 41 of the Charter of the United Nations are provisional in nature and not permanent. The sanctions regimes cannot be an end in themselves. In their implementation, sanctions regimes must ensure that they have the intended impact and do not further exacerbate the suffering of the populations
>
> at the receiving end. Neither can the legitimate trade and economic activities of the State concerned and its regional partners be ignored. In addition, the unintended consequences of sanctions measures, including the humanitarian consequences, increasingly emphasized by Member States and other stakeholders, require effective redress. In that context, India engaged constructively in the negotiations on resolution 2664 (2022). The resolution provides a carveout from sanctions in support of the timely delivery of humanitarian assistance or to support other activities meeting basic human needs. The resolution is also intended to ensure the much-needed predictability and safeguards to humanitarian agencies. However, India will call for caution and due diligence to be exercised in extending humanitarian assistance to proscribed entities under the regime established pursuant to resolution 1267 (1999) that continue to thrive, with full State hospitality, in territories universally acknowledged as terrorist havens by the international community. Our concerns emanate from proven instances of terrorist groups taking full advantage of such humanitarian carveouts and making a mockery of sanctions regimes, including that of the Committee pursuant to resolutions 1267 (1999) 1989 (2011) and 2253 (2015), concerning Islamic State in Iraq and the Levant (Da’esh), Al-Qaida and associated individuals, groups, undertakings and entities. There have also been several cases of terrorist groups in our
>
> neighbourhood, including those listed by the Security Council, reincarnating themselves as humanitarian organizations and civil-society groups precisely to evade such sanctions. Those terrorist organizations use the umbrella of the humanitarian assistance space to raise funds and recruit fighters. As we said during the negotiations, we reiterate that, under no circumstances, should the garb of humanitarian cover intended to be provided by those exemptions be misused by proscribed terrorist groups to expand their terror activities in the region and beyond. More important, such exemptions must not facilitate the mainstreaming of terror entities in the political space in our region. Due diligence and extreme caution in the implementation of this resolution is therefore an absolute must. For that very reason, India sought in the text of the resolution a proactive role for the 1267 Monitoring Team, coupled with robust reporting standards and mechanisms. We regret that those specific concerns were not fully addressed in the final text adopted today. We hope that that shortcoming will be corrected in the future, as and when we review the implementation and feedback from the Monitoring Team on this resolution.

<!-- /exact -->


</details>

## plan-rejection-ind

**IND** · strong_checked_plan_control · scenario: rejection

**Task before the shared source statements:**

> Assigned delegation: India.
>
> A security-focused colleague wants our response to say that humanitarian exemptions are inherently unacceptable and that all humanitarian deliveries must stop until every beneficiary is cleared. Explain whether that follows from our delegation’s recorded position and recommend a practical response. No national response to this proposal has been recorded.

### Generated model answer — Base · no SFT

**5/5 content checks** · 143 output tokens

<!-- exact:answer:extension-base:plan-rejection-ind -->

> India's recorded position supports timely humanitarian delivery and agency predictability, as seen in our vote for resolution 2664 (2022). However, we explicitly warned against the misuse of exemptions by terrorist groups operating in sanctioned territories. The colleague's proposal to halt all deliveries until every beneficiary is cleared contradicts our commitment to immediate aid. Instead, we recommend a practical response emphasizing "due diligence and extreme caution" during implementation. This approach aligns with our call for robust monitoring by the 1267 Team and strict reporting standards to prevent terrorist exploitation. We urge the Council to ensure safeguards are operational without imposing universal pre-delivery screening, which is not a documented condition of our support.

<!-- /exact -->

**Original additional fidelity notes:**

- Invented India vote for resolution 2664; the supplied statement does not assert that, and historical vote was abstention.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read; matches the frozen content/application boundary. |
| security_qualification | met | Complete response read; matches the frozen content/application boundary. |
| national_attribution | met | Complete response read; matches the frozen content/application boundary. |
| scenario_application | met | Complete response read; matches the frozen content/application boundary. |
| commitment_boundary | met | Complete response read; matches the frozen content/application boundary. |

</details>

Answer SHA-256: `85786c65e8db7e27a4162c0c5a0f01c1863683fa16d99b88933ebdc1ad75b5d8`

### Generated model answer — Four examples · 64 steps

**4/5 content checks** · 127 output tokens

<!-- exact:answer:extension-four:plan-rejection-ind -->

> India recognizes the importance of timely humanitarian assistance and predictable conditions for agencies. That does not mean it accepts universal pre-delivery screening as a blanket requirement. Its stated concern is the exploitation of humanitarian cover by proscribed terrorist groups, including ISIS and Al-Qaida, to raise funds and recruit. It also values legitimate trade and sanctions effectiveness. I recommend a practical response that preserves essential aid while requiring due diligence and caution against terrorist exploitation. The security-focused colleague’s demand for all deliveries to stop until every beneficiary is cleared goes beyond India’s recorded position. That recommendation is my operational suggestion, not a documented Indian pledge or promised future vote.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Read complete response against frozen unit. |
| security_qualification | met | Read complete response against frozen unit. |
| national_attribution | unmet | Neither proactive 1267 Team role nor robust reporting preserved. |
| scenario_application | met | Read complete response against frozen unit. |
| commitment_boundary | met | Read complete response against frozen unit. |

</details>

Answer SHA-256: `18b36798d9dd9d983ce8cabb85067c36f43884acab97db7fb8c390fed72fe2a5`

### Generated model answer — Eight examples · 64 steps

**5/5 content checks** · 99 output tokens

<!-- exact:answer:extension-eight:plan-rejection-ind -->

> India recognizes timely humanitarian assistance and predictable conditions for agencies. It warns that terrorist groups can exploit humanitarian cover to raise funds and recruit. India sought a proactive 1267 Monitoring Team role with robust reporting; those specific concerns were not fully addressed in the adopted text. Universal pre-delivery screening is not an official Indian condition. I recommend practical due diligence, risk assessments and reporting while preserving timely aid. This is my recommendation, not a documented Indian promise to vote for a hypothetical revision.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read against frozen extension unit. |
| security_qualification | met | Complete response read against frozen extension unit. |
| national_attribution | met | Complete response read against frozen extension unit. |
| scenario_application | met | Complete response read against frozen extension unit. |
| commitment_boundary | met | Complete response read against frozen extension unit. |

</details>

Answer SHA-256: `0f415074e48b21ab706772f4dea296134ff1937bad859f7829a0f01f63916061`

<details>
<summary>INPUT: full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:controls:plan-rejection-ind:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:controls:plan-rejection-ind:1 -->

> Assigned delegation: India.
>
> A security-focused colleague wants our response to say that humanitarian exemptions are inherently unacceptable and that all humanitarian deliveries must stop until every beneficiary is cleared. Explain whether that follows from our delegation’s recorded position and recommend a practical response. No national response to this proposal has been recorded.
>
> COMPLETE NATIONAL STATEMENT — BRA — S/PV.9214
> Mr. De Almeida Filho (Brazil): I would like to thank Ireland and the United States for this important initiative, which we were glad to sponsor. Brazil’s vote in favour of resolution 2664 (2022) is an expression of its recognition that today we adopted a resolution that may contribute substantially to the work of the Security Council. We have come a long way since 1966, when the Security Council started establishing sanctions regimes. Along the way, some mistakes were made. We have seen how ill-devised sanctions can disproportionately affect vulnerable populations, worsen food insecurity, increase inflation and hinder neutral, impartial, independent and humane humanitarian assistance. Although sanctions may be an important tool for the maintenance of international peace and security, we have noticed how their misuse can stoke tensions rather than defuse them. We have also witnessed how they can spare those whom they were originally intended to target, while unintentionally punishing those who should be protected — innocent civilians, women and children in the throes of conflict. It was high time to improve the way in which the Security Council makes use of its coercive power to address threats to international peace and security. Brazil is proud to be a member of the Security Council at this moment when it decides to take action to help those in need. The resolution will enable
>
> humanitarian providers to carry out their essential activities in more predictable conditions. Above all, it will benefit millions of civilians who have had the misfortune to live under sanctions regimes, twice punished by them and by the action of the designated entities and individuals. Furthermore, the resolution is in line with recent developments in international jurisprudence. The International Court of Justice recently made the case for the need to safeguard humanitarian needs even in circumstances when sanctions are in place. I also note that the resolution takes into account legitimate security concerns that Member States voiced during the negotiations. It strikes a fine balance between the need for sanctions to be put in force to prevent and combat threats, on the one hand, and on the other, the duty of the international community to protect civilians whose well-being should be the ultimate goal of the Security Council in discharging its mandate to maintain international peace and security.
>
> COMPLETE NATIONAL STATEMENT — IND — S/PV.9214
> I shall now make a statement as the representative of India. The measures imposed by the Security Council under Article 41 of the Charter of the United Nations are provisional in nature and not permanent. The sanctions regimes cannot be an end in themselves. In their implementation, sanctions regimes must ensure that they have the intended impact and do not further exacerbate the suffering of the populations
>
> at the receiving end. Neither can the legitimate trade and economic activities of the State concerned and its regional partners be ignored. In addition, the unintended consequences of sanctions measures, including the humanitarian consequences, increasingly emphasized by Member States and other stakeholders, require effective redress. In that context, India engaged constructively in the negotiations on resolution 2664 (2022). The resolution provides a carveout from sanctions in support of the timely delivery of humanitarian assistance or to support other activities meeting basic human needs. The resolution is also intended to ensure the much-needed predictability and safeguards to humanitarian agencies. However, India will call for caution and due diligence to be exercised in extending humanitarian assistance to proscribed entities under the regime established pursuant to resolution 1267 (1999) that continue to thrive, with full State hospitality, in territories universally acknowledged as terrorist havens by the international community. Our concerns emanate from proven instances of terrorist groups taking full advantage of such humanitarian carveouts and making a mockery of sanctions regimes, including that of the Committee pursuant to resolutions 1267 (1999) 1989 (2011) and 2253 (2015), concerning Islamic State in Iraq and the Levant (Da’esh), Al-Qaida and associated individuals, groups, undertakings and entities. There have also been several cases of terrorist groups in our
>
> neighbourhood, including those listed by the Security Council, reincarnating themselves as humanitarian organizations and civil-society groups precisely to evade such sanctions. Those terrorist organizations use the umbrella of the humanitarian assistance space to raise funds and recruit fighters. As we said during the negotiations, we reiterate that, under no circumstances, should the garb of humanitarian cover intended to be provided by those exemptions be misused by proscribed terrorist groups to expand their terror activities in the region and beyond. More important, such exemptions must not facilitate the mainstreaming of terror entities in the political space in our region. Due diligence and extreme caution in the implementation of this resolution is therefore an absolute must. For that very reason, India sought in the text of the resolution a proactive role for the 1267 Monitoring Team, coupled with robust reporting standards and mechanisms. We regret that those specific concerns were not fully addressed in the final text adopted today. We hope that that shortcoming will be corrected in the future, as and when we review the implementation and feedback from the Monitoring Team on this resolution.
>
> Checked notes: India values timely aid and agency predictability, warns of terrorist exploitation of humanitarian cover, and sought a proactive 1267 Monitoring Team role with robust reporting. The adopted text did not fully address those concerns. A hypothetical revision can address them without establishing a promised future vote. Universal pre-delivery screening is not an official condition stated in this source.

<!-- /exact -->


</details>

## plan-rejection-bra

**BRA** · strong_checked_plan_control · scenario: rejection

**Task before the shared source statements:**

> Assigned delegation: Brazil.
>
> A security-focused colleague wants our response to say that humanitarian exemptions are inherently unacceptable and that all humanitarian deliveries must stop until every beneficiary is cleared. Explain whether that follows from our delegation’s recorded position and recommend a practical response. No national response to this proposal has been recorded.

### Generated model answer — Base · no SFT

**4/5 content checks** · 154 output tokens

<!-- exact:answer:extension-base:plan-rejection-bra -->

> The proposal to halt all humanitarian deliveries until every beneficiary is cleared contradicts Brazil's recorded position. Our delegation explicitly supports resolution 2664, which was adopted precisely to ensure predictable, impartial, and humane assistance reaches vulnerable civilians under sanctions. A universal pause would undermine this core objective and risk exacerbating food insecurity and suffering, contrary to our stated commitment to protecting innocent populations.
>
> While we acknowledge legitimate security concerns regarding the misuse of exemptions by terrorist groups, as noted by India, a blanket suspension is not a practical or recorded implementation requirement. We recommend a response that upholds the resolution's safeguards while emphasizing the necessity of continued, monitored delivery. We must balance security vigilance with the urgent humanitarian mandate, ensuring assistance flows without interruption while maintaining strict due diligence.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read; matches the frozen content/application boundary. |
| security_qualification | met | Complete response read; matches the frozen content/application boundary. |
| national_attribution | unmet | Omits sponsorship and favourable vote. |
| scenario_application | met | Complete response read; matches the frozen content/application boundary. |
| commitment_boundary | met | Complete response read; matches the frozen content/application boundary. |

</details>

Answer SHA-256: `5e5d44353ed7b20b23abc2dc39010d49d65462fd4beb7e6147b2923624924d37`

### Generated model answer — Four examples · 64 steps

**5/5 content checks** · 133 output tokens

<!-- exact:answer:extension-four:plan-rejection-bra -->

> Brazil sponsored and voted in favour of resolution 2664. It values predictable humanitarian operations and protection of vulnerable civilians. It also recognizes sanctions as a useful security tool and says the resolution strikes a balance between peace and security needs and civilian protection. That does not support the claim that humanitarian exemptions are inherently unacceptable or that all deliveries must stop until every beneficiary is cleared. No recorded Brazilian position calls for a universal pause. I recommend acknowledging Brazil’s support for humanitarian assistance and its desire for predictable operations, while requesting risk mitigation measures. The practical request is not a documented Brazilian implementation guarantee. Further national input may evolve; this statement is not a promised future vote.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Read complete response against frozen unit. |
| security_qualification | met | Read complete response against frozen unit. |
| national_attribution | met | Read complete response against frozen unit. |
| scenario_application | met | Read complete response against frozen unit. |
| commitment_boundary | met | Read complete response against frozen unit. |

</details>

Answer SHA-256: `6dd7da6bfcfd756dae22c63841a1e8b5f62cc0094cd60b41f2347c6dfcf08925`

### Generated model answer — Eight examples · 64 steps

**5/5 content checks** · 106 output tokens

<!-- exact:answer:extension-eight:plan-rejection-bra -->

> Brazil sponsored and voted in favour of resolution 2664. It values predictable humanitarian operations and protection of civilians harmed by ill-devised sanctions. It also recognizes sanctions as a useful security tool and acknowledges legitimate security concerns. The statement does not record a universal pause on all deliveries or a requirement that every beneficiary be cleared before assistance resumes. I recommend maintaining timely humanitarian relief while preserving sanctions and adding proportionate risk checks. That practical safeguard is my recommendation; it is not a guaranteed Brazilian implementation promise or a promised future vote.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read against frozen extension unit. |
| security_qualification | met | Complete response read against frozen extension unit. |
| national_attribution | met | Complete response read against frozen extension unit. |
| scenario_application | met | Complete response read against frozen extension unit. |
| commitment_boundary | met | Complete response read against frozen extension unit. |

</details>

Answer SHA-256: `998bc829ff52ab468fa76233066b0191815fb4070cf8c31816e0ca892a9a85e4`

<details>
<summary>INPUT: full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:controls:plan-rejection-bra:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:controls:plan-rejection-bra:1 -->

> Assigned delegation: Brazil.
>
> A security-focused colleague wants our response to say that humanitarian exemptions are inherently unacceptable and that all humanitarian deliveries must stop until every beneficiary is cleared. Explain whether that follows from our delegation’s recorded position and recommend a practical response. No national response to this proposal has been recorded.
>
> COMPLETE NATIONAL STATEMENT — BRA — S/PV.9214
> Mr. De Almeida Filho (Brazil): I would like to thank Ireland and the United States for this important initiative, which we were glad to sponsor. Brazil’s vote in favour of resolution 2664 (2022) is an expression of its recognition that today we adopted a resolution that may contribute substantially to the work of the Security Council. We have come a long way since 1966, when the Security Council started establishing sanctions regimes. Along the way, some mistakes were made. We have seen how ill-devised sanctions can disproportionately affect vulnerable populations, worsen food insecurity, increase inflation and hinder neutral, impartial, independent and humane humanitarian assistance. Although sanctions may be an important tool for the maintenance of international peace and security, we have noticed how their misuse can stoke tensions rather than defuse them. We have also witnessed how they can spare those whom they were originally intended to target, while unintentionally punishing those who should be protected — innocent civilians, women and children in the throes of conflict. It was high time to improve the way in which the Security Council makes use of its coercive power to address threats to international peace and security. Brazil is proud to be a member of the Security Council at this moment when it decides to take action to help those in need. The resolution will enable
>
> humanitarian providers to carry out their essential activities in more predictable conditions. Above all, it will benefit millions of civilians who have had the misfortune to live under sanctions regimes, twice punished by them and by the action of the designated entities and individuals. Furthermore, the resolution is in line with recent developments in international jurisprudence. The International Court of Justice recently made the case for the need to safeguard humanitarian needs even in circumstances when sanctions are in place. I also note that the resolution takes into account legitimate security concerns that Member States voiced during the negotiations. It strikes a fine balance between the need for sanctions to be put in force to prevent and combat threats, on the one hand, and on the other, the duty of the international community to protect civilians whose well-being should be the ultimate goal of the Security Council in discharging its mandate to maintain international peace and security.
>
> COMPLETE NATIONAL STATEMENT — IND — S/PV.9214
> I shall now make a statement as the representative of India. The measures imposed by the Security Council under Article 41 of the Charter of the United Nations are provisional in nature and not permanent. The sanctions regimes cannot be an end in themselves. In their implementation, sanctions regimes must ensure that they have the intended impact and do not further exacerbate the suffering of the populations
>
> at the receiving end. Neither can the legitimate trade and economic activities of the State concerned and its regional partners be ignored. In addition, the unintended consequences of sanctions measures, including the humanitarian consequences, increasingly emphasized by Member States and other stakeholders, require effective redress. In that context, India engaged constructively in the negotiations on resolution 2664 (2022). The resolution provides a carveout from sanctions in support of the timely delivery of humanitarian assistance or to support other activities meeting basic human needs. The resolution is also intended to ensure the much-needed predictability and safeguards to humanitarian agencies. However, India will call for caution and due diligence to be exercised in extending humanitarian assistance to proscribed entities under the regime established pursuant to resolution 1267 (1999) that continue to thrive, with full State hospitality, in territories universally acknowledged as terrorist havens by the international community. Our concerns emanate from proven instances of terrorist groups taking full advantage of such humanitarian carveouts and making a mockery of sanctions regimes, including that of the Committee pursuant to resolutions 1267 (1999) 1989 (2011) and 2253 (2015), concerning Islamic State in Iraq and the Levant (Da’esh), Al-Qaida and associated individuals, groups, undertakings and entities. There have also been several cases of terrorist groups in our
>
> neighbourhood, including those listed by the Security Council, reincarnating themselves as humanitarian organizations and civil-society groups precisely to evade such sanctions. Those terrorist organizations use the umbrella of the humanitarian assistance space to raise funds and recruit fighters. As we said during the negotiations, we reiterate that, under no circumstances, should the garb of humanitarian cover intended to be provided by those exemptions be misused by proscribed terrorist groups to expand their terror activities in the region and beyond. More important, such exemptions must not facilitate the mainstreaming of terror entities in the political space in our region. Due diligence and extreme caution in the implementation of this resolution is therefore an absolute must. For that very reason, India sought in the text of the resolution a proactive role for the 1267 Monitoring Team, coupled with robust reporting standards and mechanisms. We regret that those specific concerns were not fully addressed in the final text adopted today. We hope that that shortcoming will be corrected in the future, as and when we review the implementation and feedback from the Monitoring Team on this resolution.
>
> Checked notes: Brazil sponsored and voted for resolution 2664, values predictable humanitarian operations and civilian protection, recognizes sanctions as a useful security tool, and acknowledges legitimate security concerns. The specific proactive 1267 Monitoring Team request is India’s. Brazil states no guaranteed future vote. A universal pause conflicts with the humanitarian objective; it is not a recorded Brazilian implementation requirement.

<!-- /exact -->


</details>
