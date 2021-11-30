"""
Challenge 4c solver function for the IBM Quantum Fall Challenge 2021
Author: Kentaro Ohno 
Score: 240524

Summary of the approach:
1. Reduce the number of QFT and its inverse as much as possible by exploiting cancellation in successive QFT-addition and by initializing qr_data.
This reduces the score from 80M to 1.4M.
2. Shift each cost value in C1, C2, and C_max so that C1 becomes a zero vector, which does not change the optimization problem.
This enables us to remove the addition of values in C1 and reduce the number of qubits to store the total cost, which reduces the score by 1M. 
3. When using QFTAdder to add a constant number, we pre-compute the total phase transition and then apply a phase gate, instead of applying phase gates indivisually for each bit of addend (which is described in the original paper).
This reduces the score by 50k.
4. Lastly, we noticed that c+1 qubits is sufficient for the test problem instances, where c is the least integer such that C_max -1< 2^c.
Although this may not hold generally (e.g., when sum(C2) > 2*C_max), we can reduce the score a little further by decreasing the number of qubits for qr_data in this challenge.
"""
from typing import List, Union
import math
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit import Gate
from qiskit.circuit.library.standard_gates import *

def solver_function(L1: list, L2: list, C1: list, C2: list, C_max: int) -> QuantumCircuit:
    
    #print("Kentaro Ohno, score: 297524")
    
    # Preprocessing (Approach 2)
    # We shift the cost value in the given problem so that C1 becomes a zero vector (see also cost_calculation function).
    C_max = C_max - sum(C1)
    # Since we frequently use 
    # - a value c which is the least integer such that C_max -1 < 2^c, and
    # - offset = 2^c - C_max, which we need to test the constraint using a overflowed bit,
    # we define them here globally.
    exponent = 1
    upper = 2
    while upper < C_max:
        upper *= 2
        exponent += 1
    offset = upper - C_max
        
    # the number of qubits representing answers
    index_qubits = len(L1)
    
    # the maximum possible total cost
    max_c = sum(C2) - sum(C1)
    
    # the number of qubits representing data values can be defined using the maximum possible total cost as follows:
    data_qubits = exponent + 1  # This is empirically sufficient for the judge (Approach 4), but in general more bits may be necessary.
    
    ### Phase Operator ###
    # return part
    def phase_return(index_qubits: int, gamma: float, L1: list, L2: list, to_gate=True) -> Union[Gate, QuantumCircuit]:
        qr_index = QuantumRegister(index_qubits, "index")
        qc = QuantumCircuit(qr_index)

        ##############################
        ### U_1(gamma * (lambda2 - lambda1)) for each qubit ###
        for i in range(index_qubits):
            qc.p(-gamma * (L2[i]-L1[i])/2, qr_index[i])
        ##############################

        return qc.to_gate(label=" phase return ") if to_gate else qc
    
    # penalty part
    def subroutine_add_const(data_qubits: int, const: int, to_gate=True) -> Union[Gate, QuantumCircuit]:
        '''
        Here we use the QFTAdder for constant addition.
        On the QFT in QFTAdder (Approach 1, which is the most significant improvement):
        - Most inverse QFT in QFTAdder is cancelled by QFT in the next addition, so we move them to cost calculation to apply them only once in a QAOA loop.
        '''
        qc = QuantumCircuit(data_qubits)
        ##############################
        ### Phase Rotation ###

        for i in range(data_qubits):
            # We pre-compute the total phase, then apply a phase gate only once for each qubits (Approach 3)
            phi = 0
            for j in range(i+1):
                if (const >> j) & 1:
                    phi += 1 / 2 ** (i+1-j)
            if phi > 0:
                qc.p(2 * math.pi * phi, i)
        return qc.to_gate(label=" [+"+str(const)+"] ") if to_gate else qc


    def const_adder(data_qubits: int, const: int, to_gate=True) -> Union[Gate, QuantumCircuit]:

        qr_data = QuantumRegister(data_qubits, "data")
        qc = QuantumCircuit(qr_data)
        
        ### Phase Rotation ###
        qc.append(subroutine_add_const(data_qubits, const), qr_data)

        return qc.to_gate(label=" [ +" + str(const) + "] ") if to_gate else qc
        
    # penalty part
    def cost_calculation(index_qubits: int, data_qubits: int, list1: list, list2: list, to_gate = True) -> Union[Gate, QuantumCircuit]:
        '''
        We calculate the total cost here.
        The resulted qr_data satisfies the following:
        qr_data[exponent] = 1 if the constraint is violated
        (The case when (total cost)=C_max is the special case, where qr_data[exponent]=1 AND constraint is valid, but no problem because the penalty equals 0)
        '''
        qr_index = QuantumRegister(index_qubits, "index")
        qr_data = QuantumRegister(data_qubits, "data")
        qc = QuantumCircuit(qr_index, qr_data)

        # We moved QFT and addition of offset to the circuit initialization (outside this function) (Approach 1)
        # since they are cancelled in successive QAOA loops.

        for i, (val1, val2) in enumerate(zip(list1, list2)):
            ### Add val2 **-val1** using const_adder controlled by i-th index register (set to 1) ###
            qc.append(const_adder(data_qubits, val2-val1).control(), [qr_index[i]] + qr_data[:])
        
        ### IQFT ### (see the explanation above for reduction of the number of (inverse) QFT in QFTAdder)
        for i in range(data_qubits):
            for j in range(i):
                qc.cp(-math.pi / 2**(i-j), qr_data[i], qr_data[j])
            qc.h(qr_data[i])
        return qc.to_gate(label=" Cost Calculation ") if to_gate else qc
        
    # penalty part
    def constraint_testing(data_qubits: int, C_max: int, to_gate = True) -> Union[Gate, QuantumCircuit]:
        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_data, qr_f)

        qc.cx(qr_data[exponent], qr_f)
        
        return qc.to_gate(label=" Constraint Testing ") if to_gate else qc
    
    # penalty part
    def penalty_dephasing(data_qubits: int, alpha: float, gamma: float, to_gate = True) -> Union[Gate, QuantumCircuit]:

        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_data, qr_f)

        ##############################
        ### Phase Rotation ###

        # The penalty needs to be positive only when qr_f=1, so we use a phase gate controlled by qr_f.
        # The magnitude of penalty equals to (total cost) - C_max, which equals to (value represented in qr_data) - 2^c.
        # This value can be simply represented by bits lower than the highest (c-th) bit.
        for i in range(exponent):
            theta = gamma * alpha * 2**i 
            qc.cp(theta, qr_data[i], qr_f)

        ##############################

        return qc.to_gate(label=" Penalty Dephasing ") if to_gate else qc
        
    # penalty part
    def reinitialization(index_qubits: int, data_qubits: int, C1: list, C2: list, C_max: int, to_gate = True) -> Union[Gate, QuantumCircuit]:

        qr_index = QuantumRegister(index_qubits, "index")
        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_index, qr_data, qr_f)

        ### Reinitialization Circuit ###
        qc.append(constraint_testing(data_qubits=data_qubits, C_max=C_max).inverse(), qr_data[:] + qr_f[:])
        qc.append(cost_calculation(index_qubits, data_qubits, C1, C2).inverse(), qr_index[:] + qr_data[:])

        return qc.to_gate(label=" Reinitialization ") if to_gate else qc

    ### Mixing Operator ###
    def mixing_operator(index_qubits: int, beta: float, to_gate = True) -> Union[Gate, QuantumCircuit]:

        qr_index = QuantumRegister(index_qubits, "index")
        qc = QuantumCircuit(qr_index)

        ### Mixing Operator ###
        qc.rx(2*beta, qr_index)

        return qc.to_gate(label=" Mixing Operator ") if to_gate else qc
    
    qr_index = QuantumRegister(index_qubits, "index") # index register
    qr_data = QuantumRegister(data_qubits, "data") # data register
    qr_f = QuantumRegister(1, "flag") # flag register
    cr_index = ClassicalRegister(index_qubits, "c_index") # classical register storing the measurement result of index register
    qc = QuantumCircuit(qr_index, qr_data, qr_f, cr_index)
                    
    ### initialize the index register with uniform superposition state ###
    qc.h(qr_index)

    # Initialize with adding the offset for C_max (offset = 2^c - C_max where c is the least integer such that offset is non-negative)
    # This shift method enables to detect the constraint violation by using a overflow bit (see the cited paper for this challenge). 
    for i in range(data_qubits):
        if (offset >> i) & 1:
            qc.x(qr_data[i])
    ### QFT ###
    for i in range(data_qubits):
        qc.h(qr_data[-1-i])
        for j in range(i+1,data_qubits):
            qc.cp(math.pi / 2**(j-i), qr_data[-1-j], qr_data[-1-i])
    
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
