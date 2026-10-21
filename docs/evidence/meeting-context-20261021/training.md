# Four complete authentic scenario/delegation SFT sequences

[Evidence index](README.md)

The readable-marker sequence below was the actual fitting representation. Prefix and target header are masked; the full authentic completion plus existing record-end token is supervised. These are four targets repeated 32 times: 128 updates, not 128 unique examples.

[Original tokenized training pack](../../../research/scenario-role-sft-20261017-v1/pack/train.jsonl)

## 9214-GBR

<details>
<summary>Complete masked scenario, chronological history and requested-role prefix</summary>

<!-- exact:prompt:scenario-training:9214-GBR -->

> &lt;|scenario|&gt;
> UN Security Council; New York; 9 December 2022, 10 a.m.
> Agenda: General issues relating to sanctions.
> Document before the Council at opening: draft S/2022/925.
> Opening phase: before voting. Later phase changes are supplied only through preceding record events.
> History window: all earlier body turns are shown; cover metadata is represented in this scenario.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=NONE; institution=UNSC; capacity=record_event; representative=UN verbatim record; phase=before_vote
> &lt;|speech|&gt;
> The meeting was called to order at 10 a.m. Adoption of the agenda The agenda was adopted. General issues relating to sanctions&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=&lt;|country_IND|&gt;; institution=UNSC; capacity=council_president; representative=Mrs. Kamboj; phase=before_vote
> &lt;|speech|&gt;
> In accordance with rule 37 of the Council’s provisional rules of procedure, I invite the representatives of Australia, Austria, the Bahamas, Belgium, Bulgaria Canada, Croatia, Cyprus, Czechia, Denmark, the Dominican Republic, Estonia, Fiji, Finland, Germany, Greece, Iceland, Italy, Latvia, Lesotho, Liechtenstein, Luxembourg, Malta, Marshall Islands, New Zealand, Portugal, Romania, Samoa, San Marino, Slovenia, Spain, Switzerland and Ukraine to participate in this meeting. The Security Council will now begin its consideration of the item on its agenda. Members of the Council have before them document S/2022/925, which contains the text of a draft resolution submitted by Albania, Australia, Austria, the Bahamas, Belgium, Brazil, Bulgaria, Canada, Croatia, Cyprus, Czechia, Denmark, the Dominican Republic, Estonia, Fiji, Finland, France, Germany, Greece, Iceland, Ireland, Italy, Latvia, Lesotho, Liechtenstein, Luxembourg, Malta, Marshall Islands, New Zealand, Norway, Portugal, Romania, Samoa, San Marino, Slovenia, Spain, Switzerland, Ukraine, the United Kingdom of Great Britain and Northern Ireland and the United States of America. The Council is ready to proceed to the vote on the draft resolution before it. I shall now give the floor to those members of the Council who wish to make statements before the voting.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=USA; institution=UNSC; capacity=national_delegation; representative=Mrs. Thomas-Greenfield; phase=before_vote
> &lt;|speech|&gt;
> As this if my first time in the Chamber since you took over as President, Madam, I would like to welcome your presidency. We look forward to working with you. I also want to take the opportunity to thank our colleagues from Ghana for their presidency over the previous month. The United States is proud to introduce, together with Ireland, this landmark draft resolution (S/2022/925), which will save lives. As the world’s leading global humanitarian donor, the United States has always understood the centrality of humanitarian
>
> access for aid delivery. Our partners operate in dangerous environments, and they face serious risks. We hope the members of the Security Council will vote in favour of this draft resolution, because we must all do everything in our power to help humanitarian partners reach the world’s most vulnerable, regardless of where they live, who they live with and who controls their territory. The United States decided to pursue this initiative after extensive thought and deliberation. We made a point to proactively reach out and listen to the United Nations and the non-governmental organization community. We heard about the challenges they face and how we, as the international community, can best support their life-saving efforts. They told us that the second-order impacts of some United Nations sanctions were creating an impediment to humanitarian assistance in the field. To be clear, this is not related to the merits of the sanctions themselves. The Council has reached consensus repeatedly in upholding United Nations sanctions as an effective foreign policy tool to constrain bad actors, terrorists and human rights abusers. Our goal is always to stop terrorists and human rights abusers by using a legitimate tool to maintain peace and security, but still allow life-saving humanitarian efforts to continue for those in need. Bilaterally, in response to the concerns of the humanitarian community, the United States has already stepped up. The United States Department of the Treasury has issued licenses to facilitate humanitarian aid and the provision of food and medicine. We reached out directly to banks to explain how humanitarian activities would be carved out from individual sanctions regimes when applicable. And we have offered letters to further clarify our position. The humanitarian community told us that those efforts have been incredibly helpful. And we know we have more work to do on this front. But the humanitarian community also shared that United Nations sanctions still need to be addressed to ensure that unintentional, second-order impacts do not impede their work. They asked for a clear, standard carveout of humanitarian assistance and activities to meet basic human needs for all United Nations sanctions regimes. And that is exactly what we are voting on today. This draft resolution is impartial. It makes sense. And it will save innocent lives all around the world.
>
> It is what the humanitarian community has asked us for. And I urge members to vote in favour and to support this life-saving, landmark commitment to humanitarian work.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=&lt;|country_IND|&gt;; institution=UNSC; capacity=council_president; representative=Mrs. Kamboj; phase=before_vote
> &lt;|speech|&gt;
> I shall put the draft resolution to the vote now.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=NONE; institution=UNSC; capacity=record_event; representative=UN verbatim record; phase=vote_event
> &lt;|speech|&gt;
> A vote was taken by show of hands. In favour: Albania, Brazil, China, France, Gabon, Ghana, Ireland, Kenya, Mexico, Norway, Russian Federation, United Arab Emirates, United Kingdom of Great Britain and Northern Ireland, United States of America Against: None Abstaining: India&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=&lt;|country_IND|&gt;; institution=UNSC; capacity=council_president; representative=Mrs. Kamboj; phase=after_vote
> &lt;|speech|&gt;
> The draft resolution received 14 votes in favour, none against and one abstention. The draft resolution has been adopted as resolution 2664 (2022). I shall now give the floor to those members of the Council who wish to make statements after the voting.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=IRL; institution=UNSC; capacity=national_delegation; representative=Mr. Mythen; phase=after_vote
> &lt;|speech|&gt;
> Ireland welcomes the adoption of resolution 2664 (2022), which introduces a horizontal humanitarian carveout to Security Council sanctions regimes. This is a landmark resolution. As co-penholder with the United States, we took time over its negotiation. We are conscious that its effect on the United Nations sanctions landscape will be significant. With this resolution, we diminish the unintended consequences of sanctions without diminishing United Nations sanctions themselves. The protection of the humanitarian space is an overarching priority for Ireland, and this vote is therefore of particular significance. From our extensive outreach, it is clear that Council members share the desire to mitigate any inadvertent effects that sanctions might have on humanitarian activity. More than 300 million people will require humanitarian aid next year to survive. More than 800 million people worldwide do not have enough food to eat. The resolution safeguards humanitarian action to assist them in contexts in which the Council has also had to impose sanctions. It demonstrates that
>
> the Council can still take action to respond to those in greatest need. It is clear that the use of sanctions has faced criticism in recent years. A key factor in that has been reports from humanitarian actors that sanctions can impede their work. Although it was never the Council’s intention, the reality is that the imposition of United Nations sanctions does not always coexist harmoniously with the need to ensure that legitimate humanitarian activity is uninterrupted. Today’s vote marks a turning point. Resolution 2664 (2022) exempts humanitarian assistance and other activities that support basic human needs from the scope of asset-freezing measures imposed by United Nations sanctions. That provides certainty and clarity for humanitarian actors, donors and implementing partners alike by confirming in one horizontal resolution that the provision of humanitarian aid is permitted. The resolution, while significant, is not a panacea. It may take some time for its effects to be implemented by States and executed by all relevant stakeholders. More broadly, there remains work to do on other aspects of United Nations sanctions, such as due process. We look forward to supporting the Council’s work in that regard moving forward, including as a member of the Group of Like-Minded States on Targeted Sanctions. However, for today, we can rest assured that the Council has taken decisive action in response to appeals by humanitarians worldwide. The resolution will have a tangible, positive impact for those working in some of the most challenging environments across the globe, who can now continue helping the world’s most vulnerable with the knowledge that even where United Nations sanctions are in effect, their activities are permitted. Lastly, we want to thank all Council members for their engagement on this important file and the humanitarian community for its long-term advocacy and technical support for this effort. We also thank the more than 40 Member States that sponsored the resolution, demonstrating that the commitment to protecting the humanitarian space is a global concern. And we recognize the Secretariat for its support.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=&lt;|country_GBR|&gt;; institution=UNSC; capacity=national_delegation; representative=Dame Barbara Woodward; phase=after_vote
> &lt;|speech|&gt;
>

