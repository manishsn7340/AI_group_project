"""A small STRIPS state-space planner for the Mars rover PDDL files.

It loads the typed problem files, grounds the actions in Domain.pddl's action
semantics, and supports greedy best-first (satisficing) and A* with an admissible
heuristic (optimal) search.  It also simulates the returned plan.
"""

from __future__ import annotations

import argparse
from collections import deque
import heapq
import itertools
import re
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STATIC_PREDICATES = {"connected", "soft", "hard"}


def parse_sexpr(text):
    text = re.sub(r";[^\n]*", "", text)
    tokens = re.findall(r"\(|\)|[^\s()]+", text)
    position = 0

    def read():
        nonlocal position
        token = tokens[position]
        position += 1
        if token == "(":
            result = []
            while tokens[position] != ")":
                result.append(read())
            position += 1
            return result
        return token

    return read()


def section(tree, name):
    for item in tree:
        if isinstance(item, list) and item and item[0] == name:
            return item
    raise ValueError(f"Missing section {name}")


def typed_symbols(tokens):
    result = {}
    pending = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "-":
            kind = tokens[index + 1]
            for symbol in pending:
                result[symbol] = kind
            pending = []
            index += 2
        else:
            pending.append(token)
            index += 1
    for symbol in pending:
        result[symbol] = "object"
    return result


def atom(item):
    if not isinstance(item, list) or not item:
        raise ValueError(f"Expected atom, got {item}")
    return tuple(item)


def parse_problem(path):
    tree = parse_sexpr(Path(path).read_text(encoding="utf-8"))
    objects = typed_symbols(section(tree, ":objects")[1:])
    init = {atom(item) for item in section(tree, ":init")[1:]}
    goal_section = section(tree, ":goal")
    goal_items = goal_section[1][1:] if goal_section[1][0] == "and" else [goal_section[1]]
    goal = {atom(item) for item in goal_items}
    static = {fact for fact in init if fact[0] in STATIC_PREDICATES}
    dynamic = frozenset(init - static)
    return objects, static, dynamic, goal


def facts_at(state, predicate, position=None):
    for fact in state:
        if fact[0] != predicate:
            continue
        if position is None or fact[position] == position:
            yield fact


def current_location(state, rover):
    return next(fact[2] for fact in state if fact[0] == "at-rover" and fact[1] == rover)


def action(name, *args):
    return (name,) + tuple(args)


def applicable_actions(state, static, objects):
    rover = next(symbol for symbol, kind in objects.items() if kind == "rover")
    locations = [symbol for symbol, kind in objects.items() if kind == "location"]
    rocks = [symbol for symbol, kind in objects.items() if kind == "rock"]
    bays = [symbol for symbol, kind in objects.items() if kind == "bay"]
    drills = [symbol for symbol, kind in objects.items() if kind == "drill"]
    here = current_location(state, rover)
    actions = []

    for fact in static:
        if fact[0] == "connected" and fact[1] == here:
            actions.append(action("move", rover, here, fact[2]))

    for drill in drills:
        if ("at-drill", drill, here) in state:
            actions.append(action("pick-drill", rover, drill, here))

    for rock in rocks:
        if ("at-rock", rock, here) not in state:
            continue
        rock_type = "soft" if ("soft", rock) in static else "hard"
        empty_bays = sorted(bay for bay in bays if ("bay-empty", bay) in state)
        # The bays are interchangeable.  Using the first available bay is a
        # symmetry-breaking rule and does not remove any plan up to renaming
        # Bay1 and Bay2.
        for bay in empty_bays[:1]:
            if rock_type == "hard" and not any(fact[0] == "drill-carried" for fact in state):
                continue
            if rock_type == "soft":
                actions.append(action("collect-soft", rover, rock, here, bay))
            else:
                for drill in drills:
                    actions.append(action("collect-hard", rover, rock, here, bay, drill))

    for fact in state:
        if fact[0] == "in-bay":
            actions.append(action("deposit", rover, fact[1], fact[2], here))
    return sorted(actions)


def apply_action(state, grounded):
    name = grounded[0]
    args = grounded[1:]
    state = set(state)
    if name == "move":
        _, rover, origin, destination = grounded
        state.remove(("at-rover", rover, origin))
        state.add(("at-rover", rover, destination))
    elif name == "pick-drill":
        _, _rover, drill, location = grounded
        state.remove(("at-drill", drill, location))
        state.add(("drill-carried", drill))
    elif name in ("collect-soft", "collect-hard"):
        _, _rover, rock, location, bay = grounded[:5]
        state.remove(("at-rock", rock, location))
        state.remove(("bay-empty", bay))
        state.add(("in-bay", rock, bay))
    elif name == "deposit":
        _, _rover, rock, bay, location = grounded
        state.remove(("in-bay", rock, bay))
        state.add(("bay-empty", bay))
        state.add(("at-rock", rock, location))
    else:
        raise ValueError(f"Unknown action {name}")
    return frozenset(state)


