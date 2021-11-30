def perf_ans_calc(L1, L2, C1, C2, C_max):
    vals = [0] * len(L1)
    wts = [0] * len(L1)
    W = C_max - sum(C1)
    for jj, (l1, l2, c1, c2) in enumerate(zip(L1, L2, C1, C2)):
        vals[jj] = l2 - l1
        wts[jj] = c2 - c1

    def dp(W, wt, val, n):
        k = [[0 for x in range(W + 1)] for x in range(n + 1)]
        for i in range(n + 1):
            for w in range(W + 1):
                if i == 0 or w == 0:
                    k[i][w] = 0
                elif wt[i - 1] <= w:
                    k[i][w] = max(val[i - 1] + k[i - 1][w - wt[i - 1]],
                                  k[i - 1][w])
                else:
                    k[i][w] = k[i - 1][w]

        picks = [0 for x in range(n)]
        volume = W
        for i in range(n, -1, -1):
            if (k[i][volume] > k[i - 1][volume]):
                picks[i - 1] = 1
                volume -= wt[i - 1]
        return k[n][W], picks

    n = len(vals)
    ans_str = ['0'] * n
    ans_wt = sum(C1)
    for i in range(n):
        if dp(W, wts, vals, n)[1][i]:
            ans_str[i] = '1'
            ans_wt += wts[i]
    return ''.join(ans_str), ans_wt, dp(W, wts, vals, n)[0]


def test_res(res, L1, L2, C1, C2, C_max):
    ans_str, ans_wt, ans_val = perf_ans_calc(L1, L2, C1, C2, C_max)

    def test_exceed(bitstring, L1, L2, C1, C2, C_max):
        C_cur = sum(C1)
        L_cur = sum(L1)
        for ii, char in enumerate(bitstring):
            if char == '1':
                C_cur += C2[ii] - C1[ii]
                L_cur += L2[ii] - L1[ii]

        if C_max >= C_cur:
            return 1, L_cur, C_cur  # should call function test_no_exceed, but wtf
        else:
            return 0, L_cur, C_cur

    Nf = 0
    prec = 0
    counts = res
    best_percent = -1
    for bs, cts in counts.items():

        exceed, L_cur, C_cur = test_exceed(bs, L1, L2, C1, C2, C_max)
        Nf += exceed * cts
        prec += exceed * cts * L_cur
        if best_percent < exceed * L_cur / (ans_val + sum(L1)):
            best_percent = exceed * L_cur / (ans_val + sum(L1))
    if Nf == 0:
        return 0
    prec /= (Nf * (ans_val + sum(L1)))

    return prec, best_percent