<!-- /exact -->


</details>

**Complete supervised authentic target, including record-end marker:**

<!-- exact:target:scenario:9214-GBR -->

> The United Kingdom congratulates the United States and Ireland on the Council’s adoption of resolution 2664 (2022) today. We have been unequivocal in our support throughout the development of the resolution. As
>
> humanitarian week at the United Nations draws to a close and humanitarian needs around the world are soaring, I am proud that the Security Council is working together to support vital humanitarian aid delivery around the world. Sanctions are a core part of the Council’s toolkit. In line with the Charter of the United Nations, they are rightly used to address threats to international peace and security. Whether the problem is violent gangs in Haiti or extremist groups such as Al-Shabaab and Al-Qaida, we have used sanctions to stop weapons flows and tackle terrorism. The resolution will provide that certain activities necessary for humanitarian assistance or in support of basic human needs, when carried out by specified organizations, do not violate United Nations asset freezes. The resolution will help save lives by providing clarity, to help ensure that humanitarian providers and their service providers can continue to help the most vulnerable. It will support getting aid to those in need more effectively. The United Kingdom is pleased to have voted in favour and to have been a sponsor of resolution 2664 (2022).&lt;|im_end|&gt;

<!-- /exact -->

<details>
<summary>Original history-window provenance</summary>

````json
{
  "source": "9214",
  "source_sha256": "6419b5f2a0042294447b748e1b74f5d01116e871a62f238dac022b4e673c0fa9",
  "window": [
    1846,
    11735
  ],
  "turns": [
    {
      "start": 0,
      "content_start": 0,
      "end": 126,
      "country": "NONE",
      "capacity": "record_event",
      "representative": "UN verbatim record",
      "institution": "UNSC",
      "phase": "before_vote"
    },
    {
      "start": 127,
      "content_start": 142,
      "end": 1471,
      "country": "IND",
      "capacity": "council_president",
      "representative": "Mrs. Kamboj",
      "institution": "UNSC",
      "phase": "before_vote"
    },
    {
      "start": 1472,
      "content_start": 1523,
      "end": 4631,
      "country": "USA",
      "capacity": "national_delegation",
      "representative": "Mrs. Thomas-Greenfield",
      "institution": "UNSC",
      "phase": "before_vote"
    },
    {
      "start": 4632,
      "content_start": 4647,
      "end": 4696,
      "country": "IND",
      "capacity": "council_president",
      "representative": "Mrs. Kamboj",
      "institution": "UNSC",
      "phase": "before_vote"
    },
    {
      "start": 4697,
      "content_start": 4697,
      "end": 4973,
      "country": "NONE",
      "capacity": "record_event",
      "representative": "UN verbatim record",
      "institution": "UNSC",
      "phase": "vote_event"
    },
    {
      "start": 4974,
      "content_start": 4989,
      "end": 5241,
      "country": "IND",
      "capacity": "council_president",
      "representative": "Mrs. Kamboj",
      "institution": "UNSC",
      "phase": "after_vote"
    },
    {
      "start": 5242,
      "content_start": 5264,
      "end": 8507,
      "country": "IRL",
      "capacity": "national_delegation",
      "representative": "Mr. Mythen",
      "institution": "UNSC",
      "phase": "after_vote"
    },
    {
      "start": 8508,
      "content_start": 8548,
      "end": 9889,
      "country": "GBR",
      "capacity": "national_delegation",
      "representative": "Dame Barbara Woodward",
      "institution": "UNSC",
      "phase": "after_vote"
    }
  ],
  "target": [
    10394,
    11735
  ],
  "prior_history_omitted": false,
  "earlier_unlabelled_tokens": 1640
}
````


</details>

## 9214-IND

<details>
<summary>Complete masked scenario, chronological history and requested-role prefix</summary>

<!-- exact:prompt:scenario-training:9214-IND -->

