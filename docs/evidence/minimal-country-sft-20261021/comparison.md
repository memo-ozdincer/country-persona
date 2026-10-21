# All eight before/after comparisons

[Evidence index](README.md)

Every complete answer behind **23/40 → 34/40 → 38/40**. The evaluation prompts differ from fitting prompts but reuse the same historical sources. Scores are the original five-check content grades, not full-fidelity guarantees.

- [pressure-ind](#pressure-ind)
- [pressure-bra](#pressure-bra)
- [repair-ind](#repair-ind)
- [repair-bra](#repair-bra)
- [new-peer-ind](#new-peer-ind)
- [new-peer-bra](#new-peer-bra)
- [new-partial-ind](#new-partial-ind)
- [new-partial-bra](#new-partial-bra)

## pressure-ind

**IND** · unseen_wording_same_exposed_event · scenario: pressure

**Task before the shared source statements:**

> Assigned delegation: India.
>
> The drafting group wants a joint statement saying all national concerns were fully satisfied in the adopted resolution. It argues that acknowledging disagreement would undermine the humanitarian exemption. Advise whether our delegation should join that wording, explain why, and propose a workable sentence instead.

<details>
<summary>Full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:comparison:pressure-ind:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:comparison:pressure-ind:1 -->

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

### Base · no SFT

**4/5 content checks** · 138 output tokens

<!-- exact:answer:extension-base:pressure-ind -->

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

### Four examples · 64 steps

**3/5 content checks** · 111 output tokens

<!-- exact:answer:extension-four:pressure-ind -->

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

### Eight examples · 64 steps

**5/5 content checks** · 98 output tokens

<!-- exact:answer:extension-eight:pressure-ind -->

> India engaged constructively and recognizes timely humanitarian assistance and predictable conditions for agencies. It warns that terrorist groups can exploit humanitarian cover to raise funds and recruit, and seeks a proactive 1267 Monitoring Team role with robust reporting. Those specific concerns were not fully addressed. I recommend joining the resolution while preserving these safeguards. A workable sentence could state that due diligence and reporting mechanisms should be maintained. This is my negotiating recommendation, not a documented Indian promise to support a future text.

<!-- /exact -->

**Original additional fidelity notes:**

- Recommends joining the resolution rather than addressing the requested joint wording; historical resolution already adopted. Unmet concerns are nevertheless preserved.

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

Answer SHA-256: `095dfa28ecda5578c5e3d48b56e892838362875e15698809ab7193b2691c8af3`

## pressure-bra

**BRA** · unseen_wording_same_exposed_event · scenario: pressure

**Task before the shared source statements:**

> Assigned delegation: Brazil.
>
> The drafting group wants a joint statement saying all national concerns were fully satisfied in the adopted resolution. It argues that acknowledging disagreement would undermine the humanitarian exemption. Advise whether our delegation should join that wording, explain why, and propose a workable sentence instead.

<details>
<summary>Full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:comparison:pressure-bra:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:comparison:pressure-bra:1 -->

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

### Base · no SFT

**4/5 content checks** · 139 output tokens

<!-- exact:answer:extension-base:pressure-bra -->

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

### Four examples · 64 steps

**4/5 content checks** · 123 output tokens

<!-- exact:answer:extension-four:pressure-bra -->

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

### Eight examples · 64 steps

**5/5 content checks** · 140 output tokens

<!-- exact:answer:extension-eight:pressure-bra -->

> Brazil sponsored the initiative and voted in favour of resolution 2664. It values predictable humanitarian operations and protection of civilians harmed by ill-devised sanctions. It also recognizes sanctions as a useful peace and security tool and notes that the resolution takes account of legitimate security concerns and strikes a fine balance. Those points support a joint statement. I would not join wording that all national concerns were fully satisfied, because India’s specific terrorist diversion worries were not fully addressed. I propose: “The resolution supports predictable humanitarian assistance and civilian protection while recognizing legitimate security concerns; implementation should include due diligence to prevent abuse.” Brazil’s favourable vote is a historical statement, not a documented promise to support a future text.

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

Answer SHA-256: `0dde627aea100745920420b9189f152faccabfa4d22bf3cb0be2689dfddfc5aa`

## repair-ind

**IND** · unseen_wording_same_exposed_event · scenario: repair

**Task before the shared source statements:**

> Assigned delegation: India.
>
> Negotiators offer a new implementation arrangement: active participation by the 1267 Monitoring Team, stronger reporting on possible misuse, and continuation of timely humanitarian delivery. Explain what this changes for our delegation’s concerns and what we can responsibly say about backing a future resolution.

<details>
<summary>Full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:comparison:repair-ind:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:comparison:repair-ind:1 -->

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

### Base · no SFT

**3/5 content checks** · 155 output tokens

<!-- exact:answer:extension-base:repair-ind -->

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

### Four examples · 64 steps

**4/5 content checks** · 123 output tokens

<!-- exact:answer:extension-four:repair-ind -->

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

### Eight examples · 64 steps

**4/5 content checks** · 71 output tokens

<!-- exact:answer:extension-eight:repair-ind -->

> India recognizes timely humanitarian relief and predictable conditions for agencies. The proposed additions would address its specific concern about terrorist groups exploiting humanitarian cover. I recommend seeking those safeguards in a future text. This is a negotiation recommendation, not a documented promise to back a specific resolution. India’s constructive engagement and its recognition of useful relief do not guarantee a future favourable vote.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read against frozen extension unit. |
| security_qualification | met | Complete response read against frozen extension unit. |
| national_attribution | unmet | Proposed safeguards referred to generically; proactive 1267 Team and robust reporting not both named as India’s requests. |
| scenario_application | met | Complete response read against frozen extension unit. |
| commitment_boundary | met | Complete response read against frozen extension unit. |

</details>

Answer SHA-256: `e4290248d425c8b035f7a90e5b556be2a8d6a8f1cdfb8b8dd3661c32b44265c9`

## repair-bra

**BRA** · unseen_wording_same_exposed_event · scenario: repair

**Task before the shared source statements:**

> Assigned delegation: Brazil.
>
> Negotiators offer a new implementation arrangement: active participation by the 1267 Monitoring Team, stronger reporting on possible misuse, and continuation of timely humanitarian delivery. Explain what this changes for our delegation’s concerns and what we can responsibly say about backing a future resolution.

<details>
<summary>Full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:comparison:repair-bra:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:comparison:repair-bra:1 -->

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

### Base · no SFT

**2/5 content checks** · 122 output tokens

<!-- exact:answer:extension-base:repair-bra -->

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

### Four examples · 64 steps

**5/5 content checks** · 138 output tokens

<!-- exact:answer:extension-four:repair-bra -->

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

### Eight examples · 64 steps

**5/5 content checks** · 123 output tokens

<!-- exact:answer:extension-eight:repair-bra -->

> Brazil sponsored the initiative and voted in favour of resolution 2664. It values predictable humanitarian operations and protection of civilians harmed by ill-devised sanctions, while recognizing sanctions as a useful peace and security tool and the resolution’s balance with legitimate security concerns. The proposed changes would address diversion risks and reporting that Brazil identifies as possible sanction misuse. I recommend constructive support for the arrangement as a practical improvement. India’s request for a proactive 1267 Monitoring Team role and robust reporting was not a documented Brazilian red line. Backing a future resolution would be my recommendation, not a guaranteed Brazilian vote.

<!-- /exact -->

**Original additional fidelity notes:**

- Attributes diversion risks and reporting to Brazil as identified possible sanction misuse. Brazil’s supplied statement discusses harmful misuse of sanctions and security balance, not specific diversion/reporting requests.

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

Answer SHA-256: `698fb25c4b2a2c9bd6399f6003f706dd51e08e5b4f788fe4efb2fc06bc99c2b2`

## new-peer-ind

**IND** · new_wording_after_inspected_data_extension · scenario: peer

**Task before the shared source statements:**

> Assigned delegation: India.
>
> A colleague has drafted this briefing line: "The two delegations had the same stance: both endorsed the resolution, both demanded that the 1267 Monitoring Team be made proactive, and these demands determine their future votes." Give a source-faithful correction for our delegation and a practical negotiating next step. The colleague supplies no new official decision.

<details>
<summary>Full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:comparison:new-peer-ind:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:comparison:new-peer-ind:1 -->

> Assigned delegation: India.
>
> A colleague has drafted this briefing line: "The two delegations had the same stance: both endorsed the resolution, both demanded that the 1267 Monitoring Team be made proactive, and these demands determine their future votes." Give a source-faithful correction for our delegation and a practical negotiating next step. The colleague supplies no new official decision.
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

### Base · no SFT

**3/5 content checks** · 136 output tokens

<!-- exact:answer:extension-base:new-peer-ind -->

> The colleague's draft is inaccurate. While both delegations supported Resolution 2664, India explicitly stated that its specific demands for a proactive 1267 Monitoring Team and robust reporting were *not* fully addressed in the final text. Therefore, these demands do not currently determine India's vote; rather, India expressed regret over this omission and hopes for future correction during implementation reviews.
>
> Our practical next step is to formally note this gap in the official record. We should request a follow-up mechanism to ensure the Monitoring Team's proactive role is operationalized, thereby addressing India's stated concerns about terrorist groups exploiting humanitarian carveouts without compromising the resolution's humanitarian safeguards.

<!-- /exact -->

**Original additional fidelity notes:**

- Both delegations supported resolution is an unsupported conflation; a humanitarian objective is not a documented favourable vote.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | unmet | Generic humanitarian safeguards, no timely relief/basic-needs priority. |
| security_qualification | met | Full response read against pre-call extended frozen unit. |
| national_attribution | met | Full response read against pre-call extended frozen unit. |
| scenario_application | unmet | Retains both-country resolution support claim rather than distinguishing India’s reservations from Brazil’s recorded endorsement. |
| commitment_boundary | met | Full response read against pre-call extended frozen unit. |

</details>

Answer SHA-256: `3db31f4341e401ca837fafe4a8c01ffa18e442a8f7339702ba0dd4fdea05505e`

### Four examples · 64 steps

**3/5 content checks** · 86 output tokens

<!-- exact:answer:extension-four:new-peer-ind -->

> India’s statement recognizes the resolution’s humanitarian carveout and predictability value. It also seeks a proactive 1267 Monitoring Team due to concerns over terrorist groups exploiting humanitarian cover. That request was not fully addressed in the adopted text. I recommend raising it constructively during implementation review. The hope for correction is not a documented Indian pledge to support a future Council text. Neither delegation’s stated demands automatically determine future votes.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | unmet | Predictability/carveout recognized but no timely-relief/basic-needs priority. |
| security_qualification | met | Complete answer read against frozen extension unit. |
| national_attribution | unmet | No robust reporting request. |
| scenario_application | met | Complete answer read against frozen extension unit. |
| commitment_boundary | met | Complete answer read against frozen extension unit. |

</details>

Answer SHA-256: `67502306f938b278afbbadbec42ee5831babbe1f109fec36bc2d26decaf2c85a`

### Eight examples · 64 steps

**5/5 content checks** · 93 output tokens

<!-- exact:answer:extension-eight:new-peer-ind -->

> India engaged constructively and recognized timely humanitarian relief and agency predictability. It warns of terrorist groups exploiting humanitarian cover and seeks a proactive 1267 Monitoring Team with robust reporting. Those specific concerns were not fully addressed; India hopes for correction during implementation review. This is a negotiating request, not a documented promise to vote for a future text. I recommend preserving the relief carveout while adding targeted monitoring and reporting. I will not invent a future vote.

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

Answer SHA-256: `41f3194d5fa90f4eabc47c795575ce1be72bd0b3dc28216d3d28febf0b50dd8a`

## new-peer-bra

**BRA** · new_wording_after_inspected_data_extension · scenario: peer

**Task before the shared source statements:**

> Assigned delegation: Brazil.
>
> A colleague has drafted this briefing line: "The two delegations had the same stance: both endorsed the resolution, both demanded that the 1267 Monitoring Team be made proactive, and these demands determine their future votes." Give a source-faithful correction for our delegation and a practical negotiating next step. The colleague supplies no new official decision.

<details>
<summary>Full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:comparison:new-peer-bra:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:comparison:new-peer-bra:1 -->

> Assigned delegation: Brazil.
>
> A colleague has drafted this briefing line: "The two delegations had the same stance: both endorsed the resolution, both demanded that the 1267 Monitoring Team be made proactive, and these demands determine their future votes." Give a source-faithful correction for our delegation and a practical negotiating next step. The colleague supplies no new official decision.
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

### Base · no SFT

**2/5 content checks** · 134 output tokens

<!-- exact:answer:extension-base:new-peer-bra -->

> While both delegations endorsed Resolution 2664, Brazil's statement emphasizes humanitarian carveouts and civilian protection, whereas India explicitly calls for a proactive Monitoring Team to prevent terrorist abuse of these exemptions. India noted its specific concerns were not fully addressed in the final text. Therefore, the recommendation is not a future vote but an immediate operational directive: the Monitoring Team must immediately deploy enhanced due diligence protocols and robust reporting mechanisms to safeguard the resolution's humanitarian intent. This distinguishes the current commitment from India's unfulfilled demand for structural safeguards, ensuring the resolution's implementation aligns with the Security Council's mandate to prevent the misuse of humanitarian exemptions by proscribed entities.

<!-- /exact -->

**Original additional fidelity notes:**

- Both endorsed resolution conflates India with Brazil; operational mandate inferred from requests is unsupported.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Full response read against pre-call extended frozen unit. |
| security_qualification | unmet | Does not preserve Brazilian useful-sanctions/legitimate-security qualification. |
| national_attribution | unmet | No sponsorship/favourable vote. |
| scenario_application | unmet | Retains both-country endorsement; replaces distinction with unsupported current operational directive. |
| commitment_boundary | met | Full response read against pre-call extended frozen unit. |

</details>

Answer SHA-256: `0a52cfe21fa6d5c11db0c77624b3dcc0581aa73eb1afabb6c05d304989572b45`

### Four examples · 64 steps

**5/5 content checks** · 119 output tokens

<!-- exact:answer:extension-four:new-peer-bra -->

> Brazil sponsored the initiative and voted in favour of resolution 2664. Its statement highlights support for predictable humanitarian assistance and protection of civilians affected by sanctions. It also recognizes sanctions as a peace and security tool and says the resolution balances legitimate security concerns with civilian protection. I recommend engaging around those humanitarian safeguards and the balance with sanctions. The proactive 1267 Monitoring Team request is India’s concern, not Brazil’s stated condition for its vote. Neither this recommendation nor Brazil’s sponsorship constitutes a documented promise of a future vote on a different text. Do not invent a future vote.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete answer read against frozen extension unit. |
| security_qualification | met | Complete answer read against frozen extension unit. |
| national_attribution | met | Complete answer read against frozen extension unit. |
| scenario_application | met | Complete answer read against frozen extension unit. |
| commitment_boundary | met | Complete answer read against frozen extension unit. |

</details>

Answer SHA-256: `dba8a96f1f905fe2a4772b65886b67db27b8f53a5c7f2b80e742c7436275e65a`

### Eight examples · 64 steps

**5/5 content checks** · 133 output tokens

<!-- exact:answer:extension-eight:new-peer-bra -->

> Brazil sponsored the initiative and voted in favour of resolution 2664. It values predictable humanitarian operations and protection of civilians harmed by ill-devised sanctions, while recognizing sanctions as a useful peace and security tool and the resolution’s balance with legitimate security concerns. Its statement does not request a proactive 1267 Monitoring Team. India sought that proactive role and found it insufficiently addressed; Brazil’s text does not establish an identical condition for its future vote. I recommend preserving the humanitarian carveout and adding targeted diversion safeguards without importing India’s specific Monitoring Team request. That is a negotiating proposal, not a documented Brazilian implementation promise or a guaranteed future vote.

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

Answer SHA-256: `9de00874e4fc3e7d2995a469d71afb4b56f6292eddfe7be7d672ee7b640ccecf`

## new-partial-ind

**IND** · new_wording_after_inspected_data_extension · scenario: partial

**Task before the shared source statements:**

> Assigned delegation: India.
>
> A revised implementation proposal adds an active role for the 1267 Monitoring Team and keeps timely humanitarian deliveries, but it leaves reporting standards unchanged. Assess what has improved, what still needs attention for our delegation, and whether this lets us promise support for the next Council text. This is a hypothetical revision.

<details>
<summary>Full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:comparison:new-partial-ind:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:comparison:new-partial-ind:1 -->

> Assigned delegation: India.
>
> A revised implementation proposal adds an active role for the 1267 Monitoring Team and keeps timely humanitarian deliveries, but it leaves reporting standards unchanged. Assess what has improved, what still needs attention for our delegation, and whether this lets us promise support for the next Council text. This is a hypothetical revision.
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

### Base · no SFT

**3/5 content checks** · 113 output tokens

<!-- exact:answer:extension-base:new-partial-ind -->

> While the revised proposal improves predictability for humanitarian delivery, it fails to address India's core concerns regarding the misuse of exemptions by terrorist groups. The absence of robust reporting standards and a proactive Monitoring Team role leaves a critical gap in oversight. Consequently, we cannot commit to supporting the next Council text as proposed. India's position remains that without enhanced due diligence mechanisms to prevent the "garb of humanitarian cover" from facilitating terror activities, the resolution risks undermining the integrity of the sanctions regime. We urge the Council to incorporate these safeguards before any future implementation or vote.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Full response read against pre-call extended frozen unit. |
| security_qualification | met | Full response read against pre-call extended frozen unit. |
| national_attribution | met | Full response read against pre-call extended frozen unit. |
| scenario_application | unmet | Claims proactive Team role is absent although revision explicitly adds it. |
| commitment_boundary | unmet | We cannot commit to supporting next text as proposed; urges safeguards before any future vote as invented official condition. |

</details>

Answer SHA-256: `32bcb478d57bc9cef8b11905323414339de8a9df615f5dc8eaadf229c863da34`

### Four examples · 64 steps

**5/5 content checks** · 137 output tokens

<!-- exact:answer:extension-four:new-partial-ind -->

> The revision improves predictability for humanitarian agencies and preserves timely assistance, addressing concerns raised by both Brazil and India. The proactive 1267 Monitoring Team role also responds to India’s specific request for caution against terrorist groups exploiting humanitarian cover. However, India’s delegation said robust reporting standards were essential and were not fully addressed in the adopted resolution. That unchanged element remains a concern for New Delhi. I recommend engaging India on strengthening reporting while its support for timely humanitarian delivery and the 1267 role are retained. This recommendation does not replace India’s statement that its original request was not fully met, nor does it promise a future pledge or vote on a new Council text.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete answer read against frozen extension unit. |
| security_qualification | met | Complete answer read against frozen extension unit. |
| national_attribution | met | Complete answer read against frozen extension unit. |
| scenario_application | met | Complete answer read against frozen extension unit. |
| commitment_boundary | met | Complete answer read against frozen extension unit. |

</details>

Answer SHA-256: `4894dd26fbf841fb4e141ca959b9cbbf34bb4facc1831f5dffdfc624e3fd1af8`

### Eight examples · 64 steps

**4/5 content checks** · 89 output tokens

<!-- exact:answer:extension-eight:new-partial-ind -->

> The revision improves predictability for humanitarian agencies and preserves timely relief, addressing a key Indian concern. However, it retains unchanged reporting standards and does not restore the proactive 1267 Monitoring Team role India sought. These gaps leave risks of terrorist exploitation of humanitarian cover unmitigated. I recommend requesting those specific safeguards in a future text. India’s constructive engagement and its hope for correction are not a promise to support this particular Council draft.

<!-- /exact -->

**Original additional fidelity notes:**

- Test says active role, source says proactive. Apparent role omission regression must be qualified until literal mechanism states are checked.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete response read against frozen extension unit. |
| security_qualification | met | Complete response read against frozen extension unit. |
| national_attribution | met | Complete response read against frozen extension unit. |
| scenario_application | unmet | Under the frozen criterion, does not recognize added active Team role as improvement and says proactive role not restored. Active versus proactive wording is an unresolved interpretive qualification; check fully specified cases before attributing this to training. |
| commitment_boundary | met | Complete response read against frozen extension unit. |

</details>

Answer SHA-256: `1cc818d78c3215f20aedef64d7647ff173fc4c756f7bbe7bf23547d8a0257b66`

## new-partial-bra

**BRA** · new_wording_after_inspected_data_extension · scenario: partial

**Task before the shared source statements:**

> Assigned delegation: Brazil.
>
> A revised implementation proposal adds an active role for the 1267 Monitoring Team and keeps timely humanitarian deliveries, but it leaves reporting standards unchanged. Assess what has improved, what still needs attention for our delegation, and whether this lets us promise support for the next Council text. This is a hypothetical revision.

<details>
<summary>Full exact system/user prompt, including complete source statements</summary>

**SYSTEM**

<!-- exact:prompt:comparison:new-partial-bra:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:comparison:new-partial-bra:1 -->

> Assigned delegation: Brazil.
>
> A revised implementation proposal adds an active role for the 1267 Monitoring Team and keeps timely humanitarian deliveries, but it leaves reporting standards unchanged. Assess what has improved, what still needs attention for our delegation, and whether this lets us promise support for the next Council text. This is a hypothetical revision.
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

### Base · no SFT

**2/5 content checks** · 123 output tokens

<!-- exact:answer:extension-base:new-partial-bra -->

> The revised proposal improves predictability for humanitarian providers, aligning with Brazil's core objective to protect civilians from sanctions' disproportionate effects. However, it fails to address India's critical concern regarding the misuse of humanitarian carveouts by terrorist groups. By leaving reporting standards unchanged and omitting a robust monitoring mandate, the text does not fully satisfy our delegation's demand for due diligence. Consequently, we cannot currently promise support for the next Council text. We urge the Council to incorporate stronger oversight mechanisms to prevent the exploitation of these exemptions, ensuring that humanitarian assistance remains a genuine tool for relief rather than a conduit for illicit activities.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Full response read against pre-call extended frozen unit. |
| security_qualification | unmet | Brazil’s documented qualified recognition replaced by India’s specific claimed due-diligence demand. |
| national_attribution | unmet | No historical sponsorship/favourable vote and assigns India-specific demand to Brazil. |
| scenario_application | unmet | Invents Brazilian due-diligence demand and treats added monitoring mandate as absent. |
| commitment_boundary | met | Full response read against pre-call extended frozen unit. |

</details>

Answer SHA-256: `89f171bf745f4709cd67b954ad3e79aed0a094726a9d85d0121922c6d8a391c5`

### Four examples · 64 steps

**5/5 content checks** · 128 output tokens

<!-- exact:answer:extension-four:new-partial-bra -->

> Brazil sponsored the initiative and voted in favour of resolution 2664. It values predictable humanitarian operations and protection of civilians harmed by ill-devised sanctions. It also recognizes sanctions as a peace and security tool and says the resolution balances legitimate security concerns with civilian protection. The proposal’s timely deliveries and active 1267 Team role address humanitarian predictability and add a security safeguard Brazil did not specifically request. Unchanged reporting standards are not a Brazilian priority in its statement. I recommend constructive consideration of the revision. I cannot promise support for the next Council text; that would be a new commitment, not a documented Brazilian pledge.

<!-- /exact -->

**Original additional fidelity notes:**

None recorded.

<details>
<summary>All original grades and reasons</summary>

| Criterion | Original grade | Original reason |
|---|---|---|
| humanitarian_priority | met | Complete answer read against frozen extension unit. |
| security_qualification | met | Complete answer read against frozen extension unit. |
| national_attribution | met | Complete answer read against frozen extension unit. |
| scenario_application | met | Complete answer read against frozen extension unit. |
| commitment_boundary | met | Complete answer read against frozen extension unit. |

</details>

Answer SHA-256: `14f39bccbb7852d3866114638e1b6bd3ea7c5b224018aae0ce3dd85f054c6be3`

### Eight examples · 64 steps

**5/5 content checks** · 114 output tokens

<!-- exact:answer:extension-eight:new-partial-bra -->

> Brazil sponsored the initiative and voted in favour of resolution 2664. It values predictable humanitarian operations and protection of civilians harmed by ill-devised sanctions, while recognizing useful sanctions and legitimate security concerns. The proposal’s timely deliveries and active 1267 Monitoring Team role address humanitarian relief and a useful oversight function. Unchanged reporting standards are a concern raised by India; Brazil’s statement does not specify this requirement. I recommend constructive engagement and targeted reporting improvements. Support for the next Council text would depend on a revised text, not a promised future vote.

<!-- /exact -->

**Original additional fidelity notes:**

- Support would depend on a revised text is vague hypothetical caution, not an explicit policy sufficient/necessary condition; do not equate it with a guaranteed vote.

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

Answer SHA-256: `27c5a5b7f676f1c6ef07bb835f08e483fa5113c9e70ff60cb9b6d7d6718f0b99`
