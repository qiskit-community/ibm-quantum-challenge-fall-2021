import numpy as np
from qiskit import Aer
from qiskit import IBMQ
import os

from typing import List, Union
import math
from qiskit.extensions import *
from qiskit import BasicAer, execute
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, assemble
from qiskit.compiler import transpile
from qiskit.circuit import Gate
from qiskit.circuit.library.standard_gates import *
from qiskit.circuit.library import QFT,CXGate
from qiskit import QuantumCircuit

def solver_function(L1: list, L2: list, C1: list, C2: list, C_max: int) -> QuantumCircuit:
    author = 'Kento Ueda'
    score = 232824
    print(f'{author}: {score}')
    index_qubits = len(L1)
    
    # the maximum possible total cost
    max_c = sum([l1-l0 for l0, l1 in zip(C1, C2)])
    data_qubits = math.ceil(math.log(max_c, 2)) if not max_c & (max_c - 1) == 0 else math.ceil(math.log(max_c, 2)) + 1
    C_max -= sum(C1)
    def phase_return(index_qubits: int, gamma: float, L1: list, L2: list, to_gate=True) -> Union[Gate, QuantumCircuit]:
        qr_index = QuantumRegister(index_qubits, "index")
        qc = QuantumCircuit(qr_index)
        for index, (l1, l2) in enumerate(zip(L1,L2)):
            qc.p(gamma*(l1-l2)/2,index)
        return qc.to_gate(label=" phase return ") if to_gate else qc
    

    def subroutine_add_const(data_qubits,const, to_gate=True) -> Union[Gate, QuantumCircuit]:
        const = bin(const)[2:].zfill(data_qubits)[::-1]
        qr_data =QuantumRegister(data_qubits, "data")
        qc = QuantumCircuit(qr_data)
        for i in range(data_qubits):
            res = 0
            for j in range(0, data_qubits-i):
                if const[data_qubits-i-j-1]=='1':
                    res +=np.pi/float(2**(j))
            if res:
                qc.p(res, qr_data[data_qubits-i-1])
        return qc.to_gate(label=" add_const ") if to_gate else qc
    def subroutine_subtract_const(data_qubits,const, to_gate=True) -> Union[Gate, QuantumCircuit]:
        const = bin(const)[2:].zfill(data_qubits)[::-1]
        qr_data =QuantumRegister(data_qubits, "data")
        qc = QuantumCircuit(qr_data)
        for i in range(data_qubits):
            res = 0
            for j in range(0, data_qubits-i):
                if const[data_qubits-i-j-1]=='1':
                    res-=np.pi/float(2**(j))
            if res:
                qc.p(res, qr_data[data_qubits-i-1])
        return qc.to_gate(label=" add_const ") if to_gate else qc
    def cost_calculation(index_qubits: int, data_qubits: int, list1: list, list2: list, to_gate = True) -> Union[Gate, QuantumCircuit]:
        qr_index = QuantumRegister(index_qubits, "index")
        qr_data = QuantumRegister(data_qubits, "data")
        qc = QuantumCircuit(qr_index, qr_data)
        qc.h(qr_data)
        for i, (val1, val2) in enumerate(zip(list1, list2)):
            qc.append(subroutine_add_const(data_qubits,val2-val1).control(1),[qr_index[i]]+qr_data[:])
        return qc.to_gate(label=" add_const ") if to_gate else qc

    def constraint_testing(data_qubits: int, C_max: int, to_gate = True) -> Union[Gate, QuantumCircuit]:
        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_data, qr_f)
        qc.append(subroutine_subtract_const(data_qubits,C_max),qr_data[:])
        qc.append(QFT(data_qubits,inverse=True,do_swaps=False).to_gate(),qr_data[:])
        qc.append(CXGate(ctrl_state=0),[qr_data[-1]]+qr_f[:])
        return qc.to_gate(label=" Cost Calculation ") if to_gate else qc

    def penalty_dephasing(data_qubits: int, alpha: float, gamma: float, to_gate = True) -> Union[Gate, QuantumCircuit]:
        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_data, qr_f)
        qc.p(-1*2**(data_qubits-1)+1*alpha*gamma, qr_f)
        return qc.to_gate(label=" Penalty Dephasing ") if to_gate else qc
        
        
    def reinitialization(index_qubits: int, data_qubits: int, C1: list, C2: list, C_max: int, to_gate = True) -> Union[Gate, QuantumCircuit]:
        qr_index = QuantumRegister(index_qubits, "index")
        qr_data = QuantumRegister(data_qubits, "data")
        qr_f = QuantumRegister(1, "flag")
        qc = QuantumCircuit(qr_index, qr_data, qr_f)
        qc.append(constraint_testing(data_qubits,C_max).inverse(), qr_data[:] +qr_f[:])
        qc.append(cost_calculation(index_qubits, data_qubits, C1, C2, to_gate = True).inverse(),qr_index[:] + qr_data[:])
        return qc.to_gate(label=" Reinitialization ") if to_gate else qc

    def mixing_operator(index_qubits: int, beta: float, to_gate = True) -> Union[Gate, QuantumCircuit]:
        qr_index = QuantumRegister(index_qubits, "index")
        qc = QuantumCircuit(qr_index)
        qc.rx(2*beta,qr_index)
        return qc.to_gate(label=" Mixing Operator ") if to_gate else qc    
    
    qr_index = QuantumRegister(index_qubits, "index") # index register
    qr_data = QuantumRegister(data_qubits, "data") # data register
    qr_f = QuantumRegister(1, "flag") # flag register
    cr_index = ClassicalRegister(index_qubits, "c_index") # classical register storing the measurement result of index register
    qc = QuantumCircuit(qr_index, qr_data, qr_f, cr_index)
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