> &lt;|scenario|&gt;
> UN Security Council; New York; 9 December 2022, 10 a.m.
> Agenda: General issues relating to sanctions.
> Document before the Council at opening: draft S/2022/925.
> Opening phase: before voting. Later phase changes are supplied only through preceding record events.
> History window: all earlier body turns are shown; cover metadata is represented in this scenario.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=NONE; institution=UNSC; capacity=record_event; representative=UN verbatim record; phase=before_vote
> &lt;|speech|&gt;
> The meeting was called to order at 10 a.m. Adoption of the agenda The agenda was adopted. General issues relating to sanctions&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=&lt;|country_IND|&gt;; institution=UNSC; capacity=council_president; representative=Mrs. Kamboj; phase=before_vote
> &lt;|speech|&gt;
> In accordance with rule 37 of the Council’s provisional rules of procedure, I invite the representatives of Australia, Austria, the Bahamas, Belgium, Bulgaria Canada, Croatia, Cyprus, Czechia, Denmark, the Dominican Republic, Estonia, Fiji, Finland, Germany, Greece, Iceland, Italy, Latvia, Lesotho, Liechtenstein, Luxembourg, Malta, Marshall Islands, New Zealand, Portugal, Romania, Samoa, San Marino, Slovenia, Spain, Switzerland and Ukraine to participate in this meeting. The Security Council will now begin its consideration of the item on its agenda. Members of the Council have before them document S/2022/925, which contains the text of a draft resolution submitted by Albania, Australia, Austria, the Bahamas, Belgium, Brazil, Bulgaria, Canada, Croatia, Cyprus, Czechia, Denmark, the Dominican Republic, Estonia, Fiji, Finland, France, Germany, Greece, Iceland, Ireland, Italy, Latvia, Lesotho, Liechtenstein, Luxembourg, Malta, Marshall Islands, New Zealand, Norway, Portugal, Romania, Samoa, San Marino, Slovenia, Spain, Switzerland, Ukraine, the United Kingdom of Great Britain and Northern Ireland and the United States of America. The Council is ready to proceed to the vote on the draft resolution before it. I shall now give the floor to those members of the Council who wish to make statements before the voting.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=USA; institution=UNSC; capacity=national_delegation; representative=Mrs. Thomas-Greenfield; phase=before_vote
> &lt;|speech|&gt;
> As this if my first time in the Chamber since you took over as President, Madam, I would like to welcome your presidency. We look forward to working with you. I also want to take the opportunity to thank our colleagues from Ghana for their presidency over the previous month. The United States is proud to introduce, together with Ireland, this landmark draft resolution (S/2022/925), which will save lives. As the world’s leading global humanitarian donor, the United States has always understood the centrality of humanitarian
>
> access for aid delivery. Our partners operate in dangerous environments, and they face serious risks. We hope the members of the Security Council will vote in favour of this draft resolution, because we must all do everything in our power to help humanitarian partners reach the world’s most vulnerable, regardless of where they live, who they live with and who controls their territory. The United States decided to pursue this initiative after extensive thought and deliberation. We made a point to proactively reach out and listen to the United Nations and the non-governmental organization community. We heard about the challenges they face and how we, as the international community, can best support their life-saving efforts. They told us that the second-order impacts of some United Nations sanctions were creating an impediment to humanitarian assistance in the field. To be clear, this is not related to the merits of the sanctions themselves. The Council has reached consensus repeatedly in upholding United Nations sanctions as an effective foreign policy tool to constrain bad actors, terrorists and human rights abusers. Our goal is always to stop terrorists and human rights abusers by using a legitimate tool to maintain peace and security, but still allow life-saving humanitarian efforts to continue for those in need. Bilaterally, in response to the concerns of the humanitarian community, the United States has already stepped up. The United States Department of the Treasury has issued licenses to facilitate humanitarian aid and the provision of food and medicine. We reached out directly to banks to explain how humanitarian activities would be carved out from individual sanctions regimes when applicable. And we have offered letters to further clarify our position. The humanitarian community told us that those efforts have been incredibly helpful. And we know we have more work to do on this front. But the humanitarian community also shared that United Nations sanctions still need to be addressed to ensure that unintentional, second-order impacts do not impede their work. They asked for a clear, standard carveout of humanitarian assistance and activities to meet basic human needs for all United Nations sanctions regimes. And that is exactly what we are voting on today. This draft resolution is impartial. It makes sense. And it will save innocent lives all around the world.
>
> It is what the humanitarian community has asked us for. And I urge members to vote in favour and to support this life-saving, landmark commitment to humanitarian work.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=&lt;|country_IND|&gt;; institution=UNSC; capacity=council_president; representative=Mrs. Kamboj; phase=before_vote
> &lt;|speech|&gt;
> I shall put the draft resolution to the vote now.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=NONE; institution=UNSC; capacity=record_event; representative=UN verbatim record; phase=vote_event
> &lt;|speech|&gt;
> A vote was taken by show of hands. In favour: Albania, Brazil, China, France, Gabon, Ghana, Ireland, Kenya, Mexico, Norway, Russian Federation, United Arab Emirates, United Kingdom of Great Britain and Northern Ireland, United States of America Against: None Abstaining: India&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=&lt;|country_IND|&gt;; institution=UNSC; capacity=council_president; representative=Mrs. Kamboj; phase=after_vote
> &lt;|speech|&gt;
> The draft resolution received 14 votes in favour, none against and one abstention. The draft resolution has been adopted as resolution 2664 (2022). I shall now give the floor to those members of the Council who wish to make statements after the voting.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=IRL; institution=UNSC; capacity=national_delegation; representative=Mr. Mythen; phase=after_vote
> &lt;|speech|&gt;
> Ireland welcomes the adoption of resolution 2664 (2022), which introduces a horizontal humanitarian carveout to Security Council sanctions regimes. This is a landmark resolution. As co-penholder with the United States, we took time over its negotiation. We are conscious that its effect on the United Nations sanctions landscape will be significant. With this resolution, we diminish the unintended consequences of sanctions without diminishing United Nations sanctions themselves. The protection of the humanitarian space is an overarching priority for Ireland, and this vote is therefore of particular significance. From our extensive outreach, it is clear that Council members share the desire to mitigate any inadvertent effects that sanctions might have on humanitarian activity. More than 300 million people will require humanitarian aid next year to survive. More than 800 million people worldwide do not have enough food to eat. The resolution safeguards humanitarian action to assist them in contexts in which the Council has also had to impose sanctions. It demonstrates that
>
> the Council can still take action to respond to those in greatest need. It is clear that the use of sanctions has faced criticism in recent years. A key factor in that has been reports from humanitarian actors that sanctions can impede their work. Although it was never the Council’s intention, the reality is that the imposition of United Nations sanctions does not always coexist harmoniously with the need to ensure that legitimate humanitarian activity is uninterrupted. Today’s vote marks a turning point. Resolution 2664 (2022) exempts humanitarian assistance and other activities that support basic human needs from the scope of asset-freezing measures imposed by United Nations sanctions. That provides certainty and clarity for humanitarian actors, donors and implementing partners alike by confirming in one horizontal resolution that the provision of humanitarian aid is permitted. The resolution, while significant, is not a panacea. It may take some time for its effects to be implemented by States and executed by all relevant stakeholders. More broadly, there remains work to do on other aspects of United Nations sanctions, such as due process. We look forward to supporting the Council’s work in that regard moving forward, including as a member of the Group of Like-Minded States on Targeted Sanctions. However, for today, we can rest assured that the Council has taken decisive action in response to appeals by humanitarians worldwide. The resolution will have a tangible, positive impact for those working in some of the most challenging environments across the globe, who can now continue helping the world’s most vulnerable with the knowledge that even where United Nations sanctions are in effect, their activities are permitted. Lastly, we want to thank all Council members for their engagement on this important file and the humanitarian community for its long-term advocacy and technical support for this effort. We also thank the more than 40 Member States that sponsored the resolution, demonstrating that the commitment to protecting the humanitarian space is a global concern. And we recognize the Secretariat for its support.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=&lt;|country_GBR|&gt;; institution=UNSC; capacity=national_delegation; representative=Dame Barbara Woodward; phase=after_vote
> &lt;|speech|&gt;
> The United Kingdom congratulates the United States and Ireland on the Council’s adoption of resolution 2664 (2022) today. We have been unequivocal in our support throughout the development of the resolution. As
>
> humanitarian week at the United Nations draws to a close and humanitarian needs around the world are soaring, I am proud that the Security Council is working together to support vital humanitarian aid delivery around the world. Sanctions are a core part of the Council’s toolkit. In line with the Charter of the United Nations, they are rightly used to address threats to international peace and security. Whether the problem is violent gangs in Haiti or extremist groups such as Al-Shabaab and Al-Qaida, we have used sanctions to stop weapons flows and tackle terrorism. The resolution will provide that certain activities necessary for humanitarian assistance or in support of basic human needs, when carried out by specified organizations, do not violate United Nations asset freezes. The resolution will help save lives by providing clarity, to help ensure that humanitarian providers and their service providers can continue to help the most vulnerable. It will support getting aid to those in need more effectively. The United Kingdom is pleased to have voted in favour and to have been a sponsor of resolution 2664 (2022).&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=&lt;|country_BRA|&gt;; institution=UNSC; capacity=national_delegation; representative=De Almeida Filho; phase=after_vote
> &lt;|speech|&gt;
> I would like to thank Ireland and the United States for this important initiative, which we were glad to sponsor. Brazil’s vote in favour of resolution 2664 (2022) is an expression of its recognition that today we adopted a resolution that may contribute substantially to the work of the Security Council. We have come a long way since 1966, when the Security Council started establishing sanctions regimes. Along the way, some mistakes were made. We have seen how ill-devised sanctions can disproportionately affect vulnerable populations, worsen food insecurity, increase inflation and hinder neutral, impartial, independent and humane humanitarian assistance. Although sanctions may be an important tool for the maintenance of international peace and security, we have noticed how their misuse can stoke tensions rather than defuse them. We have also witnessed how they can spare those whom they were originally intended to target, while unintentionally punishing those who should be protected — innocent civilians, women and children in the throes of conflict. It was high time to improve the way in which the Security Council makes use of its coercive power to address threats to international peace and security. Brazil is proud to be a member of the Security Council at this moment when it decides to take action to help those in need. The resolution will enable
>
> humanitarian providers to carry out their essential activities in more predictable conditions. Above all, it will benefit millions of civilians who have had the misfortune to live under sanctions regimes, twice punished by them and by the action of the designated entities and individuals. Furthermore, the resolution is in line with recent developments in international jurisprudence. The International Court of Justice recently made the case for the need to safeguard humanitarian needs even in circumstances when sanctions are in place. I also note that the resolution takes into account legitimate security concerns that Member States voiced during the negotiations. It strikes a fine balance between the need for sanctions to be put in force to prevent and combat threats, on the one hand, and on the other, the duty of the international community to protect civilians whose well-being should be the ultimate goal of the Security Council in discharging its mandate to maintain international peace and security.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=NOR; institution=UNSC; capacity=national_delegation; representative=Heimerback; phase=after_vote
> &lt;|speech|&gt;
> Norway voted in favour of and co-sponsored resolution 2664 (2022), and we would like to express our appreciation to Ireland and the United States for proposing it. The humanitarian community has consistently documented and called attention to the unintended negative consequences of sanctions for principled humanitarian action and the consequent human costs for people in need of humanitarian assistance and protection. We therefore wholeheartedly support the resolution. Norway attaches great importance to ensuring that sanctions are well designed, and we have consistently advocated broad humanitarian exemptions. We are pleased that the practices of the Security Council have developed on such issues in the past few years. The carveout will, in our view, be effective, as it covers all sanctions regimes and is clear in terms of the actors and activities that it covers. We trust that it will provide the necessary clarity to all relevant actors, from Member States to humanitarian actors, as well as providers from the private and financial sectors that humanitarian actors need to rely on. It is crucial that Member States now take the necessary steps to implement the exception in their domestic legal systems. Implementing the resolution will help save lives and alleviate the suffering of people affected by armed conflict.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=RUS; institution=UNSC; capacity=national_delegation; representative=Evstigneeva; phase=after_vote
> &lt;|speech|&gt;
> The Russian Federation voted in favour of resolution 2664 (2022) on humanitarian exemptions to asset freezes for the purpose of extending humanitarian assistance. Security Council sanctions are one of the strongest forms of reacting to threats to peace, and they need to be applied very carefully. They need to be impeccably justified and nuanced. It is unacceptable to use them as a means of punishment. They need to reflect the situation in countries on which sanctions are imposed and be in line with relevant political process. However, it is unfortunately not always the case that the Council respects these guidelines, which has to do, in many instances in recent decades, and at the instigation of Western States, with the Security Council’s fondness for the use of sanctions instruments. According to our analysis, many of the sanctions regimes in place today — in the Sudan, in the Democratic Republic of the Congo, in the Central African Republic, in South Sudan and in Somalia — are out of sync with the actual situations on the ground, and they impede the national Governments’ plans for State-building and their countries’ socioeconomic development. We regret that the issue of humanitarian exemptions has, as a matter of principle, become such a topical issue. Ideally, a Security Council restriction should not affect humanitarian assistance, which needs to be conducted in line with United Nations humanitarian principles and in coordination with legitimate Governments. But in practice that is far from being the case. We have consistently spoken in favour of adopting a comprehensive approach to this issue and if we have to make a decision about humanitarian exemptions, then we think it is imperative to make sure that they function smoothly and are free of any kind of a politicized stance by an individual State. A very good example for us of a timely measure undertaken by the Security Council in this regard is resolution 2615 (2021), which provided for the extension without delay of humanitarian assistance to Afghanistan using all possible channels and containing no sanctions restrictions. We have called upon our peers on many an occasion to think about ways of minimizing the broad interpretations of sanctions provisions, including through clarifying the terminology. We have also called on them to conduct an impartial evaluation of the humanitarian consequences of international
>
> restrictions. Our ideas have been voiced in detail at key international forums, including within the framework of the debate on sanctions during of our Security Council presidency in February 2022 (see S/PV.8962). We are pleased that these many calls of ours were finally heeded by those who, for many years now and under various pretexts, kept postponing the resolution of this issue. We in turn have been very constructive in our approach to the negotiating process from the beginning, and the resolution we adopted today now includes provisions we proposed in relation to assessing the potential humanitarian consequences prior to the Security Council taking a decision about imposing a sanctions regime; the readiness to conduct a review to correct or stop sanctions regimes where it becomes necessary to do so; and emphasizing the fact that sanctions are temporary in nature. Today’s resolution also contains a request to the Secretary-General to prepare a written report about unintended adverse humanitarian consequences of Security Council sanctions. As regards the use of humanitarian exemptions under the sanctions regime imposed by the Security Council Committee established pursuant to resolutions 1267 (1999), 1989 (2011) and 2253 (2015) concerning Islamic State in Iraq and the Levant (Da’esh), Al-Qaida and associated individuals, groups, undertakings and entities, our thinking was that it is very important to ensure that the 1267 Committee conducts monitoring with the help of the Analytical Support and Sanctions Monitoring Team in order to make sure that the assistance does not end up in the hands of terrorists or unchecked organizations on the ground. At the same time, the resolution does not cover the issue of so-called secondary unilateral restrictions, which are introduced on top of sanctions imposed by the Council. These sanctions are a very serious impediment to the full functioning of humanitarian exemptions. Under the threat of ending up with very severe national or even extraterritorial restrictions, agencies decline signing contracts to purchase humanitarian assistance that is allowed by the Security Council or to transport it. Difficulties also arise as to cargo insurance, and banks are saying that it is impossible for them to conduct transactions. These problems are very clearly seen in the example of the Democratic People’s Republic of Korea. The secondary sanctions imposed by major
>
> Western countries create an atmosphere of toxicity around Pyongyang and impede their willingness to cooperate in areas that are not subject to international restrictions. The fact that this issue is not at all resolved in resolution 2664 (2022) , and that the resolution had to be adopted today, is a major drawback. It is yet another example of hypocrisy and the cost of that hypocrisy, namely, the well-being and lives of a large number of people. We are not surprised by that, however, given the national policy of the sponsors of the resolution. We in turn think that Security Council sanctions are the only legitimate kind of sanctions. The use of unilateral coercive measures by individual countries or groups of countries are, in our view, an intrusion on Council prerogatives and undermine the norms and institutions of international law. The extraterritorial effect of sanctions contravenes basic norms of international law, but what can we say in this context if the Western countries, in their frenzied fondness for sanctions against Russia, including on agricultural products and fertilizers, are ready to destabilize world markets for food and energy resources and break all kinds of supply chains? We will not only continue paying attention to the issue of unilateral illegitimate measures, but we will keep on seeking to expand the number of countries that are against them, because this situation compounds the difficulties experienced in many countries. In conclusion, I would like to emphasize that the area covered by resolution 2664 (2022) is fairly limited. The resolution does not resolve many of the issues that exist when it comes to Security Council sanctions, but if it can help humanitarians in certain countries to be more effective in providing assistance to the most vulnerable people, that already in itself is a worthwhile result.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=CHN; institution=UNSC; capacity=national_delegation; representative=Geng Shuang; phase=after_vote
> &lt;|speech|&gt;
> Sanctions are a unique tool granted to the Security Council by the United Nations Charter. China has always maintained that the Council should approach the issue of sanctions in a prudent and responsible manner and avoid abuses that could have negative humanitarian implications. In February, at the Security Council open meeting on sanctions (see S/PV.8962), China proposed that the Security Council should establish a standing exemption mechanism for certain humanitarian agencies and humanitarian assistance. The proposal was widely supported by many countries.
>
> We are pleased to see that Ireland and the United States responded to the appeals and demands of all parties and introduced today’s resolution on humanitarian exemptions. China supports the Security Council’s action to improve the sanctions regime by actively participating in consultations and promoting the improvement of the draft. We just voted in favour of the resolution. Resolution 2664 (2022) clarifies the relationship between humanitarian assistance and sanctions and dispels the concerns and worries of the providers of assistance. We hope that States Members of the United Nations and international humanitarian agencies will actively implement the humanitarian exemptions provided for in the resolution and prevent an expanded interpretation or excessive implementation of sanctions. We also hope that the international community, especially developed countries, scale up humanitarian assistance and provide more substantive support for humanitarian operations. At the same time, the international community should pay great attention to the negative impact of unilateral sanctions on humanitarian operations. Undeniably, the greatest legal and political risks faced by humanitarian agencies do not come from Security Council sanctions, but from increasing unilateral sanctions and the long-arm jurisdiction of some countries. In reality, they often trigger great chaos and disastrous situations and thereby create or exacerbate humanitarian crises. We hope that the countries concerned will uphold the spirit of humanity embodied in the just-adopted resolution 2664 (2022) and stop imposing unilateral sanctions outside of the Council’s sanctions framework as soon as possible. In conclusion, I would like to stress that the Security Council should establish clear and feasible exit arrangements for the existing sanctions mechanisms, conduct regular reviews and adjust or lift sanctions in a timely manner. The humanitarian exemption resolution just adopted by the Security Council must not lead to the perpetuation and permanent adjustment of some sanctions mechanisms that should have been adjusted long ago. China will work with all members of the Security Council to continue to promote the improvement of sanctions mechanisms in a responsible manner so as to minimize the negative impact of sanctions on humanitarian activities and people’s livelihoods.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=ALB; institution=UNSC; capacity=national_delegation; representative=Dautllari; phase=after_vote
> &lt;|speech|&gt;
> Let me begin by expressing my delegation’s appreciation for the leadership of the co-penholders, the United States of America and Ireland, as well as the constructive engagement of other members of the Security Council. Albania voted in favour of, and co-sponsored, resolution 2664 (2022) today. We welcome its adoption. It is a milestone development of the Council in making the sanctions regime more effective by minimizing its potential unintended consequences and by strengthening its legitimacy. Today’s adoption is a clear example of how the Security Council can be responsive to the concerns and issues raised by State and non-State representatives with regard to the undesired effects that different sanctions regimes may have on the provision of humanitarian assistance. While reiterating our position that sanctions are an important tool under the Charter of the United Nations in maintaining and restoring international peace and security, we are very pleased that the Council demonstrated today that it is able not only to listen to such expressions of concern, but also act upon them by demonstrating its commitment that the implementation of all measures imposed by the Council be consistent with international human rights law and international humanitarian law. We are confident that today’s resolution will not only provide humanitarian actors the necessary clarity to effectively execute their humanitarian operations, but will also demonstrate the ability of the Security Council to act swiftly and effectively.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=ARE; institution=UNSC; capacity=national_delegation; representative=Abushahab; phase=after_vote
> &lt;|speech|&gt;
> The United Arab Emirates joined the Security Council with a commitment to support humanitarian efforts. During the past 11 months, we have worked in support of humanitarian exemptions to several sanctions regimes. The United Arab Emirates is therefore pleased that today’s landmark humanitarian resolution 2664 (2022) was adopted. We thank Ireland and the United States of America, as well as all our colleagues on the Council, for the work undertaken and the outcome achieved. As humanitarian needs rise around the world, we must do all that we can to enable aid to reach people in need, while ensuring that the appropriate safeguards are in place to prevent any possible misuse of humanitarian
>
> assistance. Today’s resolution is an important step towards ensuring that legitimate humanitarian aid is not inhibited by sanctions measures. Supporting humanitarian causes is part of the national ethos of the United Arab Emirates. Our humanitarian aid comes from the Government, as well as our country’s many charitable organizations. The United Arab Emirates works closely with the United Nations humanitarian agencies, the Emirates Red Crescent, our own national non-profit groups and local organizations doing valuable humanitarian work. While we are pleased that the resolution covers many different forms of aid delivery, including the critical work done by the United Nations and national Red Cross and Red Crescent societies, we recognize that, across the globe, food, medical and other aid is delivered by different actors and by different means. Although most aid providers are covered by this resolution, some genuine humanitarian organizations may be left out. While we recognize this resolution as a milestone in the Security Council’s support for people in need of humanitarian assistance, we nevertheless see some potential for overcompliance. We therefore believe that it is important to regularly review how the resolution is being implemented on the ground and adjust it as needed. The goal is to ensure that all parts and partners of the humanitarian system are not impeded by sanctions measures and that this resolution’s safeguards remain fit for purpose. Going forward, our collective responsibility will be to shepherd the full implementation of resolution 2664 (2022), including by providing guidance to Member States, the private sector and other actors. The United Arab Emirates will continue to support the ability of humanitarian organizations to do their life-saving work throughout our term on the Security Council and beyond.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=&lt;|country_IND|&gt;; institution=UNSC; capacity=council_president; representative=Mrs. Kamboj; phase=after_vote
> &lt;|speech|&gt;
> I shall now make a statement as the representative of India.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=&lt;|country_IND|&gt;; institution=UNSC; capacity=national_delegation; representative=Mrs. Kamboj; phase=after_vote
> &lt;|speech|&gt;
>

