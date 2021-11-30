"""
Challenge 4c solver function for the IBM Quantum Fall Challenge 2021
Author: Firstname Lastname  # TODO 1: change to your name and email
Score: 263220 # TODO 1: change to your score

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
1.I use the idea of exercise 2 where C2-C1 can be formed into a single vector and C_max = Cmax- sum(C1), to reduce the cost and to be able to use fewer controlled gates. 
2. Using phase_return how in the hints.
3.We can use pure Hadamard gates instead of QFT at the beginning of each summation in the data_qubits qubits, also it is not necessary to put in each one a QFT and inverse QFT, we can use only one or two at the beginning of the summation and another one at the end of all the qubits subroutine_add_const, therefore it is possible to use only the subroutine and the cost_calculation method, before the for is the hadamrd equivalent to the QFT and inside the fort is made subroutine_add_const with the difference of val2-val1 as in exercise 4b.
4.For constraint_testing we need only add w and using a cx for the last qubit in the qr_data, and apply the inverse of QFT,
5.penalty_dephasing only modfied the penalty the 3 first qubits of qr_data and the falg, it could  be all but is not neccesary for the number of qubits in the add results.
6.reinitialization is only apply the inverse for cost_calculation and  constraint_tesing because they only modified the qr_data and not penalty_dephasing this modified the addres of the best case.
7.mixing_operator is apply rx(2*betas) how explain in the  textbook
8.- the last iteration for micing_operator  2*beta is equal to 0 or 1Pi so is not relevant we can eliminate them in i<p-1 .
"""
# TODO 3: import all required libraries and modules
from typing import List, Union
import math
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, assemble
from qiskit.compiler import transpile
from qiskit.circuit import Gate
from qiskit.circuit.library.standard_gates import *
from qiskit.circuit.library import QFT
import numpy as np


