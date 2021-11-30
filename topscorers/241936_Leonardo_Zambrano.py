"""
Challenge 4c solver function for the IBM Quantum Fall Challenge 2021
Author: Leonardo Zambrano  # TODO 1: change to your name and email
Score: 241936 # TODO 1: change to your score
TODO:
1. Add author name, email and score at the top of the file
2. Write a summary of your approach in the header and highlight
the techniques that gave you the biggest improvement
3. Import all required libraries and modules
4. Print author name and score inside the `solver_function`
5. Copy code to each sub-functions (e.g.phase_return, subroutine_add_constant)
and explain the implementation in comments
# TODO 2: write summary of your approach
# TODO 2: please highlight the techniques that gave you the biggest improvement
Summary of the approach:
1. After I got the right solution, I removed all the intermediate Fourier transforms
in the algorithm, and I left just two, One outside the functions, becase we don't care about the
state of data_qubtis, we only need these qubits to give us the right relative phase.
The other Fourier transform is inside cost_calculation. The rest were useless
since we were adding a lot of terms. Doing this also avoids extra Fourier transforms from
reinicialization. This was the biggest improvement, from 80 million
to 1 million. Then I removed all the phase operations with angle zero. This was also
a great improvement. Finally, I reescaled the problem substracting C1, which gave me
the current score. I didn't use the flag, since I used data_qubits[-1] as flag.
2.
3.
"""
# TODO 3: import all required libraries and modules
import numpy as np
from typing import List, Union
import math
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, assemble
from qiskit.compiler import transpile
from qiskit.circuit import Gate
from qiskit.circuit.library.standard_gates import *
from qiskit.circuit.library import QFT


