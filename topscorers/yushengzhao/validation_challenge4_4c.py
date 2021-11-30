import time

from qiskit import Aer
from qiskit.compiler import transpile
from qiskit import execute

backend = Aer.get_backend("qasm_simulator")

seed = 42
shots = 512
precision_limit = 0.60

from problem_set import validation_set_4c_fixed, validation_set_4c_random

problem_set = validation_set_4c_fixed + validation_set_4c_random

def new_grader_function(hist, L1, L2, C1, C2, C_max, optimal_value, max_labels=20):
    sorted_hist = sorted(hist.items(), key=lambda x: -x[1])[:max_labels]
    max_precision = 0
    for key, _ in sorted_hist:
        ans_cost = 0
        ans_value = 0
        for i, a in enumerate(key):
            if a == "0":
                ans_value += L1[i]
                ans_cost += C1[i]
            else:
                ans_value += L2[i]
                ans_cost += C2[i]
        if ans_cost <= C_max and max_precision < ans_value / optimal_value:
            max_precision = ans_value / optimal_value
    return max_precision

def compute_score(depth, num_ops, precision = 1):
    score = depth * 50 + num_ops.get("cx", 0) * 10 + (num_ops.get("rz", 0) + num_ops.get("sx", 0)) * 1
    return score

def prepare_ex4c(submitted_function):

    qcs = []

    for _, input_i in enumerate(problem_set):
        (L1, L2, C1, C2, C_max, _) = input_i.values()
        qc = submitted_function(L1, L2, C1, C2, C_max)
        tqc = transpile(qc, backend = backend, basis_gates = ["sx", "rz", "cx"], optimization_level = 0, seed_transpiler = seed)
        qcs.append(tqc)

    print("run job")
    t1 = time.time()
    job = execute(qcs, backend = backend, shots = shots, optimization_level = 0, seed_simulator = seed)
    t2 = time.time()
    print("created jobs (", t2 - t1, "s)")
    return qcs, job

def grade(qcs, result):

    precisions = []
    total_score = 0
    num_inputs = len(problem_set)
    for i, input_i in enumerate(problem_set):
        (L1, L2, C1, C2, C_max, optimal_value) = input_i.values()
        hist = result.get_counts(i)
        precision = new_grader_function(hist, L1, L2, C1, C2, C_max, optimal_value)
        precisions.append(precision)
        print("Precision for instance", i + 1, ":", precision)

        depth, num_ops = qcs[i].depth(), qcs[i].count_ops()
        print("depth:", depth)
        print("num_ops:", num_ops)
        score = compute_score(depth, num_ops)
        print("Score:", score)

        total_score += score
        print()
            
    print()
    average_precision = sum(precisions) / num_inputs
    print("Average Precision:", average_precision)
    print("Total Score:", total_score)

    if average_precision >= precision_limit:
        return True, total_score
    else:
        msg = "Unscored. The average precision is lower than the threshold " + str(precision_limit)
        return False, msg

"""
USAGE

from validation_challenge4_4c import prepare_ex4c, grade

qcs, job = prepare_ex4c(submitted_function)
pass_or_not, score = grade(qcs, job.result())
print(pass_or_not)
print(score)

"""