<!-- /exact -->


</details>

**Complete supervised authentic target, including record-end marker:**

<!-- exact:target:scenario:9214-IND -->

> The measures imposed by the Security Council under Article 41 of the Charter of the United Nations are provisional in nature and not permanent. The sanctions regimes cannot be an end in themselves. In their implementation, sanctions regimes must ensure that they have the intended impact and do not further exacerbate the suffering of the populations
>
> at the receiving end. Neither can the legitimate trade and economic activities of the State concerned and its regional partners be ignored. In addition, the unintended consequences of sanctions measures, including the humanitarian consequences, increasingly emphasized by Member States and other stakeholders, require effective redress. In that context, India engaged constructively in the negotiations on resolution 2664 (2022). The resolution provides a carveout from sanctions in support of the timely delivery of humanitarian assistance or to support other activities meeting basic human needs. The resolution is also intended to ensure the much-needed predictability and safeguards to humanitarian agencies. However, India will call for caution and due diligence to be exercised in extending humanitarian assistance to proscribed entities under the regime established pursuant to resolution 1267 (1999) that continue to thrive, with full State hospitality, in territories universally acknowledged as terrorist havens by the international community. Our concerns emanate from proven instances of terrorist groups taking full advantage of such humanitarian carveouts and making a mockery of sanctions regimes, including that of the Committee pursuant to resolutions 1267 (1999) 1989 (2011) and 2253 (2015), concerning Islamic State in Iraq and the Levant (Da’esh), Al-Qaida and associated individuals, groups, undertakings and entities. There have also been several cases of terrorist groups in our
>
> neighbourhood, including those listed by the Security Council, reincarnating themselves as humanitarian organizations and civil-society groups precisely to evade such sanctions. Those terrorist organizations use the umbrella of the humanitarian assistance space to raise funds and recruit fighters. As we said during the negotiations, we reiterate that, under no circumstances, should the garb of humanitarian cover intended to be provided by those exemptions be misused by proscribed terrorist groups to expand their terror activities in the region and beyond. More important, such exemptions must not facilitate the mainstreaming of terror entities in the political space in our region. Due diligence and extreme caution in the implementation of this resolution is therefore an absolute must. For that very reason, India sought in the text of the resolution a proactive role for the 1267 Monitoring Team, coupled with robust reporting standards and mechanisms. We regret that those specific concerns were not fully addressed in the final text adopted today. We hope that that shortcoming will be corrected in the future, as and when we review the implementation and feedback from the Monitoring Team on this resolution.&lt;|im_end|&gt;

