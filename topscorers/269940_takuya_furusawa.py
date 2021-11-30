#!/usr/bin/env python
# coding: utf-8

# # Challenge 4c solver function for the IBM Quantum Fall Challenge 2021
# Author: Takuya Furusawa 
# Score: 269940
# 
# Summary of the approach:
# 1. Use the Quantum Fourier Transformation only once
# 2. Set C1 to be [0,...,0] to reduce the data_qubits
# 3. Set 1 in C2 to be 0 to reduce the data_qubits
# 


# In[2]:
import numpy as np
import math
from typing import List, Union
from qiskit import QuantumCircuit,QuantumRegister, ClassicalRegister
from qiskit.circuit import Gate
from qiskit.circuit.library.standard_gates import *
from qiskit.circuit.library import QFT

def solver_function(L1: list, L2: list, C1: list, C2: list, C_max: int) -> QuantumCircuit:
    # print name and score
    author = 'Takuya Furusawa'
    score = 269940
    print(f'{author}: {score}')

    #### Make the problem easier first
    C_max = C_max - sum(C1) # Reduce C_max
    num_of_ones = 0
    for i in range(len(C1)):
        C2[i]-= C1[i] # Only the difference is important
        C1[i] = 0 # Set C1 = [0,...,0]
        if C2[i]==1:
            C2[i]=0 # Set 1 in C2 to be 0
            num_of_ones +=1 # Count the number of 1 in C2
    C_max -= int(num_of_ones/2) # Subtracting nothing is less but subtracting num_of_ones is too much...
    c = int( math.log(C_max,2) )
    if not( C_max == 2**c ):
        c += 1
    geta = 2**c - C_max-1 
    C_max = 2**c-1 # Set C_max = 2**c - 1
    C1[0] += geta # the difference between the original and new C_max is added
    C2[0] += geta # the difference between the original and new C_max is added

    # the number of qubits representing answers
    index_qubits = len(L1)

    # the maximum possible total cost
    max_c = sum([max(l0, l1) for l0, l1 in zip(C1, C2)])

    # the number of qubits representing data values can be defined using the maximum possible total cost as follows:
    data_qubits = math.ceil(math.log(max_c, 2)) if not max_c & (max_c - 1) == 0 else math.ceil(math.log(max_c, 2)) + 1
    
    ### Phase Operator ###
    # return part
    def phase_return(index_qubits: int, gamma: float, L1: list, L2: list, to_gate=True) -> Union[Gate, QuantumCircuit]:
        qr_index = QuantumRegister(index_qubits, "index")
        qc = QuantumCircuit(qr_index)
        threshold = 1
        for i in range(index_qubits):
            angle = L1[i]-L2[i]
            if angle<-threshold:
                qc.p(gamma*angle,i)
        return qc.to_gate(label=" phase return ") if to_gate else qc
        

    # penalty part
    def subroutine_add_const(data_qubits: int, const: int, to_gate=True) -> Union[Gate, QuantumCircuit]:
        qc = QuantumCircuit(data_qubits)
        for i in range(data_qubits):
            angle = const/(2**(data_qubits - i))
            if not angle == int(angle):
                qc.p(2*np.pi*angle, i)
        return qc.to_gate(label=" [+"+str(const)+"] ") if to_gate else qc
        

    # penalty part
    def const_adder(data_qubits: int, const: int, to_gate=True) -> Union[Gate, QuantumCircuit]:
        qr_data = QuantumRegister(data_qubits, "data")
        qc = QuantumCircuit(qr_data)
        qc.append(subroutine_add_const(data_qubits=data_qubits,const=const),qr_data[:]) # No QFT here
        return qc.to_gate(label=" [ +" + str(const) + "] ") if to_gate else qc
        
    # penalty part
    def cost_calculation(index_qubits: int, data_qubits: int, list1: list, list2: list, to_gate = True) -> Union[Gate, QuantumCircuit]:
        qr_index = QuantumRegister(index_qubits, "index")
        qr_data = QuantumRegister(data_qubits, "data")
        qc = QuantumCircuit(qr_index, qr_data)
        
        threshold = 1
        
        qc.append(QFT(data_qubits).to_gate(),qr_data) # QFT needs only here #! Added by Bo Yang
        for i, (val1, val2) in enumerate(zip(list1, list2)):
            if val2>threshold: ## Neglect val2=0 to save the cost
                const_adder_2 = const_adder(data_qubits=data_qubits,const=val2).control(1)
                qc.append(const_adder_2, [qr_index[i]] + qr_data[:])
            
            if i==0:
                const_adder_1 = const_adder(data_qubits=data_qubits,const=val1).control(1)
                qc.x(qr_index[i])
                qc.append(const_adder_1, [qr_index[i]] + qr_data[:]) # No addition of C1 except C1[0]
                qc.x(qr_index[i])
        qc.append(QFT(data_qubits,inverse=True).to_gate(),qr_data) # inverse QFT needs only here
        return qc.to_gate(label=" Cost Calculation ") if to_gate else qc

    # penalty part
    def constraint_testing(data_qubits: int, C_max: int, to_gate = True) -> Union[Gate, QuantumCircuit]:
        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_data, qr_f)
        
        # Since C_max = 2**c - 1, e.g., qr_data = xxxyyy is ok (i.e., flag=0) if all of x's are 0.
        a = int(math.log(C_max,2))
        qc.x(qr_data[:])
        if data_qubits-a>1:
            qc.mcx(qr_data[a+1:],qr_f)
        qc.x(qr_f)
        return qc.to_gate(label=" Constraint Testing ") if to_gate else qc

    # penalty part
    def penalty_dephasing(data_qubits: int, alpha: float, gamma: float, to_gate = True) -> Union[Gate, QuantumCircuit]:
        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_data, qr_f)
        
        for i in range(data_qubits):
            qc.cp(2*alpha*gamma*(2**(data_qubits)-1-2**i ),qr_f,qr_data[i])
        qc.p(-2*alpha*gamma*C_max,qr_f)
        return qc.to_gate(label=" Penalty Dephasing ") if to_gate else qc

    # penalty part
    def reinitialization(index_qubits: int, data_qubits: int, C1: list, C2: list, C_max: int, to_gate = True) -> Union[Gate, QuantumCircuit]:
        qr_index = QuantumRegister(index_qubits, "index")
        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_index, qr_data, qr_f)
        
        qc.append(constraint_testing(data_qubits=data_qubits,C_max=C_max,to_gate=True),qr_data[:]+qr_f[:])
        qc.append(cost_calculation(index_qubits=index_qubits,data_qubits=data_qubits,list1=C1,list2=C2,to_gate=True).inverse(),qr_index[:]+qr_data[:])
        return qc.to_gate(label=" Reinitialization ") if to_gate else qc

    ### Mixing Operator ###
    def mixing_operator(index_qubits: int, beta: float, to_gate = True) -> Union[Gate, QuantumCircuit]:
        qr_index = QuantumRegister(index_qubits, "index")
        qc = QuantumCircuit(qr_index)
        if beta>1e-5: # beta = 0 is identity so this reduces # of gates.
            for i in range(index_qubits):
                qc.rx(2*beta,i)
        return qc.to_gate(label=" Mixing Operator ") if to_gate else qc

    qr_index = QuantumRegister(index_qubits, "index")  # index register
    qr_data = QuantumRegister(data_qubits, "data")  # data register
    qr_f = QuantumRegister(1, "flag")  # flag register
    cr_index = ClassicalRegister(index_qubits,"c_index")  # classical register storing the measurement result of index register
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
