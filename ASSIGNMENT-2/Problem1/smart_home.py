"""Problem 1: Smart-home Bayesian network assignment.
"""

from __future__ import annotations

import itertools
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


OUT_DIR = Path(__file__).resolve().parent
SEED = 42
DATASET_SIZES = (500, 5000, 20000)

DOMAINS = {
    "Weather": ("Hot", "Mild", "Cold"),
    "DayType": ("Weekday", "Weekend"),
    "Occupancy": ("High", "Low"),
    "AC": ("On", "Off"),
    "ApplianceLoad": ("Heavy", "Light"),
    "EnergyConsumption": ("High", "Low"),
}

PARENTS = {
    "Weather": (),
    "DayType": (),
    "Occupancy": ("DayType",),
    "AC": ("Weather", "Occupancy"),
    "ApplianceLoad": ("Occupancy",),
    "EnergyConsumption": ("AC", "ApplianceLoad"),
}
TOPOLOGICAL_ORDER = (
    "Weather",
    "DayType",
    "Occupancy",
    "AC",
    "ApplianceLoad",
    "EnergyConsumption",
)


def binary_cpt(probability_of_first: float, first: str, second: str):
    return {first: probability_of_first, second: 1.0 - probability_of_first}


def expert_model():
    return {
        "Weather": {(): {"Hot": 0.50, "Mild": 0.30, "Cold": 0.20}},
        "DayType": {(): {"Weekday": 0.70, "Weekend": 0.30}},
        "Occupancy": {
            ("Weekday",): binary_cpt(0.45, "High", "Low"),
            ("Weekend",): binary_cpt(0.80, "High", "Low"),
        },
        "AC": {
            ("Hot", "High"): binary_cpt(0.90, "On", "Off"),
            ("Hot", "Low"): binary_cpt(0.60, "On", "Off"),
            ("Mild", "High"): binary_cpt(0.40, "On", "Off"),
            ("Mild", "Low"): binary_cpt(0.15, "On", "Off"),
            ("Cold", "High"): binary_cpt(0.10, "On", "Off"),
            ("Cold", "Low"): binary_cpt(0.05, "On", "Off"),
        },
        "ApplianceLoad": {
            ("High",): binary_cpt(0.75, "Heavy", "Light"),
            ("Low",): binary_cpt(0.35, "Heavy", "Light"),
        },
        "EnergyConsumption": {
            ("On", "Heavy"): binary_cpt(0.92, "High", "Low"),
            ("On", "Light"): binary_cpt(0.68, "High", "Low"),
            ("Off", "Heavy"): binary_cpt(0.55, "High", "Low"),
            ("Off", "Light"): binary_cpt(0.12, "High", "Low"),
        },
    }


def validate_cpts(model):
    errors = []
    rows = 0
    for node, table in model.items():
        for parent_values, distribution in table.items():
            rows += 1
            total = sum(distribution.values())
            if not np.isclose(total, 1.0):
                errors.append(f"{node}{parent_values}: sum={total}")
            if set(distribution) != set(DOMAINS[node]):
                errors.append(f"{node}{parent_values}: incomplete outcomes")
    if errors:
        raise ValueError("Invalid CPTs: " + "; ".join(errors))
    return rows


def joint_probability(assignment, model):
    value = 1.0
    for node in TOPOLOGICAL_ORDER:
        parent_values = tuple(assignment[parent] for parent in PARENTS[node])
        value *= model[node][parent_values][assignment[node]]
    return value


def query(model, target, target_value, evidence=None):
    evidence = evidence or {}
    numerator = 0.0
    denominator = 0.0
    remaining = [
        node for node in TOPOLOGICAL_ORDER if node not in evidence and node != target
    ]
    for values in itertools.product(*(DOMAINS[node] for node in remaining)):
        assignment = dict(evidence)
        assignment[target] = target_value
        assignment.update(dict(zip(remaining, values)))
        p = joint_probability(assignment, model)
        numerator += p
    for target_candidate in DOMAINS[target]:
        for values in itertools.product(*(DOMAINS[node] for node in remaining)):
            assignment = dict(evidence)
            assignment[target] = target_candidate
            assignment.update(dict(zip(remaining, values)))
            denominator += joint_probability(assignment, model)
    return numerator / denominator