<!-- /exact -->

<details>
<summary>Original history-window provenance</summary>

````json
{
  "source": "9214",
  "source_sha256": "6419b5f2a0042294447b748e1b74f5d01116e871a62f238dac022b4e673c0fa9",
  "window": [
    1846,
    32567
  ],
  "turns": [
    {
      "start": 0,
      "content_start": 0,
      "end": 126,
      "country": "NONE",
      "capacity": "record_event",
      "representative": "UN verbatim record",
      "institution": "UNSC",
      "phase": "before_vote"
    },
    {
      "start": 127,
      "content_start": 142,
      "end": 1471,
      "country": "IND",
      "capacity": "council_president",
      "representative": "Mrs. Kamboj",
      "institution": "UNSC",
      "phase": "before_vote"
    },
    {
      "start": 1472,
      "content_start": 1523,
      "end": 4631,
      "country": "USA",
      "capacity": "national_delegation",
      "representative": "Mrs. Thomas-Greenfield",
      "institution": "UNSC",
      "phase": "before_vote"
    },
    {
      "start": 4632,
      "content_start": 4647,
      "end": 4696,
      "country": "IND",
      "capacity": "council_president",
      "representative": "Mrs. Kamboj",
      "institution": "UNSC",
      "phase": "before_vote"
    },
    {
      "start": 4697,
      "content_start": 4697,
      "end": 4973,
      "country": "NONE",
      "capacity": "record_event",
      "representative": "UN verbatim record",
      "institution": "UNSC",
      "phase": "vote_event"
    },
    {
      "start": 4974,
      "content_start": 4989,
      "end": 5241,
      "country": "IND",
      "capacity": "council_president",
      "representative": "Mrs. Kamboj",
      "institution": "UNSC",
      "phase": "after_vote"
    },
    {
      "start": 5242,
      "content_start": 5264,
      "end": 8507,
      "country": "IRL",
      "capacity": "national_delegation",
      "representative": "Mr. Mythen",
      "institution": "UNSC",
      "phase": "after_vote"
    },
    {
      "start": 8508,
      "content_start": 8548,
      "end": 9889,
      "country": "GBR",
      "capacity": "national_delegation",
      "representative": "Dame Barbara Woodward",
      "institution": "UNSC",
      "phase": "after_vote"
    },
    {
      "start": 9890,
      "content_start": 9921,
      "end": 12307,
      "country": "BRA",
      "capacity": "national_delegation",
      "representative": "De Almeida Filho",
      "institution": "UNSC",
      "phase": "after_vote"
    },
    {
      "start": 12308,
      "content_start": 12333,
      "end": 13667,
      "country": "NOR",
      "capacity": "national_delegation",
      "representative": "Heimerback",
      "institution": "UNSC",
      "phase": "after_vote"
    },
    {
      "start": 13669,
      "content_start": 13726,
      "end": 20435,
      "country": "RUS",
      "capacity": "national_delegation",
      "representative": "Evstigneeva",
      "institution": "UNSC",
      "phase": "after_vote"
    },
    {
      "start": 20436,
      "content_start": 20480,
      "end": 23419,
      "country": "CHN",
      "capacity": "national_delegation",
      "representative": "Geng Shuang",
      "institution": "UNSC",
      "phase": "after_vote"
    },
    {
      "start": 23421,
      "content_start": 23446,
      "end": 24976,
      "country": "ALB",
      "capacity": "national_delegation",
      "representative": "Dautllari",
      "institution": "UNSC",
      "phase": "after_vote"
    },
    {
      "start": 24977,
      "content_start": 25015,
      "end": 27568,
      "country": "ARE",
      "capacity": "national_delegation",
      "representative": "Abushahab",
      "institution": "UNSC",
      "phase": "after_vote"
    },
    {
      "start": 27569,
      "content_start": 27584,
      "end": 27644,
      "country": "IND",
      "capacity": "council_president",
      "representative": "Mrs. Kamboj",
      "institution": "UNSC",
      "phase": "after_vote"
    },
    {
      "start": 27645,
      "content_start": 27645,
      "end": 30721,
      "country": "IND",
      "capacity": "national_delegation",
      "representative": "Mrs. Kamboj",
      "institution": "UNSC",
      "phase": "after_vote"
    }
  ],
  "target": [
    29491,
    32567
  ],
  "prior_history_omitted": false,
  "earlier_unlabelled_tokens": 5150
}
````


