"""
Challenge 4c solver function for the IBM Quantum Fall Challenge 2021
Author: Kamen Petroff (kpe)
Score: old:260_084 new:3_482_625

The first accepted solution was implemented using the qiskit builtin QFT.
While unit testing the const_adder() I've also implemented a QFT from scratch,
following the figures/diagrams in arXiv:quant-ph/0008033.pdf, and it looked like
my custom QFT version performed slightly better than the built in one.

Only then I noticed, that the qubit requirements of the original problem
could be reduced by solving the equivalent problem (0, C2-C1, C_max-sum(C1)).

Once it worked I started looking for ways of optimizing the score, and noticed
that I could wrap all subroutine_add_const() calls in the QRAM part in
a single QFT/IQFT block. Later I also included the addition of the w offset
in the same block, so in total I had only one QFT/IQFT.

Observing that for all 24 instances max_c <= 23 and C_max <= 11, we 
conclude that all cost summations and constrain calculations can be
completed within a 5 qubit register - using the MSB as a infeasibility flag,
by shifting the cost sum range from (0, max_c) by `2**4 - C_max`
to (2**4-C_max, 2**4-C_max+max_c) which
for the given 24 instances with max(max_c)=23 and max(C_max)=11 results
in the maximal interval [5,28] thus fitting in the 5 qubits.

A further optimization is to observe that the first QFT acts on
the data qubits initialized to H|0> by applying a H-Gate on each
qubit followed by conditional rotations. The second application of
the H-Gate sets the data qubit back to the |0>, so that the following
conditional rotations have no effect. Therefore the initial QFT can be
replaced by a H-Gate on all data qubits.

Summary of the approach:
1. Solving the smaller equivalent problem with C1=0, i.e. (0, C2-C1, C_max-sum(C1)).
2. Using a single QFT/IQFT transform and performing all additions in QFT space.
3. Reducing/replacing the initial QFT with H.
4. Using the most significant `carry` bit in the data register (2**c - C_max -1 + cost) directly as a flag qubit and c=data_bits-1.
5. Using approximate QFT with approximation_degree 1 or 2.
6. Using transpile(['cx','u3'], optimization_level=3)

Please find additional comments in the code.
**N.B.**

1. even the present solution uses one qubit less than the suggested `data_qubits` value (6 for the reduced problem),
   it accurately sets the constraint flag (the MSB data_qubit) to 1 for infeasible solutions with cost > C_max.

2. the correctness of the solution can be verified by using better suited values
   for the parameters p and alpha (like p=7,9 and alpha=2):

- p=9,alpha=2):
  - top20 max ratio - is 100% for all problem instances except 2 for which it is 97% and 98%
  - the best solution (max ratio) has maximal count rank 0 in 14 cases, in 7 cases is between 1 and 5,
    and has in only 2 cases rank between 6 and 10 (rank being the position when sorting by counts)
  - the counts of the best solution is on average around 43 (when using 512 shots)

   ratio: 100 100 98 100 100 100 100 100 100 100 100 100 100 100 100 100 100 100 100 100 100 100 100 97
  counts: 56 45 13 21 51 30 29 42 126 17 105 29 18 30 57 65 69 13 39 16 50 23 73 24
   ranks: 0 0 10 0 0 1 1 1 0 0 0 0 7 2 0 0 0 4 0 1 0 3 0 5
   
"""

from typing import Union
import math

import numpy as np

import qiskit
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit import Gate

# True for using the explicit flag qubit, False for using the MSB in data register
# when USE_FLAG_QUBIT==True - we need only (data_qubits-1) qubits
USE_SCORING    = "new"  # new, old

USE_5_QUBITS   = True   # True to use 1 qubit less than the template suggestion
QFT_AD         = 1      # QFT approximation degree (number of terms to omit)
OPT_LEVEL      = 3      # transpiler optimization level (0-3) or -1 to disable