def all_queries(model):
    return {
        "Q1": query(model, "EnergyConsumption", "High"),
        "Q2": query(model, "EnergyConsumption", "High", {"Weather": "Hot"}),
        "Q3": query(model, "EnergyConsumption", "High", {"DayType": "Weekend"}),
        "Q4": query(
            model,
            "EnergyConsumption",
            "High",
            {"Weather": "Cold", "Occupancy": "High"},
        ),
        "Q5": query(
            model,
            "Weather",
            "Hot",
            {"EnergyConsumption": "High"},
        ),
        "Q6": query(
            model,
            "AC",
            "On",
            {"EnergyConsumption": "High"},
        ),
        "Q7": query(
            model,
            "AC",
            "On",
            {"EnergyConsumption": "High", "ApplianceLoad": "Heavy"},
        ),
    }


def hand_calculation_q1(model):
    lines = []
    total = 0.0
    lines.append(
        "P(E=High) = sum[w,d,o] P(w)P(d)P(o|d) "
        "sum[a,l] P(a|w,o)P(l|o)P(E=High|a,l)"
    )
    for weather, day, occupancy in itertools.product(
        DOMAINS["Weather"], DOMAINS["DayType"], DOMAINS["Occupancy"]
    ):
        prefix = (
            model["Weather"][()][weather]
            * model["DayType"][()][day]
            * model["Occupancy"][(day,)][occupancy]
        )
        inner = 0.0
        pieces = []
        for ac, load in itertools.product(DOMAINS["AC"], DOMAINS["ApplianceLoad"]):
            term = (
                model["AC"][(weather, occupancy)][ac]
                * model["ApplianceLoad"][(occupancy,)][load]
                * model["EnergyConsumption"][(ac, load)]["High"]
            )
            inner += term
            pieces.append(f"{term:.8f}")
        contribution = prefix * inner
        total += contribution
        lines.append(
            f"  {weather:4s}, {day:7s}, {occupancy:4s}: "
            f"prefix={prefix:.8f} * ({' + '.join(pieces)}) "
            f"= {contribution:.8f}"
        )
    lines.append(f"Q1 = {total:.10f}")
    return total, lines


def draw_network():
    positions = {
        "Weather": (0.0, 1.0),
        "DayType": (0.0, -1.0),
        "Occupancy": (2.0, -1.0),
        "AC": (4.0, 1.0),
        "ApplianceLoad": (4.0, -1.0),
        "EnergyConsumption": (6.0, 0.0),
    }
    edges = [
        ("DayType", "Occupancy"),
        ("Weather", "AC"),
        ("Occupancy", "AC"),
        ("Occupancy", "ApplianceLoad"),
        ("AC", "EnergyConsumption"),
        ("ApplianceLoad", "EnergyConsumption"),
    ]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    boxes = {}
    for node, (x, y) in positions.items():
        color = "#f6bd60" if node in ("Weather", "DayType") else "#84a59d"
        if node == "EnergyConsumption":
            color = "#f28482"
        text = ax.text(
            x,
            y,
            node,
            ha="center",
            va="center",
            fontsize=10,
            zorder=3,
            bbox={"boxstyle": "round,pad=0.55", "fc": color, "ec": "#263238"},
        )
        boxes[node] = text.get_bbox_patch()
    for source, target in edges:
        ax.annotate(
            "",
            xy=positions[target],
            xytext=positions[source],
            arrowprops={
                "arrowstyle": "-|>",
                "lw": 1.8,
                "color": "#355c7d",
                "mutation_scale": 18,
                "patchA": boxes[source],
                "patchB": boxes[target],
                "shrinkA": 2,
                "shrinkB": 2,
            },
            zorder=1,
        )
    ax.set_title("Expert Bayesian Network")
    ax.set_xlim(-0.9, 6.9)
    ax.set_ylim(-1.7, 1.7)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "bayesian_network.png", dpi=180)
    plt.close(fig)