</details>

## 8923-IND

<details>
<summary>Complete masked scenario, chronological history and requested-role prefix</summary>

<!-- exact:prompt:scenario-training:8923-IND -->

> &lt;|scenario|&gt;
> UN Security Council; New York; 9 December 2021, 10 a.m.
> Agenda: Maintenance of international peace and security — Security in the context of terrorism and climate change.
> Opening document: Letter dated 30 November 2021 from Niger, S/2021/988.
> Phase: open debate; this input supplies no subsequent vote or outcome.
> History window: only the immediately preceding complete speech is shown; earlier turns are omitted. Their absence is not evidence that a statement was not made.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=RUS; institution=UNSC; capacity=national_delegation; representative=Mr. Nebenzia; phase=open_debate
> &lt;|speech|&gt;
> We are pleased to see you, Mr. President, presiding over the Security Council. The Russian Federation wholeheartedly shares the common international concerns about the issues that are at the centre of our debate today. The consequences of climate change, natural disasters and terrorism are
>
> catastrophes that are cross-border in nature and require active international cooperation. We are committed to working on these priorities. In addition, our colleagues from the Niger raised another subject for discussion, namely, the possible connection between terrorism and climate change and issues of security, as well as the role of the Security Council in this context. First, climate change is an issue that holds a very important place for us both in the national context and in terms of international cooperation. According to our calculations, the climate in Russia is changing 2.5 times faster than the global average. At the same time, we see ever more destructive natural phenomena, and the need to cut greenhouse gases and adapt to the negative consequences of climate change is increasingly obvious to us. On 29 October this year, the Russian Federation a government order that established a strategy for low-carbon socioeconomic development until 2050. This strategy sets the specific goal of achieving a balance between human-made greenhouse-gas emissions and the mitigation thereof through carbon capture by 2060. In the spirit of such approaches, the Russian delegation played an active role at the twenty-sixth session of the Conference of the Parties to the United Nations Framework Convention on Climate Change (UNFCCC), in Glasgow in November, and helped achieve a consensus. We think that the success in Glasgow possible was due to the balance struck between climate- and environmental-protection efforts and the socioeconomic interests of countries at different levels of development and therefore at different levels of vulnerability. Help in protecting countries from climate change and natural disasters is an important element in national efforts and international global cooperation, especially in the framework of the United Nations development system. Nevertheless, there is a range of different sub-issues on the agenda, from sea-level rise, which is an issue for island States, to the desertification in countries in Africa. Those require different approaches to assistance for the States in question. There is no disagreement that cooperation in the fight against international terrorism should also be global in nature. In this context, we think that States Members of the United Nations are able to define threats and issues with the support of the counter-terrorism monitoring activity of the Counter-Terrorism Committee Executive Directorate (CTED), which helps to prepare reports
>
> on States’ implementation of specialized counter-terrorism resolutions, in particular resolutions 1373 (2001) and 1624 (2005). This mechanism has been able to keep up with its work despite the coronavirus disease (COVID-19) pandemic. On the basis of CTED’s recommendations, States can be provided with technical assistance through such specialized United Nations structures as the United Nations Office of Counter-Terrorism and the United Nations Office on Drugs and Crime. We stress that this assistance should be provided upon the request of local authorities and taking into account the specifics of the country and the region, and there are indeed many specifics. Accordingly, despite the active fight going on with the Islamic State in Iraq and the Levant in Syria and Iraq, we are also seeing the terrorist threat spread from the Middle East and North Africa to neighbouring countries and regions, particularly deeper into Africa. The reasons for that are problems of border security, given that the borders are porous, socioeconomic conditions are difficult, the COVID-19 crisis is deepening, and the central authorities on the ground are showing weakness. Terrorists are successfully taking advantage of this, broadening their propaganda and finding new recruits from the dissatisfied population, above all, young people. There is also no disagreement that, in the Sahel, for example, a great many factors, including problems of extreme poverty, a lack of jobs, population growth, desertification, natural disasters, migration, internal conflicts and terrorist activity, have come together into a single knot. The current situation with the coronavirus is also making the situation more difficult. A completely logical question therefore presents itself. In order to solve the aforementioned problems, what should the United Nations and the Security Council do? We have to recognize that our approach differs from the opinion of many of our Security Council colleagues. First and foremost, we are convinced that each country or region needs to be looked at individually as well as in connection with other often more significant factors that give rise to socioeconomic or political instability, including foreign intervention in States, or the lack of outside assistance in situations where the local authorities and State institutions cannot cope with the task at hand. A generic one-size-fits-all approach or some kind of automatic attribution of cause and effect
>
> will only lead the Security Council down the wrong path in solving these problems. We are convinced that each of the negative factors in this context should be analysed and overcome with the consent of the national Governments of recipient countries and the use of the specific expert potential and the toolkit that the United Nations can bring, once again without some one-size-fits-all approach. We defended and will continue to defend the notion that the United Nations works effectively when its labour is properly divided. Forcing climate monitoring detached from fundamental scientific work into the mandate of peacekeeping operations or special political missions would be a disastrous politicization of the climate agenda and lead us away from unified and genuinely global cooperation, which is what the Paris Agreement on Climate Change and the UNFCCC are aiming to achieve. Let us be honest: cutting greenhouse-gas emissions in region A is not going to stop floods or droughts in region B over the next 50 or 100 years. Furthermore, in looking for the deep-rooted reasons for terrorism, moving the focus from poverty, sanctions or weak State institutions to climate simply means going away from an open discussion of the reasons for the extreme vulnerability of States, in particular those that have suffered from foreign intervention. Can this really be helped by moving the discussion to the Security Council? For us, the direct connection between terrorism and climate change is not clear. Perhaps our colleagues, by including this subject in the Security Council agenda, simply want to raise the profile of debate on climate. However, I think that Council members would agree that whether any particular issue is included or not on the Security Council agenda should not serve as a yardstick as to whether or not it is important. Climate change is certainly an issue where this is a concern. As part of its specific nature, it should be looked at with the involvement of all States Members of the United Nations. Nothing can really be helped by including it on the agenda of the Security Council, with its limited membership and very specific toolkit, but it certainly could lead to a muddling and a doubling of efforts. On the whole, we think that working on this issue within the UNFCCC, the General Assembly, the Economic and Social Council, the High-level
>
> Political Forum, and the Peacebuilding Commission and other United Nations forums — and respecting the division of labour within the Organization — has great potential for addressing the socioeconomic recovery of developing countries. In particular, developing countries need to strengthen their capacities to overcome the obstacles to development that are relevant to them, as well as increased and better access to financing and to participation in the global trading system, vaccines against COVID-19, the best available technologies and early-warning systems for extreme natural phenomena, humanitarian assistance, education and vocational guidance for the younger generation, particularly women. We call for working along those lines in the frameworks that I mentioned, leaving it to the Security Council to address the root causes of conflicts and resolve existing ones.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=&lt;|country_IND|&gt;; institution=UNSC; capacity=national_delegation; representative=Mr. Tirumurti; phase=open_debate
> &lt;|speech|&gt;
>