if USE_SCORING == 'new':
    QFT_AD       = 2
    USE_5_QUBITS = True
elif USE_SCORING == 'old':
    QFT_AD       = 1
    USE_5_QUBITS = False
else:
    raise "Unexpected value for USE_SCORING (expecting one of {new, old})"




def transpile(qc: QuantumCircuit) -> QuantumCircuit:
    # this was added, but can be disabled with setting OPT_LEVEL to -1 above.
    if OPT_LEVEL != -1:
        qc = qiskit.transpile(qc, basis_gates=['cx', 'u3'], seed_transpiler=42, optimization_level=OPT_LEVEL)
    return qc


def transpile_optimize(fn):
    def wrapper(*args, **kwargs):
        return transpile(fn(*args, **kwargs))
    return wrapper


@transpile_optimize
def solver_function(L1: list, L2: list, C1: list, C2: list, C_max: int) -> QuantumCircuit:
    """
    Solves the 4c knapsack problem (assuming C1<C2, and L1<L2).
    """

    # print name and score
    author = 'Kamen Petroff (kpe)'
    score = 'old:260_084 new:3_482_625'
    print(f'{author}: {score}')

    # first let's convert it to the equivalent problem with cost (0, C2-C1)
    C1, C2 = np.array(C1), np.array(C2)
    C1, C2, C_max = C1 - C1, C2 - C1, C_max - C1.sum()

    # the number of qubits representing answers
    index_qubits = len(L1)

    # the maximum possible total cost
    max_c = sum([max(l0, l1) for l0, l1 in zip(C1, C2)])

    # the number of qubits representing data values can be defined using the maximum possible total cost as follows:
    data_qubits = math.ceil(math.log(max_c, 2)) + 1 if not max_c & (max_c - 1) == 0 else math.ceil(math.log(max_c, 2)) + 2

    if USE_5_QUBITS:
        data_qubits -= 1

    ### Phase Operator ###
    # return part
    def phase_return(index_qubits: int, gamma: float, L1: list, L2: list, to_gate=True) -> Union[Gate, QuantumCircuit]:
        qr_index = QuantumRegister(index_qubits, "index")
        qc = QuantumCircuit(qr_index)

        for ndx in range(index_qubits):
            qc.p(- gamma * (L2[ndx] - L1[ndx]), qr_index[ndx])

        return qc.to_gate(label=" phase return ") if to_gate else qc

    #
    # QFT implementation (with qiskit bit ordering).
    #
    def qft(data_qubits: int, approximation_degree: int = QFT_AD, to_gate=True) -> Union[Gate, QuantumCircuit]:
        qr = QuantumRegister(data_qubits)
        qc = QuantumCircuit(qr)

        for target in reversed(range(data_qubits)):
            qc.h(target)
            for k, control in enumerate(reversed(range(target)), start=2):
                if k > (data_qubits - approximation_degree):
                    continue
                qc.cp(2 * np.pi / (2 ** k), control, target)

        return qc.to_gate(label=" qft ") if to_gate else qc

    #
    # Adds a constant to tha data register in QFT space.
    # Should be used with the above QFT implementation.
    #
    def subroutine_add_const(data_qubits: int, const: int, to_gate=True) -> Union[Gate, QuantumCircuit]:
        qr_data = QuantumRegister(data_qubits)
        qc = QuantumCircuit(qr_data)

        # prepares the const bits in a list
        cbits = list(map(int, reversed(f"{np.abs(const):02b}".zfill(data_qubits))))

        for target in reversed(range(data_qubits)):
            tsum = 0  # cumulative phase for target
            for k, control in enumerate(reversed(range(target + 1)), start=1):
                cbit = cbits[control]
                if cbit:
                    tsum += 1 / 2 ** k
            if tsum > 0:
                qc.p(np.sign(const) * 2 * np.pi * tsum, qr_data[target])

        return qc.to_gate(label=" [+" + str(const) + "] ") if to_gate else qc

    #
    # This is how a **single** QFT addition of a const to the
    # data register would look like, however we'll not use this method,
    # but instead do a single QFT, do all phase rotations there, before
    # doing the inverse IQFT transformation.
    # (This is actually the main idea in optimizing the 4c solution.)
    #
    def const_adder(data_qubits: int, const: int, to_gate=True) -> Union[Gate, QuantumCircuit]:
        qr_data = QuantumRegister(data_qubits)
        qc = QuantumCircuit(qr_data)

        qc.append(qft(data_qubits), qr_data[:])
        qc.append(subroutine_add_const(data_qubits, const, to_gate=False).to_gate(), qr_data[:])
        qc.append(qft(data_qubits).inverse(), qr_data[:])

        return qc.to_gate(label=" [+" + str(const) + "] ") if to_gate else qc

    #
    # This is how the QRAM cost calculation function would look like, however
    # we will not use it directly, but do all additions in QFT space, wrapped
    # in a single QFT.
    #
    def _cost_calculation(index_qubits: int, data_qubits: int, list1: list, list2: list, to_gate=True) -> Union[Gate, QuantumCircuit]:
        qr_index = QuantumRegister(index_qubits, "index")
        qr_data = QuantumRegister(data_qubits, "data")
        qc = QuantumCircuit(qr_index, qr_data)

        # note the -1 bellow - the cost would fit in (data_qubits-1) bits,
        # and we'll use the most significant bit to flag solutions with an infeasible cost.
        for i, (val1, val2) in enumerate(zip(list1, list2)):
            qc.append(const_adder(data_qubits - 1, val2).control(1), [qr_index[i]] + qr_data[:-1])
            qc.x(qr_index[i])
            qc.append(const_adder(data_qubits - 1, val1).control(1), [qr_index[i]] + qr_data[:-1])
            qc.x(qr_index[i])

        return qc.to_gate(label=" Cost Calculation ") if to_gate else qc

    #
    # This is the actual cost_calculation() used:
    #
    # Here we'll complete the QRAM cost addition to the data register
    # in QFT space and also add a (2^c - (C_max+1)) term, so that the
    # most significant bit of the data register is set to 1 whenever
    # the cost in the data register exceeds C_max (i.e. cost > C_max).
    #
    # N.B. even the paper uses a (cost >= C_max) condition to set a penalty
    # of alpha*(cost - C_max), the penalty would be zero for cost == C_max,
    # therefore we use a strict inequality.
    #
    def cost_calculation(index_qubits: int, data_qubits: int, list1: list, list2: list, to_gate: bool = True) -> Union[Gate, QuantumCircuit]:
        qr_index = QuantumRegister(index_qubits, "index")
        qr_data = QuantumRegister(data_qubits, "data")
        qc = QuantumCircuit(qr_index, qr_data)

        ## lets mark only cost > C_max

        c = data_qubits - 1      # use the MSB in data directly as a flag qubit
        w = 2 ** c - (C_max + 1)

        ###########
        ## QFT start - do all additions in QFT space
        # qc.append(qft(data_qubits), qr_data[:])
        qc.h(qr_data[:])  # initially all data qubits are |0> so qft is just Hadamard

        # QRAM
        for i, (val1, val2) in enumerate(zip(list1, list2)):
            assert val1 == 0
            qc.append(subroutine_add_const(data_qubits, val2).control(1), [qr_index[i]] + qr_data[:])

    	qc.append(subroutine_add_const(data_qubits, w), qr_data[:])  # offset by w = 2**c -(C_max+1) to flag infeasible costs in MSB

        qc.append(qft(data_qubits).inverse(), qr_data[:])
        ## QFT end
        ####################

        return qc.to_gate(label=" Cost Constraint Testing ") if to_gate else qc

    #
    # After returning from QFT space, we can use the MSB of the data register
    # to set the flag qubit (for infeasible solutions).
    #
    def constraint_testing(data_qubits: int, C_max: int, to_gate=True) -> Union[Gate, QuantumCircuit]:
        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_data, qr_f)


        # qc.cx(qr_data[-1], qr_f) # we'll be using the MSB directly without the explicit qr_f qubit

        return qc.to_gate(label=" Constraint Testing ") if to_gate else qc

    # penalty part
    def penalty_dephasing(data_qubits: int, alpha: float, gamma: float, to_gate=True) -> Union[Gate, QuantumCircuit]:
        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_data, qr_f)

        c = data_qubits - 1

        #
        # we use the qr_data[-1] as a flag directly
        #
        qr_f = qr_data[-1]

        for k in range(c):
            qc.cp(alpha * gamma * (2**k), qr_f, qr_data[k])
        qc.p(-alpha * gamma * (2**c), qr_f)

        return qc.to_gate(label=" Penalty Dephasing ") if to_gate else qc

    # penalty part
    def reinitialization(index_qubits: int, data_qubits: int, C1: list, C2: list, C_max: int, to_gate=True) -> Union[Gate, QuantumCircuit]:
        qr_index = QuantumRegister(index_qubits, "index")
        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_index, qr_data, qr_f)

        # constrain_testing is empty see above
        qc.append(constraint_testing(data_qubits, C_max).inverse(), qr_data[:] + qr_f[:])
        qc.append(cost_calculation(index_qubits, data_qubits, C1, C2, to_gate=True).inverse(), qr_index[:] + qr_data[:])

        return qc.to_gate(label=" Reinitialization ") if to_gate else qc

    ### Mixing Operator ###
    def mixing_operator(index_qubits: int, beta: float, to_gate=True) -> Union[Gate, QuantumCircuit]:
        qr_index = QuantumRegister(index_qubits, "index")
        qc = QuantumCircuit(qr_index)

        for ndx in range(index_qubits):
            qc.rx(2 * beta, ndx)

        return qc.to_gate(label=" Mixing Operator ") if to_gate else qc

    #
    # everything bellow this line was not touched, with exception
    # of the transpiling/optimization in the last line which can be
    # controlled using the OPT_LEVEL=-1 define above.
    #
    ##############################

    qr_index = QuantumRegister(index_qubits, "index")  # index register
    qr_data = QuantumRegister(data_qubits, "data")  # data register
    qr_f = QuantumRegister(1, "flag")  # flag register
    cr_index = ClassicalRegister(index_qubits, "c_index")  # classical register storing the measurement result of index register
    qc = QuantumCircuit(qr_index, qr_data, qr_f, cr_index)

    ### initialize the index register with uniform superposition state ###
    qc.h(qr_index)

    ### DO NOT CHANGE THE CODE BELOW
    p = 5
    alpha = 1
    for i in range(p):
        ### set fixed parameters for each round ###
        beta = 1 - (i + 1) / p
        gamma = (i + 1) / p

        ### return part ###
        qc.append(phase_return(index_qubits, gamma, L1, L2), qr_index)

        ### step 1: cost calculation ###
        qc.append(cost_calculation(index_qubits, data_qubits, C1, C2), qr_index[:] + qr_data[:])

        ### step 2: Constraint testing ###
        qc.append(constraint_testing(data_qubits, C_max), qr_data[:] + qr_f[:])

        ### step 3: penalty dephasing ###
        qc.append(penalty_dephasing(data_qubits, alpha, gamma), qr_data[:] + qr_f[:])

        ### step 4: reinitialization ###
        qc.append(reinitialization(index_qubits, data_qubits, C1, C2, C_max), qr_index[:] + qr_data[:] + qr_f[:])

        ### mixing operator ###
        qc.append(mixing_operator(index_qubits, beta), qr_index)

    ### measure the index ###
    ### since the default measurement outcome is shown in big endian, it is necessary to reverse the classical bits in order to unify the endian ###
    qc.measure(qr_index, cr_index[::-1])

    return qc
