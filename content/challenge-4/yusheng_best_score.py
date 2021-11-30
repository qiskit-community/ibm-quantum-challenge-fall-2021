from qiskit import QuantumCircuit, QuantumRegister
import numpy as np
from typing import List, Union
import math
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, assemble
from qiskit.compiler import transpile
from qiskit.circuit import Gate
from qiskit.circuit.library.standard_gates import *
from qiskit.circuit.library import QFT


def solver_function(L1: list, L2: list, C1: list, C2: list,
                    C_max: int) -> QuantumCircuit:
    # instance_examples :
    """[{'L1': [7, 4, 5, 3, 2, 4, 3, 7, 4, 2, 7],
    'L2': [9, 6, 6, 6, 6, 9, 5, 9, 9, 8, 9],
    'C1': [2, 3, 2, 3, 2, 3, 2, 3, 2, 2, 3],
    'C2': [3, 4, 4, 5, 3, 4, 4, 4, 5, 5, 4],
    'C_max': 36},
    {'L1': [5, 4, 3, 3, 3, 7, 6, 4, 3, 5, 3],
    'L2': [9, 7, 5, 5, 7, 8, 8, 7, 5, 7, 9],
    'C1': [2, 2, 4, 2, 3, 4, 2, 2, 2, 2, 2],
    'C2': [3, 4, 5, 4, 4, 5, 3, 3, 5, 3, 5],
    'C_max': 35},
    {'L1': [2, 3, 6, 4, 5, 2, 4, 6, 3, 4, 5],
    'L2': [6, 6, 7, 8, 6, 5, 7, 9, 6, 8, 8],
    'C1': [2, 2, 3, 3, 2, 4, 3, 2, 2, 4, 3],
    'C2': [4, 3, 5, 5, 4, 5, 5, 3, 4, 5, 5],
    'C_max': 39},
    {'L1': [4, 3, 2, 2, 2, 4, 5, 3, 4, 4, 3],
    'L2': [6, 7, 6, 5, 5, 9, 9, 7, 9, 5, 5],
    'C1': [3, 2, 2, 2, 3, 2, 3, 2, 2, 3, 2],
    'C2': [4, 5, 4, 4, 5, 5, 4, 5, 5, 4, 4],
    'C_max': 37},
    {'L1': [5, 4, 2, 4, 2, 6, 4, 4, 3, 7, 2],
    'L2': [8, 8, 7, 5, 6, 8, 6, 5, 6, 9, 9],
    'C1': [3, 2, 3, 3, 2, 4, 3, 4, 3, 2, 2],
    'C2': [4, 4, 5, 4, 4, 5, 4, 5, 5, 5, 4],
    'C_max': 40},
    {'L1': [3, 7, 3, 4, 2, 6, 2, 2, 4, 6, 6],
    'L2': [7, 8, 7, 6, 6, 9, 6, 7, 6, 7, 7],
    'C1': [2, 2, 2, 3, 2, 4, 2, 2, 2, 2, 2],
    'C2': [4, 3, 3, 4, 4, 5, 3, 4, 4, 3, 4],
    'C_max': 33},
    {'L1': [5, 6, 4, 2, 2, 2, 2, 4, 3, 4, 6],
    'L2': [8, 8, 7, 5, 6, 6, 5, 9, 9, 5, 8],
    'C1': [4, 3, 3, 2, 2, 3, 3, 2, 3, 4, 3],
    'C2': [5, 4, 4, 5, 5, 4, 4, 5, 4, 5, 4],
    'C_max': 40},
    {'L1': [3, 5, 3, 2, 5, 2, 5, 3, 7, 2, 2],
    'L2': [8, 6, 7, 5, 9, 5, 9, 8, 8, 6, 7],
    'C1': [2, 3, 3, 3, 3, 3, 2, 3, 3, 2, 2],
    'C2': [5, 5, 5, 4, 4, 4, 5, 4, 4, 4, 5],
    'C_max': 39}]
    """
    author = 'Yusheng Zhao'
    score = 275498 # if you change QFT approx level to 2 and 1, can get 273,998
    print(f'{author}: {score}')

    dotranspile = True

    # the number of qubits representing answers
    index_qubits = len(L1)

    # the maximum and min possible total cost
    max_c = sum([max(l0, l1) for l0, l1 in zip(C1, C2)])
    min_c = sum([min(l0, l1) for l0, l1 in zip(C1, C2)])

    adjust = 0  # Let == C_max through, don't seem to need
    target_min_c = 1  # make min_c 1 for now

    # adjust to make C_max 2**w
    w_bits = math.ceil(math.log(C_max - min_c + target_min_c, 2))
    diff = 2**(w_bits) - (C_max - min_c + target_min_c)

    #assuming C_max <= max_c otherwise problem is meaningless
    max_c = max_c - min_c + target_min_c + diff  #reduce number of qubits used

    # engae ULTRA qubit saving mode!
    if 2**(w_bits + 1) - 1 >= max_c:
        data_qubits = w_bits + 1
        # use flag qubit as last bit in data_qubits
        ultra = True
    else:
        data_qubits = math.ceil(math.log(
            max_c, 2)) if not max_c & (max_c - 1) == 0 else math.ceil(
                math.log(max_c, 2)) + 1
        ultra = False

    ### Phase Operator ###
    # return part
    def phase_return(index_qubits: int,
                     gamma: float,
                     L1: list,
                     L2: list,
                     to_gate=True) -> Union[Gate, QuantumCircuit]:
        qr_index = QuantumRegister(index_qubits, "index")
        qc = QuantumCircuit(qr_index)

        ##############################
        ### U_1(gamma * (lambda2 - lambda1)) for each qubit ###
        # Provide your code here

        for ii in range(index_qubits):
            # if problem statement is correct,
            # L2 > L1 cannot give zero here
            # note the order of index qr is reversed
            qc.p(-gamma * (L2[ii] - L1[ii]), qr_index[ii])

        if dotranspile:
            qc = transpile(qc,
                           optimization_level=2,
                           basis_gates=['rz', 'sx', 'cx'],
                           seed_transpiler=42)
        ##############################
        return qc.to_gate(label=" phase return ") if to_gate else qc

    # penalty part
    def subroutine_add_const(data_qubits: int,
                             const: int,
                             to_gate=True) -> Union[Gate, QuantumCircuit]:
        qc = QuantumCircuit(data_qubits)
        ##############################
        ### Phase Rotation ###
        # Provide your code here
        const_str = bin(const)[2:].zfill(data_qubits)[::-1]

        for ii in range(data_qubits):
            for jj in range(data_qubits - ii):
                if const_str[ii] == '1':
                    # seems simplist, same code as Draper QFT Adder
                    qc.p(np.pi / (2**(jj)), ii + jj)

        if dotranspile:
            qc = transpile(qc,
                           optimization_level=2,
                           basis_gates=['rz', 'sx', 'cx'],
                           seed_transpiler=42)

        ##############################
        return qc.to_gate(label=" [+" + str(const) + "] ") if to_gate else qc

    # penalty part
    def const_adder(data_qubits: int,
                    const: int,
                    to_gate=True) -> Union[Gate, QuantumCircuit]:

        qr_data = QuantumRegister(data_qubits, "data")
        qc = QuantumCircuit(qr_data)

        ##############################
        ### Phase Rotation ###
        # Use `subroutine_add_const`
        qc.append(subroutine_add_const(data_qubits, const, to_gate), qr_data)

        ##############################

        return qc.to_gate(label=" [ +" + str(const) + "] ") if to_gate else qc

    # penalty part
    def cost_calculation(index_qubits: int,
                         data_qubits: int,
                         list1: list,
                         list2: list,
                         to_gate=True) -> Union[Gate, QuantumCircuit]:

        qr_index = QuantumRegister(index_qubits, "index")
        qr_data = QuantumRegister(data_qubits, "data")
        qc = QuantumCircuit(qr_index, qr_data)
        # in the other version, the first set of values in zip(list1,list2)
        # are initialized here to the qr_data
        # but now I move them outside

        # I move QFT here avoid repetitive QFT and IQFT
        # max approx is 1
        qft = QFT(data_qubits,
                  approximation_degree=1,
                  do_swaps=False,
                  inverse=False,
                  insert_barriers=False,
                  name=None).decompose()

        if dotranspile:
            qft = transpile(qft,
                            basis_gates=['sx', 'rz', 'cx'],
                            optimization_level=2,
                            seed_transpiler=42)

        qc.append(qft, qr_data)

        for i, (val1, val2) in enumerate(zip(list1[1:], list2[1:])):

            ##############################
            ### Add val2 using const_adder controlled by i-th index register (set to 1) ###
            # Provide your code here
            # In theory this if is not needed, I just put it here in case
            # the generated date messes with me
            # I only need to add the larger one, the smaller one is
            # adjusted to 0 by the shifiting min_c to 0 at the very beginning
            # note min_c will need to be shifted to 1 to avoid bad result
            # and then to 1 + diff to make C_max = 2**w
            if val2 > val1:
                adder_gate2 = const_adder(data_qubits, val2 - val1, True)
                ctrl_adder_gate2 = adder_gate2.control()
                qc.append(ctrl_adder_gate2, [qr_index[i + 1]] + qr_data[:])
            ##############################
            else:
                qc.x(qr_index[i + 1])
                adder_gate1 = const_adder(data_qubits, val1 - val2, True)
                ctrl_adder_gate1 = adder_gate1.control()
                qc.append(ctrl_adder_gate1, [qr_index[i + 1]] + qr_data[:])

        if dotranspile:
            qc = transpile(qc,
                           basis_gates=['sx', 'rz', 'cx'],
                           optimization_level=2,
                           seed_transpiler=42)

        # unforutnately cannot seem to move this block out
        qfti = QFT(data_qubits,
                   approximation_degree=1,
                   do_swaps=False,
                   inverse=True).decompose()

        if dotranspile:
            qfti = transpile(qfti,
                             basis_gates=['sx', 'rz', 'cx'],
                             optimization_level=2,
                             seed_transpiler=42)

        qc.append(qfti, qr_data)
        qc = qc.decompose()
        if dotranspile:
            qc = transpile(qc,
                           basis_gates=['rz', 'sx', 'cx'],
                           optimization_level=2,
                           seed_transpiler=42)

        return qc.to_gate(label=" Cost Calculation ") if to_gate else qc

    # penalty part
    def constraint_testing(data_qubits: int,
                           C_max: int,
                           to_gate=True) -> Union[Gate, QuantumCircuit]:

        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_data, qr_f)

        ##############################
        ### Set the flag register for indices with costs larger than C_max ###

        if not ultra:
            # the usual testing method, will use ccx at most
            # improves a little but hey, I will take everything
            # that's free
            num_bit = w_bits
            qc.x(qr_f)
            qc.x(qr_data[num_bit:])
            qc.mct(qr_data[num_bit:], qr_f)
            qc.x(qr_data[num_bit:])
        else:
            # in ultra mode, only when the last bit is on
            # we know c_cur > C_max
            # we made sure max_c - C_max < 2**w
            # so max_c will not overflow and create a problem
            qc.cx(qr_data[-1], qr_f)

        if dotranspile:
            qc = transpile(qc,
                           optimization_level=2,
                           basis_gates=['rz', 'sx', 'cx'],
                           seed_transpiler=42)
        ##############################

        return qc.to_gate(label=" Constraint Testing ") if to_gate else qc

    # penalty part
    def penalty_dephasing(data_qubits: int,
                          alpha: float,
                          gamma: float,
                          to_gate=True) -> Union[Gate, QuantumCircuit]:

        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_data, qr_f)

        ##############################
        ### Phase Rotation ###
        # Provide your code here

        factor = math.ceil(C_max /
                           2**w_bits)  # adjust for the C_max value shift
        # could be caused by the simulator precision problem?

        for ii in range(data_qubits):
            qc.cp(factor * alpha * gamma * 2**(ii), qr_f, qr_data[ii])

        qc.p(-factor * alpha * gamma * (2**w_bits), qr_f)
        if dotranspile:
            qc = transpile(qc,
                           optimization_level=2,
                           basis_gates=['rz', 'sx', 'cx'],
                           seed_transpiler=42)
        ##############################
        return qc.to_gate(label=" Penalty Dephasing ") if to_gate else qc

    # penalty part
    def reinitialization(index_qubits: int,
                         data_qubits: int,
                         C1: list,
                         C2: list,
                         C_max: int,
                         to_gate=True) -> Union[Gate, QuantumCircuit]:

        qr_index = QuantumRegister(index_qubits, "index")
        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_index, qr_data, qr_f)

        ##############################
        ### Reinitialization Circuit ###
        # Provide your code here

        ctt_inv = constraint_testing(data_qubits, C_max, to_gate=True).inverse()

        qc.append(ctt_inv, qr_data[:] + qr_f[:])

        cost_inv = cost_calculation(index_qubits,
                                    data_qubits,
                                    C1,
                                    C2,
                                    to_gate=True).inverse()

        qc.append(cost_inv, qr_index[:] + qr_data[:])

        if dotranspile:
            qc = transpile(qc,
                           optimization_level=2,
                           basis_gates=['rz', 'sx', 'cx'],
                           seed_transpiler=42)

        ##############################

        return qc.to_gate(label=" Reinitialization ") if to_gate else qc

    ### Mixing Operator ###
    def mixing_operator(index_qubits: int,
                        beta: float,
                        to_gate=True) -> Union[Gate, QuantumCircuit]:

        qr_index = QuantumRegister(index_qubits, "index")
        qc = QuantumCircuit(qr_index)

        ##############################
        ### Mixing Operator ###
        # Provide your code here

        qc.rx(2 * beta, qr_index)

        if dotranspile:
            qc = transpile(qc,
                           optimization_level=2,
                           basis_gates=['rz', 'sx', 'cx'],
                           seed_transpiler=42)
        ##############################
        return qc.to_gate(label=" Mixing Operator ") if to_gate else qc

    qr_index = QuantumRegister(index_qubits, "index")  # index register
    qr_data = QuantumRegister(data_qubits, "data")  # data register
    qr_f = QuantumRegister(1, "flag")  # flag register
    cr_index = ClassicalRegister(
        index_qubits, "c_index"
    )  # classical register storing the measurement result of index register
    qc = QuantumCircuit(qr_index, qr_data, qr_f, cr_index)

    ### initialize the index register with uniform superposition state ###
    qc.h(qr_index)
    # notice how I initialize first values in C1 and C2 here
    # in theory data_qr is still clean b/c we know how to revert them
    # consistently with unitary gates
    #
    diff_str_inv = bin(target_min_c + diff -
                       adjust)[2:].zfill(data_qubits)[::-1]

    for ii in range(data_qubits):
        if diff_str_inv[ii] == '1':
            qc.x(qr_data[ii])

    if C2[0] > C1[0]:  #just to make sure
        first_val_diff = C2[0] - C1[0] + target_min_c + diff - adjust
    else:
        first_val_diff = C1[0] - C2[0] + target_min_c + diff - adjust

    first_val_diff_str = bin(first_val_diff)[2:].zfill(data_qubits)[::-1]

    for ii in range(data_qubits):
        if diff_str_inv[ii] != first_val_diff_str[ii]:
            qc.cx(qr_index[0], qr_data[ii])

    ### DO NOT CHANGE THE CODE BELOW
    ### My formatter formatted the below code
    ### I did not change anything meaningful
    p = 5
    alpha = 1
    for i in range(p):
        ### set fixed parameters for each round ###
        beta = 1 - (i + 1) / p
        gamma = (i + 1) / p

        ### return part ###
        qc.append(phase_return(index_qubits, gamma, L1, L2), qr_index)

        ### step 1: cost calculation ###
        qc.append(cost_calculation(index_qubits, data_qubits, C1, C2),
                  qr_index[:] + qr_data[:])

        ### step 2: Constraint testing ###
        qc.append(constraint_testing(data_qubits, C_max), qr_data[:] + qr_f[:])

        ### step 3: penalty dephasing ###
        qc.append(penalty_dephasing(data_qubits, alpha, gamma),
                  qr_data[:] + qr_f[:])

        ### step 4: reinitialization ###
        qc.append(reinitialization(index_qubits, data_qubits, C1, C2, C_max),
                  qr_index[:] + qr_data[:] + qr_f[:])

        ### mixing operator ###
        qc.append(mixing_operator(index_qubits, beta), qr_index)

    ### measure the index ###
    ### since the default measurement outcome is shown in big endian, it is necessary to reverse the classical bits in order to unify the endian ###
    qc.measure(qr_index, cr_index[::-1])

    return qc