<!-- /exact -->


</details>

**Complete supervised authentic target, including record-end marker:**

<!-- exact:target:scenario:8923-IND -->

> Let me begin by conveying best wishes and greetings from the Prime Minister of India, Shri Narendra Modi, to the President of the Republic of the Niger, His Excellency Mr. Mohamed Bazoum, on the Niger’s presidency of the Security Council. I also thank Secretary-General António Guterres, Mr. Moussa Faki Mahamat, Chairperson of the African Union Commission, and Ambassador Mamman Nuhu, Executive Secretary of the Lake Chad Basin Commission, for their respective briefings. The briefing by His Excellency the President of the Niger again drew the attention of the Security Council to the threat of terrorism in the Sahel region and beyond. That is indeed a serious global concern. The fight against terrorism remains significant even after 20 years since landmark resolution 1373 (2001) was adopted in the wake of the 9/11 terrorist attacks. The threat of terrorism in Africa has adversely impacted African countries in their pursuit of economic progress and development. The security situation in the countries of the Group of Five for the Sahel (G-5 Sahel) in particular has deteriorated in the past three years, as is evident from the scores of attacks by terrorists and armed groups targeting civilians and security forces. Furthermore, the threat posed by terrorist groups in the Sahel region and beyond is well documented, including in the Secretary-General’s periodic reports. Jama’a Nusrat ul-Islam wa al-Muslimin, affiliated to Al-Qaida and the Islamic State in the Greater Sahara, has expanded its activities. Groups linked to Al-Qaida
>
> and the Islamic State in Iraq and the Sham and Boko Haram have also continued to expand around the eastern and northern shores of Lake Chad. The attacks against the United Nations Multidimensional Integrated Stabilization Mission in Mali a few days ago, which resulted in the killing of seven peacekeepers from Togo and a Malian national, demonstrate the danger posed by terrorist and armed groups to the Sahel region. India strongly condemns the attack on peacekeepers and expresses its deepest condolences to the families of those who lost their lives. India appreciates the initiative of the G-5 Sahel Joint Force, a joint effort of countries in the Sahel, including the Niger. However, the Joint Force continues to be plagued by multiple challenges, such as a lack of training, resources, logistics and access to sustainable and predictable financing, all of which have hampered the full operationalization of the Force. The current model of support to the Joint Force is inadequate and unsustainable — a reality that was highlighted by the Secretary-General in his recent reports and echoed by His Excellency the President of the Niger just now. We believe that it is high time that regional security initiatives such as the G-5 Sahel Joint Force be provided adequate and sustainable resources, as well as training and logistics support. A resource-constrained counter-terrorism strategy can be a recipe for failure. The Council needs to take effective measures, including by supporting regional and subregional organizations in their security initiatives. Climate change is one of the defining challenges of our time. Over the past several decades, Member States have engaged purposefully in a focused manner to put in place commitments relating to mitigation, adaptation, financing, the transfer of technology, et cetera so that climate change can be addressed holistically, as is done by the process led by the United Nations Framework Convention on Climate Change (UNFCCC) with annual meetings of the Conference of the Parties (COP). The measures to tackle climate change have been built on an integrated structure that is equitable to all parties, especially developing countries. In addition to that, countries across the globe have taken on many commitments under the nationally determined contributions. Given that background, we do not think that it is appropriate to draw a separate link between security and climate change, especially when all aspects of climate change are already being dealt with holistically
>
> under the mandate of the UNFCCC. Any action in the Security Council ignoring the basic principles and provisions relating to climate change has the potential to disrupt the nature of our overall discussion on this important topic. To move the climate change discourse from a consensus-driven template to a possibly divisive process may not be advisable. Let us not deviate from an established and inclusive process of decision-making, with all developing countries participating, and attempt to create an alternative platform for climate change. While we recognize the fact that climate change has impacted the lives of people and exacerbated conflicts in many places, viewing conflicts only through the prism of climate change presents a misleading perspective. The report of the Intergovernmental Panel on Climate Change clearly states that the effect of climate variability on violence is contested. There is also no clear scientific pronouncement directly equating climate change with security concerns. It is therefore important that matters of climate science be discussed in the relevant forums under the UNFCCC. The oversimplification of causes of conflict will not help to resolve them, and neither can it justify terrorist acts or extreme policy measures. We recently completed the twenty-sixth session of the Conference of the Parties to the UNFCCC (COP26) in Glasgow, the United Kingdom, where we adopted the Glasgow Climate Pact by consensus. That document contains the collective will of the international community on all aspects related to climate change in a holistic manner and the climate action envisaged. We are firmly committed to achieving the outcome of COP26 based on the Glasgow Climate Pact. We now need to bring our focus back to where it should be — combating climate change. India is a leader in climate action and is on track to meet its commitments under the Paris Agreement on Climate Change. India’s climate-responsive development is evident in the announcements at COP26, where India also committed to reducing the emissions intensity of its gross domestic product by 45 per cent by 2030 from the 2005 level; achieving 50 per cent cumulative electric power installed capacity from non-fossil-fuel-based energy resources by 2030; achieving 1 billion ton reductions in the projected emissions between now and 2030; achieving 500 gigawatts of non-fossil fuel energy capacity by 2030; and achieving the target of net zero by the year 2070, which our Prime Minister has collectively called the panchamrit, or five goals.
>
> Apart from domestic actions, India has also taken the lead in bringing together international coalitions to generate long-term impacts through partnerships. The International Solar Alliance (ISA) is a leading example of how collective action translates into positive global action. We recently launched the Green Grids Initiative — One Sun One World One Grid, together with the United Kingdom, endorsed by the ISA, which will facilitate cross-border renewable energy transfer projects. The Coalition for Disaster-Resilient Infrastructure (CDRI) is another successful initiative by India for enhancing cooperation and building resilience against natural disasters. At COP26, a new initiative for technical assistance and capacity-building in island States, called the Infrastructure for Resilient Island States, was introduced under the CDRI. What we now need is to enhance action on all important policies that address climate change, including the fulfilment of commitments on climate finance and technology transfer. Developed countries cannot pass on their obligations to developing countries and must meet their commitments equitably, on both mitigation and adaptation. Today it is necessary that, as we track the progress made in climate mitigation, we should also track climate financing and urge developed countries to begin providing climate financing of $1 trillion at the earliest. In conclusion, the threat of terrorism to the Sahel region is far greater and more severe than many other challenges facing the region today. India has always been willing to extend and expand its capacity-building assistance to the armed forces of the affected countries to support them in their fight against terrorism. India’s recent initiatives in that regard have been the inclusion of Chad in our training under the Indian Technical and Economic Cooperation Programme, with 10 military training slots last year, and a specialized in-situ training programme in counter-insurgency and counter-terrorism for nearly 200 Nigerian army personnel this year. We believe that it is important that the Council continue to extend all possible assistance and support to the G-5 Sahel Joint Force, in the overarching interest of peace, security and stability in the region. Both terrorism and climate change are complex issues that the global community is grappling with. After decades of painstaking international efforts, today we have institutional mechanisms to address each of these issues. We should continue to work
>
> through those established mechanisms. That should be the way forward.&lt;|im_end|&gt;

<!-- /exact -->

<details>
<summary>Original history-window provenance</summary>

````json
{
  "source": "8923",
  "source_sha256": "be9a09dc1ed07d974860596af75117ab0e8e49e4da9c7ecb9062a6f17d6d5833",
  "window": [
    77649,
    95471
  ],
  "turns": [
    {
      "start": 0,
      "content_start": 54,
      "end": 8593,
      "country": "RUS",
      "representative": "Mr. Nebenzia",
      "institution": "UNSC",
      "capacity": "national_delegation",
      "phase": "open_debate"
    },
    {
      "start": 8594,
      "content_start": 8617,
      "end": 17822,
      "country": "IND",
      "representative": "Mr. Tirumurti",
      "institution": "UNSC",
      "capacity": "national_delegation",
      "phase": "open_debate"
    }
  ],
  "target": [
    86266,
    95471
  ],
  "prior_history_omitted": true,
  "earlier_unlabelled_tokens": 15758
}
````


