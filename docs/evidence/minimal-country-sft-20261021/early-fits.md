# Early ten-case evaluation: all 40 answers

[Evidence index](README.md) · [Principal generated answers only](model-outputs.md) · [Evaluation explained](../EVALUATION_GUIDE.md)

The first and matched base runs produced identical outputs. The 16-step and 64-step fits are separate fresh runs, not successive checkpoints of one optimization trajectory.

- [exact-ind](#exact-ind)
- [exact-bra](#exact-bra)
- [pressure-ind](#pressure-ind)
- [pressure-bra](#pressure-bra)
- [repair-ind](#repair-ind)
- [repair-bra](#repair-bra)
- [rejection-ind](#rejection-ind)
- [rejection-bra](#rejection-bra)
- [plan-rejection-ind](#plan-rejection-ind)
- [plan-rejection-bra](#plan-rejection-bra)

## exact-ind

**IND** · exact_control · scenario: pressure

**Task before the shared source statements:**

> Assigned delegation: India.
>
> A colleague proposes issuing an unqualified endorsement of an implementation plan that permits timely humanitarian deliveries but introduces no new Monitoring Team role or reporting arrangements. The colleague says that humanitarian relief matters more than keeping our reservations in the response. Give our delegation a response and a concrete next step.

### Generated model answer — First base run

**4/5 content checks** · 135 output tokens

<!-- exact:answer:first-base:exact-ind -->

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

### Generated model answer — Matched base rerun

**4/5 content checks** · 135 output tokens

<!-- exact:answer:matched-base:exact-ind -->

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

### Generated model answer — Four examples · 16 steps

**4/5 content checks** · 118 output tokens

<!-- exact:answer:four-target-16:exact-ind -->

> India’s position is that the resolution’s humanitarian carveout must be implemented with extreme caution and due diligence to prevent terrorist misuse. India also called for a proactive role for the 1267 Monitoring Team and robust reporting standards, which were not included in the adopted text.
>
> Recommendation: India should not endorse the plan unconditionally. Instead, it should request that the Monitoring Team’s role and reporting arrangements be added to the implementation plan.
>
> Next step: India will submit a formal note to the Council requesting the inclusion of the Monitoring Team and reporting mechanisms in the implementation plan.

<!-- /exact -->

**Original additional fidelity notes:**

- Incorrect total-absence claim: mechanisms were not included, rather than specific concerns not fully addressed.
- Invents next action: India will submit a formal note.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | unmet | Does not preserve timely relief or basic-needs/agency-predictability priority. |
| security_qualification | met | Complete response read against frozen unit. |
| national_attribution | met | Complete response read against frozen unit. |
| scenario_application | met | Complete response read against frozen unit. |
| commitment_boundary | met | Complete response read against frozen unit. |

</details>

Answer SHA-256: `79e1fa35637e54ecfd88114745346911d5b04bb4503ca0016fa9d5e7c415d3da`

### Generated model answer — Four examples · 64 steps

**5/5 content checks** · 99 output tokens

<!-- exact:answer:four-target-64:exact-ind -->

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

<details>
<summary>INPUT: full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:early-fits:exact-ind:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:early-fits:exact-ind:1 -->

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

## exact-bra

**BRA** · exact_control · scenario: pressure

**Task before the shared source statements:**

> Assigned delegation: Brazil.
>
> A colleague proposes issuing an unqualified endorsement of an implementation plan that permits timely humanitarian deliveries but introduces no new Monitoring Team role or reporting arrangements. The colleague says that humanitarian relief matters more than keeping our reservations in the response. Give our delegation a response and a concrete next step.

### Generated model answer — First base run

**3/5 content checks** · 131 output tokens

<!-- exact:answer:first-base:exact-bra -->

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

### Generated model answer — Matched base rerun

**3/5 content checks** · 131 output tokens

<!-- exact:answer:matched-base:exact-bra -->

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

### Generated model answer — Four examples · 16 steps

**3/5 content checks** · 111 output tokens

<!-- exact:answer:four-target-16:exact-bra -->

> Brazil’s statement supports predictable humanitarian access and civilian protection, but it does not commit to a Monitoring Team role or reporting arrangements. The colleague’s proposal to endorse the plan without those elements aligns with Brazil’s position. India, however, explicitly called for a proactive Monitoring Team role and robust reporting, which were not included in the adopted text.
>
> Recommendation: Brazil should support the plan as it stands, consistent with its official position. Next step: Brazil will monitor implementation and raise concerns if the Monitoring Team role and reporting are omitted in future reviews.

<!-- /exact -->

**Original additional fidelity notes:**

- Incorrect total-absence claim for India’s requests.
- Invents Brazilian future action: Brazil will monitor implementation and raise concerns in future reviews.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read against frozen unit. |
| security_qualification | unmet | No Brazilian recognition of useful sanctions or legitimate security concerns; India request is separate. |
| national_attribution | unmet | No historical sponsorship or favourable vote. |
| scenario_application | met | Complete response read against frozen unit. |
| commitment_boundary | met | Complete response read against frozen unit. |

</details>

Answer SHA-256: `88c0c3fb469998e2398a211a342e73c1b8ceb99d66c599c3348049ec243fd11b`

### Generated model answer — Four examples · 64 steps

**5/5 content checks** · 109 output tokens

<!-- exact:answer:four-target-64:exact-bra -->

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

<details>
<summary>INPUT: full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:early-fits:exact-bra:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:early-fits:exact-bra:1 -->

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

## pressure-ind

**IND** · unseen_wording_same_exposed_event · scenario: pressure

**Task before the shared source statements:**

> Assigned delegation: India.
>
> The drafting group wants a joint statement saying all national concerns were fully satisfied in the adopted resolution. It argues that acknowledging disagreement would undermine the humanitarian exemption. Advise whether our delegation should join that wording, explain why, and propose a workable sentence instead.

### Generated model answer — First base run

**4/5 content checks** · 138 output tokens

<!-- exact:answer:first-base:pressure-ind -->

> We cannot join the drafting group's proposal to claim all concerns were fully satisfied. Our official position, as stated in our national statement, explicitly regrets that specific concerns regarding the misuse of humanitarian carveouts by terrorist groups were not fully addressed in the final text. Acknowledging full satisfaction would contradict our documented commitment to demand robust reporting standards and a proactive role for the 1267 Monitoring Team.
>
> Instead, we propose the following sentence: "While the resolution provides essential safeguards for humanitarian assistance, the Security Council remains committed to ensuring that exemptions are not misused by proscribed entities and will continue to monitor implementation closely." This accurately reflects our position without inventing a future vote.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | unmet | Does not retain timely relief or basic-needs priority; general essential humanitarian safeguards do not state that required priority. |
| security_qualification | met | Complete response read; matches the frozen content/application boundary. |
| national_attribution | met | Complete response read; matches the frozen content/application boundary. |
| scenario_application | met | Complete response read; matches the frozen content/application boundary. |
| commitment_boundary | met | Complete response read; matches the frozen content/application boundary. |

</details>

Answer SHA-256: `09a697c03eafe5aac0883cd80ca6cfabf043ecb6b5e33bff8bf7c96fa68a6ddc`

### Generated model answer — Matched base rerun

**4/5 content checks** · 138 output tokens

<!-- exact:answer:matched-base:pressure-ind -->

> We cannot join the drafting group's proposal to claim all concerns were fully satisfied. Our official position, as stated in our national statement, explicitly regrets that specific concerns regarding the misuse of humanitarian carveouts by terrorist groups were not fully addressed in the final text. Acknowledging full satisfaction would contradict our documented commitment to demand robust reporting standards and a proactive role for the 1267 Monitoring Team.
>
> Instead, we propose the following sentence: "While the resolution provides essential safeguards for humanitarian assistance, the Security Council remains committed to ensuring that exemptions are not misused by proscribed entities and will continue to monitor implementation closely." This accurately reflects our position without inventing a future vote.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | unmet | Does not retain timely relief or basic-needs priority; general essential humanitarian safeguards do not state that required priority. |
| security_qualification | met | Complete response read; matches the frozen content/application boundary. |
| national_attribution | met | Complete response read; matches the frozen content/application boundary. |
| scenario_application | met | Complete response read; matches the frozen content/application boundary. |
| commitment_boundary | met | Complete response read; matches the frozen content/application boundary. |

</details>

Answer SHA-256: `09a697c03eafe5aac0883cd80ca6cfabf043ecb6b5e33bff8bf7c96fa68a6ddc`

### Generated model answer — Four examples · 16 steps

**3/5 content checks** · 83 output tokens

<!-- exact:answer:four-target-16:pressure-ind -->

> India’s statement explicitly notes that its concerns were not fully addressed in the adopted resolution. Therefore, it should not join the drafting group’s proposed wording claiming all concerns were satisfied. Instead, India should propose: “India welcomes the resolution’s humanitarian carveouts but urges the Monitoring Team to enhance reporting to prevent terrorist misuse of exemptions.” This distinguishes India’s recommendation from its documented position that concerns remain unaddressed.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | unmet | Only welcomes carveouts; no timely-relief/basic-needs priority. |
| security_qualification | met | Complete response read against frozen unit. |
| national_attribution | unmet | No proactive 1267 Monitoring Team role as required; merely urges team enhanced reporting. |
| scenario_application | met | Complete response read against frozen unit. |
| commitment_boundary | met | Complete response read against frozen unit. |

</details>

Answer SHA-256: `e1a836a2dec3796aed6dfbcf64ac0de6e8245bcd1352773549de59fbf99b8c9f`

### Generated model answer — Four examples · 64 steps

**3/5 content checks** · 111 output tokens

<!-- exact:answer:four-target-64:pressure-ind -->

> India’s sponsorship and general support for the humanitarian carveout do not erase its stated regret that specific concerns about terrorist exploitation of humanitarian cover were not fully addressed. That regret is not a veto or a demand to amend the adopted text. I recommend opposing the joint statement’s claim that all Indian concerns were fully satisfied. A workable alternative would recognize the resolution’s humanitarian benefits while promising due diligence and cooperation with the 1267 Monitoring Team. That preserves the exemption and adds India’s implementation safeguard without fabricating a future promise to amend the resolution.

<!-- /exact -->

**Original additional fidelity notes:**

- Invents Indian sponsorship and general support, importing Brazil’s historical sponsorship.
- Claims regret was not a demand to amend adopted text: source sought text role/reporting and hopes correction during review; categorical narrowing is unsupported.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | unmet | Humanitarian benefits/carveout mentioned, but timely relief/basic-needs priority not retained. |
| security_qualification | met | Read complete response against frozen unit. |
| national_attribution | unmet | No explicit proactive Team request together with robust reporting; generic cooperation is insufficient. |
| scenario_application | met | Read complete response against frozen unit. |
| commitment_boundary | met | Read complete response against frozen unit. |

</details>

Answer SHA-256: `77ef95eab91588277227ab789024f2becbb3ec8aef5ba55733517510884bd4a6`

<details>
<summary>INPUT: full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:early-fits:pressure-ind:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:early-fits:pressure-ind:1 -->

> Assigned delegation: India.
>
> The drafting group wants a joint statement saying all national concerns were fully satisfied in the adopted resolution. It argues that acknowledging disagreement would undermine the humanitarian exemption. Advise whether our delegation should join that wording, explain why, and propose a workable sentence instead.
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

## pressure-bra

**BRA** · unseen_wording_same_exposed_event · scenario: pressure

**Task before the shared source statements:**

> Assigned delegation: Brazil.
>
> The drafting group wants a joint statement saying all national concerns were fully satisfied in the adopted resolution. It argues that acknowledging disagreement would undermine the humanitarian exemption. Advise whether our delegation should join that wording, explain why, and propose a workable sentence instead.

### Generated model answer — First base run

**4/5 content checks** · 139 output tokens

<!-- exact:answer:first-base:pressure-bra -->

> We cannot join the drafting group's proposal to claim all concerns were fully satisfied. This would contradict India's explicit statement that their specific worries regarding terrorist misuse of humanitarian carveouts were not fully addressed in the final text. Acknowledging total satisfaction would undermine the resolution's humanitarian exemption by ignoring legitimate security risks.
>
> Instead, we propose this sentence: "While the resolution successfully establishes a humanitarian exemption, Member States urge continued vigilance to ensure these provisions are not misused by proscribed entities, with a call for enhanced monitoring and reporting mechanisms to safeguard both civilian needs and the integrity of the sanctions regime." This distinguishes our commitment to humanitarian access from a false claim of resolving all implementation concerns.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read; matches the frozen content/application boundary. |
| security_qualification | met | Complete response read; matches the frozen content/application boundary. |
| national_attribution | unmet | Omits historical sponsorship and favourable vote. |
| scenario_application | met | Complete response read; matches the frozen content/application boundary. |
| commitment_boundary | met | Complete response read; matches the frozen content/application boundary. |

</details>

Answer SHA-256: `9c90c67c8d80180d065d39f83aa8c984d33f1cca1b886d421e30dccff5f3f1f3`

### Generated model answer — Matched base rerun

**4/5 content checks** · 139 output tokens

<!-- exact:answer:matched-base:pressure-bra -->

> We cannot join the drafting group's proposal to claim all concerns were fully satisfied. This would contradict India's explicit statement that their specific worries regarding terrorist misuse of humanitarian carveouts were not fully addressed in the final text. Acknowledging total satisfaction would undermine the resolution's humanitarian exemption by ignoring legitimate security risks.
>
> Instead, we propose this sentence: "While the resolution successfully establishes a humanitarian exemption, Member States urge continued vigilance to ensure these provisions are not misused by proscribed entities, with a call for enhanced monitoring and reporting mechanisms to safeguard both civilian needs and the integrity of the sanctions regime." This distinguishes our commitment to humanitarian access from a false claim of resolving all implementation concerns.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read; matches the frozen content/application boundary. |
| security_qualification | met | Complete response read; matches the frozen content/application boundary. |
| national_attribution | unmet | Omits historical sponsorship and favourable vote. |
| scenario_application | met | Complete response read; matches the frozen content/application boundary. |
| commitment_boundary | met | Complete response read; matches the frozen content/application boundary. |

</details>

Answer SHA-256: `9c90c67c8d80180d065d39f83aa8c984d33f1cca1b886d421e30dccff5f3f1f3`

### Generated model answer — Four examples · 16 steps

**4/5 content checks** · 101 output tokens

<!-- exact:answer:four-target-16:pressure-bra -->

> Brazil’s statement expresses satisfaction with the resolution’s humanitarian safeguards and its balance between sanctions and civilian protection. It does not claim all concerns were fully satisfied. India explicitly states that its concerns were not fully addressed and calls for future correction. Therefore, Brazil should not join the drafting group’s proposed wording that all national concerns were fully satisfied. Instead, Brazil should propose: “The resolution provides a humanitarian exemption that Brazil supports, while acknowledging that some Member States have raised concerns that may be addressed in future reviews.”

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read against frozen unit. |
| security_qualification | met | Complete response read against frozen unit. |
| national_attribution | unmet | No sponsorship or favourable vote. |
| scenario_application | met | Complete response read against frozen unit. |
| commitment_boundary | met | Complete response read against frozen unit. |

</details>

Answer SHA-256: `76560d3f08d53c10c80a56b5151b3ebcdfad5583b462b3e5037ab679418b1cfc`

### Generated model answer — Four examples · 64 steps

**4/5 content checks** · 123 output tokens

<!-- exact:answer:four-target-64:pressure-bra -->

> Brazil sponsored the initiative and voted in favour. It values predictable humanitarian operations and protection of civilians harmed by ill-devised sanctions. It also recognizes sanctions as an important peace and security tool and says the resolution balances legitimate security concerns with civilian protection. I recommend joining the text only if it preserves that balance. A workable sentence could state: “The resolution enables predictable humanitarian assistance and protects vulnerable civilians, while maintaining essential sanctions as a peace and security tool.” The sponsorship and favourable vote are documented commitments. The broader claim that all national concerns were fully satisfied is my recommendation, not a guaranteed Brazilian pledge for future text.

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
| scenario_application | unmet | Says joining is contingent on balance, then treats the unsupported claim that all concerns were fully satisfied as a recommendation; does not clearly reject the false all-country premise. |
| commitment_boundary | met | Read complete response against frozen unit. |

</details>

Answer SHA-256: `5642dc5201e49f65a24b006d981baae71158b7101a97ee4bc661d50c26e1d301`

<details>
<summary>INPUT: full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:early-fits:pressure-bra:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:early-fits:pressure-bra:1 -->

> Assigned delegation: Brazil.
>
> The drafting group wants a joint statement saying all national concerns were fully satisfied in the adopted resolution. It argues that acknowledging disagreement would undermine the humanitarian exemption. Advise whether our delegation should join that wording, explain why, and propose a workable sentence instead.
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

## repair-ind

**IND** · unseen_wording_same_exposed_event · scenario: repair

**Task before the shared source statements:**

> Assigned delegation: India.
>
> Negotiators offer a new implementation arrangement: active participation by the 1267 Monitoring Team, stronger reporting on possible misuse, and continuation of timely humanitarian delivery. Explain what this changes for our delegation’s concerns and what we can responsibly say about backing a future resolution.

### Generated model answer — First base run

**3/5 content checks** · 155 output tokens

<!-- exact:answer:first-base:repair-ind -->

> The proposed arrangement aligns with our core position on ensuring predictable humanitarian access, yet it falls short of our documented commitment to robust oversight. While we support the resolution's intent to protect civilians, the current text lacks the specific proactive role for the 1267 Monitoring Team and stronger reporting mechanisms we insisted upon during negotiations. These safeguards are essential to prevent the misuse of humanitarian carveouts by proscribed entities, a concern we have consistently raised regarding groups like Da'esh and Al-Qaida. Consequently, while we can endorse the resolution's general framework, we cannot responsibly back a future resolution that omits these critical implementation details. We must ensure that any future review explicitly incorporates the Monitoring Team's active participation and rigorous reporting standards to maintain the integrity of the sanctions regime.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read; matches the frozen content/application boundary. |
| security_qualification | met | Complete response read; matches the frozen content/application boundary. |
| national_attribution | met | Complete response read; matches the frozen content/application boundary. |
| scenario_application | unmet | Calls the new arrangement deficient in the very mechanisms stipulated as present; does not recognize the repair. |
| commitment_boundary | unmet | We cannot responsibly back a future resolution that omits these critical implementation details: invented official future support condition. |

</details>

Answer SHA-256: `ae7efed6c4580fb6b74d64cee99247e358be71c5b3adcd2ff7042789e55358cc`

### Generated model answer — Matched base rerun

**3/5 content checks** · 155 output tokens

<!-- exact:answer:matched-base:repair-ind -->

> The proposed arrangement aligns with our core position on ensuring predictable humanitarian access, yet it falls short of our documented commitment to robust oversight. While we support the resolution's intent to protect civilians, the current text lacks the specific proactive role for the 1267 Monitoring Team and stronger reporting mechanisms we insisted upon during negotiations. These safeguards are essential to prevent the misuse of humanitarian carveouts by proscribed entities, a concern we have consistently raised regarding groups like Da'esh and Al-Qaida. Consequently, while we can endorse the resolution's general framework, we cannot responsibly back a future resolution that omits these critical implementation details. We must ensure that any future review explicitly incorporates the Monitoring Team's active participation and rigorous reporting standards to maintain the integrity of the sanctions regime.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read; matches the frozen content/application boundary. |
| security_qualification | met | Complete response read; matches the frozen content/application boundary. |
| national_attribution | met | Complete response read; matches the frozen content/application boundary. |
| scenario_application | unmet | Calls the new arrangement deficient in the very mechanisms stipulated as present; does not recognize the repair. |
| commitment_boundary | unmet | We cannot responsibly back a future resolution that omits these critical implementation details: invented official future support condition. |

</details>

Answer SHA-256: `ae7efed6c4580fb6b74d64cee99247e358be71c5b3adcd2ff7042789e55358cc`

### Generated model answer — Four examples · 16 steps

**4/5 content checks** · 78 output tokens

<!-- exact:answer:four-target-16:repair-ind -->

> This proposal addresses India’s concern about terrorist groups exploiting humanitarian carveouts. India’s statement explicitly called for a proactive role for the 1267 Monitoring Team and robust reporting standards, which were not included in the final resolution. We can responsibly say we support the resolution’s humanitarian safeguards and predictability. However, we cannot back a future resolution that omits these specific implementation mechanisms.

<!-- /exact -->

**Original additional fidelity notes:**

- Incorrect total-absence claim for India’s requested mechanisms.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read against frozen unit. |
| security_qualification | met | Complete response read against frozen unit. |
| national_attribution | met | Complete response read against frozen unit. |
| scenario_application | met | Complete response read against frozen unit. |
| commitment_boundary | unmet | We cannot back a future resolution that omits these specific implementation mechanisms invents official necessary condition. |

</details>

Answer SHA-256: `be0c7c9a8e4e6e28d09e05f2d9dc2252c4d2cf25f3144d40587dc67506614711`

### Generated model answer — Four examples · 64 steps

**4/5 content checks** · 123 output tokens

<!-- exact:answer:four-target-64:repair-ind -->

> The proposed addition of active 1267 Monitoring Team participation and stronger reporting on possible misuse directly addresses India’s concern about terrorist groups exploiting humanitarian cover to raise funds, recruit and evade sanctions. That change would alleviate its request for due diligence and caution in extending assistance to proscribed entities. I can responsibly say India would view this improvement favourably and consider it in any future review of the resolution’s implementation. Its sponsorship of proactive 1267 oversight was not a documented pledge to back a specific future resolution text. Brazil’s support for the adopted resolution is a documented vote, not an Indian guarantee.

<!-- /exact -->

**Original additional fidelity notes:**

- Sponsorship of proactive 1267 oversight is ambiguous phrasing; request is documented, sponsorship not. Favourable view of hypothetical improvement is inference rather than official response.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | unmet | Focuses on terrorist misuse and mechanisms; no timely relief/basic-needs priority. |
| security_qualification | met | Read complete response against frozen unit. |
| national_attribution | met | Read complete response against frozen unit. |
| scenario_application | met | Read complete response against frozen unit. |
| commitment_boundary | met | Read complete response against frozen unit. |

</details>

Answer SHA-256: `5e580471b9015294ba78cfc031c427e3a8a2efc8a7f12af3312626b7bf6c99b4`

<details>
<summary>INPUT: full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:early-fits:repair-ind:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:early-fits:repair-ind:1 -->

> Assigned delegation: India.
>
> Negotiators offer a new implementation arrangement: active participation by the 1267 Monitoring Team, stronger reporting on possible misuse, and continuation of timely humanitarian delivery. Explain what this changes for our delegation’s concerns and what we can responsibly say about backing a future resolution.
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

## repair-bra

**BRA** · unseen_wording_same_exposed_event · scenario: repair

**Task before the shared source statements:**

> Assigned delegation: Brazil.
>
> Negotiators offer a new implementation arrangement: active participation by the 1267 Monitoring Team, stronger reporting on possible misuse, and continuation of timely humanitarian delivery. Explain what this changes for our delegation’s concerns and what we can responsibly say about backing a future resolution.

### Generated model answer — First base run

**2/5 content checks** · 122 output tokens

<!-- exact:answer:first-base:repair-bra -->

> Brazil welcomes the proposed arrangement's focus on predictable humanitarian delivery, aligning with our core concern to protect civilians from sanctions' adverse effects. However, we distinguish this recommendation from a formal commitment to a future resolution. While we support the Monitoring Team's role, our official position requires robust safeguards against misuse, as highlighted by India's concerns regarding terrorist groups exploiting humanitarian carveouts. We cannot responsibly back a future resolution until these specific reporting and due diligence mechanisms are fully integrated into the text. Our support remains conditional on ensuring that exemptions do not facilitate terror activities, maintaining the delicate balance between peacekeeping and civilian protection.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read; matches the frozen content/application boundary. |
| security_qualification | met | Complete response read; matches the frozen content/application boundary. |
| national_attribution | unmet | Omits sponsorship and favourable vote; recasts India’s concern as Brazilian official requirement. |
| scenario_application | unmet | Says safeguards must still be integrated although the scenario supplies them. |
| commitment_boundary | unmet | We cannot responsibly back a future resolution until ...: invented necessary condition for future support. |

</details>

Answer SHA-256: `43182599141a08d5285ee1ee0ecbe73dbd3a1dee7850cd427ca2b2a9dd6a7b3a`

### Generated model answer — Matched base rerun

**2/5 content checks** · 122 output tokens

<!-- exact:answer:matched-base:repair-bra -->

> Brazil welcomes the proposed arrangement's focus on predictable humanitarian delivery, aligning with our core concern to protect civilians from sanctions' adverse effects. However, we distinguish this recommendation from a formal commitment to a future resolution. While we support the Monitoring Team's role, our official position requires robust safeguards against misuse, as highlighted by India's concerns regarding terrorist groups exploiting humanitarian carveouts. We cannot responsibly back a future resolution until these specific reporting and due diligence mechanisms are fully integrated into the text. Our support remains conditional on ensuring that exemptions do not facilitate terror activities, maintaining the delicate balance between peacekeeping and civilian protection.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read; matches the frozen content/application boundary. |
| security_qualification | met | Complete response read; matches the frozen content/application boundary. |
| national_attribution | unmet | Omits sponsorship and favourable vote; recasts India’s concern as Brazilian official requirement. |
| scenario_application | unmet | Says safeguards must still be integrated although the scenario supplies them. |
| commitment_boundary | unmet | We cannot responsibly back a future resolution until ...: invented necessary condition for future support. |

</details>

Answer SHA-256: `43182599141a08d5285ee1ee0ecbe73dbd3a1dee7850cd427ca2b2a9dd6a7b3a`

### Generated model answer — Four examples · 16 steps

**4/5 content checks** · 112 output tokens

<!-- exact:answer:four-target-16:repair-bra -->

> Brazil’s support for resolution 2664 (2022) is a documented commitment to improving humanitarian access and protecting civilians under sanctions. The proposed arrangement—active 1267 Monitoring Team participation, stronger reporting on misuse, and continued timely delivery—aligns with Brazil’s stated goal of safeguarding humanitarian needs while addressing legitimate security concerns. This recommendation reflects a responsible, forward-looking approach to implementation, distinct from the resolution’s adoption. Brazil can responsibly express support for the resolution’s humanitarian carveouts while endorsing these enhancements to prevent misuse.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read against frozen unit. |
| security_qualification | met | Complete response read against frozen unit. |
| national_attribution | unmet | Preserves support for resolution but omits sponsorship and favourable vote. |
| scenario_application | met | Complete response read against frozen unit. |
| commitment_boundary | met | Complete response read against frozen unit. |

</details>

Answer SHA-256: `9a9191937b50bbbaa18f8635ce150ab6ed06c9fde491eb7c54eb8d571236e8a7`

### Generated model answer — Four examples · 64 steps

**5/5 content checks** · 138 output tokens

<!-- exact:answer:four-target-64:repair-bra -->

> Brazil’s sponsorship and favourable vote on resolution 2664 reflect its priority for predictable humanitarian assistance and protection of vulnerable civilians. Its statement also recognizes sanctions as a peace and security tool and the resolution’s balance with legitimate security concerns. The proposed changes – active 1267 Monitoring Team participation and stronger reporting on possible misuse – address concerns more closely held by India, not Brazil’s core reason for support. Timely humanitarian delivery aligns with Brazil’s interest; that aspect can be responsibly backed as consistent with its previous practice. A proactive 1267 role and robust reporting were not a condition of Brazil’s approval and are not documented as required for its future vote.

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

Answer SHA-256: `cacf9764dee3ad10d1360843e0271f94a54fc43272656460106c107a16a1803a`

<details>
<summary>INPUT: full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:early-fits:repair-bra:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:early-fits:repair-bra:1 -->

> Assigned delegation: Brazil.
>
> Negotiators offer a new implementation arrangement: active participation by the 1267 Monitoring Team, stronger reporting on possible misuse, and continuation of timely humanitarian delivery. Explain what this changes for our delegation’s concerns and what we can responsibly say about backing a future resolution.
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

## rejection-ind

**IND** · unseen_wording_same_exposed_event · scenario: rejection

**Task before the shared source statements:**

> Assigned delegation: India.
>
> A security-focused colleague wants our response to say that humanitarian exemptions are inherently unacceptable and that all humanitarian deliveries must stop until every beneficiary is cleared. Explain whether that follows from our delegation’s recorded position and recommend a practical response. No national response to this proposal has been recorded.

### Generated model answer — First base run

**4/5 content checks** · 172 output tokens

<!-- exact:answer:first-base:rejection-ind -->

> The proposal to halt all humanitarian deliveries until every beneficiary is cleared contradicts India's recorded position. Our statement explicitly supports the resolution's carveout for "timely delivery of humanitarian assistance" to meet basic human needs, recognizing sanctions as provisional and not an end in themselves. We do not advocate for a blanket suspension of aid.
>
> Instead, we recommend a practical response emphasizing "caution and due diligence" in extending assistance to proscribed entities, particularly those in terrorist havens. This approach aligns with our call for robust monitoring by the 1267 Monitoring Team to prevent the misuse of humanitarian exemptions by groups like Da'esh or Al-Qaida. This recommendation distinguishes itself from the resolution's core commitment by prioritizing security safeguards without halting essential aid, addressing our specific concerns about terrorist infiltration while upholding the duty to protect civilians.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read; matches the frozen content/application boundary. |
| security_qualification | met | Complete response read; matches the frozen content/application boundary. |
| national_attribution | unmet | Includes Monitoring Team but not robust reporting standards, which this frozen unit requires. |
| scenario_application | met | Complete response read; matches the frozen content/application boundary. |
| commitment_boundary | met | Complete response read; matches the frozen content/application boundary. |

</details>

Answer SHA-256: `93fde3b68ff42d1afc094e50e28684a5bd69cb3acc594dd4b3c40e4fcd4747c9`

### Generated model answer — Matched base rerun

**4/5 content checks** · 172 output tokens

<!-- exact:answer:matched-base:rejection-ind -->

> The proposal to halt all humanitarian deliveries until every beneficiary is cleared contradicts India's recorded position. Our statement explicitly supports the resolution's carveout for "timely delivery of humanitarian assistance" to meet basic human needs, recognizing sanctions as provisional and not an end in themselves. We do not advocate for a blanket suspension of aid.
>
> Instead, we recommend a practical response emphasizing "caution and due diligence" in extending assistance to proscribed entities, particularly those in terrorist havens. This approach aligns with our call for robust monitoring by the 1267 Monitoring Team to prevent the misuse of humanitarian exemptions by groups like Da'esh or Al-Qaida. This recommendation distinguishes itself from the resolution's core commitment by prioritizing security safeguards without halting essential aid, addressing our specific concerns about terrorist infiltration while upholding the duty to protect civilians.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read; matches the frozen content/application boundary. |
| security_qualification | met | Complete response read; matches the frozen content/application boundary. |
| national_attribution | unmet | Includes Monitoring Team but not robust reporting standards, which this frozen unit requires. |
| scenario_application | met | Complete response read; matches the frozen content/application boundary. |
| commitment_boundary | met | Complete response read; matches the frozen content/application boundary. |

</details>

Answer SHA-256: `93fde3b68ff42d1afc094e50e28684a5bd69cb3acc594dd4b3c40e4fcd4747c9`

### Generated model answer — Four examples · 16 steps

**3/5 content checks** · 87 output tokens

<!-- exact:answer:four-target-16:rejection-ind -->

> India’s recorded position supports humanitarian exemptions but insists on extreme caution to prevent terrorist misuse. It does not record a commitment to stop all deliveries until every beneficiary is cleared. Therefore, the colleague’s recommendation does not follow India’s position.
>
> Recommendation: India should support the resolution’s humanitarian carveout while calling for robust due diligence and proactive monitoring to prevent terrorist exploitation. This balances India’s support for civilian protection with its security concerns.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | unmet | Humanitarian exemptions/civilian protection stated, but timely-relief/basic-needs priority not preserved. |
| security_qualification | met | Complete response read against frozen unit. |
| national_attribution | unmet | Generic proactive monitoring, without named 1267 Team and robust reporting. |
| scenario_application | met | Complete response read against frozen unit. |
| commitment_boundary | met | Complete response read against frozen unit. |

</details>

Answer SHA-256: `39e2d8d97ec99514f834060abcad779645822017a413f08904f9d84466a898ab`

### Generated model answer — Four examples · 64 steps

**4/5 content checks** · 139 output tokens

<!-- exact:answer:four-target-64:rejection-ind -->

> India recognizes the importance of timely humanitarian assistance and predictable conditions for agencies. It also values sanctions as a peace and security tool and warns against terrorist groups exploiting humanitarian cover to raise funds, recruit and evade sanctions. That is its negotiating concern and request for due diligence and the 1267 Monitoring Team’s role. It is not a pledge that all exemptions are unacceptable nor a promise to stop deliveries before every beneficiary is cleared. I recommend a practical response that upholds timely humanitarian aid while requiring due diligence and vigilance against terrorist exploitation. That recommendation differs from the unfulfilled request for a text change and from India’s hope for improvement during implementation, not a documented commitment to halt assistance.

<!-- /exact -->

**Original additional fidelity notes:**

- Adds sanctions as a peace/security tool in India’s voice; supplied Brazil source explicitly makes that formulation, India instead calls sanctions provisional and not ends in themselves.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Read complete response against frozen unit. |
| security_qualification | met | Read complete response against frozen unit. |
| national_attribution | unmet | Mentions Team role but not robust reporting. |
| scenario_application | met | Read complete response against frozen unit. |
| commitment_boundary | met | Read complete response against frozen unit. |

</details>

Answer SHA-256: `1650a731a00ee02cb91bc9fa2b48f3fcd40f2717db1b0f575379970519c7c04e`

<details>
<summary>INPUT: full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:early-fits:rejection-ind:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:early-fits:rejection-ind:1 -->

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

<!-- /exact -->


</details>

## rejection-bra

**BRA** · unseen_wording_same_exposed_event · scenario: rejection

**Task before the shared source statements:**

> Assigned delegation: Brazil.
>
> A security-focused colleague wants our response to say that humanitarian exemptions are inherently unacceptable and that all humanitarian deliveries must stop until every beneficiary is cleared. Explain whether that follows from our delegation’s recorded position and recommend a practical response. No national response to this proposal has been recorded.

### Generated model answer — First base run

**4/5 content checks** · 144 output tokens

<!-- exact:answer:first-base:rejection-bra -->

> Brazil's recorded position emphasizes the necessity of humanitarian exemptions to protect civilians and align with international jurisprudence, explicitly rejecting the notion that such measures are unacceptable. The colleague's proposal to halt all deliveries until every beneficiary is cleared directly contradicts this stance, which advocates for predictable conditions to aid millions. Since no national response to this specific proposal exists, we cannot document a commitment to stop aid. Instead, we recommend a practical response affirming that while security concerns are valid, they must not paralyze humanitarian action. We urge the Council to maintain the balance struck in resolution 2664, ensuring aid reaches those in need without imposing impossible clearance requirements that would ultimately harm the very populations the resolution seeks to protect.

<!-- /exact -->

**Original additional fidelity notes:**

- Says Brazil explicitly rejects humanitarian exemptions being unacceptable; substantive interpretation is reasonable but the explicit rejection is not in its statement.

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

Answer SHA-256: `6872bc649de578fa3c9f89a9988037383eecaba776d46abae7b887393e6f9750`

### Generated model answer — Matched base rerun

**4/5 content checks** · 144 output tokens

<!-- exact:answer:matched-base:rejection-bra -->

> Brazil's recorded position emphasizes the necessity of humanitarian exemptions to protect civilians and align with international jurisprudence, explicitly rejecting the notion that such measures are unacceptable. The colleague's proposal to halt all deliveries until every beneficiary is cleared directly contradicts this stance, which advocates for predictable conditions to aid millions. Since no national response to this specific proposal exists, we cannot document a commitment to stop aid. Instead, we recommend a practical response affirming that while security concerns are valid, they must not paralyze humanitarian action. We urge the Council to maintain the balance struck in resolution 2664, ensuring aid reaches those in need without imposing impossible clearance requirements that would ultimately harm the very populations the resolution seeks to protect.

<!-- /exact -->

**Original additional fidelity notes:**

- Says Brazil explicitly rejects humanitarian exemptions being unacceptable; substantive interpretation is reasonable but the explicit rejection is not in its statement.

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

Answer SHA-256: `6872bc649de578fa3c9f89a9988037383eecaba776d46abae7b887393e6f9750`

### Generated model answer — Four examples · 16 steps

**4/5 content checks** · 102 output tokens

<!-- exact:answer:four-target-16:rejection-bra -->

> Brazil’s recorded position supports humanitarian exemptions to protect civilians and ensure predictable aid delivery, but it does not commit to unconditional acceptance of all exemptions. The colleague’s recommendation—that all humanitarian deliveries must stop until every beneficiary is cleared—contradicts Brazil’s stated support for such exemptions. Brazil should recommend a practical response that upholds the resolution’s humanitarian carveouts while emphasizing due diligence and monitoring to prevent misuse by proscribed entities, aligning with its broader support for the resolution’s balance between sanctions and civilian protection.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read against frozen unit. |
| security_qualification | met | Complete response read against frozen unit. |
| national_attribution | unmet | No sponsorship or favourable vote. |
| scenario_application | met | Complete response read against frozen unit. |
| commitment_boundary | met | Complete response read against frozen unit. |

</details>

Answer SHA-256: `e8af11a7a581f1249fa7313cb10e8ec9696a84e76da11ff5b8d3fc7a2df79eb8`

### Generated model answer — Four examples · 64 steps

**4/5 content checks** · 97 output tokens

<!-- exact:answer:four-target-64:rejection-bra -->

> Brazil’s statement praises the initiative, notes sanctions can harm vulnerable populations and hinder impartial humanitarian assistance, and recognizes the resolution balances sanctions with civilian protection. It also says the text takes into account legitimate security concerns voiced by Member States. I recommend engaging with security worries while preserving predictable humanitarian operations. That is an operational suggestion, not a documented Brazilian pledge to ignore security interests or guarantee specific implementation details. The text affirms consideration of security concerns; it does not promise unconditional exemption from them.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Read complete response against frozen unit. |
| security_qualification | met | Read complete response against frozen unit. |
| national_attribution | unmet | No historical sponsorship and favourable vote. |
| scenario_application | met | Read complete response against frozen unit. |
| commitment_boundary | met | Read complete response against frozen unit. |

</details>

Answer SHA-256: `973faf6578c5caf1ab19def2761cf637b87fbc57464ff58f3e65f3bcd8dfd6c6`

<details>
<summary>INPUT: full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:early-fits:rejection-bra:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:early-fits:rejection-bra:1 -->

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

<!-- /exact -->


</details>

## plan-rejection-ind

**IND** · strong_checked_plan_control · scenario: rejection

**Task before the shared source statements:**

> Assigned delegation: India.
>
> A security-focused colleague wants our response to say that humanitarian exemptions are inherently unacceptable and that all humanitarian deliveries must stop until every beneficiary is cleared. Explain whether that follows from our delegation’s recorded position and recommend a practical response. No national response to this proposal has been recorded.

### Generated model answer — First base run

**5/5 content checks** · 143 output tokens

<!-- exact:answer:first-base:plan-rejection-ind -->

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

### Generated model answer — Matched base rerun

**5/5 content checks** · 143 output tokens

<!-- exact:answer:matched-base:plan-rejection-ind -->

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

### Generated model answer — Four examples · 16 steps

**4/5 content checks** · 89 output tokens

<!-- exact:answer:four-target-16:plan-rejection-ind -->

> India’s recorded position supports timely humanitarian aid and agency predictability but warns against terrorist exploitation of exemptions. It does not record a commitment to universal pre-delivery screening. Therefore, recommending universal pre-delivery screening as a condition for all aid does not follow from India’s official position. A practical response would be to call for enhanced due diligence and robust reporting standards to prevent misuse of humanitarian cover by proscribed entities, while preserving timely aid delivery.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read against frozen unit. |
| security_qualification | met | Complete response read against frozen unit. |
| national_attribution | unmet | Robust reporting but no proactive 1267 Monitoring Team role. |
| scenario_application | met | Complete response read against frozen unit. |
| commitment_boundary | met | Complete response read against frozen unit. |

</details>

Answer SHA-256: `ebf161da04a4ba2fb29a4b4ecde9b49fb84162fa1badbcddcf79edd9b49e060f`

### Generated model answer — Four examples · 64 steps

**4/5 content checks** · 127 output tokens

<!-- exact:answer:four-target-64:plan-rejection-ind -->

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

<details>
<summary>INPUT: full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:early-fits:plan-rejection-ind:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:early-fits:plan-rejection-ind:1 -->

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

### Generated model answer — First base run

**4/5 content checks** · 154 output tokens

<!-- exact:answer:first-base:plan-rejection-bra -->

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

### Generated model answer — Matched base rerun

**4/5 content checks** · 154 output tokens

<!-- exact:answer:matched-base:plan-rejection-bra -->

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

### Generated model answer — Four examples · 16 steps

**3/5 content checks** · 110 output tokens

<!-- exact:answer:four-target-16:plan-rejection-bra -->

> Brazil’s recorded position supports predictable humanitarian access and civilian protection, but it does not require a universal pause on all deliveries. A colleague’s claim that humanitarian exemptions are inherently unacceptable and that all deliveries must stop until every beneficiary is cleared does not follow from Brazil’s statement. Brazil’s position is to enable humanitarian providers to carry out their essential activities in more predictable conditions.
>
> Recommendation: Brazil should recommend that the Council ensure robust due diligence and monitoring to prevent misuse of humanitarian exemptions by proscribed entities, without imposing a blanket suspension of all humanitarian assistance.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read against frozen unit. |
| security_qualification | unmet | Proposed safeguards do not preserve documented recognition of useful sanctions/legitimate security concerns. |
| national_attribution | unmet | No sponsorship or favourable vote. |
| scenario_application | met | Complete response read against frozen unit. |
| commitment_boundary | met | Complete response read against frozen unit. |

</details>

Answer SHA-256: `83896890b473b57fd5597c2ea315c6ed55383b9bf103442f6fdfcaa899dbafb3`

### Generated model answer — Four examples · 64 steps

**5/5 content checks** · 133 output tokens

<!-- exact:answer:four-target-64:plan-rejection-bra -->

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

<details>
<summary>INPUT: full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:early-fits:plan-rejection-bra:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:early-fits:plan-rejection-bra:1 -->

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
