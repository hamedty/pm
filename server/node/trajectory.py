import numpy as np


def calc_curve(Vmax, Amax, J, V0, A0, min_delay):
    t_reaching_Amax = np.roots([J, A0 - Amax])[-1]

    t = t_reaching_Amax
    v__t_reaching_Amax = .5 * J * t**2 + A0 * t + V0

    dt_gliding_a = (Vmax - v__t_reaching_Amax) / float(Amax)
    assert dt_gliding_a > 0

    # print(t_reaching_Amax, v__t_reaching_Amax, dt_gliding_a)

    XT_t__1 = [0]
    while XT_t__1[-1] < t_reaching_Amax:
        r = np.roots([J / 6.0, A0 / 2, V0, -len(XT_t__1)])
        XT_t__1.append(np.real(r[-1]))
    # print(XT_t)

    XT_t__2 = [0]
    A = Amax
    V = v__t_reaching_Amax
    while XT_t__2[-1] < dt_gliding_a:
        r = np.roots([A / 2., V, -len(XT_t__2)])
        XT_t__2.append(np.real(r[-1]))
    XT_t__2 = XT_t__2[1:] + XT_t__1[-1]
    '''
    XT_t__3 = [0]
    A = Amax
    V = v__t_reaching_Amax + Amax * dt_gliding_a
    while XT_t__3[-1] < t_reaching_Amax :
        r = np.roots([-J/6.0, A/2., V, -len(XT_t__3)])
        XT_t__3.append(np.real(r[-1]))



    XT_t__3 = XT_t__3[1:] + XT_t__2[-1]
    '''
    XT_t = np.concatenate([XT_t__1, XT_t__2])

    # plt.plot(XT_t, range(len(XT_t)))
    # plt.show()

    delays = np.round(np.diff(XT_t) * 1e6)
    delay_change = np.where(delays[:-1] != delays[1:])[0] + 1
    curve_a = []
    for i in delay_change:
        # print(int(delays[i-1]), i)
        if(min_delay < delays[i - 1] < 200):
            curve_a.append(int(delays[i - 1]))
            curve_a.append(int(i))

    curve_d = [[curve_a[2 * i + 1], curve_a[2 * i]]
               for i in range(int(len(curve_a) / 2))]
    curve_d = sum(curve_d, [])

    curve_d = curve_d[::-1]

    curve = {
        'index': 0,
        'curve_a': curve_a,
        'curve_d': curve_d,
    }

    return curve


CURVE_STATION = calc_curve(
    Vmax=80 * 1000,
    Amax=5000 * 1000,
    J=100 * 1000 * 1000 * 1000,
    A0=40 * 1000,
    V0=12 * 1000,
    min_delay=19,
)


CURVE_ROBOT = calc_curve(
    Vmax=80 * 1000,
    Amax=5000 * 1000,
    J=100 * 1000 * 1000 * 1000,
    A0=40 * 1000,
    V0=12 * 1000,
    min_delay=19,
)

CURVE_RAIL = calc_curve(
    Vmax=80 * 1000,
    Amax=6000 * 1000,
    J=100 * 1000 * 1000 * 1000,
    A0=600 * 1000,
    V0=10 * 1000,
    min_delay=25,
)
