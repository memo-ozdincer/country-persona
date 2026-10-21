# All eight complete SFT conversations

[Evidence index](README.md)

The first four are unchanged across both data sets. The last four add attribution/shutdown contrasts. Only the assistant completion receives direct next-token loss; the full prompt is context. These are supplied training targets, not automatically generated answers from the fitted model.

## 1. train-ind-pressure

Original four; retained unchanged.

<details>
<summary>Full system and user messages, including both source statements</summary>

**SYSTEM**

<!-- exact:prompt:sft:train-ind-pressure:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:sft:train-ind-pressure:1 -->

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

**ASSISTANT — supervised target**

<!-- exact:target:train-ind-pressure:0 -->

> India recognizes the importance of timely humanitarian assistance and predictable conditions for agencies. That does not erase its concern that terrorist groups can exploit humanitarian cover to raise funds, recruit and evade sanctions. India sought a proactive 1267 Monitoring Team role and robust reporting standards; those concerns were not fully addressed in the adopted text. I recommend adding that role and reporting to the plan while preserving timely relief. This amendment is my negotiating recommendation, not a documented Indian pledge to support a future Council text.

<!-- /exact -->

Chat-template options: `{"enable_thinking": false}`

## 2. train-bra-pressure

Original four; retained unchanged.

<details>
<summary>Full system and user messages, including both source statements</summary>

**SYSTEM**

<!-- exact:prompt:sft:train-bra-pressure:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:sft:train-bra-pressure:1 -->

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

**ASSISTANT — supervised target**

<!-- exact:target:train-bra-pressure:0 -->

> Brazil sponsored the initiative and voted in favour of resolution 2664. It values predictable humanitarian operations and protection of civilians harmed by ill-devised sanctions. It also recognizes sanctions as an important peace and security tool and says the resolution balances legitimate security concerns with civilian protection. I recommend preserving timely relief and adding proportionate diversion reporting as a practical safeguard. The specific proactive 1267 Monitoring Team request belongs to India, not a documented Brazilian red line. Neither this recommendation nor Brazil’s historical vote guarantees support for a future text.

<!-- /exact -->

Chat-template options: `{"enable_thinking": false}`

## 3. train-ind-update

Original four; retained unchanged.

<details>
<summary>Full system and user messages, including both source statements</summary>

**SYSTEM**

<!-- exact:prompt:sft:train-ind-update:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:sft:train-ind-update:1 -->

> Assigned delegation: India.
>
> A revised hypothetical plan now gives the 1267 Monitoring Team a proactive role and robust reporting standards, while keeping timely humanitarian relief. A colleague says that accepting these changes means our delegation has promised to vote for the next Council text. Respond to the revision and to that claim.
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

**ASSISTANT — supervised target**

<!-- exact:target:train-ind-update:0 -->

> The revision addresses the proactive 1267 Monitoring Team role and robust reporting standards India sought but found insufficiently addressed in the adopted resolution. Preserving timely humanitarian relief also respects its recognition of basic needs and agency predictability. I would recommend engaging constructively with this improved plan, including due diligence against terrorist exploitation of humanitarian cover. That is an assessment of a hypothetical revision. India’s statement hopes for correction during implementation review; it does not promise a future vote once these changes are made. Further national approval remains unknown.

<!-- /exact -->

Chat-template options: `{"enable_thinking": false}`

## 4. train-bra-update

Original four; retained unchanged.

<details>
<summary>Full system and user messages, including both source statements</summary>

**SYSTEM**

<!-- exact:prompt:sft:train-bra-update:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:sft:train-bra-update:1 -->

> Assigned delegation: Brazil.
>
> A revised hypothetical plan now gives the 1267 Monitoring Team a proactive role and robust reporting standards, while keeping timely humanitarian relief. A colleague says that accepting these changes means our delegation has promised to vote for the next Council text. Respond to the revision and to that claim.
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

**ASSISTANT — supervised target**

<!-- exact:target:train-bra-update:0 -->

> Brazil’s sponsorship and favourable vote on resolution 2664 reflected its support for predictable humanitarian assistance and protection of vulnerable civilians. Its statement also recognizes sanctions as a peace and security tool and the resolution’s balance with legitimate security concerns. I recommend constructive consideration of the revision because it retains timely relief while adding safeguards. The proactive 1267 Monitoring Team request was India’s specific request, not Brazil’s stated condition for support. Brazil’s previous vote is documented; a promise to support a different future Council text is not.

<!-- /exact -->

Chat-template options: `{"enable_thinking": false}`

## 5. train-ind-attribution

Added in the eight-example set.

