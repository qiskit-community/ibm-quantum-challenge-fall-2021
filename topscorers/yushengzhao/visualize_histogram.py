import plotly.graph_objects as go
import math


def costs(key, L1, L2, C1, C2, C_max, optimal_value):
    ans_cost = 0
    for i, a in enumerate(key):
        if a == "0":
            ans_cost += C1[i]
        else:
            ans_cost += C2[i]
    return ans_cost


def revenues(key, L1, L2, C1, C2, C_max, optimal_value):
    ans_cost = 0
    ans_value = 0
    for i, a in enumerate(key):
        if a == "0":
            ans_value += L1[i]
            ans_cost += C1[i]
        else:
            ans_value += L2[i]
            ans_cost += C2[i]
    if ans_cost > C_max:
        return 0
    else:
        return ans_value / optimal_value


def reinit_correct(hist, L1, L2, C1, C2, C_max, optimal_value):
    index_qubits = len(L1)
    # the maximum possible total cost
    max_c = sum([max(l0, l1) for l0, l1 in zip(C1, C2)])
    min_c = sum([min(l0, l1) for l0, l1 in zip(C1, C2)])
    #print('C_max, min_c, max_c before')
    #print(C_max, min_c, max_c)
    adjust = 1  # Let == C_max through, don't seem to need
    target_min_c = 1  #make min_c 1

    # adjust to make C_max 2**w
    w_bits = math.ceil(math.log(C_max - min_c + target_min_c, 2))
    if 2**w_bits == C_max - min_c + target_min_c:
        target_min_c -= 1
        print('just enough')
    diff = 2**(w_bits) - (C_max + adjust - min_c + target_min_c)

    #assuming C_max <= max_c otherwise problem is meaningless
    max_c = max_c - min_c + target_min_c + diff  #reduce number of qubits used
    # print(
    #     'after adjust C_max = 2**w_bits, min_c, max_c, shift for C_max, shift for minmax 1 less'
    # )
    # print(2**w_bits, target_min_c, max_c, 2**w_bits - C_max,
    #       min_c - target_min_c - diff)
    data_qubits = w_bits + 1
    ultra = True
    if max_c > 2**(data_qubits) - 1:
        ultra = False
        data_qubits = math.ceil(math.log(max_c, 2))
        if max_c > 2**(data_qubits) - 1:
            data_qubits += 1
    ### Phase Operator ###

    # sort the histogram with its values
    hist_sorted = sorted(hist.items(), key=lambda x: x[1])
    # obtain probability, function value, and bitstrings
    bitstrings = [x[0][0:index_qubits] for x in hist_sorted]
    sumed = [x[0][index_qubits:len(x[0]) - 1] for x in hist_sorted]

    for i, bis in enumerate(bitstrings):
        cost = 0
        cursum = int(sumed[i][::-1], 2)
        if cost != cursum:
            print(i, cost, cursum)


def add_correct(hist, L1, L2, C1, C2, C_max, optimal_value):
    index_qubits = len(L1)
    # the maximum possible total cost
    max_c = sum([max(l0, l1) for l0, l1 in zip(C1, C2)])
    min_c = sum([min(l0, l1) for l0, l1 in zip(C1, C2)])
    #print('C_max, min_c, max_c before')
    #print(C_max, min_c, max_c)
    adjust = 1  # Let == C_max through, don't seem to need
    target_min_c = 1  #make min_c 1

    # adjust to make C_max 2**w
    w_bits = math.ceil(math.log(C_max - min_c + target_min_c, 2))
    if 2**w_bits == C_max - min_c + target_min_c:
        target_min_c -= 1
        print('just enough')
    diff = 2**(w_bits) - (C_max + adjust - min_c + target_min_c)

    #assuming C_max <= max_c otherwise problem is meaningless
    max_c = max_c - min_c + target_min_c + diff  #reduce number of qubits used
    # print(
    #     'after adjust C_max = 2**w_bits, min_c, max_c, shift for C_max, shift for minmax 1 less'
    # )
    # print(2**w_bits, target_min_c, max_c, 2**w_bits - C_max,
    #       min_c - target_min_c - diff)
    data_qubits = w_bits + 1
    ultra = True
    if max_c > 2**(data_qubits) - 1:
        ultra = False
        data_qubits = math.ceil(math.log(max_c, 2))
        if max_c > 2**(data_qubits) - 1:
            data_qubits += 1
    ### Phase Operator ###

    # sort the histogram with its values
    hist_sorted = sorted(hist.items(), key=lambda x: x[1])
    # obtain probability, function value, and bitstrings
    bitstrings = [x[0][0:index_qubits] for x in hist_sorted]
    sumed = [x[0][index_qubits:len(x[0]) - 1] for x in hist_sorted]

    for i, bis in enumerate(bitstrings):
        cost = costs(bis, L1, L2, C1, C2, C_max,
                     optimal_value) - min_c + target_min_c + diff
        cursum = int(sumed[i][::-1], 2)
        if cost != cursum:
            print(i, cost, cursum)


