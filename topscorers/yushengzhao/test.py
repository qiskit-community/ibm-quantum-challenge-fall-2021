def subroutine_add_const(data_qubits: int,
                         const: int,
                         to_gate=True) -> Union[Gate, QuantumCircuit]:
    qc = QuantumCircuit(data_qubits)
    ##############################
    ### Phase Rotation ###
    # Provide your code here
    const_str = bin(const)[2:].zfill(data_qubits)[::-1]
    const_str = const_str  # m.s.b at the end
    for ii in range(data_qubits):
        for jj in range(data_qubits - ii):
            if const_str[ii] == '1':
                # seems simplist
                qc.p(np.pi / (2**(jj)), ii + jj)

    if dotranspile:
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
    # use diff calculated before
    diff = 0
    adjust = 0
    diff_str_inv = bin(diff - adjust)[2:].zfill(data_qubits)[::-1]

    for ii in range(data_qubits):
        if diff_str_inv[ii] == '1':
            qc.x(qr_data[ii])

    # notice order of qubits
    if list2[0] > list1[0]:  #just to make sure
        first_val_diff = list2[0] - list1[0] + diff - adjust
    else:
        first_val_diff = list1[0] - list2[0] + diff - adjust

    first_val_diff_str = bin(first_val_diff)[2:].zfill(data_qubits)[::-1]
    for ii in range(data_qubits):
        if diff_str_inv[ii] != first_val_diff_str[ii]:
            qc.cx(qr_index[-1], qr_data[ii])
    #print('init vals')
    #print_score(qc)
    # no transpile a_d = 1
    qft = QFT(data_qubits,
              approximation_degree=0,
              do_swaps=False,
              inverse=False,
              insert_barriers=False,
              name=None).decompose()

    if dotranspile:
        qft = transpile(qft,
                        basis_gates=['sx', 'rz', 'cx'],
                        optimization_level=2,
                        seed_transpiler=42)
    #print('qft')
    #qftscore = print_score(qft)
    qc.append(qft, qr_data)

    for i, (val1, val2) in enumerate(zip(list1[1:], list2[1:])):

        ##############################
        ### Add val2 using const_adder controlled by i-th index register (set to 1) ###
        # Provide your code here
        if val2 > val1:
            adder_gate2 = const_adder(data_qubits, val2 - val1, True)
            ctrl_adder_gate2 = adder_gate2.control()
            qc.append(ctrl_adder_gate2,
                      [qr_index[index_qubits - 2 - i]] + qr_data[:])
        ##############################
        else:
            qc.x(qr_index[index_qubits - 2 - i])
            ##############################
            ### Add val1 using const_adder controlled by i-th index register (set to 0) ###
            # Provide your code here
            adder_gate1 = const_adder(data_qubits, val1 - val2, True)
            ctrl_adder_gate1 = adder_gate1.control()
            qc.append(ctrl_adder_gate1,
                      [qr_index[index_qubits - 2 - i]] + qr_data[:])

        #print(f'add score step {i}')
        #qc = transpile(qc,
        #                basis_gates=['sx', 'rz', 'cx'],
        #                optimization_level=2,seed_transpiler=42)
        #addscore = print_score(qc,False) - qftscore
        #print(addscore)
        #qftscore += addscore
        #input()
    if dotranspile:
        qc = transpile(qc,
                       basis_gates=['sx', 'rz', 'cx'],
                       optimization_level=2,
                       seed_transpiler=42)
    #print('adding')
    #print(print_score(qc,False)- qftscore)
    qfti = QFT(data_qubits,
               approximation_degree=0,
               do_swaps=False,
               inverse=True).decompose()

    if dotranspile:
        qfti = transpile(qfti,
                         basis_gates=['sx', 'rz', 'cx'],
                         optimization_level=2,
                         seed_transpiler=42)
    #print('iqfr')
    #print_score(qfti)
    qc.append(qfti, qr_data)
    qc = qc.decompose()
    if dotranspile:
        qc = transpile(qc,
                       basis_gates=['rz', 'sx', 'cx'],
                       optimization_level=2,
                       seed_transpiler=42)
    #print('total')
    #print_score(qc)
    ##############################
    # qc.x(qr_index[i]) #we invert this any ways
    #print('cost calc')
    #print_score(qc)
    return qc.to_gate(label=" Cost Calculation ") if to_gate else qc


def test_cost_calc(C1, C2):
    num_qr_b = math.ceil(math.log(sum(C2), 2)) + 1
    qr_index = QuantumRegister(len(C1), "index")  # index register
    qr_data = QuantumRegister(num_qr_b, "data")  # data register
    qr_f = QuantumRegister(1, "flag")  # flag register
    cr_index = ClassicalRegister(num_qr_b, "c_index")
    qc = QuantumCircuit(qr_index, qr_data, qr_f, cr_index)
    qc.x(qr_index)

    qc.append(cost_calculation(len(C1), num_qr_b, C1, C2),
              qr_index[:] + qr_data[:])
    qc.measure(qr_data, cr_index)
    qct = transpile(qc, backend=simulator)

    counts = simulator.run(qct).result().get_counts()
    for k, v in counts.items():
        #print(int(k[::-1],2),k,v)
        return int(k, 2)