def solver_function(L1: list, L2: list, C1: list, C2: list, C_max: int) -> QuantumCircuit:
    # TODO 4: add your name and score here
    # print name and score
    author = 'Leonardo Zambrano'
    score = 241936
    print(f'{author}: {score}')

    # the number of qubits representing answers
    index_qubits = len(L1)

    # THIS IS A CHANGE. We reescale the problem
    C2 = list(np.array(C2) - np.array(C1))
    C_max = int(C_max - sum(C1))
    # the maximum possible total cost
    max_c = int(sum(C2))
    n_bits = C_max.bit_length()
    data_qubits = (2**n_bits - C_max + max_c).bit_length()

    def phase_return(index_qubits: int, gamma: float, L1: list, L2: list, to_gate=True):
        qr_index = QuantumRegister(index_qubits, "index")
        qc = QuantumCircuit(qr_index)

        ##############################
        for k in range(index_qubits):
            qc.p(-0.5*gamma*(L2[k] - L1[k]), k)


        ##############################

        return qc.to_gate(label=" phase return ") if to_gate else qc

    # penalty part
    def subroutine_add_const(data_qubits: int, const: int, to_gate=True):
        qc = QuantumCircuit(data_qubits)
        ##############################
        # I adapted this from DraperQFTAdder. I only do rotations with phase
        # different from zero.
        phases = np.zeros((data_qubits))
        bin_const = format(const, "b")
        bin_const = bin_const[::-1]
        # We group all the phases that have to be applied to every qubit in an array.
        for j in range(len(bin_const)):
            for k in range(data_qubits - j):
                if int(bin_const[j]) == 1:
                    lam = np.pi / (2 ** k)
                    phases[j+k] = phases[j+k] + lam
                    # qc.p(lam, j + k)
                else:
                    pass
        # using this we are sure that we apply p only once for every qubit.
        for j in range(data_qubits):
            if phases[j] != 0:
                qc.p(phases[j], j)

        ##############################
        return qc.to_gate(label=" [+"+str(const)+"] ") if to_gate else qc

    # penalty part
    def const_adder(data_qubits: int, const: int, to_gate=True):

        qr_data = QuantumRegister(data_qubits, "data")
        qc = QuantumCircuit(qr_data)

        ### We don't need Fourier transforms here, since we will do many aditions.
        qc.append(subroutine_add_const(data_qubits, const), qr_data[:])
        ##############################
        return qc.to_gate(label=" [ +" + str(const) + "] ") if to_gate else qc

    # penalty part
    def cost_calculation(index_qubits: int, data_qubits: int, list1: list, list2: list, to_gate = True):

        qr_index = QuantumRegister(index_qubits, "index")
        qr_data = QuantumRegister(data_qubits, "data")
        qc = QuantumCircuit(qr_index, qr_data)
        for i, (val1, val2) in enumerate(zip(list1, list2)):
            const_adder_controlled_2 = const_adder(data_qubits, val2).control(num_ctrl_qubits=1)
            qc.append(const_adder_controlled_2, [qr_index[i]] + qr_data[:])
        qc.append(QFT(data_qubits, do_swaps=False, approximation_degree=1).inverse().to_gate(), qr_data[:])

        return qc.to_gate(label=" Cost Calculation ") if to_gate else qc

    # penalty part
    def constraint_testing(data_qubits: int, C_max: int, to_gate = True):

        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_data, qr_f)
        # We don't do anything here, since we are going to use the bit qr_data[-1]
        # as a flag. This is to check if we should constrain at least one sequence.
        if max_c > C_max:
            pass
        else:
            qc.x(qr_data[-1])
        return qc.to_gate(label=" Constraint Testing ") if to_gate else qc

    # penalty part
    def penalty_dephasing(data_qubits: int, alpha: float, gamma: float, to_gate = True):

        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_data, qr_f)
        # We add rotations controlled by qr_data[-1] and not by the flag.
        for k in range(data_qubits-1):
            qc.cp(2*(2**k)*alpha*gamma, qr_data[-1], qr_data[k])
        # This is because we have added C_max-1 instead of C_max in order to
        # apply penalty to the secuencies cost(z) > C_max. I didn't apply U_1(alpha*gamma*2**k)
        # to the last qr_data because that phase cancels with U_1(-alpha*gamma*2**c). 
        # The phase for each state is now alpha*beta*(cost(z) - C_max - 1), so we have to add 
        # one more rotation, and now the phase is alpha*beta*(cost(z) - C_max)
        qc.p(2*alpha*gamma, qr_data[-1])
        ##############################

        return qc.to_gate(label=" Penalty Dephasing ") if to_gate else qc

    # penalty part
    def reinitialization(index_qubits: int, data_qubits: int, C1: list, C2: list, C_max: int, to_gate = True):

        qr_index = QuantumRegister(index_qubits, "index")
        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_index, qr_data, qr_f)

        ##############################
        ## Just apply the circuits in the reversed order
        qc.append(constraint_testing(data_qubits, C_max).inverse(), qr_data[:] + qr_f[:])
        qc.append(cost_calculation(index_qubits, data_qubits, C1, C2).inverse(), qr_index[:] + qr_data[:])
        ##############################

        return qc.to_gate(label=" Reinitialization ") if to_gate else qc

    ### Mixing Operator ###
    def mixing_operator(index_qubits: int, beta: float, to_gate = True):

        qr_index = QuantumRegister(index_qubits, "index")
        qc = QuantumCircuit(qr_index)

        ##############################
        if beta != 0:
            for k in range(index_qubits):
                qc.rx(2*beta, k)
        else:
            pass

        return qc.to_gate(label=" Mixing Operator ") if to_gate else qc

    qr_index = QuantumRegister(index_qubits, "index") # index register
    qr_data = QuantumRegister(data_qubits, "data") # data register
    qr_f = QuantumRegister(1, "flag") # flag register
    cr_index = ClassicalRegister(index_qubits, "c_index") # classical register storing the measurement result of index register
    qc = QuantumCircuit(qr_index, qr_data, qr_f, cr_index)


    qc.h(qr_index)
    # We do the fourier transforms here because we don't care about the state
    # of data_qubits, we only care that it gives us the correct relative phase.
    # Also, since we know that the initial state is |00...0> we don't need the full Fourier
    # transform, and we replace this for hadamards. This is clear if you check the first column
    # of the matrix representation of the qft, which is the result of the fourier transform applied
    # to |00..0>.
    qc.h(qr_data)
    # We start the algorithm with qr_data in the binary string associated to 2**n_bits - C_max - 1, 
    # since this is a constant that we have to add to every state, and it's better to do it right now
    # than inside the functions. 
    qc.append(const_adder(data_qubits, 2**n_bits - C_max - 1), qr_data[:])

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