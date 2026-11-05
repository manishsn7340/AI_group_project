# Group Assignment 2 – Analysis Report

**Team:** E.D.I.T.H

| Name | Roll No. |
|---|---|
| Satyam Singh | B24CS038 |
| Shivam Chaurasia | B24CS039 |
| Manish Shyoran | B24CS026 |
| Mitu Kumar | B24CS029 |

---

## Problem 1: Smart Home Energy Consumption (Bayesian Network)

Code: `Problem1/smart_home.py`. Full output: `Problem1/results.txt`.

We wrote the inference ourselves (exact enumeration over the joint distribution), so no extra library is needed apart from numpy and matplotlib.

### Part A: Expert network

The network has these edges: DayType → Occupancy, Weather → AC, Occupancy → AC, Occupancy → ApplianceLoad, AC → Energy, ApplianceLoad → Energy. The joint distribution is

P(W,D,O,A,L,E) = P(W) P(D) P(O|D) P(A|W,O) P(L|O) P(E|A,L)

The program checks all 16 CPT rows and every one sums to 1. The network drawing is in `bayesian_network.png`.

| Query | Probability |
|---|---:|
| Q1: P(E=High) | 0.5806 |
| Q2: P(E=High \| Weather=Hot) | 0.7063 |
| Q3: P(E=High \| DayType=Weekend) | 0.6402 |
| Q4: P(E=High \| Weather=Cold, Occupancy=High) | 0.4843 |
| Q5: P(Weather=Hot \| E=High) | 0.6082 |
| Q6: P(AC=On \| E=High) | 0.6929 |
| Q7: P(AC=On \| E=High, Load=Heavy) | 0.6499 |

**Q6 vs Q7 (explaining away).** AC and ApplianceLoad are both causes of high energy. If we only know the energy is high, AC being on is quite likely (0.693). Once we also learn the appliance load is heavy, that already explains the high energy, so we need the AC less to explain it, and P(AC=On) drops to 0.650.

**Q1 by hand.** P(E=High) = Σ over (w,d,o) of P(w)·P(d)·P(o|d) · Σ over (a,l) of P(a|w,o)·P(l|o)·P(E=High|a,l).

The inner sum depends only on (w,o), and we multiply it by P(w)·P(d)·P(o|d) for each of the 12 combinations:

| Weather | Day | Occ | P(w)P(d)P(o\|d) | inner sum | product |
|---|---|---|---:|---:|---:|
| Hot | Weekday | High | 0.1575 | 0.81825 | 0.128874 |
| Hot | Weekday | Low | 0.1925 | 0.56660 | 0.109071 |
| Hot | Weekend | High | 0.1200 | 0.81825 | 0.098190 |
| Hot | Weekend | Low | 0.0300 | 0.56660 | 0.016998 |
| Mild | Weekday | High | 0.0945 | 0.60950 | 0.057598 |
| Mild | Weekday | Low | 0.1155 | 0.34453 | 0.039793 |
| Mild | Weekend | High | 0.0720 | 0.60950 | 0.043884 |
| Mild | Weekend | Low | 0.0180 | 0.34453 | 0.006201 |
| Cold | Weekday | High | 0.0630 | 0.48425 | 0.030508 |
| Cold | Weekday | Low | 0.0770 | 0.29518 | 0.022728 |
| Cold | Weekend | High | 0.0480 | 0.48425 | 0.023244 |
| Cold | Weekend | Low | 0.0120 | 0.29518 | 0.003542 |

Adding the last column gives **0.5806**, which is exactly what the code prints.

### Part B: Conditional independence

1. **Weather ⊥ DayType: holds.** Both are root nodes. Every path between them goes through a collider (AC or Energy) that is not observed, so all paths are blocked. Check: P(W=Hot) = 0.5 and P(W=Hot | D=Weekend) = 0.5.
2. **Weather ⊥ DayType | Energy: does not hold.** Observing Energy opens the collider. Two paths become active: W→A→E←L←O←D, and the shorter W→A←O←D (A is a collider and its descendant E is observed). Check: P(W=Hot | E=High) = 0.6082, but P(W=Hot | E=High, D=Weekend) = 0.5998, which are different.
3. **Weather ⊥ ApplianceLoad | Occupancy: holds.** The path W→A←O→L is blocked because A is an unobserved collider (and O is observed, which blocks the fork too). The path W→A→E←L is blocked at the unobserved collider E. Check: P(W=Hot | O=High) = 0.5 and P(W=Hot | O=High, L=Heavy) = 0.5.

