"""
Challenge 4c solver function for the IBM Quantum Fall Challenge 2021
Author: Rafał Pracht
Score: 743,349

Summary of the approach:
1. Compute cost using addition with Quantum Fourier Transform
    a. For both number c1 and c2 I've calculate the binary 'and' between them
    b. Then I can add this value without control.
    c. The remaining part is added using control.
    d. Additionally we don't add cost (c1, c2) in the order of index, but we do some sort to improve pararelism.
2. Add w = 2 ** c - C_max to the cost
3. Calculate the flat if cost(z) +w > C_max + w = 2 ** c (exacly as in paper)
4. Calculate penalty_dephasing using the cost
"""

import numpy as np
from typing import Union
import math
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit import Gate
from qiskit.circuit.library import QFT


def solver_function2(L1: list, L2: list, C1: list, C2: list, C_max: int) -> QuantumCircuit:
    # the number of qubits representing answers
    index_qubits = len(L1)

    # the maximum possible total cost
    max_c = sum([max(l0, l1) for l0, l1 in zip(C1, C2)])

    # the number of qubits representing data values can be defined using the maximum possible total cost as follows:
    data_qubits = math.ceil(math.log(max_c, 2)) + 1 if not max_c & (max_c - 1) == 0 else math.ceil(
        math.log(max_c, 2)) + 2

    c = math.ceil(math.log2(C_max))
    w = 2 ** c - C_max
    ancilla_qubits = max(data_qubits - c - 2, 0)

    global sum_common
    sum_common = 0

    ### Phase Operator ###
    # return part
    def phase_return(index_qubits: int, gamma: float, L1: list, L2: list, to_gate=True) -> Union[Gate, QuantumCircuit]:
        qr_index = QuantumRegister(index_qubits, "index")
        qc = QuantumCircuit(qr_index)

        ##############################
        ### U_1(gamma * (lambda2 - lambda1)) for each qubit ###
        # Provide your code here
        for i, q in enumerate(qr_index):
            qc.u1(-0.5 * gamma * (L2[i] - L1[i]), q)
        ##############################

        return qc.to_gate(label=" phase return ") if to_gate else qc

    # penalty part
    def subroutine_add_const(data_qubits: int, const: int, to_gate=True) -> Union[Gate, QuantumCircuit]:
        # qc = QuantumCircuit(data_qubits)
        qr_data = QuantumRegister(data_qubits, "data")
        qc = QuantumCircuit(qr_data)

        ##############################
        ### Phase Rotation ###
        formatstr = '0%ib' % data_qubits
        bconst = [x for x in format(const, formatstr)]

        for i, c in enumerate(bconst[::-1]):
            if c == '1':
                for idx, j in enumerate(range(i, data_qubits)):
                    qc.p(2 * np.pi / 2 ** (idx + 1), qr_data[j])

        ##############################
        return qc.to_gate(label=" [+" + str(const) + "] ") if to_gate else qc

    # penalty part
    def const_adder(data_qubits: int, const: int, to_gate=True) -> Union[Gate, QuantumCircuit]:
        qr_data = QuantumRegister(data_qubits, "data")
        qc = QuantumCircuit(qr_data)

        ##############################
        ### QFT ###
        # do it once in the upper method
        ##############################

        ##############################
        ### Phase Rotation ###
        qc.append(subroutine_add_const(data_qubits, const), qr_data)

        ##############################

        ##############################
        ### IQFT ###
        # do it once in the upper method
        ##############################
        return qc.to_gate(label=" [ +" + str(const) + "] ") if to_gate else qc

    # penalty part
    def cost_calculation(index_qubits: int, data_qubits: int, list1: list, list2: list, to_gate=True) -> Union[
        Gate, QuantumCircuit]:

        qr_index = QuantumRegister(index_qubits, "index")
        qr_data = QuantumRegister(data_qubits + ancilla_qubits, "data")
        qc = QuantumCircuit(qr_index, qr_data)

        ### QFT ###
        qc.append(
            QFT(num_qubits=data_qubits, approximation_degree=0, do_swaps=False, inverse=False, insert_barriers=False,
                name='qft').to_gate(), qr_data[:data_qubits])

        global sum_common
        sum_common = 0
        ret = []
        for i, (val1, val2) in enumerate(zip(list1, list2)):
            # common part
            common = val1 & val2
            sum_common += common

            if val2 - common > 0:
                ret.append((i, 2, val2 - common))
            if val1 - common > 0:
                ret.append((i, 1, val1 - common))

        # sort
        nret = []
        last = ret.pop(0)
        nret.append(last)
        while len(ret) > 0:
            idx = 0
            for j, (i, x, v) in enumerate(ret):
                if i != last[0] and last[2] & v == 0:
                    idx = j
                    break
            last = ret.pop(idx)
            nret.append(last)

        for (i, x, val) in nret:
            if x == 1:
                qc.x(qr_index[i])

            qc.append(const_adder(data_qubits, val).control(1),
                      qr_index[i:(i + 1)] + qr_data[:data_qubits])

            if x == 1:
                qc.x(qr_index[i])

        # Add common
        # This will be done in constraint_testing, together with w
        # if sum_common > 0:
        #     qc.append(const_adder(data_qubits, sum_common), qr_data[:data_qubits])

        ### IQFT ###
        # qc.append(
        #     QFT(num_qubits=data_qubits, approximation_degree=0, do_swaps=False, inverse=True, insert_barriers=False,
        #         name='iqft').to_gate(), qr_data[:data_qubits])

        return qc.to_gate(label=" Cost Calculation ") if to_gate else qc

    # penalty part
    def constraint_testing(data_qubits: int, C_max: int, to_gate=True) -> Union[Gate, QuantumCircuit]:

        qr_data = QuantumRegister(data_qubits + ancilla_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_data, qr_f)

        ##############################
        if w + sum_common > 0:
            qc.append(const_adder(data_qubits, w + sum_common), qr_data[:data_qubits])
        qc.append(
            QFT(num_qubits=data_qubits, approximation_degree=0, do_swaps=False, inverse=True, insert_barriers=False,
                name='iqft').to_gate(), qr_data[:data_qubits])

        check_qubits = data_qubits - c
        for i in range(check_qubits):
            qc.x(qr_data[data_qubits - check_qubits + i])
        if check_qubits == 1:
            qc.cx(qr_data[data_qubits - check_qubits], qr_f[0])
        elif check_qubits == 2:
            qc.rccx(qr_data[data_qubits - 1], qr_data[data_qubits - 2], qr_f[0])
        else:
            qc.rccx(qr_data[data_qubits - check_qubits], qr_data[data_qubits - check_qubits + 1], qr_data[data_qubits])
            str = data_qubits - check_qubits + 2
            end = data_qubits - 1
            idx = 0
            for i in range(str, end):
                qc.rccx(qr_data[i], qr_data[data_qubits + idx], qr_data[data_qubits + idx + 1])
                idx += 1
            qc.rccx(qr_data[data_qubits - 1], qr_data[data_qubits + idx], qr_f[0])

        qc.x(qr_f[0])
        # We don't have to do this, this will undone in reinitialization, part
        for i in range(check_qubits):
            qc.x(qr_data[data_qubits - check_qubits + i])

        return qc.to_gate(label=" Constraint Testing ") if to_gate else qc

    # penalty part
    def penalty_dephasing(data_qubits: int, alpha: float, gamma: float, to_gate=True) -> Union[Gate, QuantumCircuit]:

        qr_data = QuantumRegister(data_qubits + ancilla_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_data, qr_f)

        ##############################
        ### Phase Rotation ###
        for i, q in enumerate(qr_data[:data_qubits]):
            qc.cu1((2 ** i) * alpha * gamma, qr_f[0], q)
        qc.u1(-(2 ** c) * alpha * gamma, qr_f[0])
        ##############################

        return qc.to_gate(label=" Penalty Dephasing ") if to_gate else qc

    # penalty part
    def reinitialization(index_qubits: int, data_qubits: int, C1: list, C2: list, C_max: int, to_gate=True) -> Union[
        Gate, QuantumCircuit]:

        qr_index = QuantumRegister(index_qubits, "index")
        qr_data = QuantumRegister(data_qubits + ancilla_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_index, qr_data, qr_f)

        ##############################
        ### Reinitialization Circuit ###
        qc.append(constraint_testing(data_qubits, C_max).inverse(), qr_data[:] + qr_f[:])
        qc.append(cost_calculation(index_qubits, data_qubits, C1, C2).inverse(), qr_index[:] + qr_data[:])

        ##############################

        return qc.to_gate(label=" Reinitialization ") if to_gate else qc

    ### Mixing Operator ###
    def mixing_operator(index_qubits: int, beta: float, to_gate=True) -> Union[Gate, QuantumCircuit]:

        qr_index = QuantumRegister(index_qubits, "index")
        qc = QuantumCircuit(qr_index)

        ##############################
        ### Mixing Operator ###
        for q in qr_index:
            qc.rx(2 * beta, q)
        ##############################

        return qc.to_gate(label=" Mixing Operator ") if to_gate else qc

    qr_index = QuantumRegister(index_qubits, "index")  # index register
    qr_data = QuantumRegister(data_qubits + ancilla_qubits, "data")  # data register
    qr_f = QuantumRegister(1, "flag")  # flag register
    cr_index = ClassicalRegister(index_qubits,
                                 "c_index")  # classical register storing the measurement result of index register
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


def solver_function(L1: list, L2: list, C1: list, C2: list, C_max: int) -> QuantumCircuit:
    # process the list
    newC1 = []
    newC2 = []
    sc = 0
    for (val1, val2) in zip(C1, C2):
        # common part
        com = val1 & val2
        sc += com

        newC1.append(val1 - com)
        newC2.append(val2 - com)

    return solver_function2(L1, L2, newC1, newC2, C_max - sc)