def sample_one(rng, model):
    sample = {}
    for node in TOPOLOGICAL_ORDER:
        parent_values = tuple(sample[parent] for parent in PARENTS[node])
        outcomes = DOMAINS[node]
        probabilities = [model[node][parent_values][outcome] for outcome in outcomes]
        sample[node] = rng.choice(outcomes, p=probabilities)
    return sample


def generate_samples(model, count, rng):
    return [sample_one(rng, model) for _ in range(count)]


def learn_model(data, method):
    learned = {}
    row_count = len(data)
    for node in TOPOLOGICAL_ORDER:
        parent_combinations = list(
            itertools.product(*(DOMAINS[parent] for parent in PARENTS[node]))
        ) or [()]
        learned[node] = {}
        r = len(DOMAINS[node])
        q = len(parent_combinations)
        alpha = 10.0 / (r * q) if method == "Bayesian" else 0.0
        for parent_values in parent_combinations:
            selected = [
                record
                for record in data
                if tuple(record[parent] for parent in PARENTS[node]) == parent_values
            ]
            total = len(selected)
            distribution = {}
            for outcome in DOMAINS[node]:
                count = sum(record[node] == outcome for record in selected)
                if method == "MLE":
                    distribution[outcome] = count / total if total else 1.0 / r
                else:
                    distribution[outcome] = (count + alpha) / (total + r * alpha)
            learned[node][parent_values] = distribution
    if row_count == 0:
        raise ValueError("Cannot learn from an empty dataset")
    validate_cpts(learned)
    return learned


def format_cpt(node, model, title=None):
    lines = [title or f"{node} CPT"]
    for parents, distribution in model[node].items():
        label = ", ".join(
            f"{parent}={value}" for parent, value in zip(PARENTS[node], parents)
        ) or "no parents"
        values = ", ".join(
            f"P({outcome})={distribution[outcome]:.6f}" for outcome in DOMAINS[node]
        )
        lines.append(f"  {label}: {values}")
    return lines


def empirical_summary(data):
    weather_counts = {value: sum(x["Weather"] == value for x in data) for value in DOMAINS["Weather"]}
    combination_counts = {
        (weather, occupancy): sum(
            x["Weather"] == weather and x["Occupancy"] == occupancy for x in data
        )
        for weather, occupancy in itertools.product(
            DOMAINS["Weather"], DOMAINS["Occupancy"]
        )
    }
    return weather_counts, combination_counts


def conditional_evidence_count(data, evidence):
    return sum(all(record[key] == value for key, value in evidence.items()) for record in data)


