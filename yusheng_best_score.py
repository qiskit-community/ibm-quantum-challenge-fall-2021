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

    author = 'Yusheng Zhao'
    score = 275498 # if you change QFT approx level to 2 and 1, can get 273,998
    print(f'{author}: {score}')

    dotranspile = True

    op_lvl = 2
    bgate = ['cx', 'rz', 'sx']
    # the number of qubits representing answers
    index_qubits = len(L1)

    # the maximum possible total cost
    max_c = sum([max(l0, l1) for l0, l1 in zip(C1, C2)])
    min_c = sum([min(l0, l1) for l0, l1 in zip(C1, C2)])

    adjust = 1  # Let == C_max through, don't seem to need
    target_min_c = 1  #make min_c 1

    # adjust to make C_max 2**w
    w_bits = math.ceil(math.log(C_max - min_c + target_min_c, 2))
    if 2**w_bits == C_max - min_c + target_min_c:
        target_min_c -= 1 # make sure I can downshift the shift on actual costs by 1
        # this will let == C_max values through
    diff = 2**(w_bits) - (C_max + adjust - min_c + target_min_c)

    #assuming C_max <= max_c otherwise problem is meaningless
    max_c = max_c - min_c + target_min_c + diff  #reduce number of qubits used
    data_qubits = w_bits + 1
    ultra = True
    # make sure max_c does not overflow
    # I saw in the new grader, there are some cases for this
    if max_c > 2**(data_qubits) - 1:
        ultra = False
        data_qubits = math.ceil(math.log(max_c, 2))
        if max_c > 2**(data_qubits) - 1:
            data_qubits += 1
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
            qc.p((-gamma * (L2[ii] - L1[ii])/2) % (2 * np.pi), qr_index[ii])

        if dotranspile:
            qc = transpile(qc,
                           optimization_level=op_lvl,
                           basis_gates=bgate,
                           seed_transpiler=42)
        ##############################
        return qc.to_gate(label=" phase return ") if to_gate else qc

    # penalty part
    def subroutine_add_const(data_qubits: int,
                             const: int,
                             to_gate=True) -> Union[Gate, QuantumCircuit]:
        qr_index = QuantumRegister(1)
        qr_data = QuantumRegister(data_qubits)
        qc = QuantumCircuit(qr_index, qr_data)
        ##############################
        ### Phase Rotation ###
        # Provide your code here
        for qb in range(data_qubits):
            twoP = 2**(qb + 1)  #twoP*2
            c = const % twoP
            if c != 0:
                phase = 2 * np.pi * c / twoP
                qc.cp(phase, qr_index, qr_data[qb])

        if dotranspile:
            qc = transpile(qc,
                           optimization_level=op_lvl,
                           basis_gates=bgate,
                           seed_transpiler=42)

        ##############################
        return qc.to_gate(label=" [+" + str(const) + "] ") if to_gate else qc

    # penalty part
    def const_adder(data_qubits: int,
                    const: int,
                    to_gate=True) -> Union[Gate, QuantumCircuit]:
        qr_index = QuantumRegister(1)
        qr_data = QuantumRegister(data_qubits, "data")
        qc = QuantumCircuit(qr_index, qr_data)

        ##############################
        ### Phase Rotation ###
        # Use `subroutine_add_const`
        qc.append(subroutine_add_const(data_qubits, const, to_gate),
                  [qr_index[:]] + qr_data[:])

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

        # use diff calculated before
        # this has to be here since it does not commute
        # with the mixer Hamiltonian
        # previously I had this step elsewhere
        diff_str_inv = bin(target_min_c + diff)[2:].zfill(data_qubits)[::-1]

        for ii in range(data_qubits):
            if diff_str_inv[ii] == '1':
                qc.x(qr_data[ii])

        if C2[0] > C1[0]:  #just to make sure
            first_val_diff = C2[0] - C1[0] + target_min_c + diff
        else:
            first_val_diff = C1[0] - C2[0] + target_min_c + diff

        first_val_diff_str = bin(first_val_diff)[2:].zfill(data_qubits)[::-1]

        for ii in range(data_qubits):
            if diff_str_inv[ii] != first_val_diff_str[ii]:
                qc.cx(qr_index[0], qr_data[ii])
        if dotranspile:
            qc = transpile(qc,
                        basis_gates=bgate,
                        optimization_level=op_lvl,
                        seed_transpiler=42)


        # no transpile a_d = 1
        qft = QFT(data_qubits,
                  approximation_degree=0,
                  do_swaps=False,
                  inverse=False,
                  insert_barriers=False,
                  name=None).decompose()

        if dotranspile:
            qft = transpile(qft,
                            basis_gates=bgate,
                            optimization_level=op_lvl,
                            seed_transpiler=42)
        qc.append(qft, qr_data)

        for i, (val1, val2) in enumerate(zip(list1[1:], list2[1:])):

            ##############################
            ### Add val2 using const_adder controlled by i-th index register (set to 1) ###
            # Provide your code here
            if val2 > val1:
                ctrl_adder_gate2 = const_adder(data_qubits, val2 - val1, True)
                qc.append(ctrl_adder_gate2, [qr_index[i + 1]] + qr_data[:])
            ##############################
        if dotranspile:
            qc = transpile(qc,
                           basis_gates=bgate,
                           optimization_level=op_lvl,
                           seed_transpiler=42)
        qfti = QFT(data_qubits,
                   approximation_degree=0,
                   do_swaps=False,
                   inverse=True).decompose()

        if dotranspile:
            qfti = transpile(qfti,
                             basis_gates=bgate,
                             optimization_level=2,
                             seed_transpiler=42)
        qc.append(qfti, qr_data)
        qc = qc.decompose()
        if dotranspile:
            qc = transpile(qc,
                           basis_gates=bgate,
                           optimization_level=op_lvl,
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
        # Provide your code here
        # do what the paper suggested
        # in case of ultra saving mode,
        # only the last qubit in qr_data is on
        # when cost is > C_max
        # I change the shift of all cost by -1
        # compare to C_max 's shift to 2**w_bits
        # this will let cost == C_max through the constraint process
        if ultra:
            qc.cx(qr_data[-1], qr_f)
        else:
            qc.x(qr_f)
            qc.x(qr_data[w_bits:])
            qc.mct(qr_data[w_bits:], qr_f)
            qc.x(qr_data[w_bits:])
        if dotranspile:
            qc = transpile(qc,
                           optimization_level=op_lvl,
                           basis_gates=bgate,
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
        for ii in range(data_qubits):
            qc.cp(alpha * gamma * 2**(ii), qr_f, qr_data[ii])

        qc.p(-alpha * gamma * (2**w_bits - adjust), qr_f)
        if dotranspile:
            qc = transpile(qc,
                           optimization_level=op_lvl,
                           basis_gates=bgate,
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

        ctt_inv = constraint_testing(data_qubits, C_max,
                                     to_gate=True).inverse()

        qc.append(ctt_inv, qr_data[:] + qr_f[:])

        cost_inv = cost_calculation(index_qubits,
                                    data_qubits,
                                    C1,
                                    C2,
                                    to_gate=True).inverse()

        qc.append(cost_inv, qr_index[:] + qr_data[:])

        if dotranspile:
            qc = transpile(qc,
                           optimization_level=op_lvl,
                           basis_gates=bgate,
                           seed_transpiler=42)

        #print_score(qc)
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
                           optimization_level=op_lvl,
                           basis_gates=bgate,
                           seed_transpiler=42)
        ##############################
        return qc.to_gate(label=" Mixing Operator ") if to_gate else qc

    qr_index = QuantumRegister(index_qubits, "index")  # index register
    qr_data = QuantumRegister(data_qubits, "data")  # data register
    qr_f = QuantumRegister(1, "flag")  # flag register

    # I leave testing code in
    dotest = 100 # determines which layer to do test
    if dotest < 5:
        cr_index = ClassicalRegister(
            index_qubits + 1 + data_qubits, "c_index"
        )  # classical register storing the measurement result of index register
        qc = QuantumCircuit(qr_index, qr_data, qr_f, cr_index)

    else:
        cr_index = ClassicalRegister(
            index_qubits, "c_index"
        )  # classical register storing the measurement result of index register
        qc = QuantumCircuit(qr_index, qr_data, qr_f, cr_index)

    ### initialize the index register with uniform superposition state ###
    qc.h(qr_index)

    ### DO NOT CHANGE THE CODE BELOW
    # Notice, I just formatted the rest
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

        # if dotest == i:
        #     qc.measure(qr_index,
        #                cr_index[index_qubits + data_qubits:data_qubits:-1])
        #     qc.measure(qr_data, cr_index[data_qubits:0:-1])
        #     qc.measure(qr_f, cr_index[0])
        #     return qc
        # ### mixing operator ###
        qc.append(mixing_operator(index_qubits, beta), qr_index)

    ### measure the index ###
    ### since the default measurement outcome is shown in big endian, it is necessary to reverse the classical bits in order to unify the endian ###
    qc.measure(qr_index, cr_index[::-1])

    return qc
