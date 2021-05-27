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
    Vmax=100 * 1000,
    Amax=5000 * 1000,
    J=100 * 1000 * 1000 * 1000,
    A0=100 * 1000,
    V0=25 * 1000,
    min_delay=5,
)


CURVE_ROBOT = calc_curve(
    Vmax=80 * 1000,
    Amax=5000 * 1000,
    J=100 * 1000 * 1000 * 1000,
    A0=40 * 1000,
    V0=12 * 1000,
    min_delay=17,
)

CURVE_RAIL = calc_curve(
    Vmax=80 * 1000,
    Amax=6000 * 1000,
    J=100 * 1000 * 1000 * 1000,
    A0=600 * 1000,
    V0=10 * 1000,
    min_delay=25,
)


# CURVE_ROBOT = {
#     'index': 0,
#     'curve_a': [83, 1, 81, 2, 79, 3, 76, 4, 74, 5, 72, 6, 70, 7, 69, 8, 67, 9, 66, 10, 64, 11, 63, 12, 62, 13, 61, 14, 60, 15, 59, 16, 58, 17, 57, 18, 56, 19, 55, 20, 54, 21, 53, 23, 52, 24, 51, 26, 50, 27, 49, 29, 48, 31, 47, 33, 46, 35, 45, 37, 44, 39, 43, 42, 42, 44, 41, 47, 40, 50, 39, 54, 38, 57, 37, 61, 36, 66, 35, 70, 34, 75, 33, 81, 32, 87, 31, 94, 30, 101, 29, 109, 28, 119, 27, 129, 26, 140, 25, 153, 24, 167, 23, 184, 22, 203, 21, 224, 20, 249, 19, 278, 18, 313],
#     'curve_d': [18, 313, 19, 278, 20, 249, 21, 224, 22, 203, 23, 184, 24, 167, 25, 153, 26, 140, 27, 129, 28, 119, 29, 109, 30, 101, 31, 94, 32, 87, 33, 81, 34, 75, 35, 70, 36, 66, 37, 61, 38, 57, 39, 54, 40, 50, 41, 47, 42, 44, 43, 42, 44, 39, 45, 37, 46, 35, 47, 33, 48, 31, 49, 29, 50, 27, 51, 26, 52, 24, 53, 23, 54, 21, 55, 20, 56, 19, 57, 18, 58, 17, 59, 16, 60, 15, 61, 14, 62, 13, 63, 12, 64, 11, 66, 10, 67, 9, 69, 8, 70, 7, 72, 6, 74, 5, 76, 4, 79, 3, 81, 2, 83, 1],
# }
#
# CURVE_ROBOT['curve_a'] += [17, 500, 16, 600, 15, 600]
