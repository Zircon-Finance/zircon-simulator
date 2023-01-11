# Is fed data such as reserves, vab etc to draw the graph.
# for now we just log data and write stuff like sqrt k, switch point etc.
import math

import matplotlib.pyplot as plot
import numpy

from pylonsim import zirconlib


def show_stats(reserve0, reserve1, vab, anchor_k):
    price = reserve1 / reserve0
    tpv = reserve1 * 2
    k = reserve0 * reserve1

    vfb = k / (vab * anchor_k)
    sqrt_k_factor = math.sqrt(anchor_k ** 2 - anchor_k)
    vab_multiplier = anchor_k - sqrt_k_factor if sqrt_k_factor < anchor_k else anchor_k + sqrt_k_factor
    reserve_switch = vab * vab_multiplier

    if reserve1 > reserve_switch:
        gamma = 1 - vab / tpv
    else:
        gamma = tpv / (4 * vab * anchor_k)

    print("Price is {}, vfb is {}, reserve switch is {}, while gamma is {}".format(price, vfb, reserve_switch, gamma))


def plot_pylon(reserve0, reserve1, vab, vfb, p2x, p2y, sync_r0, sync_r1):
    print("Starting to plot...")
    (k, kv, p3x, a, b) = calculate_parameters(reserve0, reserve1, vab, vfb, p2x, p2y)

    price = reserve1 / reserve0
    ftv = zirconlib.get_ftv_for_x(price, p2x, p2y, k, vab)
    gamma = ftv / (2 * reserve1)

    x = numpy.linspace(0, max(int(price), int(p3x), int(p2x)), 1000)
    y1 = [zirconlib.get_ftv_for_x(item, p2x, p2y, k, vab, True) for index, item in enumerate(x) if item < p3x]
    y2 = [zirconlib.get_ftv_for_x(item, p2x, p2y, k, vab, True) for index, item in enumerate(x[len(y1):])]
    x2 = x[len(y1):]
    x1 = x[0:len(y1)]

    # Omega Calculations
    omega = [y / vab for y in [zirconlib.get_omega_for_x(item, p2x, p2y, k, vab, True) for index, item in enumerate(x)]
             if 0 < y <= vab]
    xo = x[0:len(omega)]

    # let's change a bit the dimensions of the PNG containing the graphs
    plot.figure(figsize=[8.2, 10])
    plot.suptitle("Zircon Simulator")

    # here we start to plot the first graph
    plot.subplot(211)
    plot.title("FTV/Price")

    p1 = plot.scatter([0], [0])
    p2 = plot.scatter([p2x], [p2y])
    p3 = plot.scatter([p3x], vab)

    res = plot.scatter(price, ftv)

    plot.plot(x1, y1)
    plot.plot(x2, y2)

    plot.legend((p2, p3, res, p1, p1, p1),
                (
                 'P2 ({:.2f}, {:.2f})'.format(p2x, p2y),
                 'P3 ({:.2f}, {:.2f})'.format(p3x, vab),
                 'P: ({:.2f}, {:.2f})'
                 .format(price, ftv),
                 'Γ: {:.2f}, k: {:.2f}, kv: {:.2f}'
                 .format(gamma, k, kv),
                 'R0: {:.2f}, R1: {:.2f}, PR0: {:.2f}, PR1:{:.2f}'
                 .format(reserve0, reserve1, sync_r0, sync_r1),
                 'a: {:.2f}, b: {:.2f}'
                 .format(a, b)),
                scatterpoints=1,
                loc='lower right',
                ncol=1,
                fontsize=8)

    # Plotting Omega Graph
    plot.subplot(212)
    plot.title("Omega/Price")
    plot.plot(xo, omega, label="Omega")

    plot.show()


def calculate_parameters(reserve0, reserve1, vab, vfb, p2x, p2y):
    price = reserve1 / reserve0
    tpv = reserve1 * 2
    k = reserve0 * reserve1
    kv = vab * vfb

    p3x = 0
    # if kv <= k:
    #     p3x = ((math.sqrt(k) - math.sqrt(k - kv))/vfb) ** 2
    # else:
    p3x = vab ** 2 / k

    a, b = zirconlib.calculate_parabola_coefficients(p2x, p2y, p3x, vab)

    return k, kv, p3x, a, b


def pylon_function(x, k, vab, vfb, p3x, a, b):
    reserve1 = numpy.sqrt(k * x)
    result = numpy.zeros_like(x)

    # TODO: Switch to using the gamma formula directly

    kv = vab * vfb

    for index, item in enumerate(x):
        if x[index] >= p3x:
            result[index] = 2 * reserve1[index] - vab
        else:
            # if kv <= k:
            #     result[index] = vfb * x[index]
            # else:
            result[index] = (a * (x[index] ** 2) + b * x[index])

    return result