### Part C: Synthetic data

We used ancestral sampling, visiting nodes in the order Weather, DayType, Occupancy, AC, ApplianceLoad, Energy, with random seed **42**. The three datasets are the first 500, 5000 and 20000 rows of one generated stream.

| Size | Hot / Mild / Cold | (Weather, Occupancy) counts: HotH, HotL, MildH, MildL, ColdH, ColdL |
|---:|---|---|
| 500 | 255 / 143 / 102 | 155, 100, 75, 68, 51, 51 |
| 5000 | 2496 / 1510 / 994 | 1402, 1094, 823, 687, 558, 436 |
| 20000 | 9906 / 6116 / 3978 | 5520, 4386, 3416, 2700, 2228, 1750 |

(Expected frequencies are 0.5 / 0.3 / 0.2, and the samples get closer to that as the size grows.)

### Part D: Learning

We learned the CPTs with MLE and with Bayesian estimation (BDeu prior, equivalent sample size 10) using the same structure. The learned AC table for the 500-sample dataset, next to the expert one (P(AC=On)):

| Weather | Occupancy | Expert | MLE | Bayesian |
|---|---|---:|---:|---:|
| Hot | High | 0.900 | 0.852 | 0.848 |
| Hot | Low | 0.600 | 0.660 | 0.657 |
| Mild | High | 0.400 | 0.360 | 0.363 |
| Mild | Low | 0.150 | 0.176 | 0.184 |
| Cold | High | 0.100 | 0.098 | 0.111 |
| Cold | Low | 0.050 | 0.020 | 0.035 |

The tables for 5000 and 20000 are in `results.txt`.

### Part E: Comparison

**500 samples**

| Query | Expert | MLE | Bayesian | \|Diff\| MLE | \|Diff\| Bayes |
|---|---:|---:|---:|---:|---:|
| Q1 | 0.5806 | 0.5570 | 0.5559 | 0.0237 | 0.0247 |
| Q2 | 0.7063 | 0.7050 | 0.6991 | 0.0013 | 0.0072 |
| Q3 | 0.6402 | 0.6092 | 0.6046 | 0.0310 | 0.0356 |
| Q4 | 0.4843 | 0.4203 | 0.4268 | 0.0639 | 0.0575 |
| Q5 | 0.6082 | 0.6455 | 0.6370 | 0.0373 | 0.0288 |
| Q6 | 0.6929 | 0.7280 | 0.7236 | 0.0351 | 0.0307 |
| Q7 | 0.6499 | 0.6584 | 0.6560 | 0.0085 | 0.0061 |

**5000 samples**

| Query | Expert | MLE | Bayesian | \|Diff\| MLE | \|Diff\| Bayes |
|---|---:|---:|---:|---:|---:|
| Q1 | 0.5806 | 0.5794 | 0.5793 | 0.0012 | 0.0014 |
| Q2 | 0.7063 | 0.7034 | 0.7028 | 0.0029 | 0.0035 |
| Q3 | 0.6402 | 0.6399 | 0.6393 | 0.0003 | 0.0009 |
| Q4 | 0.4843 | 0.4860 | 0.4863 | 0.0017 | 0.0021 |
| Q5 | 0.6082 | 0.6060 | 0.6053 | 0.0022 | 0.0029 |
| Q6 | 0.6929 | 0.6884 | 0.6881 | 0.0044 | 0.0048 |
| Q7 | 0.6499 | 0.6496 | 0.6493 | 0.0003 | 0.0006 |

**20000 samples**