def heuristic(state, goal, objects, static):
    rover = next(symbol for symbol, kind in objects.items() if kind == "rover")
    base = next(fact[2] for fact in goal if fact[0] == "at-rover")
    rocks_remaining = sum(
        1 for fact in goal if fact[0] == "at-rock" and fact not in state
    )
    rover_penalty = 0 if current_location(state, rover) == base else 1
    bays_used = sum(1 for fact in state if fact[0] == "in-bay")
    return rocks_remaining * 2 + rover_penalty + bays_used


def shortest_distance(static, source, target):
    if source == target:
        return 0
    frontier = deque([(source, 0)])
    visited = {source}
    while frontier:
        location, distance = frontier.popleft()
        for fact in static:
            if fact[0] != "connected" or fact[1] != location or fact[2] in visited:
                continue
            if fact[2] == target:
                return distance + 1
            visited.add(fact[2])
            frontier.append((fact[2], distance + 1))
    return 10**6


def all_pairs_distances(static, objects):
    locations = [symbol for symbol, kind in objects.items() if kind == "location"]
    return {
        (source, target): shortest_distance(static, source, target)
        for source in locations
        for target in locations
    }


def route_lower_bound(current, targets, base, distances):
    """Shortest route visiting all targets and ending at base."""
    targets = tuple(sorted(targets))
    if not targets:
        return distances[(current, base)]
    table = {}
    for index, target in enumerate(targets):
        table[(1 << index, index)] = distances[(current, target)]
    for mask in range(1, 1 << len(targets)):
        for last in range(len(targets)):
            value = table.get((mask, last))
            if value is None:
                continue
            for next_index, target in enumerate(targets):
                if mask & (1 << next_index):
                    continue
                next_mask = mask | (1 << next_index)
                candidate = value + distances[(targets[last], target)]
                old = table.get((next_mask, next_index), 10**9)
                if candidate < old:
                    table[(next_mask, next_index)] = candidate
    full = (1 << len(targets)) - 1
    return min(table[(full, last)] + distances[(targets[last], base)] for last in range(len(targets)))


def admissible_heuristic(state, goal, distances):
    """Admissible lower bound: unavoidable actions plus required travel.

    Every not-yet-delivered rock needs collection and deposit (or only deposit
    if already in a bay).  The route term is the shortest directed route that
    visits every location still containing an uncollected rock and ends at
    Base.  These are disjoint action categories, so their sum is a lower bound.
    """
    current = next(fact[2] for fact in state if fact[0] == "at-rover")
    base = next(fact[2] for fact in goal if fact[0] == "at-rover")
    action_lower_bound = 0
    target_locations = set()
    for fact in goal:
        if fact[0] != "at-rock" or fact in state:
            continue
        rock = fact[1]
        in_bay = next((item for item in state if item[0] == "in-bay" and item[1] == rock), None)
        if in_bay:
            action_lower_bound += 1
            continue
        rock_location = next(
            item[2] for item in state if item[0] == "at-rock" and item[1] == rock
        )
        action_lower_bound += 2
        target_locations.add(rock_location)
    return action_lower_bound + route_lower_bound(current, target_locations, base, distances)


def search(problem_path, strategy):
    objects, static, initial, goal = parse_problem(problem_path)
    distances = all_pairs_distances(static, objects)
    start_time = time.perf_counter()
    expanded = 0
    parents = {initial: None}
    parent_action = {}
    depth = {initial: 0}
    if strategy == "bfs":
        frontier = deque([initial])
    else:
        counter = itertools.count()
        initial_priority = (
            heuristic(initial, goal, objects, static)
            if strategy == "greedy"
            else admissible_heuristic(initial, goal, distances)
        )
        frontier = [(initial_priority, 0, next(counter), initial)]

    found = None
    while frontier:
        if strategy == "bfs":
            state = frontier.popleft()
        elif strategy == "astar":
            _, current_depth, _, state = heapq.heappop(frontier)
            if current_depth != depth[state]:
                continue
        else:
            _, _, _, state = heapq.heappop(frontier)
        if state.issuperset(goal):
            found = state
            break
        expanded += 1
        actions = applicable_actions(state, static, objects)
        for grounded in actions:
            successor = apply_action(state, grounded)
            successor_depth = depth[state] + 1
            if successor in depth and successor_depth >= depth[successor]:
                continue
            parents[successor] = state
            parent_action[successor] = grounded
            depth[successor] = successor_depth
            if strategy == "bfs":
                frontier.append(successor)
            else:
                priority = (
                    heuristic(successor, goal, objects, static)
                    if strategy == "greedy"
                    else successor_depth + admissible_heuristic(successor, goal, distances)
                )
                heapq.heappush(
                    frontier,
                    (priority, successor_depth, next(counter), successor),
                )
    elapsed = time.perf_counter() - start_time
    if found is None:
        raise RuntimeError(f"No plan found for {problem_path} using {strategy}")
    plan = []
    state = found
    while parents[state] is not None:
        plan.append(parent_action[state])
        state = parents[state]
    plan.reverse()
    final_state = initial
    for step in plan:
        final_state = apply_action(final_state, step)
    return {
        "problem": Path(problem_path).name,
        "strategy": (
            "greedy best-first (satisficing)"
            if strategy == "greedy"
            else "A* with admissible heuristic (optimal)"
            if strategy == "astar"
            else "breadth-first (optimal)"
        ),
        "plan": plan,
        "expanded": expanded,
        "seconds": elapsed,
        "objects": objects,
        "static": static,
        "initial": initial,
        "goal": goal,
        "final": final_state,
    }