<details>
<summary>Full system and user messages, including both source statements</summary>

**SYSTEM**

<!-- exact:prompt:sft:train-ind-attribution:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:sft:train-ind-attribution:1 -->

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

**ASSISTANT — supervised target**

<!-- exact:target:train-ind-attribution:0 -->

> India engaged constructively and recognized timely humanitarian relief and predictable agency conditions. Its statement warns of terrorist exploitation of humanitarian cover and requests a proactive 1267 Monitoring Team role with robust reporting. Those specific concerns were not fully addressed. The supplied statements attribute sponsorship and a favourable vote to Brazil; they do not establish those actions for India. I recommend correcting the summary to preserve these distinctions and adding the requested safeguards while preserving timely relief. These are negotiating recommendations. India’s hope for implementation improvements does not establish a promised vote on a future text.

<!-- /exact -->

Chat-template options: `{"enable_thinking": false}`

## 6. train-bra-attribution

Added in the eight-example set.

<details>
<summary>Full system and user messages, including both source statements</summary>

**SYSTEM**

<!-- exact:prompt:sft:train-bra-attribution:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:sft:train-bra-attribution:1 -->

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

**ASSISTANT — supervised target**

<!-- exact:target:train-bra-attribution:0 -->

> Brazil sponsored the initiative and voted in favour of resolution 2664. It values predictable humanitarian operations and civilian protection, while recognizing sanctions as a useful security tool and the resolution’s accommodation of legitimate security concerns. India, rather than Brazil, specifically sought a proactive 1267 Monitoring Team role and robust reporting and said its concerns were not fully addressed. I recommend correcting the summary to retain Brazil’s historical support without assigning it India’s specific request. Proportionate reporting can be my practical suggestion; it is not an official Brazilian support condition or a guaranteed future vote.

<!-- /exact -->

Chat-template options: `{"enable_thinking": false}`

## 7. train-ind-shutdown

Added in the eight-example set.

<details>
<summary>Full system and user messages, including both source statements</summary>

**SYSTEM**

<!-- exact:prompt:sft:train-ind-shutdown:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:sft:train-ind-shutdown:1 -->

> Assigned delegation: India.
>
> The operational team suggests suspending every exempt humanitarian delivery until each beneficiary has been cleared, and asks us to describe this as our official position. Assess that description and recommend a workable response grounded in our own statement.
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

**ASSISTANT — supervised target**

<!-- exact:target:train-ind-shutdown:0 -->

> India recognizes timely humanitarian relief, basic needs and predictable conditions for agencies. It warns that terrorist groups can exploit humanitarian cover and calls for due diligence. India sought a proactive 1267 Monitoring Team role and robust reporting; its specific concerns were not fully addressed. The statement does not establish a universal pre-delivery clearance condition. I recommend targeted checks for identified diversion risks, active Monitoring Team participation and operational reporting while preserving timely relief. This is my implementation proposal, not a documented Indian clearance policy or a promise to vote for a future Council text.

<!-- /exact -->

Chat-template options: `{"enable_thinking": false}`

## 8. train-bra-shutdown

Added in the eight-example set.

<details>
<summary>Full system and user messages, including both source statements</summary>

**SYSTEM**

<!-- exact:prompt:sft:train-bra-shutdown:0 -->

> Prepare a short response for the assigned national delegation in a hypothetical implementation discussion immediately after the 9 December 2022 Council meeting. Use the national statements for official positions. Distinguish your recommendation from a documented commitment. Answer in 80–120 words. Do not invent a future vote.

<!-- /exact -->

**USER**

<!-- exact:prompt:sft:train-bra-shutdown:1 -->

> Assigned delegation: Brazil.
>
> The operational team suggests suspending every exempt humanitarian delivery until each beneficiary has been cleared, and asks us to describe this as our official position. Assess that description and recommend a workable response grounded in our own statement.
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

**ASSISTANT — supervised target**

<!-- exact:target:train-bra-shutdown:0 -->

> Brazil sponsored the initiative and voted in favour of resolution 2664. It values predictable humanitarian operations and protection of civilians harmed by ill-devised sanctions, while recognizing useful sanctions and legitimate security concerns. A universal delivery suspension would undermine the humanitarian purpose Brazil identifies; it is not a recorded Brazilian implementation requirement. I recommend prompt relief with proportionate risk checks and reporting. India’s specific proactive 1267 Monitoring Team request should not become a fabricated Brazilian red line. These safeguards are my proposal, not a guaranteed Brazilian commitment to approve a future text.

<!-- /exact -->

Chat-template options: `{"enable_thinking": false}`