| Query | Expert | MLE | Bayesian | \|Diff\| MLE | \|Diff\| Bayes |
|---|---:|---:|---:|---:|---:|
| Q1 | 0.5806 | 0.5768 | 0.5768 | 0.0038 | 0.0038 |
| Q2 | 0.7063 | 0.7028 | 0.7026 | 0.0035 | 0.0036 |
| Q3 | 0.6402 | 0.6381 | 0.6379 | 0.0021 | 0.0023 |
| Q4 | 0.4843 | 0.4838 | 0.4839 | 0.0004 | 0.0004 |
| Q5 | 0.6082 | 0.6035 | 0.6033 | 0.0047 | 0.0049 |
| Q6 | 0.6929 | 0.6922 | 0.6921 | 0.0007 | 0.0008 |
| Q7 | 0.6499 | 0.6499 | 0.6499 | 0.0001 | 0.0000 |

**Mean absolute difference over Q1–Q7** (plot: `mean_absolute_difference.png`)

| Size | MLE | Bayesian |
|---:|---:|---:|
| 500 | 0.0287 | 0.0272 |
| 5000 | 0.0019 | 0.0023 |
| 20000 | 0.0022 | 0.0023 |

**Largest error for 500 samples.** Q4 has the largest error (0.064 for MLE). Its evidence (Weather=Cold and Occupancy=High) appears only 51 times out of 500, so the learned probabilities for that case rest on very few rows and are noisy. Q1 uses all 500 rows, and Q2, Q5 and Q6 use 255 to 280, so they are more stable.

**Which estimator is better for small data?** Bayesian estimation, but only slightly in our run (0.0272 vs 0.0287). The prior adds pseudo-counts, so a rare combination can't get an extreme probability like 0 or 1 just from a few unlucky samples. With 5000 and 20000 samples the data outweighs the prior and the two are almost the same. The error does not keep going down from 5000 to 20000, which we think is just random noise from using one seed.

---

## Problem 2: Mars Rover (PDDL)

Files: `Domain.pddl`, `Problem.pddl`, `Problem_extended.pddl`. Output: `planner_output.txt`.

We wrote our own planner, `rover_planner.py`, which reads the PDDL files directly and runs greedy best-first and A* search.

### Domain and problems

The domain uses only `:strips` and `:typing`. The actions are `move`, `pick-drill`, `collect-soft`, `collect-hard` and `deposit`. Hard rocks need a separate action, `collect-hard`, which requires `(drill-carried ?d)`. This is how we avoid negative preconditions. A bay holds one rock: `(bay-empty ?b)` is a precondition for collecting and `(in-bay ?x ?b)` records what it holds. The one-way slope is just `(connected SiteC SiteD)` with no fact for SiteD to SiteC. In `Problem_extended.pddl` we added Rock6 (soft, SiteE) and Rock7 (hard, SiteF), the new goal, and removed both Base–SiteB connections for the dust storm.

### Results

| Scenario | Search | Plan length (= actions) | States expanded | Time |
|---|---|---:|---:|---:|
| Basic | Greedy best-first | 29 | 11 | 4.1 ms |
| Basic | A* (admissible heuristic) | 25 | 408 | 71.2 ms |
| Extended | Greedy best-first | 54 | 33 | 8.2 ms |
| Extended | A* (admissible heuristic) | 40 | 3341 | 620.5 ms |

The complete action sequences are in `planner_output.txt`.

**Goal check.** We simulated every plan step by step. In the final state of each plan all rocks are at Base, both bays are empty and the rover is at Base. The program prints this check for every plan.

### Task 6

**1. Satisficing vs optimal.** The greedy plans are longer (29 vs 25 and 54 vs 40). Greedy search only looks at the estimated distance to the goal and ignores the cost already spent, so it finds an answer quickly (very few states expanded) but not a short one. For example, in the basic problem it carries a single rock back to Base several times, while A* carries two rocks on most trips. A* is slower and expands many more states, but gives the shortest plan.

**2. Bays and drill in the optimal plan (basic).** There are three trips.
- Trip 1: the rover collects the soft rocks Rock2 (SiteB) and Rock4 (SiteD) into Bay1 and Bay2 and deposits both at Base (steps 1 to 8). No drill is needed here.
- Trip 2: it goes Base → SiteA → SiteC → SiteE and picks up the drill at SiteE (step 12), which is on the way to SiteF. It collects hard Rock5 at SiteF, returns via SiteE to SiteC, collects hard Rock3, and deposits both at Base (steps 13 to 21).
- Trip 3: a short trip to SiteA for Rock1, using one bay (steps 22 to 25).

