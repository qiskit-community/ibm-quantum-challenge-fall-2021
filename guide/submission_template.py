"""
Challenge 4c solver function for the IBM Quantum Fall Challenge 2021
Author: Firstname Lastname <xxxxx@email.com> # TODO 1: change to your name and email
Score: 312345 # TODO 1: change to your score

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
1.
2.
3.

"""
# TODO 3: import all required libraries and modules
from qiskit import QuantumCircuit, QuantumRegister


def solver_function(L1: list, L2: list, C1: list, C2: list, C_max: int) -> QuantumCircuit:
    # TODO 4: add your name and score here
    # print name and score
    author = 'Firstname Lastname'
    score = 312345
    print(f'{author}: {score}')

    # the number of qubits representing answers
    index_qubits = len(L1)

    # the maximum possible total cost
    max_c = sum([max(l0, l1) for l0, l1 in zip(C1, C2)])

    # the number of qubits representing data values can be defined using the maximum possible total cost as follows:
    data_qubits = math.ceil(math.log(max_c, 2)) + 1 if not max_c & (max_c - 1) == 0 else math.ceil(
        math.log(max_c, 2)) + 2

    ### Phase Operator ###
    # return part
    def phase_return():

    ##############################
    ### TODO ###
    ### Paste your code from above cells here ###
    # TODO 5: explain the implementation in comments

    ##############################

    # penalty part
    def subroutine_add_const():

    ##############################
    ### TODO ###
    ### Paste your code from above cells here ###

    ##############################

    # penalty part
    def const_adder():

    ##############################
    ### TODO ###
    ### Paste your code from above cells here ###

    ##############################

    # penalty part
    def cost_calculation():

    ##############################
    ### TODO ###
    ### Paste your code from above cells here ###

    ##############################

    # penalty part
    def constraint_testing():

    ##############################
    ### TODO ###
    ### Paste your code from above cells here ###

    ##############################

    # penalty part
    def penalty_dephasing():

    ##############################
    ### TODO ###
    ### Paste your code from above cells here ###

    ##############################

    # penalty part
    def reinitialization():

    ##############################
    ### TODO ###
    ### Paste your code from above cells here ###

    ##############################

    ### Mixing Operator ###
    def mixing_operator():

    ##############################
    ### TODO ###
    ### Paste your code from above cells here ###

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