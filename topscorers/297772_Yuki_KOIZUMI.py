"""
Challenge 4c solver function for the IBM Quantum Fall Challenge 2021
Author: Yuki KOIZUMI # TODO 1: change to your name and email
Score:297,772 # TODO 1: change to your score
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
1.Changing the values of C1 and C2
2.Using QFT circuit only once in one cycle
3.Optimizing of Constraint testing without ancillas or IntegerComparator
​
"""
from typing import List, Union
import math
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, assemble
from qiskit.compiler import transpile
from qiskit.circuit import Gate
from qiskit.circuit.library.standard_gates import *
from math import pi


def solver_function(L1: list, L2: list, C1: list, C2: list, C_max: int) -> QuantumCircuit:

    author = 'Yuki KOIZUMI'
    score = 299772 #In new grader,1824432
    print(f'{author}: {score}')
    # the number of qubits representing answers
    index_qubits = len(L1)
    
    # the maximum possible total cost
    max_c = sum([max(l0, l1) for l0, l1 in zip(C1, C2)])
    
    # the number of qubits representing data values can be defined using the maximum possible total cost as follows:
    data_qubits = 5+10
    
    ### Phase Operator ###
    # return part
    def phase_return(index_qubits: int, gamma: float, L1: list, L2: list, to_gate=True) -> Union[Gate, QuantumCircuit]:
        ##############################
        qr_index = QuantumRegister(index_qubits, "index")
        qc = QuantumCircuit(qr_index)
    
        #U１(-gammma*lambda^t)
        for i in range(index_qubits):
            if sig == 1 and i == cont:
                continue
            qc.p(-1*gamma*(L2[i]-L1[i])/2,qr_index[i]) 
    
        ##############################
    
        return qc.to_gate(label=" phase return ") if to_gate else qc
        ##############################
    
    # penalty part
    def subroutine_add_const(data_qubits: int, const: int, to_gate=True) -> Union[Gate, QuantumCircuit]:
        #Not using
        ##############################
        ### TODO ###
        ### Paste your code from above cells here ###
        qr_data = QuantumRegister(data_qubits, "data")
        qc = QuantumCircuit(qr_data)
    ##############################
    ### Phase Rotation ###
    # Provide your code here
        n = 5
        bin_const = bin(const)[2:]
        len_const = len(bin_const)
        for l in range(len_const):
            k = len_const - n #qbitが5,len=4の場合，1000は定数レジスター[2*5-2]に加算したい．
            if bin_const[l] == '1':
                qc.x(qr_data[10 -1 -l + k])
        #data_qubitは2nであり，目的の量子レジスターを0からn-1，定数のレジスターをnから2n-1とする．
        for i in range(n):
            #目的のレジスタ
            pur_label = n-1-i 
            for j in range(max(1,pur_label),pur_label+2):
            #目的の量子レジスタに2n-jのレジスタをコントロールとして，π/2**(j+1) すなわちR_(j+1)を
               #かける
                qc.cp(pi/(2**(j-1)), qr_data[pur_label+n-j+1], qr_data[pur_label])
                #qc.z(qr_data[0])
       
        #定数のレジスターを０に戻す．
        for l in range(len_const):
            k = len_const - n #qbitが5,len=4の場合，1000は定数レジスター[2*5-2]に加算したい．
            if bin_const[l] == '1':
                qc.x(qr_data[10 -1 -l + k])
        #data_qubitは2nであり，目的の量子レジスターを0からn-1，定数のレジスターをnから2n-1とする．
        
        
        ##############################
        return qc.to_gate(label=" [+"+str(const)+"] ") if to_gate else qc

    # penalty part
    def const_adder(data_qubits: int, const: int, to_gate=True) -> Union[Gate, QuantumCircuit]:
        #Not using
        qr_data = QuantumRegister(data_qubits, "data")
        qc = QuantumCircuit(qr_data)
    
    ##############################
    ### QFT ###
    # Provide your code here
        n = 5
        for i in range(n-1,-1,-1):
            qc.h(qr_data[i])   #Hゲートをi番目にかける
            for j in range(i-1,-1,-1): #j番目の制御ゲートを考える．i-1から1番目
                k = i-j #指数を考える R_k
                qc.cp(pi/2**k, qr_data[j],qr_data[i])
        
    ##############################

    ##############################
    ### Phase Rotation ###
    # Use `subroutine_add_const`
        qc.append(subroutine_add_const(data_qubits, 0),qr_data[:])
    
    ##############################
    
    ##############################
    ### IQFT ###
    # Provide your code here
        for i in range(0,n): #目的ゲートiを主体に考える
            for j in range(0,i): #制御ゲートは0からi-1
                k = i-j
                qc.cp(-pi/2**k, qr_data[j], qr_data[i])
            qc.h(qr_data[i])
    
    
    ##############################
        return qc.to_gate(label=" [ +" + str(const) + "] ") if to_gate else qc##
    
    # penalty part
    def cost_calculation(index_qubits: int, data_qubits: int, list1: list, list2: list, to_gate = True) -> Union[Gate, QuantumCircuit]:
    
        qr_index = QuantumRegister(index_qubits, "index")
        qr_data = QuantumRegister(data_qubits, "data")
        qc = QuantumCircuit(qr_index, qr_data)
        n = 5

            #目的レジスタに加算する    
        for i in range(3):
            for j in range(5):
                if i != 2:
                    val2 = New_C2[5*i+j]
        
        ##############################
            ### Add val2 using const_adder controlled by i-th index register (set to 1) ###
                    bin_val2 = bin(val2)[2:]
                    len_val2 = len(bin_val2)
                    for l in range(len_val2):
                        if bin_val2[l] == '1' and len_val2 == 2:
                            qc.cx(qr_index[5*i+j], qr_data[5+2*(j+1) - 1- l] ) 
                        elif bin_val2[l] == '1':
                            qc.cx(qr_index[5*i+j], qr_data[5+2*(j+1) - 2] )
                else:
                    val2 = New_C2[5*i+j]
                    bin_val2 = bin(val2)[2:]
                    len_val2 = len(bin_val2)
                    for l in range(len_val2):
                            #qbitが5,len=4の場合，1000は定数レジスター[2*5-2]に加算したい．
                        if bin_val2[l] == '1' and len_val2 == 2:
                            qc.cx(qr_index[5*i+j], qr_data[5+2*(j+1) - 1- l] ) 
                        elif bin_val2[l] == '1':
                            qc.cx(qr_index[5*i+j], qr_data[5+2*(j+1) - 2] ) 
                    break
               
        
            #加算場所
            if i != 2:
                for k in range(5):
                    if New_C2[5*i+k] == 3:
                        for t in range(n):
                            #目的のレジスタ
                            pur_label = n-1-t
                            for j in range(2,0,-1):
                                s = 5+2*k+(j-1)  
                                m = max(pur_label,1)+(2-j)
                    #目的の量子レジスタに2n-jのレジスタをコントロールとして，π/2**(j+1) すなわちR_(j+1)を
                       #かける   
                                if pur_label  != 0:
                                    qc.cp(pi/(2**(m-1)), qr_data[s], qr_data[pur_label])
                                elif pur_label == 0 and j ==1:
                                    qc.cp(pi/(2**(m-2)), qr_data[s], qr_data[pur_label])
                                        
                    elif New_C2[5*i+k] == 2:
                        for t in range(n):
                            #目的のレジスタ
                            pur_label = n-1-t
                            for j in range(2,1,-1):
                                s = 5+2*k+(j-1)  
                                m = max(pur_label,1)+(2-j)
                    #目的の量子レジスタに2n-jのレジスタをコントロールとして，π/2**(j+1) すなわちR_(j+1)を
                       #かける   
                                if pur_label  != 0:
                                    qc.cp(pi/(2**(m-1)), qr_data[s], qr_data[pur_label])
                                elif pur_label == 0 and j ==1:
                                    qc.cp(pi/(2**(m-2)), qr_data[s], qr_data[pur_label])
                                        
                    else:
                        for t in range(n):
                            pur_label = n-1-t
                            for j in range(1,0,-1):
                                s = 5+2*k+(j-1)  
                                m = max(pur_label,1)+(2-j)
                    #目的の量子レジスタに2n-jのレジスタをコントロールとして，π/2**(j+1) すなわちR_(j+1)を
                       #かける   
                                if pur_label  != 0:
                                    qc.cp(pi/(2**(m-1)), qr_data[s], qr_data[pur_label])
                                elif pur_label == 0 and j ==1:
                                    qc.cp(pi/(2**(m-2)), qr_data[s], qr_data[pur_label])
            else:
                for k in range(1):
                    if New_C2[5*i+k] == 3:
                        for t in range(n):
                        #目的のレジスタ
                            pur_label = n-1-t
                            for j in range(2,0,-1):
                                s = 5+2*k+(j-1)  
                                m = max(pur_label,1)+(2-j)
                    #目的の量子レジスタに2n-jのレジスタをコントロールとして，π/2**(j+1) すなわちR_(j+1)を
                       #かける   
                                if pur_label  != 0:
                                    qc.cp(pi/(2**(m-1)), qr_data[s], qr_data[pur_label])
                                elif pur_label == 0 and j ==1:
                                    qc.cp(pi/(2**(m-2)), qr_data[s], qr_data[pur_label])
                                        
                    elif New_C2[5*i+k] == 2:
                        for t in range(n):
                            #目的のレジスタ
                            pur_label = n-1-t
                            for j in range(2,1,-1):
                                s = 5+2*k+(j-1)  
                                m = max(pur_label,1)+(2-j)
                    #目的の量子レジスタに2n-jのレジスタをコントロールとして，π/2**(j+1) すなわちR_(j+1)を
                       #かける   
                                if pur_label  != 0:
                                    qc.cp(pi/(2**(m-1)), qr_data[s], qr_data[pur_label])
                                elif pur_label == 0 and j ==1:
                                    qc.cp(pi/(2**(m-2)), qr_data[s], qr_data[pur_label])
                                    
                    else:
                        for t in range(n):
                            pur_label = n-1-t
                            for j in range(1,0,-1):
                                s = 5+2*k+(j-1)  
                                m = max(pur_label,1)+(2-j)
                    #目的の量子レジスタに2n-jのレジスタをコントロールとして，π/2**(j+1) すなわちR_(j+1)を
                       #かける   
                                if pur_label  != 0:
                                    qc.cp(pi/(2**(m-1)), qr_data[s], qr_data[pur_label])
                                elif pur_label == 0 and j ==1:
                                    qc.cp(pi/(2**(m-2)), qr_data[s], qr_data[pur_label])
                        
            
        ##############################
            ### Add val2 using const_adder controlled by i-th index register (set to 1) ###
            for j in range(5):    
                if i != 2:
                    val2 = New_C2[5*i+j]
                    bin_val2 = bin(val2)[2:]
                    len_val2 = len(bin_val2)
                    for l in range(len_val2):
                        #qbitが5,len=4の場合，1000は定数レジスター[2*5-2]に加算したい．
                        if bin_val2[l] == '1' and len_val2 == 2:
                            qc.cx(qr_index[5*i+j], qr_data[5+2*(j+1) - 1- l] ) 
                        elif bin_val2[l] == '1':
                            qc.cx(qr_index[5*i+j], qr_data[5+2*(j+1) - 2] )
                else:
                    val2 =  New_C2[5*i+j]
                    bin_val2 = bin(val2)[2:]
                    len_val2 = len(bin_val2)
                    for l in range(len_val2):
                        #qbitが5,len=4の場合，1000は定数レジスター[2*5-2]に加算したい．
                        if bin_val2[l] == '1' and len_val2 == 2:
                            qc.cx(qr_index[5*i+j], qr_data[5+2*(j+1) - 1- l] ) 
                        elif bin_val2[l] == '1':
                            qc.cx(qr_index[5*i+j], qr_data[5+2*(j+1) - 2] ) 
                    break
            #IQFT
        for q in range(0,n): #目的ゲートiを主体に考える
            for x in range(0,q): #制御ゲートは0からi-1
                k = q-x
                qc.cp(-pi/2**k, qr_data[x], qr_data[q])
            qc.h(qr_data[q])
        
                
        
           
        
        return qc.to_gate(label=" Cost Calculation ") if to_gate else qc
    
    # penalty part
    def constraint_testing(data_qubits: int, C_max: int, to_gate = True) -> Union[Gate, QuantumCircuit]:
        
        
        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_data, qr_f)
    
    ##############################
        qc.cx(qr_data[4],qr_f[0])
    ### Set the flag register for indices with costs larger than C_max ###
    # Provide your code here
    
    
    
    ##############################
    
        return qc.to_gate(label=" Constraint Testing ") if to_gate else qc
    
    # penalty part
    def reinitialization(index_qubits: int, data_qubits: int, C1: list, C2: list, C_max: int, to_gate = True) -> Union[Gate, QuantumCircuit]:
    
        qr_index = QuantumRegister(index_qubits, "index")
        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_index, qr_data, qr_f)
    
    ##############################
    ### Reinitialization Circuit ###
        qc.cx(qr_data[4],qr_f[0])
        qc.append(cost_calculation(index_qubits, data_qubits, C1, C2).inverse(), 
                  qr_index[:] + qr_data[:])
    # Put your implementation here
    ##############################
    
        return qc.to_gate(label=" Reinitialization ") if to_gate else qc
        
    # penalty part
    def penalty_dephasing(data_qubits: int, alpha: float, gamma: float,  to_gate = True) -> Union[Gate, QuantumCircuit]:
    
        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_data, qr_f)
        
        n = 5
    ### Phase Rotation ###
   
        for _ in range(1):
            for i in range(4):
                qc.cp(alpha*gamma*(2**(i)),qr_f[0],qr_data[i])
            qc.p(alpha*gamma,qr_f[0])
    ##############################
    
        return qc.to_gate(label=" Penalty Dephasing ") if to_gate else qc

    
        #for i in range(cost_qubits):
            #qc.cp((2**i) * alpha * gamma, qr_f, qr_cost[i])

        # Add phase -alpha * (Cmax + w) = -alpha * 2^(cost_qubits-1) to all
        # infeasible states
        #C_max_plus_w = 2**(cost_qubits-1)-1
        #qc.p(-C_max_plus_w * alpha * gamma, qr_f)

        return qc.to_gate(label=" penalty_dephasing ") if to_gate else qc
    ### Mixing Operator ###
    def mixing_operator(index_qubits: int, beta: float, to_gate = True) -> Union[Gate, QuantumCircuit]:
        
        qr_index = QuantumRegister(index_qubits, "index")
        qc = QuantumCircuit(qr_index)
    
        ##############################
        ### Mixing Operator ###
        for i in range(index_qubits):
            if sig == 1 and i == cont:
                continue
            qc.rx(2*beta, qr_index[i])
        # Put your implementation here
        ##############################
    
        return qc.to_gate(label=" Mixing Operator ") if to_gate else qc
        ##############################
    
    # Revising C1 and C2
    New_C1= []
    New_C2 = []
    New_C_max = int(C_max)
    for i in range(len(C1)):
        New_C1.append(0)
        New_C2.append(C2[i]-C1[i])
        New_C_max -= C1[i]
    L = (sum(L2)-sum(L1))/New_C_max
    LC =  [(L2[i]-L1[i])/New_C2[i] for i in range(10)]
    maxLC = max(LC)
    sig = 0
    cont = 0
    for i in range(len(LC)):
        if LC[i] == maxLC and New_C2[i] == 1:
            sig = 1
            cont = i
            
    qr_index = QuantumRegister(index_qubits, "index") # index register
    qr_data = QuantumRegister(data_qubits, "data") # data register
    qr_f = QuantumRegister(1, "flag") # flag register
    cr_index = ClassicalRegister(index_qubits, "c_index") # classical register storing the measurement result of index register
    qc = QuantumCircuit(qr_index, qr_data, qr_f, cr_index)
    C1 = New_C1
    C2 = New_C2
    sig = 0
    ### initialize the index register with uniform superposition state ###
    qc.h(qr_index)
    #qc.x(qr_index[:4])
    if sig == 1:
        qc.h(qr_index[cont])
        qc.x(qr_index[cont])
        New_C_max -= 1
        L = (sum(L2)-sum(L1)-(L2[cont]-L1[cont]))/New_C_max
     #adding 2^c
   
    const = 15 - New_C_max 
    C_max = 15
    bin_const = bin(const)[2:]
    len_const = len(bin_const)
   
    for l in range(len_const):
        k = len_const - 5 #qbitが5,len=4の場合，1000は定数レジスター[2*5-2]に加算したい．
        if bin_const[l] == '1':
            qc.x(qr_data[5 -1 -l + k])
    
    n = 5
        #QFT
    for q in range(n-1,-1,-1):
        qc.h(qr_data[q])   #Hゲートをi番目にかける
        for x in range(q-1,-1,-1): #j番目の制御ゲートを考える．i-1から1番目
            k = q-x #指数を考える R_k
            qc.cp(pi/2**k, qr_data[x],qr_data[q])
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