</details>

## 8923-GBR

<details>
<summary>Complete masked scenario, chronological history and requested-role prefix</summary>

<!-- exact:prompt:scenario-training:8923-GBR -->

> &lt;|scenario|&gt;
> UN Security Council; New York; 9 December 2021, 10 a.m.
> Agenda: Maintenance of international peace and security — Security in the context of terrorism and climate change.
> Opening document: Letter dated 30 November 2021 from Niger, S/2021/988.
> Phase: open debate; this input supplies no subsequent vote or outcome.
> History window: only the immediately preceding complete speech is shown; earlier turns are omitted. Their absence is not evidence that a statement was not made.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=VNM; institution=UNSC; capacity=national_delegation; representative=Mr. Pham; phase=open_debate
> &lt;|speech|&gt;
> At the outset, let me thank the Niger for convening this meeting and to thank Mr. Mohamed Bazoum, President of the Niger, for presiding over this important debate. (spoke in English) I also thank the Secretary-General and the other briefers for their insightful contributions. In its latest report, the Intergovernmental Panel on Climate Change confirms that climate change is accelerating and that, in some cases, the changes in the climate are irreversible. It calls for our urgent actions to cut emissions, build resilience and adapt to and mitigate the inevitable impacts of climate change. Half of the 20 countries considered most vulnerable to climate change find themselves on the agenda of the Security Council. Climate change is increasingly becoming a dangerous threat multiplier. Their adverse effects deprive people of livelihoods, lead to food and water insecurity, cause mass displacement, generate instability and create tensions and violence. Some situations, such as that in the Sahel region, are fraught with the existing threats of terrorism and fragilities, while struggling with the adverse effects of climate change, environmental degradation and the depletion of natural resources. During its visit to the region in October, the Security Council witnessed this first-hand. We must not allow terrorist groups to exploit the tensions and grievances exacerbated by climate change to further erode State governance, increase recruitment, radicalize disenfranchised people and draw them to violent extremism. Countering terrorism has been at the very core of the agenda of the Security Council. Much progress has been achieved over the past 20 years, most notably the Council’s commitments, unity and solidarity in the fight against terrorism. Over the past two years, there have been many thematic debates on climate and security in the Council, with growing engagement from its members. The important work of the Security Council’s Informal Expert Group on Climate and Security, chaired by
>
> the Niger and Ireland, has contributed to promoting discussion on, and an understanding of, security risks of climate change in specific contexts — and much more. To address risks posed by climate change and terrorism, we would like to make the following observations. First, a holistic approach to address all aspects of these issues can help ensure the sustainability of our response and long-term success. At the global level, it means whole-of-organization collaboration by all United Nations bodies and missions, with long-term vision and strategies. Among those, the Security Council has a special role to play to address security risks and threats, including by working closely with others to prevent conflict from happening, addressing the compounding threats, including climate change and terrorism, and ensuring sustainable peace. The Security Council must demonstrate its leadership, unity and solidarity and act swiftly in fulfilling its responsibility. At the national level, that involves a whole-of-Government approach and whole-of-society engagement. In all those processes, inclusivity is key. It is important to ensure the active participation of vulnerable countries, communities, groups, women and youth. Secondly, anticipation and resilience are most effective and should be adequately invested in. Anticipation helps us better prepare well in advance, be ready to face the challenges and be more efficient in our response to both climate change and terrorism. Resilience helps communities adapt better to climate change and boosts our people’s immunity to the spread of terrorist ideology. It should strengthen and diversify livelihoods, contribute to poverty eradication and ensure equity. Thirdly, equality should be ensured by equity through international cooperation and solidarity. No single country can deal with those threats alone, especially climate change. Developing countries have limited resources and capacities, but often face worse impacts. International commitments should be based on the principle of common but differentiated responsibilities and on the specific circumstances and capacities of the countries concerned. In that connection, international cooperation should be enhanced to contribute effectively to the translation of commitments into action. The twenty-sixth Conference of the Parties to the United Nations Framework Convention on Climate
>
> Change has generated momentum on the commitments on cutting greenhouse-gas emissions. Climate financing is central to their implementation. Developed countries should take the lead in making and honouring their commitments to providing climate financing and development assistance. Resources should be set aside to provide developing and least developed countries with assistance in financing, technologies and know-how, so that no country is left behind. According to the World Bank, Viet Nam is among the six countries most severely affected by climate change. An active and effective response to climate change reflects the strong political resolve of our Government. We stand ready to engage in all collective actions to address climate-related challenges at the United Nations and other forums.&lt;|im_end|&gt;
> &lt;|speaker|&gt;country=&lt;|country_GBR|&gt;; institution=UNSC; capacity=national_delegation; representative=Dame Barbara Woodward; phase=open_debate
> &lt;|speech|&gt;
>

<!-- /exact -->


</details>

**Complete supervised authentic target, including record-end marker:**

<!-- exact:target:scenario:8923-GBR -->

> I thank you, Mr. President, in particular for your clear account of the impact of climate change and terrorism in the Niger. And I thank the other experts too for their valuable briefings. It is a cruel reality that many of the nations most affected by climate change are also among the world’s most fragile. As the Secretary-General made clear, the impacts of climate change act as a multiplier of the threats already facing vulnerable populations. And countries enduring conflict are hit especially hard. With institutions under pressure, communities displaced and societies insecure, those nations are less equipped to cope with the impacts of climate change. As you highlighted, Mr. President, in the Sahel, changes in rainfall have fuelled conflict between farmer and herder communities. That can create the conditions for violent extremism. In Iraq and Syria, farming communities affected by climate-induced crop failures and droughts were thought to have been an important source of recruits for the Islamic State in Iraq and the Levant between 2014 and 2016. We therefore welcome the United Nations efforts to address both terrorism and climate change. With the climate crisis posing an existential threat to our future — not only to our environment, but to our common security — we must act. I want to emphasize three ways we can do this. First, at the twenty-sixth Conference of the Parties to the United Nations Framework Convention on Climate Change (COP26), we saw that countries can work together to deliver ambitious commitments. Through the Glasgow Climate Pact, we have kept alive
>
> the hope of limiting the rise in global temperature to 1.5°C. We saw strong commitments made at COP26 on net zero, ending and reversing deforestation, the doubling of adaptation financing and meeting the $100 billion goal by 2023 at the latest. That will help countries increase their preparedness to climate risks and protect vulnerable communities from some of the worst impacts of climate change and its effects on stability. Secondly, we need the United Nations system to report comprehensively on the links between climate and security so that we have the best information to inform our decisions. The Council’s Counter-Terrorism Committee Executive Directorate has a clear role in that regard and should continue to examine the conditions and environments in which terrorism develops and thrives. But all parts of the United Nations, including the Security Council, have a critical role to play to meet the challenge. Therefore, we support the draft resolution submitted to the Council as an important first step. Thirdly, we wholeheartedly support a fully inclusive approach, in particular with respect to women and girls, who suffer disproportionately from conflict and climate change, so that they can play a meaningful role. In conclusion, we must act effectively, urgently and together to address the climate crisis and reduce the increasing risks of climate insecurity.&lt;|im_end|&gt;

<!-- /exact -->

<details>
<summary>Original history-window provenance</summary>

````json
{
  "source": "8923",
  "source_sha256": "be9a09dc1ed07d974860596af75117ab0e8e49e4da9c7ecb9062a6f17d6d5833",
  "window": [
    102867,
    111134
  ],
  "turns": [
    {
      "start": 0,
      "content_start": 39,
      "end": 5246,
      "country": "VNM",
      "representative": "Mr. Pham",
      "institution": "UNSC",
      "capacity": "national_delegation",
      "phase": "open_debate"
    },
    {
      "start": 5247,
      "content_start": 5287,
      "end": 8267,
      "country": "GBR",
      "representative": "Dame Barbara Woodward",
      "institution": "UNSC",
      "capacity": "national_delegation",
      "phase": "open_debate"
    }
  ],
  "target": [
    108154,
    111134
  ],
  "prior_history_omitted": true,
  "earlier_unlabelled_tokens": 19763
}
````


</details>
