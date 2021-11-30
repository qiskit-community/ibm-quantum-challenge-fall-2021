def solver_function(L1: list, L2: list, C1: list, C2: list,
                    C_max: int) -> QuantumCircuit:

    # the number of qubits representing answers
    index_qubits = len(L1)

    # the maximum possible total cost
    max_c = sum([max(l0, l1) for l0, l1 in zip(C1, C2)])
    min_c = sum([min(l0, l1) for l0, l1 in zip(C1, C2)])
    max_c -= min_c  #reduce number of qubits used

    # the number of qubits representing data values can be defined using the maximum possible total cost as follows:
    data_qubits = math.ceil(math.log(max_c, 2)) + 1 if not max_c & (
        max_c - 1) == 0 else math.ceil(math.log(max_c, 2)) + 2

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
            qc.p(-gamma * (L2[ii] - L1[ii]), qr_index[ii])

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
        const_str = bin(const)[2:].zfill(data_qubits)
        const_str = const_str[::-1]
        rotation_angles = [0] * data_qubits
        for ii in range(data_qubits):
            for jj in range(ii, data_qubits):
                if const_str[ii] == '1':
                    # seems simplist
                    rotation_angles[jj] += np.pi / (2**(jj - ii))

        for jj in range(data_qubits):
            qc.p(rotation_angles[jj], jj)

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

        # just to make sure
        num_bit = data_qubits - 1

        diff = 2**num_bit - (C_max - min_c) - 2  # 2 works, 1 not sure

        # should I subtract from cost(z) any ways?
        # this one won't subtrace in some cases
        if diff < 0:
            diff = 0

        diff_str_inv = bin(diff)[2:].zfill(data_qubits)[::-1]

        for ii in range(data_qubits):
            if diff_str_inv[ii] == '1':
                qc.x(qr_data[ii])

        qc.h(qr_index[0])

        if list2[0] > list1[0]:  #just to make sure
            first_val_diff = list2[0] - list1[0] + diff
        else:
            first_val_diff = list1[0] - list2[0] + diff

        first_val_diff_str = bin(first_val_diff)[2:].zfill(data_qubits)[::-1]

        for ii in range(data_qubits):
            if diff_str_inv[ii] != first_val_diff_str[ii]:
                qc.cx(qr_index[0], qr_data[ii])

        # no transpile a_d = 1
        qft = QFT(data_qubits,
                  approximation_degree=1,
                  do_swaps=False,
                  inverse=False,
                  insert_barriers=False,
                  name=None).decompose()

        qft = transpile(qft,
                        basis_gates=['sx', 'rz', 'cx'],
                        optimization_level=2,
                        seed_transpiler=42)

        qc.append(qft, qr_data)

        for i, (val1, val2) in enumerate(zip(list1[1:], list2[1:])):

            ##############################
            ### Add val2 using const_adder controlled by i-th index register (set to 1) ###
            # Provide your code here
            if val2 > val1:
                adder_gate2 = const_adder(data_qubits, val2 - val1, True)
                ctrl_adder_gate2 = adder_gate2.control()
                qc.append(ctrl_adder_gate2, [qr_index[i + 1]] + qr_data[:])
            ##############################
            else:
                qc.x(qr_index[i + 1])
                ##############################
                ### Add val1 using const_adder controlled by i-th index register (set to 0) ###
                # Provide your code here
                adder_gate1 = const_adder(data_qubits, val1 - val2, True)
                ctrl_adder_gate1 = adder_gate1.control()
                qc.append(ctrl_adder_gate1, [qr_index[i + 1]] + qr_data[:])

        qc = transpile(qc,
                       basis_gates=['sx', 'rz', 'cx'],
                       optimization_level=2,
                       seed_transpiler=42)

        qfti = QFT(data_qubits,
                   approximation_degree=1,
                   do_swaps=False,
                   inverse=True,
                   insert_barriers=False,
                   name=None).decompose()

        qfti = transpile(qfti,
                         basis_gates=['sx', 'rz', 'cx'],
                         optimization_level=2,
                         seed_transpiler=42)

        qc.append(qfti, qr_data)
        qc = qc.decompose()
        ##############################
        # qc.x(qr_index[i]) #we invert this any ways

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

        num_bit = data_qubits - 1

        # I think I can simplify to just 1 cx
        qc.cx(qr_data[num_bit], qr_f)
        qc = transpile(qc,
                       optimization_level=2,
                       basis_gates=['rz', 'sx', 'cx'],
                       seed_transpiler=42)

        #print('constraint')
        #print(transpile(qc,backend=sim,optimization_level=0,basis_gates=['rz','sx','cx']).size())
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

        num_bit = data_qubits - 1
        qc.p(-alpha * gamma * (2**num_bit),
             qr_f)  # -2 the same ammount did not help
        qc = transpile(qc,
                       optimization_level=2,
                       basis_gates=['rz', 'sx', 'cx'],
                       seed_transpiler=42)
        ##############################
        #print('dephasing')
        #print(transpile(qc,backend=sim,optimization_level=0,basis_gates=['rz','sx','cx']).size())
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

        qc = transpile(qc,
                       optimization_level=2,
                       basis_gates=['rz', 'sx', 'cx'],
                       seed_transpiler=42)
        #print('reinit')
        #print(transpile(qc,backend=sim,optimization_level=0,basis_gates=['rz','sx','cx']).size())

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

        for ii in range(index_qubits):
            qc.rx(2 * beta, qr_index[ii])

        qc = transpile(qc,
                       optimization_level=2,
                       basis_gates=['rz', 'sx', 'cx'],
                       seed_transpiler=42)
        ##############################
        #print('mixing')
        #print(transpile(qc,backend=sim,optimization_level=0,basis_gates=['rz','sx','cx']).size())
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