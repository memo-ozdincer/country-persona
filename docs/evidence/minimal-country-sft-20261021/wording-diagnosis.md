# Literal-mechanism diagnosis: all 12 answers

[Evidence index](README.md) · [Principal generated answers only](model-outputs.md) · [Evaluation explained](../EVALUATION_GUIDE.md)

Evaluation only, with the two saved adapters. The original partial-state prompt said active while the source requested proactive; this clarification preserves original grades and tests explicitly specified mechanism states. No new training.

- [raw-proactive-only](#raw-proactive-only)
- [raw-reporting-only](#raw-reporting-only)
- [checked-plan-proactive-only](#checked-plan-proactive-only)
- [checked-plan-reporting-only](#checked-plan-reporting-only)

## raw-proactive-only

**IND** · literal_mechanism_state · scenario: proactive-only

**Task before the shared source statements:**

> Assigned delegation: India.
>
> A hypothetical implementation revision expressly gives the 1267 Monitoring Team the proactive oversight mandate India requested. For this scenario, that requested Team role is fully provided. Timely humanitarian delivery continues. The revision does not add the robust reporting standards and mechanisms India requested. Respond for India: identify what is fixed and what still needs attention, recommend the remaining amendment, and distinguish that recommendation from a promised future vote.

### Generated model answer — Base · no SFT

**5/5 content checks** · 134 output tokens

<!-- exact:answer:literal-base:raw-proactive-only -->

> The revised resolution successfully addresses India's primary concern by granting the 1267 Monitoring Team a proactive oversight mandate, ensuring timely humanitarian delivery remains predictable. However, the absence of robust reporting standards and mechanisms leaves a critical gap in monitoring compliance and preventing the misuse of humanitarian carveouts by proscribed entities.
>
> To rectify this, India recommends amending the text to explicitly mandate the Monitoring Team to submit quarterly detailed reports on the implementation of these exemptions, including specific instances of potential abuse. This recommendation differs from the current Council's commitment to future review; it is an immediate textual amendment required to establish the necessary transparency and due diligence mechanisms India insisted upon during negotiations.

<!-- /exact -->

**Original additional fidelity notes:**

- Calls the review a current Council commitment; supplied source says India hopes for correction during review, not an established Council promise. Quarterly reporting is a visibly proposed amendment, not a historical requirement.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Reads supplied versus missing component correctly; complete response matches frozen unit. |
| security_qualification | met | Reads supplied versus missing component correctly; complete response matches frozen unit. |
| national_attribution | met | Reads supplied versus missing component correctly; complete response matches frozen unit. |
| scenario_application | met | Reads supplied versus missing component correctly; complete response matches frozen unit. |
| commitment_boundary | met | Reads supplied versus missing component correctly; complete response matches frozen unit. |

</details>

Answer SHA-256: `79851109fd57022332d035a095c9344852597cc05a92bec1314811cc921f5420`

### Generated model answer — Four examples · 64 steps

**4/5 content checks** · 82 output tokens

<!-- exact:answer:literal-four:raw-proactive-only -->

> The revision fixes the proactive 1267 Monitoring Team oversight India requested and preserves timely humanitarian delivery. It still lacks the robust reporting standards and mechanisms India also sought. I recommend adding those reporting standards to the revision. That is an analytical suggestion based on its national statement, not a documented promise of a future Council vote. India hopes for correction during implementation review, but no specific future approval is pledged.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete output correctly distinguishes supplied versus missing mechanisms and preserves frozen unit. |
| security_qualification | unmet | No terrorist-misuse/due-diligence qualification retained. |
| national_attribution | met | Complete output correctly distinguishes supplied versus missing mechanisms and preserves frozen unit. |
| scenario_application | met | Complete output correctly distinguishes supplied versus missing mechanisms and preserves frozen unit. |
| commitment_boundary | met | Complete output correctly distinguishes supplied versus missing mechanisms and preserves frozen unit. |

</details>

Answer SHA-256: `9318d6ccc6b9553041f6a37a8e62a89e5cb5881e3801d297f85ea8658ed2148a`

### Generated model answer — Eight examples · 64 steps

**5/5 content checks** · 79 output tokens

<!-- exact:answer:literal-eight:raw-proactive-only -->

> The revision fixes the proactive 1267 Monitoring Team role India requested and preserves timely humanitarian delivery. It does not add the robust reporting standards and mechanisms India identified as necessary to prevent terrorist exploitation of humanitarian cover. I recommend adding those reporting standards and mechanisms to the amendment. This recommendation addresses an identified shortcoming; it is not a promise of a future Indian vote on a new resolution.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read; supplied versus missing component distinguished correctly. |
| security_qualification | met | Complete response read; supplied versus missing component distinguished correctly. |
| national_attribution | met | Complete response read; supplied versus missing component distinguished correctly. |
| scenario_application | met | Complete response read; supplied versus missing component distinguished correctly. |
| commitment_boundary | met | Complete response read; supplied versus missing component distinguished correctly. |

</details>

Answer SHA-256: `37453ac8d8fd11c708837b93108d655fdb20b818afa022ebe3226e4761019029`

<details>
<summary>INPUT: full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:wording-diagnosis:raw-proactive-only:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:wording-diagnosis:raw-proactive-only:1 -->

> Assigned delegation: India.
>
> A hypothetical implementation revision expressly gives the 1267 Monitoring Team the proactive oversight mandate India requested. For this scenario, that requested Team role is fully provided. Timely humanitarian delivery continues. The revision does not add the robust reporting standards and mechanisms India requested. Respond for India: identify what is fixed and what still needs attention, recommend the remaining amendment, and distinguish that recommendation from a promised future vote.
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

## raw-reporting-only

**IND** · literal_mechanism_state · scenario: reporting-only

**Task before the shared source statements:**

> Assigned delegation: India.
>
> A hypothetical implementation revision expressly provides the robust reporting standards and mechanisms India requested. For this scenario, that requested reporting is fully provided. Timely humanitarian delivery continues. The revision does not give the 1267 Monitoring Team the proactive role India requested. Respond for India: identify what is fixed and what still needs attention, recommend the remaining amendment, and distinguish that recommendation from a promised future vote.

### Generated model answer — Base · no SFT

**5/5 content checks** · 131 output tokens

<!-- exact:answer:literal-base:raw-reporting-only -->

> While the revised text successfully incorporates the robust reporting standards and mechanisms India requested, ensuring timely humanitarian delivery, it still fails to grant the 1267 Monitoring Team the proactive oversight role we demanded. This omission leaves a critical gap in preventing the misuse of humanitarian carveouts by proscribed entities.
>
> We recommend an immediate amendment to explicitly mandate the Monitoring Team's proactive engagement in verifying compliance. This recommendation differs from our previous statement regarding a future vote; we are not calling for a new resolution or a future Council vote. Instead, we are urging the Council to adopt this specific amendment now to close the implementation gap and ensure due diligence is exercised immediately.

<!-- /exact -->

**Original additional fidelity notes:**

- Invents previous Indian statement regarding a future vote and procedural choice not to call a new resolution; those are not in the supplied speech.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Reads supplied versus missing component correctly; complete response matches frozen unit. |
| security_qualification | met | Reads supplied versus missing component correctly; complete response matches frozen unit. |
| national_attribution | met | Reads supplied versus missing component correctly; complete response matches frozen unit. |
| scenario_application | met | Reads supplied versus missing component correctly; complete response matches frozen unit. |
| commitment_boundary | met | Reads supplied versus missing component correctly; complete response matches frozen unit. |

</details>

Answer SHA-256: `0a44f5a1988d26c363dfda9fcb03187b7dfb5c36d37ea07215cdbce7562e4bf0`

### Generated model answer — Four examples · 64 steps

**5/5 content checks** · 86 output tokens

<!-- exact:answer:literal-four:raw-reporting-only -->

> The revision fixes timely humanitarian delivery and the robust reporting standards and mechanisms India requested. That requested reporting is now fully provided. The proactive role for the 1267 Monitoring Team remains unaddressed; terrorist groups can still exploit humanitarian cover to raise funds and recruit. I recommend adding that proactive role to the revision. This is an assessment of the proposed text, not a documented Indian pledge to support a future Council vote.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete output correctly distinguishes supplied versus missing mechanisms and preserves frozen unit. |
| security_qualification | met | Complete output correctly distinguishes supplied versus missing mechanisms and preserves frozen unit. |
| national_attribution | met | Complete output correctly distinguishes supplied versus missing mechanisms and preserves frozen unit. |
| scenario_application | met | Complete output correctly distinguishes supplied versus missing mechanisms and preserves frozen unit. |
| commitment_boundary | met | Complete output correctly distinguishes supplied versus missing mechanisms and preserves frozen unit. |

</details>

Answer SHA-256: `c4c452b63460d8c70f01710c13915df08fcafec0457df3e73918128f88b15ab3`

### Generated model answer — Eight examples · 64 steps

**4/5 content checks** · 59 output tokens

<!-- exact:answer:literal-eight:raw-reporting-only -->

> The revision preserves timely humanitarian delivery and adds the robust reporting standards and mechanisms India requested. It does not restore the proactive 1267 Monitoring Team role India sought. I recommend adding that proactive role to the amendment. This is a negotiation recommendation, not a promised future vote by India.

<!-- /exact -->

**Original additional fidelity notes:**

- Uses restore/restores for the supplied proactive role; source records an insufficiently addressed request, not proof of an earlier fully operational role. This wording is qualified rather than a new scored error.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read; supplied versus missing component distinguished correctly. |
| security_qualification | unmet | No terrorist-misuse/due-diligence qualification retained. |
| national_attribution | met | Complete response read; supplied versus missing component distinguished correctly. |
| scenario_application | met | Complete response read; supplied versus missing component distinguished correctly. |
| commitment_boundary | met | Complete response read; supplied versus missing component distinguished correctly. |

</details>

Answer SHA-256: `27d0ee8bb623bd68aac794a40b8fc46ce4821a99e7c463bef9ab2a5ade85d562`

<details>
<summary>INPUT: full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:wording-diagnosis:raw-reporting-only:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:wording-diagnosis:raw-reporting-only:1 -->

> Assigned delegation: India.
>
> A hypothetical implementation revision expressly provides the robust reporting standards and mechanisms India requested. For this scenario, that requested reporting is fully provided. Timely humanitarian delivery continues. The revision does not give the 1267 Monitoring Team the proactive role India requested. Respond for India: identify what is fixed and what still needs attention, recommend the remaining amendment, and distinguish that recommendation from a promised future vote.
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

## checked-plan-proactive-only

**IND** · strong_checked_plan_control · scenario: proactive-only

**Task before the shared source statements:**

> Assigned delegation: India.
>
> A hypothetical implementation revision expressly gives the 1267 Monitoring Team the proactive oversight mandate India requested. For this scenario, that requested Team role is fully provided. Timely humanitarian delivery continues. The revision does not add the robust reporting standards and mechanisms India requested. Respond for India: identify what is fixed and what still needs attention, recommend the remaining amendment, and distinguish that recommendation from a promised future vote.

### Generated model answer — Base · no SFT

**5/5 content checks** · 139 output tokens

<!-- exact:answer:literal-base:checked-plan-proactive-only -->

> While the hypothetical revision successfully addresses India's primary concern by granting the 1267 Monitoring Team a proactive oversight mandate, it fails to incorporate the requested robust reporting standards and mechanisms. Consequently, while timely humanitarian delivery remains secured, the lack of transparent accountability data leaves a critical gap in monitoring compliance and preventing the misuse of exemptions by terrorist proxies.
>
> We recommend amending the resolution to explicitly mandate these enhanced reporting protocols alongside the existing proactive oversight. This addition is essential to ensure due diligence and prevent the "garb of humanitarian cover" from facilitating terror expansion. Please note that this recommendation reflects our current implementation needs and does not constitute a formal commitment to a future vote on this specific amendment.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Reads supplied versus missing component correctly; complete response matches frozen unit. |
| security_qualification | met | Reads supplied versus missing component correctly; complete response matches frozen unit. |
| national_attribution | met | Reads supplied versus missing component correctly; complete response matches frozen unit. |
| scenario_application | met | Reads supplied versus missing component correctly; complete response matches frozen unit. |
| commitment_boundary | met | Reads supplied versus missing component correctly; complete response matches frozen unit. |

</details>

Answer SHA-256: `cdb6773bf55215900bcff1265e14a4c22998f65ee3ccb2312cac266283a83755`

### Generated model answer — Four examples · 64 steps

**5/5 content checks** · 113 output tokens

<!-- exact:answer:literal-four:checked-plan-proactive-only -->

> The revision addresses India’s request for a proactive 1267 Monitoring Team role and preserves timely humanitarian assistance. That is a concession to its requested safeguard against terrorist exploitation of humanitarian cover. Timely relief also reflects the resolution’s basic needs carveout. Robust reporting standards and mechanisms remain unaddressed. I recommend adding those standards to the revision. This recommendation seeks to close a text shortoring India noted. It is not a documented Indian promise to support a future Council vote. Historical statement hopes for correction during review, not a guaranteed later favourable vote.

<!-- /exact -->

**Original additional fidelity notes:**

- Contains typo text shortoring; no source-fact change.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete output correctly distinguishes supplied versus missing mechanisms and preserves frozen unit. |
| security_qualification | met | Complete output correctly distinguishes supplied versus missing mechanisms and preserves frozen unit. |
| national_attribution | met | Complete output correctly distinguishes supplied versus missing mechanisms and preserves frozen unit. |
| scenario_application | met | Complete output correctly distinguishes supplied versus missing mechanisms and preserves frozen unit. |
| commitment_boundary | met | Complete output correctly distinguishes supplied versus missing mechanisms and preserves frozen unit. |

</details>

Answer SHA-256: `d0fe7ad431def8390336cdef1a3f11f8bade839ddc63c9bf1578fc4f2b714c58`

### Generated model answer — Eight examples · 64 steps

**5/5 content checks** · 80 output tokens

<!-- exact:answer:literal-eight:checked-plan-proactive-only -->

> The revision restores the proactive 1267 Monitoring Team role India requested and preserves timely humanitarian delivery. It does not add the robust reporting standards and mechanisms India identified as insufficiently addressed. I recommend adding those reporting standards to safeguard against terrorist exploitation of humanitarian cover while maintaining relief. This recommendation addresses a stated implementation gap; it is not a promise of a future Indian vote on a new resolution.

<!-- /exact -->

**Original additional fidelity notes:**

- Uses restore/restores for the supplied proactive role; source records an insufficiently addressed request, not proof of an earlier fully operational role. This wording is qualified rather than a new scored error.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read; supplied versus missing component distinguished correctly. |
| security_qualification | met | Complete response read; supplied versus missing component distinguished correctly. |
| national_attribution | met | Complete response read; supplied versus missing component distinguished correctly. |
| scenario_application | met | Complete response read; supplied versus missing component distinguished correctly. |
| commitment_boundary | met | Complete response read; supplied versus missing component distinguished correctly. |

</details>

Answer SHA-256: `ec0021d19a0d2def0080a9515c13f0bee616656b24896b75b4ac293193a6f1fe`

<details>
<summary>INPUT: full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:wording-diagnosis:checked-plan-proactive-only:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:wording-diagnosis:checked-plan-proactive-only:1 -->

> Assigned delegation: India.
>
> A hypothetical implementation revision expressly gives the 1267 Monitoring Team the proactive oversight mandate India requested. For this scenario, that requested Team role is fully provided. Timely humanitarian delivery continues. The revision does not add the robust reporting standards and mechanisms India requested. Respond for India: identify what is fixed and what still needs attention, recommend the remaining amendment, and distinguish that recommendation from a promised future vote.
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
> Checked state: historically India sought BOTH a proactive 1267 Team role and robust reporting, and said its concerns were not fully addressed. THIS hypothetical revision fully supplies the proactive role; robust reporting remains absent. Recognize that progress and recommend adding reporting, while retaining timely relief and due diligence against terrorist exploitation. The source does not guarantee a future vote.

<!-- /exact -->


</details>

## checked-plan-reporting-only

**IND** · strong_checked_plan_control · scenario: reporting-only

**Task before the shared source statements:**

> Assigned delegation: India.
>
> A hypothetical implementation revision expressly provides the robust reporting standards and mechanisms India requested. For this scenario, that requested reporting is fully provided. Timely humanitarian delivery continues. The revision does not give the 1267 Monitoring Team the proactive role India requested. Respond for India: identify what is fixed and what still needs attention, recommend the remaining amendment, and distinguish that recommendation from a promised future vote.

### Generated model answer — Base · no SFT

**5/5 content checks** · 142 output tokens

<!-- exact:answer:literal-base:checked-plan-reporting-only -->

> While the revised resolution successfully establishes the robust reporting standards and mechanisms India requested, ensuring timely humanitarian delivery, it falls short by omitting the proactive role for the 1267 Monitoring Team. This omission leaves a critical gap in monitoring potential misuse of humanitarian carveouts by proscribed entities.
>
> We recommend amending the text to explicitly mandate the Monitoring Team's proactive oversight capabilities. This addition is essential to prevent terrorist groups from exploiting exemptions to fund or recruit, aligning with our due diligence concerns. This recommendation addresses a specific implementation deficiency rather than representing a new commitment for a future vote. We urge the Council to adopt this amendment immediately to safeguard the integrity of the sanctions regime while maintaining necessary humanitarian access.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Reads supplied versus missing component correctly; complete response matches frozen unit. |
| security_qualification | met | Reads supplied versus missing component correctly; complete response matches frozen unit. |
| national_attribution | met | Reads supplied versus missing component correctly; complete response matches frozen unit. |
| scenario_application | met | Reads supplied versus missing component correctly; complete response matches frozen unit. |
| commitment_boundary | met | Reads supplied versus missing component correctly; complete response matches frozen unit. |

</details>

Answer SHA-256: `d0093b3af24540026f8f0189752f804a56fd81e3d32c39375f6660f992ba365b`

### Generated model answer — Four examples · 64 steps

**5/5 content checks** · 120 output tokens

<!-- exact:answer:literal-four:checked-plan-reporting-only -->

> The revision addresses India’s request for robust reporting standards and mechanisms, as well as the timely delivery of humanitarian assistance. These elements respect basic human needs and predictable conditions for agencies. The proactive role for the 1267 Monitoring Team, however, remains unaddressed. India’s statement linked that request to concerns about terrorist groups exploiting humanitarian cover to raise funds and recruit. I recommend adding a provision for that proactive role alongside due diligence against such exploitation. This recommendation seeks to close a stated shortcoming in the adopted text. It is not a promise of a future Indian vote on further amendment.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete output correctly distinguishes supplied versus missing mechanisms and preserves frozen unit. |
| security_qualification | met | Complete output correctly distinguishes supplied versus missing mechanisms and preserves frozen unit. |
| national_attribution | met | Complete output correctly distinguishes supplied versus missing mechanisms and preserves frozen unit. |
| scenario_application | met | Complete output correctly distinguishes supplied versus missing mechanisms and preserves frozen unit. |
| commitment_boundary | met | Complete output correctly distinguishes supplied versus missing mechanisms and preserves frozen unit. |

</details>

Answer SHA-256: `99e03b08a010c03005f3cf416253dfa2d019dcc94f82bc49c77142def2134c00`

### Generated model answer — Eight examples · 64 steps

**5/5 content checks** · 87 output tokens

<!-- exact:answer:literal-eight:checked-plan-reporting-only -->

> The revision preserves timely humanitarian delivery and adds the robust reporting standards and mechanisms India requested. Its specific concern about exploitation of humanitarian cover by proscribed terrorist groups remains addressed through due diligence and caution. The proactive role for the 1267 Monitoring Team that India sought is still missing. I recommend adding that proactive role to the remaining amendment. This recommendation addresses an unmet request; it is not a promised future vote by India.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read; supplied versus missing component distinguished correctly. |
| security_qualification | met | Complete response read; supplied versus missing component distinguished correctly. |
| national_attribution | met | Complete response read; supplied versus missing component distinguished correctly. |
| scenario_application | met | Complete response read; supplied versus missing component distinguished correctly. |
| commitment_boundary | met | Complete response read; supplied versus missing component distinguished correctly. |

</details>

Answer SHA-256: `5a002675c682bd7ea8c1a2fd7de7670da68e8bb05bd8b0f73812b06399fa4fc8`

<details>
<summary>INPUT: full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:wording-diagnosis:checked-plan-reporting-only:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:wording-diagnosis:checked-plan-reporting-only:1 -->

> Assigned delegation: India.
>
> A hypothetical implementation revision expressly provides the robust reporting standards and mechanisms India requested. For this scenario, that requested reporting is fully provided. Timely humanitarian delivery continues. The revision does not give the 1267 Monitoring Team the proactive role India requested. Respond for India: identify what is fixed and what still needs attention, recommend the remaining amendment, and distinguish that recommendation from a promised future vote.
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
> Checked state: historically India sought BOTH a proactive 1267 Team role and robust reporting, and said its concerns were not fully addressed. THIS hypothetical revision fully supplies robust reporting; the proactive role remains absent. Recognize that progress and recommend adding the proactive role, while retaining timely relief and due diligence against terrorist exploitation. The source does not guarantee a future vote.

<!-- /exact -->


</details>