The drill is picked up once, before the first hard rock, and kept for the rest of the mission.

**3. Extended scenario after the dust storm.** Base to SiteB is closed, so SiteB can only be reached from SiteD. The rover goes Base → SiteA → SiteC → SiteD → SiteB, and **it does use the one-way route SiteC → SiteD** to get there. On the way back it goes SiteB → SiteD → SiteE → SiteC → SiteA → Base. It never needs to go from SiteD to SiteC, since SiteE connects SiteD to SiteC. In the optimal plan the rover first takes Rock6 and the drill at SiteE and collects Rock3, then Rock5 and Rock7 from SiteF, then Rock4 and Rock2 through that SiteB route, and finally Rock1.

---

## Problem 3: Royal Archive (Resolution Refutation)

Code: `Problem3/royal_archive_access.pl`.

### Knowledge representation

- **Constants:** mira, scroll_7, royal_archive
- **Variables:** X (a person), R (a record)
- **Predicates:** archivist(X), verifies(X,R), trusted(X), access(X,R), sealed(R), permitted_inspect(X,R), inspects(X,R), hidden_mark(R), stored(R,A)

| # | Statement | FOL |
|---|---|---|
| 1 | Archivist who verifies a record is trusted | ∀X∀R (archivist(X) ∧ verifies(X,R) → trusted(X)) |
| 2 | Trusted person with access to a sealed record may inspect it | ∀X∀R (trusted(X) ∧ access(X,R) ∧ sealed(R) → permitted_inspect(X,R)) |
| 3 | Inspecting and finding a hidden mark means verifying | ∀X∀R (inspects(X,R) ∧ hidden_mark(R) → verifies(X,R)) |
| 4 | Records stored in the archive are sealed | ∀R (stored(R,royal_archive) → sealed(R)) |
| 5 | scroll_7 is stored in the archive | stored(scroll_7, royal_archive) |
| 6 | Mira has access to scroll_7 | access(mira, scroll_7) |
| 7 | Mira inspects scroll_7 and finds a hidden mark | inspects(mira, scroll_7) ∧ hidden_mark(scroll_7) |
| 8 | Mira is an archivist | archivist(mira) |

**Negated goal:** ¬trusted(mira)

### Conversion to clauses

Removing implications (A → B becomes ¬A ∨ B) and moving negations inward gives only negated atoms, so nothing more needs to be pushed in. All variables are universal, so there is no existential quantifier and **no Skolemization is needed**. Each rule uses its own variable names (standardizing apart), and we split fact 7 into two unit clauses. The CNF clauses are:

1. ¬archivist(X) ∨ ¬verifies(X,R) ∨ trusted(X)
2. ¬trusted(X) ∨ ¬access(X,R) ∨ ¬sealed(R) ∨ permitted_inspect(X,R)
3. ¬inspects(X,R) ∨ ¬hidden_mark(R) ∨ verifies(X,R)
4. ¬stored(R,royal_archive) ∨ sealed(R)
5. stored(scroll_7, royal_archive)
6. access(mira, scroll_7)
7. inspects(mira, scroll_7)
8. hidden_mark(scroll_7)
9. archivist(mira)
10. ¬trusted(mira) (negated goal)

### Resolution

| Step | Resolving | Resolvent |
|---|---|---|
| R1 | clause 3 and clause 7 | ¬hidden_mark(scroll_7) ∨ verifies(mira, scroll_7) |
| R2 | R1 and clause 8 | verifies(mira, scroll_7) |
| R3 | clause 1 and clause 9 | ¬verifies(mira,R) ∨ trusted(mira) |
| R4 | R3 and R2 | trusted(mira) |
| R5 | R4 and clause 10 | [ ] (empty clause) |

The empty clause means the negated goal contradicts the knowledge base, so **Mira is trusted**. Clauses 2, 4, 5 and 6 are not needed for this proof (they only lead to permitted_inspect, which the goal doesn't use). The Prolog file has a section for each transformation step and prints these resolution steps in order, ending with `[]`.
