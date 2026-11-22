# Learning flexible speaker routing

The alternating schedule gives each speaker at most two slots on the original four-option grid. It therefore cannot certify impasses that require one role to state three exclusions. The flexible channel adds a single next-speaker choice to each admitted signed claim. The sender can nominate itself or the other delegate. The decision certificate uses only the signed claims. A delegate's policy receives its own menu and the public ledger, and never receives the other delegate's private menu. The horizon equals the number of packages, so an impasse with positive openings requires exactly one new exclusion per remaining package.

On the four-option development grid, the flexible script recovers all 108 impasses with all 916 agreements intact. The best earlier alternating control reaches 84 impasses. Keeping the new claim priorities but restoring alternation reaches 60. This latter matched control isolates the change in routing from the revised claim priorities.

## Routing alone and joint learning

The shared routing-only policy evaluates stay and handoff with counterfactual rollouts under centralized training on three- and four-option worlds. It accepts switches only if they reduce turns while preserving class coverage. No switch passed. The frozen policy was therefore identical to the flexible script on width five, certifying 5,860/5,860 agreements and 460/540 impasses. Of the 80 disjoint misses, 60 have two compatible packages in the left role and three in the right, while 20 have two in each role. [Routing-only fit](evidence/counterfactual/training.json) · [Width-five outcomes](evidence/counterfactual/heldout.json)

The joint policy admits a choice among legal claim types and a next-speaker bit. Both agents share one local policy initialized from the flexible script. Counterfactual self-play on widths three through five evaluates the effect of alternative actions on the common certificate reward with a 0.025 slot cost. Four table updates preserve every training agreement and increase training impasse recall from 586/666 to 666/666. On the first unseen six-option grid, the learned policy retained every agreement and used 5,760 fewer agreement slots. It also lost 720 impasses and gained 150, for a net loss of 570. All 720 regressions first diverged at the second slot when the policy sent a nonmatching acceptance where the script would send an exclusion. [Joint fit](evidence/joint/training.json) · [Initial width-six test](evidence/joint/heldout.json)

## Guarding room for an impasse certificate

A nonmatching acceptance cannot exclude a package. If the number of unexcluded packages is at least the number of available slots, replacing a scripted exclusion with that acceptance leaves too little capacity to certify an impasse. The guard retains the scripted exclusion in this condition. The saved policy is unchanged. Width six informed the guard, then the complete seven-option grid was evaluated for the first time.

| Positive-opening grid | Policy | Verified agreements | Verified impasses |
|---|---|---:|---:|
| Six options, development | Flexible script | 34,434/34,434 | 1,920/2,430 |
| Six options, development | Learned | 34,434/34,434 | 1,350/2,430 |
| Six options, development | Learned with guard | 34,434/34,434 | 2,430/2,430 |
| Seven options, fresh test | Flexible script | 190,498/190,498 | 7,140/10,206 |
| Seven options, fresh test | Learned | 190,498/190,498 | 4,662/10,206 |
| Seven options, fresh test | Learned with guard | 190,498/190,498 | 10,206/10,206 |

The guarded policy and script use the same aggregate number of slots on both grids. A single trained rule that keeps the floor after a particular exclusion reproduces every guarded action on widths six and seven. Applying the guard to the script alone leaves its actions unchanged. The gain therefore comes from a learned change in who speaks next, while the guard suppresses the learned changes that traded impasses for faster agreements. These are exhaustive presentations of a synthetic game, and multiple presentations share the same mandate pair. [Six-option metrics](evidence/guard/metrics-6.json) · [Seven-option metrics](evidence/guard/metrics-7.json) · [Replay](evidence/replay.json)

## UNBench sanctions workshop

A new seven-package workshop uses the already exposed S/2022/925 anchor. The Council adopted the draft 14–0–1 as resolution 2664 (2022), with Brazil in favour and India abstaining. India's recorded concerns about the role of the 1267 Monitoring Team and reporting motivate the workshop's subject. All seven options and private workshop mandates are fictional. The report does not attribute any of those instructions to historical delegations. [UNBench anchor audit](../../../../judge/benchmark-development.json) · [UN vote record](https://digitallibrary.un.org/record/3997276) · [Meeting record](https://digitallibrary.un.org/record/3997357/files/S_PV.9214-EN.pdf) · [Adopted text](https://digitallibrary.un.org/record/3997259/files/S_RES_2664_%282022%29-EN.pdf)

Both arms use the same seven continuation slots and are tested on every allowed positive opening pair. The script and guarded policy certify all eight agreement openings. The guarded policy raises impasse certification from four of six to six of six. The adapter translates truthful local actions into the workshop's existing public ledger, which independently certifies dispositions using the emitted claims. The raw evidence includes every admission. This is a structured application on an exposed historical family, with no new Qwen inference or final-memo grading. [Sanctions workshop](sanctions.json) · [Workshop results](evidence/sanctions.json)

The run metadata, trained rules and replay hashes are in the workspace. The complete raw grid traces remain in the project run directories named in the launch records.
