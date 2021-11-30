"""
Challenge 4c solver function for the IBM Quantum Fall Challenge 2021
Author: Naphan Benchasattabuse  # TODO 1: change to your name and email
Score: 173344 # TODO 1: change to your score
​
TODO:
1. Add author name, email and score at the top of the file
2. Write a summary of your approach in the header and highlight
the techniques that gave you the biggest improvement
3. Import all required libraries and modules
4. Print author name and score inside the `solver_function`
5. Copy code to each sub-functions (e.g.phase_return, subroutine_add_constant)
and explain the implementation in comments
​
# TODO 2: write summary of your approach
# TODO 2: please highlight the techniques that gave you the biggest improvement
Summary of the approach:
1. The main idea is that we do not need to change basis everytime we want to add something, so instead of QFT-add-iQFT, 
we can just do QFT once at the start of the calculating cost function, perform iQFT to flag the overflow and also transform
the value back to binary so we can perform the penalty dephase. After that we just inverse the constraint check and cost calculation.
2. Another idea that we can reduce the cost is to use approximate QFT instead of exact QFT. This will help us to reduce both the CNot
and the depth especially when data register is large. We perform the rotation up to pi/16 only. This still result in a good approximation
and we can still arrive at the solution
3. Optimization of the gates order. Make use of circuit identities ...
​
"""
# TODO 3: import all required libraries and modules
from qiskit import QuantumCircuit, QuantumRegister
from typing import List, Union
import math
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, assemble
from qiskit.compiler import transpile
from qiskit.circuit import Gate
from qiskit.circuit.library.standard_gates import *
import numpy as np

