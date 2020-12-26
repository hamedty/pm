import numpy as np
import matplotlib.pyplot as plt

# unit = edge

# RAIL
# define RAIL_PERIOD 250 usec
# MICRO_STEP_RAIL = 32
# Current Vmax
# vmax = 1 edge / 0.00025 = 4000 edge / sec = 2000 ustep / sec = 62.5 step / sec = 112.5 deg / sec = 3.4375 station / sec

# Closer
# define RAIL_PERIOD 1000 usec
# MICRO_STEP_LEADSHINE = 2
# Current Vmax
# vmax = 1 edge / 0.001 = 1000 edge / sec = 500 ustep / sec = 250 step / sec = 450 deg / sec = 1.25 rev / sec


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
        x += v * dt
        v += a * dt
        a += j * dt
        X[i] = x
        V[i] = v
        A[i] = a
        J[i] = j
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

    if reverse:
        X = X[::-1]
        V = V[::-1]
        A = A[::-1]
        J = J[::-1]

    plt.plot(T[::100], X[::100], T[::100], V[::100], T[::100], A[::100])
    plt.show()
    X = X.astype(int)
    commands = np.where(X[:-1] != X[1:])[0]
    return commands


def create_hfile(filename, acceleration, deceleration, distance=0):
    assert acceleration['Vmax'] == deceleration['Vmax']
    acceleration['reverse'] = False
    deceleration['reverse'] = True

    a = calc_curve(**acceleration)
    d = calc_curve(**deceleration)

    text = '''
    # define %(name)s_A_LEN %(a_len)d
    # define %(name)s_D_LEN %(d_len)d

    unsigned long %(name)s_A[%(name)s_A_LEN] = {%(a_str)s};
    unsigned long %(name)s_D[%(name)s_D_LEN] = {%(d_str)s};

    ''' % {
        'name': 'CURVE_' + filename.upper(),
        'a_len': len(a),
        'd_len': len(d),
        'a_str': ', '.join([str(i) for i in a]),
        'd_str': ', '.join([str(i) for i in d]),
    }

    if distance:
        d0 = len(a) + len(d)
        d1 = distance - d0
        assert d1 > 0, 'acceleration and deceleration is longer than main distance'
        time_elapsed = a[-1] + d[-1] + d1 * float(a[-1] - a[-2])
        print(time_elapsed / 1000, ' ms')
    with open('curve_%s.h' % filename.lower(), 'w') as file:
        file.write(text)


create_hfile('rail_long', {
    'Vmax': 11 * 1000.,
    'Amax': 30 * 1000.,
    'Jmax': 90 * 1000.,
    'V0': 2000,
    'A0': 5000,
},
    {
    'Vmax': 11 * 1000.,
        'Amax': 260 * 1000.,
        'Jmax': 800 * 1000.,
        'V0': 2000,
        'A0': 5000,
},
    distance=11636,
)

create_hfile('rail_short', {
    'Vmax': 8 * 1000.,
    'Amax': 50 * 1000.,
    'Jmax': 500 * 1000.,
    'V0': 2000,
    'A0': 5000,
},
    {
    'Vmax': 8 * 1000.,
    'Amax': 400 * 1000.,
    'Jmax': 500 * 1000.,
    'V0': 2000,
    'A0': 5000,
},
    distance=2327,
)
