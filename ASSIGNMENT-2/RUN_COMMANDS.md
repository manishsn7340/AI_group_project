# Commands to run each problem

Open a terminal in the `ASSIGNMENT-2` folder first.

```bash
cd /home/mitudk/aa_AI/LAB/GROUP_ASSIGNMENT/ASSIGNMENT-2
pip install -r requirements.txt
```

## Problem 1 – Bayesian Network

```bash
python3 Problem1/smart_home.py
```

Prints all results (Parts A–E) and saves `Problem1/results.txt`, `Problem1/bayesian_network.png` and `Problem1/mean_absolute_difference.png`.
The output is long, so scroll and take a few screenshots, and also one of each of the two PNG files.

## Problem 2 – Mars Rover (PDDL)

```bash
python3 Problem2/rover_planner.py --all --output Problem2/planner_output.txt
```

Runs greedy best-first and A* on both `Problem.pddl` and `Problem_extended.pddl`, prints each plan with its length, states expanded, time and goal check, and saves `Problem2/planner_output.txt`.

To run a single case instead:

```bash
python3 Problem2/rover_planner.py --problem Problem2/Problem.pddl --strategy greedy
python3 Problem2/rover_planner.py --problem Problem2/Problem.pddl --strategy astar
python3 Problem2/rover_planner.py --problem Problem2/Problem_extended.pddl --strategy greedy
python3 Problem2/rover_planner.py --problem Problem2/Problem_extended.pddl --strategy astar
```

## Problem 3 – Royal Archive (Prolog)

```bash
swipl -q -s Problem3/royal_archive_access.pl
```

Prints the transformation steps and the resolution steps, ending with the empty clause `[]`.
