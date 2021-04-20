import numpy as np
import matplotlib.pyplot as plt

# unit = edge

# M4 (big motor)
# 800 Pulse per rev
# 1600 edge per rev
# 200 edge per mm
# 200,000 edge per meter

# Total course: 43,000 edge
# Vmax: 66,000 edge/s
# D min for edge: ~15us


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

    plt.plot(T[::100], X[::100], T[::100], V[::100], T[::100], A[::100])
    plt.show()
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


def create_hfile(filename, acceleration, deceleration, distance=0):
    assert acceleration['Vmax'] == deceleration['Vmax']
    acceleration['reverse'] = False
    deceleration['reverse'] = True

    a, a_distance = calc_curve(**acceleration)
    d, d_distance = calc_curve(**deceleration)

    a = sum(a, [])
    d = sum(d, [])

    text = '''
    # define %(name)s_A_LEN %(a_len)d
    # define %(name)s_A_DISTANCE %(a_distance)d

    # define %(name)s_D_LEN %(d_len)d
    # define %(name)s_D_DISTANCE %(d_distance)d

    unsigned long %(name)s_A[%(name)s_A_LEN] = {%(a_str)s};
    unsigned long %(name)s_D[%(name)s_D_LEN] = {%(d_str)s};

    ''' % {
        'name': 'CURVE_' + filename.upper(),
        'a_distance': a_distance,
        'd_distance': d_distance,
        'a_len': len(a),
        'd_len': len(d),
        'a_str': ', '.join([str(i) for i in a]),
        'd_str': ', '.join([str(i) for i in d]),
    }

    if distance:
        cruise_distance = distance - a_distance - d_distance
        assert cruise_distance > 0, 'acceleration and deceleration is longer than main distance'
        f = a + d
        time_elapsed = cruise_distance * \
            a[-2] + sum([f[2 * i] * f[2 * i + 1]
                         for i in range(int(len(f) / 2))])
        print(time_elapsed / 1000, ' ms')
    with open('../src/curve_%s.h' % filename.lower(), 'w') as file:
        file.write(text)


vmax = 40  # 1000 edge/s
create_hfile('rail_long', {
    'Vmax': vmax * 1000.,
    'Amax': 70 * 1000.,
    'Jmax': 400 * 1000.,
    'V0': 10 * 1000,
    'A0': 40 * 1000,
},
    {
    'Vmax': vmax * 1000.,
        'Amax': 400 * 1000.,
        'Jmax': 2000 * 1000.,
        'V0': 10 * 1000,
        'A0': 100 * 1000,
},


    distance=24000 * 2,
)
#
# create_hfile('rail_short', {
#     'Vmax': 8 * 1000.,
#     'Amax': 50 * 1000.,
#     'Jmax': 500 * 1000.,
#     'V0': 2000,
#     'A0': 5000,
# },
#     {
#     'Vmax': 8 * 1000.,
#     'Amax': 400 * 1000.,
#     'Jmax': 500 * 1000.,
#     'V0': 2000,
#     'A0': 5000,
# },
#     distance=2327,
# )