def both_correct(hist, L1, L2, C1, C2, C_max, optimal_value):
    index_qubits = len(L1)
    # the maximum possible total cost
    max_c = sum([max(l0, l1) for l0, l1 in zip(C1, C2)])
    min_c = sum([min(l0, l1) for l0, l1 in zip(C1, C2)])
    #print('C_max, min_c, max_c before')
    #print(C_max, min_c, max_c)
    adjust = 1  # Let == C_max through, don't seem to need
    target_min_c = 1  #make min_c 1

    # adjust to make C_max 2**w
    w_bits = math.ceil(math.log(C_max - min_c + target_min_c, 2))
    if 2**w_bits == C_max - min_c + target_min_c:
        target_min_c -= 1
        print('just enough')
    diff = 2**(w_bits) - (C_max + adjust - min_c + target_min_c)

    #assuming C_max <= max_c otherwise problem is meaningless
    max_c = max_c - min_c + target_min_c + diff  #reduce number of qubits used
    # print(
    #     'after adjust C_max = 2**w_bits, min_c, max_c, shift for C_max, shift for minmax 1 less'
    # )
    # print(2**w_bits, target_min_c, max_c, 2**w_bits - C_max,
    #       min_c - target_min_c - diff)
    data_qubits = w_bits + 1
    ultra = True
    if max_c > 2**(data_qubits) - 1:
        ultra = False
        data_qubits = math.ceil(math.log(max_c, 2))
        if max_c > 2**(data_qubits) - 1:
            data_qubits += 1
    ### Phase Operator ###

    # sort the histogram with its values
    hist_sorted = sorted(hist.items(), key=lambda x: x[1])
    # obtain probability, function value, and bitstrings
    bitstrings = [x[0][0:index_qubits] for x in hist_sorted]
    sumed = [x[0][index_qubits:len(x[0]) - 1] for x in hist_sorted]

    probabilities = [x[1] for x in hist_sorted]
    values = [
        revenues(x, L1, L2, C1, C2, C_max, optimal_value) for x in bitstrings
    ]
    flaged = [x[0][-1] for x in hist_sorted]
    for i, bis in enumerate(bitstrings):
        cost = costs(bis, L1, L2, C1, C2, C_max,
                     optimal_value) - min_c + target_min_c + diff
        cursum = int(sumed[i][::-1], 2)

        if flaged[i] == '1':
            if cost < 2**w_bits:
                print(i, 'flagged', sumed[i], 2**w_bits, cost, cursum)
        else:
            if cost > 2**w_bits:
                print(i, 'noflagg', sumed[i], 2**w_bits, cost, cursum,
                      values[i])


def flag_correct(hist, L1, L2, C1, C2, C_max, optimal_value):
    # sort the histogram with its values
    hist_sorted = sorted(hist.items(), key=lambda x: x[1])
    # obtain probability, function value, and bitstrings
    probabilities = [x[1] for x in hist_sorted]
    values = [
        revenues(x[0][1:], L1, L2, C1, C2, C_max, optimal_value)
        for x in hist_sorted
    ]
    bitstrings = [x[0][1:] for x in hist_sorted]
    flaged = [x[0][0] for x in hist_sorted]
    for i, bis in enumerate(bitstrings):
        if flaged[i] == '1' and values[i] != 0:
            print(bis, probabilities[i])
        else:
            if values[i] > 0:
                print(bis, probabilities[i], values[i])
    # plot bar chart


def plot_hist(hist, L1, L2, C1, C2, C_max, optimal_value):

    # sort the histogram with its values
    hist_sorted = sorted(hist.items(), key=lambda x: x[1])
    # obtain probability, function value, and bitstrings
    probabilities = [x[1] for x in hist_sorted]
    values = [
        revenues(x[0], L1, L2, C1, C2, C_max, optimal_value)
        for x in hist_sorted
    ]
    bitstrings = [x[0] for x in hist_sorted]
    # plot bar chart
    sample_plot = go.Bar(x=bitstrings,
                         y=probabilities,
                         marker=dict(cmin=min(values),
                                     cmax=1,
                                     color=values,
                                     colorscale='viridis',
                                     colorbar=dict(title='revenue')))
    fig = go.Figure(data=sample_plot, layout=dict(xaxis=dict(type='category')))
    fig.show()