def solver_function(L1: list, L2: list, C1: list, C2: list, C_max: int) -> QuantumCircuit:
    # TODO 4: add your name and score here
    # print name and score
    author = 'Naphan Benchasattabuse'
    score = 173344
    print(f'{author}: {score}')

    # the number of qubits representing answers
    index_qubits = len(L1)

    # the maximum possible total cost
    max_c = sum([l1-l0 for l0, l1 in zip(C1, C2)])
    C_max -= sum(C1)

    # the number of qubits representing data values can be defined using the maximum possible total cost as follows:
    data_qubits = math.ceil(math.log(max_c, 2)) + 1 if not max_c & (max_c - 1) == 0 else math.ceil(math.log(max_c, 2)) + 2

    ### Phase Operator ###
    # return part
    def phase_return(index_qubits: int, gamma: float, L1: list, L2: list, to_gate=True) -> Union[Gate, QuantumCircuit]:
        qr_index = QuantumRegister(index_qubits, "index")
        qc = QuantumCircuit(qr_index)

        for i in range(index_qubits):
            qc.rz(-1 * gamma * (L2[i] - L1[i]), qr_index[i])

        return qc.to_gate(label=" phase return ") if to_gate else qc

    ##############################
    ### TODO ###
    ### Paste your code from above cells here ###
    # TODO 5: explain the implementation in comments

    ##############################

    # helper function, approximate QFT
    def qft_rotations_approximate(n, front_rz=True):
        if n == 0:
            return QuantumCircuit()
        qc = QuantumCircuit(n)
        
        # # precalculate Rz
        if front_rz:
            for i in range(n-1):
                qc.rz((2**(n-i-1)-1)*np.pi / 2**(n-i), i)
            # qc.barrier()
        
        qc.h(n-1)
        if n > 1:
            qc.rz((2**(n-1)-1)*np.pi / 2**(n) ,n-1)
        
        for i in reversed(range(max(0, n-4), n-1)):
            qc.cx(n-1, i)
        for i in range(max(0, n-4), n-1):
            qc.rz(-np.pi / (2**(n-i)), i)
        for i in reversed(range(max(0, n-4), n-1)):
            qc.cx(n-1, i)
        if n > 1:
            qc.compose(qft_rotations_approximate(n-1, front_rz=False), inplace=True)
        return qc
    qft_rotations = qft_rotations_approximate

    # penalty part
    def subroutine_add_const(data_qubits: int, const: int, to_gate=True) -> Union[Gate, QuantumCircuit]:
        qc = QuantumCircuit(data_qubits)
        # Note that we don't swap order of the qubits during QFT-basis
        for i in range(data_qubits):
            qc.rz(np.pi * const / (2**(data_qubits-1-i)), data_qubits - 1 - i)
        
        return qc.to_gate(label=" [+"+str(const)+"] ") if to_gate else qc

    # penalty part
    def const_adder():
        pass

    # penalty part
    def cost_calculation(index_qubits: int, data_qubits: int, list1: list, list2: list, to_gate = True) -> Union[Gate, QuantumCircuit]:
        qr_index = QuantumRegister(index_qubits, "index")
        qr_data = QuantumRegister(data_qubits, "data")
        qc = QuantumCircuit(qr_index, qr_data)

        # transform into QFT-basis (since we start with all |0>) just apply H
        # leave data[0] out because we can just cx first then H later
        qc.h(qr_data[1:])

        phase_data = [0] * data_qubits
        ## This structure of circuit layout is taken from Pulkit Sinha's ICPC Quantum Challenge 2021 - problem 2
        # phase for the control bits
        for i, (val1, val2) in enumerate(zip(list1, list2)):
            qc.rz(np.pi * (val2 - val1) * (2**(data_qubits)-1) / (2**(data_qubits)), qr_index[i])

        # calculate accumulate phase needs to be applied
        for i, (val1, val2) in reversed(list(enumerate(zip(list1, list2)))):
            const = val2 - val1
            for j in range(data_qubits):
                if j == data_qubits-1:
                    if const % 2 == 1:
                        qc.cx(qr_index[i], qr_data[0])
                    continue
                ph = np.pi * const / (2**(data_qubits-j))
                phase_data[data_qubits-1-j] += ph
        qc.h(qr_data[0])
            
        for i in reversed(range(1, data_qubits)):
            qc.rz(phase_data[i], qr_data[i])
            qc.cx(qr_index[-1], qr_data[i])

        for j in reversed(range(index_qubits - 1)):
            qc.cx(qr_index[j], qr_index[j+1])

        for i, (val1, val2) in reversed(list(enumerate(zip(list1, list2)))):
            for j in reversed(range(data_qubits-1)):
                ph = np.pi * (val2-val1) / (2**(data_qubits-j))
                qc.rz(-ph, qr_data[data_qubits-1-j])
                if i == 0:
                    continue
                qc.cx(qr_index[i], qr_data[data_qubits-1-j])

        for i in range(1, data_qubits):
            qc.cx(qr_index[0], qr_data[i])
        
        return qc.to_gate(label=" Cost Calculation ") if to_gate else qc

    # penalty part
    def constraint_testing(data_qubits: int, C_max: int, to_gate = True) -> Union[Gate, QuantumCircuit]:
        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_data, qr_f)
        
        const = 2**(data_qubits-1) - C_max
        qc.append(subroutine_add_const(data_qubits, const, True), qr_data[:])
        qc.append(qft_rotations(data_qubits).inverse().to_gate(), qr_data[:])
        qc.cx(qr_data[-1], qr_f)   
        return qc.to_gate(label=" Constraint Testing ") if to_gate else qc


    # penalty part
    def penalty_dephasing(data_qubits: int, alpha: float, gamma: float, to_gate = True) -> Union[Gate, QuantumCircuit]:
        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_data, qr_f)

        # combine phase to be applied
        ph_c = 0
        for i in range(data_qubits-1):
            ph = gamma * (2**(i)) * alpha
            ph_c += ph
        qc.rz(ph_c, qr_data[-1])

        # stripe pattern to reduce depth (utilizing the fact that both data[-1] and flag have the same value)
        for i in range(data_qubits-1):
            ph = gamma * (2**(i)) * alpha
            qc.rz(ph, qr_data[i])
            if i % 2 == 0:
                qc.cx(qr_f[0], qr_data[i])
            else:
                qc.cx(qr_data[-1], qr_data[i])
            qc.rz(-ph, qr_data[i])
            
        # stripe pattern to reduce depth
        for i in range(data_qubits-1):
            ph = gamma * (2**(i)) * alpha
            if i % 2 == 0:
                qc.cx(qr_f[0], qr_data[i])
            else:
                qc.cx(qr_data[-1], qr_data[i])

        return qc.to_gate(label=" Penalty Dephasing ") if to_gate else qc

    # penalty part
    def reinitialization(index_qubits: int, data_qubits: int, C1: list, C2: list, C_max: int, to_gate = True) -> Union[Gate, QuantumCircuit]:
        qr_index = QuantumRegister(index_qubits, "index")
        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_index, qr_data, qr_f)

        qc.append(constraint_testing(data_qubits, C_max, to_gate=True).inverse(), qr_data[:] + qr_f[:])
        qc.append(cost_calculation(index_qubits, data_qubits, C1, C2, to_gate=True).inverse(), qr_index[:] + qr_data[:])
        
        return qc.to_gate(label=" Reinitialization ") if to_gate else qc

    ### Mixing Operator ###
    def mixing_operator(index_qubits: int, beta: float, to_gate = True) -> Union[Gate, QuantumCircuit]:    
        qr_index = QuantumRegister(index_qubits, "index")
        qc = QuantumCircuit(qr_index)
        
        for i in range(index_qubits):
            qc.rx(2*beta, qr_index[i])
        
        return qc.to_gate(label=" Mixing Operator ") if to_gate else qc

    ##############################

    qr_index = QuantumRegister(index_qubits, "index")  # index register
    qr_data = QuantumRegister(data_qubits, "data")  # data register
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