def action_text(grounded):
    return "(" + " ".join(grounded) + ")"


def result_text(result):
    lines = [
        f"Scenario: {result['problem']}",
        f"Search: {result['strategy']}",
        f"Plan length / total actions: {len(result['plan'])}",
        f"States expanded: {result['expanded']}",
        f"Planning time: {result['seconds'] * 1000:.3f} ms",
        "Action sequence:",
    ]
    lines.extend(f"  {index:02d}. {action_text(step)}" for index, step in enumerate(result["plan"], 1))
    final = result["final"]
    all_rocks_at_base = all(
        fact in final for fact in result["goal"] if fact[0] == "at-rock"
    )
    both_bays_empty = all(
        fact in final for fact in result["goal"] if fact[0] == "bay-empty"
    )
    rover_at_base = all(
        fact in final for fact in result["goal"] if fact[0] == "at-rover"
    )
    lines.extend(
        [
            "Final state (relevant facts):",
            "  " + ", ".join(sorted(f"{fact}" for fact in final if fact[0] in {"at-rover", "at-rock", "in-bay", "bay-empty", "drill-carried"})),
            f"Goal verification: rocks at Base={all_rocks_at_base}, bays empty={both_bays_empty}, rover at Base={rover_at_base}",
            f"Overall plan valid: {all_rocks_at_base and both_bays_empty and rover_at_base}",
        ]
    )
    return "\n".join(lines)


def shortest_path(static, source, target):
    if source == target:
        return [source]
    frontier = deque([source])
    previous = {source: None}
    while frontier:
        location = frontier.popleft()
        neighbours = sorted(
            fact[2] for fact in static if fact[0] == "connected" and fact[1] == location
        )
        for neighbour in neighbours:
            if neighbour in previous:
                continue
            previous[neighbour] = location
            frontier.append(neighbour)
            if neighbour == target:
                path = [target]
                while path[-1] != source:
                    path.append(previous[path[-1]])
                return list(reversed(path))
    raise RuntimeError(f"No route from {source} to {target}")


def compact_initial_state(initial, objects, goal, static):
    rover = next(symbol for symbol, kind in objects.items() if kind == "rover")
    rocks = tuple(symbol for symbol, kind in objects.items() if kind == "rock")
    base = next(fact[2] for fact in goal if fact[0] == "at-rover")
    current = next(fact[2] for fact in initial if fact[0] == "at-rover")
    statuses = []
    for rock in rocks:
        location = next(fact[2] for fact in initial if fact[0] == "at-rock" and fact[1] == rock)
        statuses.append(("base",) if location == base else ("at", location))
    return (current, False, tuple(statuses)), rover, rocks, base


def compact_heuristic(state, rocks, base, distances):
    current, _drill_carried, statuses = state
    target_locations = set()
    action_lower_bound = 0
    for status in statuses:
        if status[0] == "at":
            action_lower_bound += 2
            target_locations.add(status[1])
        elif status[0] == "bay":
            action_lower_bound += 1
    return action_lower_bound + route_lower_bound(current, target_locations, base, distances)