def main():
    expert = expert_model()
    cpt_rows = validate_cpts(expert)
    draw_network()
    expert_queries = all_queries(expert)
    q1_hand, hand_lines = hand_calculation_q1(expert)
    assert np.isclose(q1_hand, expert_queries["Q1"])

    output = []
    output.append("PROBLEM 1: SMART HOME ENERGY CONSUMPTION ANALYSIS")
    output.append("Team: E.D.I.T.H")
    output.append("Group members: SATYAM SINGH (B24CS038); SHIVAM CHAURASIA (B24CS039); "
                  "Manish Shyoran (B24CS026); MITU KUMAR (B24CS029)")
    output.append(f"Random seed: {SEED}")
    output.append(f"CPT validation: PASS ({cpt_rows} rows; every row sums to 1)")
    output.append("\nPART A - EXPERT MODEL")
    output.append("Network edges: DayType->Occupancy, Weather->AC, Occupancy->AC, "
                  "Occupancy->ApplianceLoad, AC->EnergyConsumption, "
                  "ApplianceLoad->EnergyConsumption")
    for key, value in expert_queries.items():
        output.append(f"{key}: {value:.10f}")
    output.append("\nQ1 hand calculation:")
    output.extend(hand_lines)
    output.append(f"Code Q1 = {expert_queries['Q1']:.10f}; hand Q1 = {q1_hand:.10f}; MATCH")
    output.append(
        f"Explaining away: Q6=P(AC=On|E=High)={expert_queries['Q6']:.10f}; "
        f"Q7=P(AC=On|E=High,L=Heavy)={expert_queries['Q7']:.10f}. "
        "Observing the alternative cause ApplianceLoad=Heavy explains part of the high-energy "
        "evidence, so the posterior probability of AC=On DECREASES "
        f"({expert_queries['Q6']:.4f} -> {expert_queries['Q7']:.4f})."
    )

    output.append("\nPART B - CONDITIONAL INDEPENDENCE")
    b1_left = query(expert, "Weather", "Hot")
    b1_right = query(expert, "Weather", "Hot", {"DayType": "Weekend"})
    b2_left = query(expert, "Weather", "Hot", {"EnergyConsumption": "High"})
    b2_right = query(
        expert,
        "Weather",
        "Hot",
        {"EnergyConsumption": "High", "DayType": "Weekend"},
    )
    b3_left = query(expert, "Weather", "Hot", {"Occupancy": "High"})
    b3_right = query(
        expert,
        "Weather",
        "Hot",
        {"Occupancy": "High", "ApplianceLoad": "Heavy"},
    )
    output.append("1. Weather independent of DayType: YES. They are separate root nodes.")
    output.append(f"   Numerical check: {b1_left:.10f} vs {b1_right:.10f}")
    output.append(
        "2. Weather independent of DayType given EnergyConsumption: NO. "
        "Observing the collider EnergyConsumption opens two paths: "
        "Weather->AC->EnergyConsumption<-ApplianceLoad<-Occupancy<-DayType, and the shorter "
        "Weather->AC<-Occupancy<-DayType, where the collider AC is opened because its "
        "descendant EnergyConsumption is observed."
    )
    output.append(f"   Numerical check: {b2_left:.10f} vs {b2_right:.10f}")
    output.append(
        "3. Weather independent of ApplianceLoad given Occupancy: YES. "
        "The path Weather->AC<-Occupancy->ApplianceLoad is blocked at the collider AC "
        "and conditioning on Occupancy blocks the fork path."
    )
    output.append(f"   Numerical check: {b3_left:.10f} vs {b3_right:.10f}")

    rng = np.random.default_rng(SEED)
    all_data = generate_samples(expert, max(DATASET_SIZES), rng)
    comparison = {}
    output.append("\nPART C - SYNTHETIC DATA")
    for size in DATASET_SIZES:
        data = all_data[:size]
        weather_counts, combination_counts = empirical_summary(data)
        output.append(f"Dataset size {size}:")
        output.append("  Weather counts: " + ", ".join(
            f"{key}={value} ({value / size:.6f})" for key, value in weather_counts.items()
        ))
        output.append("  (Weather, Occupancy) counts: " + ", ".join(
            f"({weather},{occupancy})={count}"
            for (weather, occupancy), count in combination_counts.items()
        ))

        comparison[size] = {}
        output.append(f"\nPART D - LEARNING, DATASET SIZE {size}")
        for method in ("MLE", "Bayesian"):
            learned = learn_model(data, method)
            learned_queries = all_queries(learned)
            comparison[size][method] = learned_queries
            output.append(f"{method} learned AC CPT alongside expert:")
            output.extend(format_cpt("AC", expert, "AC CPT (expert)"))
            output.extend(format_cpt("AC", learned, f"AC CPT (learned, {method})"))
            output.append("Queries: " + ", ".join(
                f"{key}={value:.10f}" for key, value in learned_queries.items()
            ))

    output.append("\nPART E - COMPARISON")
    headers = "Query       Expert          MLE             Bayesian        |Diff| MLE   |Diff| Bayesian"
    for size in DATASET_SIZES:
        output.append(f"\nDataset size: {size}")
        output.append(headers)
        for key in expert_queries:
            mle = comparison[size]["MLE"][key]
            bayes = comparison[size]["Bayesian"][key]
            output.append(
                f"{key:<11}{expert_queries[key]:<16.10f}{mle:<16.10f}"
                f"{bayes:<16.10f}{abs(expert_queries[key]-mle):<15.10f}"
                f"{abs(expert_queries[key]-bayes):.10f}"
            )
        output.append(
            f"Mean absolute difference: MLE={np.mean([abs(expert_queries[k]-comparison[size]['MLE'][k]) for k in expert_queries]):.10f}, "
            f"Bayesian={np.mean([abs(expert_queries[k]-comparison[size]['Bayesian'][k]) for k in expert_queries]):.10f}"
        )

    mean_mle = []
    mean_bayes = []
    for size in DATASET_SIZES:
        mean_mle.append(np.mean([abs(expert_queries[k] - comparison[size]["MLE"][k]) for k in expert_queries]))
        mean_bayes.append(np.mean([abs(expert_queries[k] - comparison[size]["Bayesian"][k]) for k in expert_queries]))
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(DATASET_SIZES, mean_mle, marker="o", label="MLE")
    ax.plot(DATASET_SIZES, mean_bayes, marker="o", label="Bayesian (BDeu, ESS=10)")
    ax.set_xscale("log")
    ax.set_xlabel("Dataset size (log scale)")
    ax.set_ylabel("Mean absolute difference over Q1-Q7")
    ax.set_title("Learned-model error versus dataset size")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_DIR / "mean_absolute_difference.png", dpi=180)
    plt.close(fig)

    small_data = all_data[:500]
    evidence = {
        "Q1": {},
        "Q2": {"Weather": "Hot"},
        "Q3": {"DayType": "Weekend"},
        "Q4": {"Weather": "Cold", "Occupancy": "High"},
        "Q5": {"EnergyConsumption": "High"},
        "Q6": {"EnergyConsumption": "High"},
        "Q7": {"EnergyConsumption": "High", "ApplianceLoad": "Heavy"},
    }
    errors = {
        key: abs(expert_queries[key] - comparison[500]["MLE"][key])
        for key in expert_queries
    }
    largest_query = max(errors, key=errors.get)
    output.append("\n500-sample error diagnosis")
    output.append("Evidence counts: " + ", ".join(
        f"{key}={conditional_evidence_count(small_data, value)}" for key, value in evidence.items()
    ))
    output.append(
        f"Largest MLE error: {largest_query} (absolute error={errors[largest_query]:.10f}). "
        "Its conditioning evidence is comparatively infrequent, so its learned conditional "
        "probability is estimated from fewer samples and has higher sampling variance."
    )
    output.append((
        "For this seed, Bayesian estimation is slightly better on the 500-sample dataset "
        "(mean error {mb:.4f} vs {mm:.4f} for MLE; it wins on only some queries) because the BDeu "
        "prior smooths sparse CPT rows. At 5000 and 20000 samples the two estimators are "
        "practically equal (MLE marginally ahead) and both errors are tiny. The error is not "
        "strictly monotone between 5000 and 20000 because it is dominated by sampling noise "
        "of this single seed (the datasets are nested prefixes of one stream)."
    ).format(mb=mean_bayes[0], mm=mean_mle[0]))
    output.append("\nGenerated files: bayesian_network.png, mean_absolute_difference.png")

    text = "\n".join(output) + "\n"
    (OUT_DIR / "results.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
