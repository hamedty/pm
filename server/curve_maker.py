import numpy as np
# import matplotlib.pyplot as plt


def calc_curve(Vmax, Amax, Jmax, V0=0, A0=0, reverse=False):
    x = 0
    v = V0
    a = A0
    j = 0
    mode = 'a+'  # 'a-', 'a_', 'g', 'd....'
    dt = 1e-6
    endtime = 6
    T = np.arange(0, endtime, dt)
    X = np.zeros(T.shape)
    V = X.copy()
    A = X.copy()
    J = X.copy()
    last_index = 0
    for i in range(T.size):
        X[i] = x
        V[i] = v
        A[i] = a
        J[i] = j

        x += v * dt
        v += a * dt
        a += j * dt

        if mode == 'a+':
            j = Jmax
            if a >= Amax or v >= ((Vmax - V0) / 2 + V0):
                mode = 'a-'
                j = 0
        elif mode == 'a-':
            if (Vmax - v) <= (Amax**2 * .5 / Jmax):
                mode = 'a_'
                j = -Jmax
        elif mode == 'a_':
            if a <= 0 or v >= Vmax:
                mode = 'g'
                a = 0
                j = 0
                v = Vmax
                last_index = i
                break

    T = T[:last_index].copy()
    X = X[:last_index].copy()
    V = V[:last_index].copy()
    A = A[:last_index].copy()
    J = J[:last_index].copy()

    # plt.plot(T[::100], X[::100], T[::100], V[::100], T[::100], A[::100])
    # plt.show()
    X = X.round().astype(int)
    commands = np.where(X[:-1] != X[1:])[0]
    commands = np.diff(commands)

    # Smoothing
    max_delay = commands.max()
    min_delay = commands.min()
    periods = []
    for i in range(max_delay, min_delay - 1, -1):
        ocuurances = np.where(commands == i)[0]
        period = [i, ocuurances[0], ocuurances[-1]]
        periods.append(period)
    for i in range(len(periods) - 1):
        a = periods[i]
        b = periods[i + 1]
        th = (a[2] + b[1]) / 2.0
        a[2] = int(th)
        b[1] = int(th) + 1

    for i in range(len(periods)):
        periods[i] = [periods[i][0], periods[i][2] - periods[i][1] + 1]

    print(periods)

    if reverse:
        periods = periods[::-1]

    distance = sum([i[1] for i in periods])
    return periods, distance


def calc_curve2(Vmax, Amax, J, V0=0, A0=0):
    t_reaching_Amax = np.roots([J, A0 - Amax])[0]

    t = t_reaching_Amax
    v__t_reaching_Amax = V0 + A0 * t + .5 * J * t**2
    print('length', t_reaching_Amax, 'vmax', v__t_reaching_Amax)
    XT_t = [0]
    while XT_t[-1] < t_reaching_Amax:
        r = np.roots([J / 6.0, A0 / 2.0, V0, -len(XT_t)])
        XT_t.append(np.real(r[-1]))
    # print(XT_t)

    #plt.plot(XT_t, range(len(XT_t)))
    delays = np.round(np.diff(XT_t) * 1e6)
    delay_change = np.where(delays[:-1] != delays[1:])[0] + 1
    curve = []
    for i in delay_change:
        print(int(delays[i - 1]), i)
        curve.append(int(delays[i - 1]))
        curve.append(i)
    print(int(delays[i - 1]) - 1, 1)
    curve.append(int(delays[-1]))
    curve.append(1)
    return(curve)


def create_hfile(acceleration, deceleration, distance=0):
    assert acceleration['Vmax'] == deceleration['Vmax']
    acceleration['reverse'] = False
    deceleration['reverse'] = True

    a, a_distance = calc_curve(**acceleration)
    d, d_distance = calc_curve(**deceleration)

    a = sum(a, [])
    d = sum(d, [])

    curve = {
        'index': 0,
        'curve_a': [int(i) for i in a],
        'curve_d': [int(i) for i in d],
    }

    # curve = {
    #     'index': 0,
    #     'curve_a': [5, 100],
    #     'curve_d': [5, 100],
    # }
    return curve

    # if distance:
    #     cruise_distance = distance - a_distance - d_distance
    #     assert cruise_distance > 0, 'acceleration and deceleration is longer than main distance'
    #     f = a + d
    #     time_elapsed = cruise_distance * \
    #         a[-2] + sum([f[2 * i] * f[2 * i + 1]
    #                      for i in range(int(len(f) / 2))])
    #     print(time_elapsed / 1000, ' ms')
    # with open('../src/curve_%s.h' % filename.lower(), 'w') as file:
    #     file.write(text)