def compact_successors(state, objects, static, rocks, base, drill_location, rover):
    current, drill_carried, statuses = state
    distances = all_pairs_distances(static, objects)
    successors = []

    def movement_actions(source, destination):
        path = shortest_path(static, source, destination)
        return [("move", rover, path[index], path[index + 1]) for index in range(len(path) - 1)]

    if not drill_carried:
        path = movement_actions(current, drill_location)
        successors.append(
            (
                (drill_location, True, statuses),
                path + [("pick-drill", rover, "Drill1", drill_location)],
                len(path) + 1,
            )
        )

    empty_bays = sorted(
        "Bay1" if index == 0 else "Bay2"
        for index in range(2)
        if not any(status[0] == "bay" and status[1] == ("Bay1" if index == 0 else "Bay2") for status in statuses)
    )
    for index, (rock, status) in enumerate(zip(rocks, statuses)):
        if status[0] != "at":
            continue
        rock_is_hard = ("hard", rock) in static
        if rock_is_hard and not drill_carried:
            continue
        if not empty_bays:
            continue
        bay = empty_bays[0]
        path = movement_actions(current, status[1])
        new_statuses = list(statuses)
        new_statuses[index] = ("bay", bay)
        if rock_is_hard:
            collect = ("collect-hard", rover, rock, status[1], bay, "Drill1")
        else:
            collect = ("collect-soft", rover, rock, status[1], bay)
        successors.append(
            ((status[1], drill_carried, tuple(new_statuses)), path + [collect], len(path) + 1)
        )

    for index, (rock, status) in enumerate(zip(rocks, statuses)):
        if status[0] != "bay":
            continue
        path = movement_actions(current, base)
        new_statuses = list(statuses)
        new_statuses[index] = ("base",)
        deposit = ("deposit", rover, rock, status[1], base)
        successors.append(
            ((base, drill_carried, tuple(new_statuses)), path + [deposit], len(path) + 1)
        )

    if all(status[0] == "base" for status in statuses) and current != base:
        path = movement_actions(current, base)
        successors.append(((base, drill_carried, statuses), path, len(path)))
    return successors


def compact_search(problem_path, strategy):
    objects, static, initial, goal = parse_problem(problem_path)
    distances = all_pairs_distances(static, objects)
    compact, rover, rocks, base = compact_initial_state(initial, objects, goal, static)
    drill_location = next(fact[2] for fact in initial if fact[0] == "at-drill")
    start_time = time.perf_counter()
    counter = itertools.count()
    frontier = [
        (
            compact_heuristic(compact, rocks, base, distances),
            0,
            next(counter),
            compact,
        )
    ]
    best_cost = {compact: 0}
    parents = {compact: None}
    parent_actions = {}
    expanded = 0
    found = None
    while frontier:
        _priority, queued_cost, _, state = heapq.heappop(frontier)
        if queued_cost != best_cost[state]:
            continue
        cost = queued_cost
        if all(status[0] == "base" for status in state[2]) and state[0] == base:
            found = state
            break
        expanded += 1
        for successor, action_sequence, edge_cost in compact_successors(
            state, objects, static, rocks, base, drill_location, rover
        ):
            new_cost = cost + edge_cost
            if new_cost >= best_cost.get(successor, 10**9):
                continue
            best_cost[successor] = new_cost
            parents[successor] = state
            parent_actions[successor] = action_sequence
            h = compact_heuristic(successor, rocks, base, distances)
            score = h if strategy == "greedy" else new_cost + h
            heapq.heappush(frontier, (score, new_cost, next(counter), successor))
    if found is None:
        raise RuntimeError(f"No compact plan found for {problem_path}")
    plan_chunks = []
    state = found
    while parents[state] is not None:
        plan_chunks.append(parent_actions[state])
        state = parents[state]
    plan = [step for chunk in reversed(plan_chunks) for step in chunk]
    final = initial
    for step in plan:
        final = apply_action(final, step)
    return {
        "problem": Path(problem_path).name,
        "strategy": "greedy best-first (satisficing)" if strategy == "greedy" else "A* with admissible heuristic (optimal)",
        "plan": plan,
        "expanded": expanded,
        "seconds": time.perf_counter() - start_time,
        "objects": objects,
        "static": static,
        "initial": initial,
        "goal": goal,
        "final": final,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--problem", default="Problem.pddl")
    parser.add_argument("--strategy", choices=("greedy", "bfs", "astar"), default="greedy")
    parser.add_argument("--all", action="store_true", help="run both strategies on both scenarios")
    parser.add_argument("--output", help="also save the planner output to a text file")
    args = parser.parse_args()

    if args.all:
        cases = [
            (ROOT / "Problem.pddl", "greedy"),
            (ROOT / "Problem.pddl", "astar"),
            (ROOT / "Problem_extended.pddl", "greedy"),
            (ROOT / "Problem_extended.pddl", "astar"),
        ]
    else:
        cases = [(Path(args.problem), args.strategy)]
    outputs = [result_text(compact_search(path, strategy)) for path, strategy in cases]
    text = "\n\n".join(outputs) + "\n"
    print(text, end="")
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