def solver_function(L1: list, L2: list, C1: list, C2: list, C_max: int) -> QuantumCircuit:
    # TODO 4: add your name and score here
    # print name and score
    author = 'Alberto Maldonado'
    score = 263220 
    print(f'{author}: {score}')

    # the number of qubits representing answers
    index_qubits = len(L1)

    # the maximum possible total cost
    max_c = sum([l1-l0 for l0, l1 in zip(C1, C2)])    # using the idea of 4b challenge 
    C_max = C_max - sum(C1) # we reduce the cost of C1 in C_max 
    
    # the number of qubits representing data values can be defined using the maximum possible total cost as follows:
    data_qubits = math.ceil(math.log(max_c, 2)) + 1 if not max_c & (max_c - 1) == 0 else math.ceil(math.log(max_c, 2)) + 2
    
    data_qubits = data_qubits-1 # for reduce the cost we need reduce 1 value in data_qubits
    #, and reduce the cost
    ### Phase Operator ###
    # return part
    def phase_return(index_qubits: int, gamma: float, L1: list, L2: list, to_gate=True) -> Union[Gate, QuantumCircuit]:
        qr_index = QuantumRegister(index_qubits, "index")
        qc = QuantumCircuit(qr_index)
        for i in range(index_qubits):
            qc.p(-gamma*(L2[i]-L1[i]),i)
        return qc.to_gate(label=" phase return ") if to_gate else qc
    ##############################
    ### TODO ###
    ### Paste your code from above cells here ###
    # TODO 5: explain the implementation in comments

    ##############################

    # penalty part
    def subroutine_add_const(data_qubits: int, const: int, to_gate=True) -> Union[Gate, QuantumCircuit]:
    ##############################
    ### TODO ###
    ### Paste your code from above cells here ###
        qc = QuantumCircuit(data_qubits)
        a = bin(const)[2:]
        while len(a) < data_qubits:
            a = '0'+a
        a=a[::-1]
        list_a = [0]*data_qubits # consider a list for all the rotation we can reduce 
        for i in range(data_qubits): # way to do the DraperAdder 
            if a[i] =='1':
                k = 0
                for j in range(i,data_qubits):
                    list_a[data_qubits-j-1] +=np.pi/float(2**(k)) # save the values rotation in a 
                    k+=1

        for i in range(data_qubits):
            if list_a[i] != 0:
                qc.p(list_a[i],i)
        return qc.to_gate(label=" [ +" + str(const) + "] ") if to_gate else qc



    ##############################

    # penalty part
    def const_adder(data_qubits: int, const: int, to_gate=True) -> Union[Gate, QuantumCircuit]: # this is not really necessary

        qr_data = QuantumRegister(data_qubits, "data")
        qc = QuantumCircuit(qr_data)

        qc.append(subroutine_add_const(data_qubits, const),qr_data)# only call the subroutine_add_const so is not neccesary

        ##############################
        return qc.to_gate(label=" [ +" + str(const) + "] ") if to_gate else qc

    ##############################
    ### TODO ###
    ### Paste your code from above cells here ###

    ##############################

    # penalty part
    def cost_calculation(index_qubits: int, data_qubits: int, list1: list, list2: list, to_gate = True) -> Union[Gate, QuantumCircuit]:

        qr_index = QuantumRegister(index_qubits, "index")
        qr_data = QuantumRegister(data_qubits, "data")
        qc = QuantumCircuit(qr_index, qr_data)

        qr_index_l = [qr_index[i] for i in range(index_qubits)]
        qr_data_l = [qr_data[i] for i in range(data_qubits)]
        
        for i in range(data_qubits): # is not necessary to use QFT with H is the same
            qc.h(qr_data[i])

        for i, (val1, val2) in enumerate(zip(list1, list2)):
            # do the different before the QC the difference so we need to do once   control-add gate for each  value 
            #and we use subrotine_add_const in stead of const_adder
            c_gate = subroutine_add_const(data_qubits,val2-val1).control(1) 
            qc.append(c_gate, [qr_index_l[i]]+qr_data_l)
        return qc.to_gate(label=" Cost Calculation ") if to_gate else qc

    ##############################
    ### TODO ###
    ### Paste your code from above cells here ###

    ##############################

    # penalty part
    def constraint_testing(data_qubits: int, C_max: int, to_gate = True) -> Union[Gate, QuantumCircuit]:

        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_data, qr_f)

        ##############################
        min_C = int(math.log(C_max, 2))
        w = 0
        w = (2**(min_C+1))- C_max 
        qc.append(subroutine_add_const(data_qubits,int(w)-1), qr_data) # the value to valdu the eq Cost(x) > c_max
        qc = qc.compose(QFT(num_qubits=data_qubits,inverse=True,),qr_data) # we can reduce the  QFT only i nthe last sum
        

        qc.cx(qr_data[data_qubits-1], qr_f) # the format is  in c_max = 2^c, so c is the last qubit

        return qc.to_gate(label=" Constraint Testing ") if to_gate else qc

    ##############################
    ### TODO ###
    ### Paste your code from above cells here ###

    ##############################

    # penalty part
    def penalty_dephasing(data_qubits: int, alpha: float, gamma: float, to_gate = True) -> Union[Gate, QuantumCircuit]:

        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_data, qr_f)

        ##############################
        ### Phase Rotation ###
        # Provide your code here
        for i in range(data_qubits-2): # is not neccesary penalty all, only the first qubits states, so is good to reduce the cost.
            dephase= (2**(i+2.5))*alpha*gamma
            qc.cp(dephase , qr_f,qr_data[i])
        qc.p(-((2**data_qubits)*alpha*gamma),qr_f)

        ##############################

        return qc.to_gate(label=" Penalty Dephasing ") if to_gate else qc

    # penalty part
    def reinitialization(index_qubits: int, data_qubits: int, C1: list, C2: list, C_max: int, to_gate = True) -> Union[Gate, QuantumCircuit]:
    
        qr_index = QuantumRegister(index_qubits, "index")
        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_index, qr_data,qr_f)
        # only we need return the data_qubits and flag states
        ##############################
        ### Reinitialization Circuit ###
        qc.append(constraint_testing(data_qubits, C_max).inverse(),qr_data[:] + qr_f[:]) 
        qc.append(cost_calculation(index_qubits, data_qubits, C1, C2).inverse(),qr_index[:]+qr_data[:])
        ##############################

  
        return qc.to_gate(label=" Reinitialization ") if to_gate else qc

    ### Mixing Operator ###
    def mixing_operator(index_qubits: int, beta: float, to_gate = True) -> Union[Gate, QuantumCircuit]:

    ##############################
        qr_index = QuantumRegister(index_qubits, "index")
        qc = QuantumCircuit(qr_index)
        for i in range(index_qubits):
            if beta != 0:
                qc.rx(2*beta, qr_index[i])
    ##############################
        return qc.to_gate(label=" Mixing Operator ") if to_gate else qc
    

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
