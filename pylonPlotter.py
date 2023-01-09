# Is fed data such as reserves, vab etc to draw the graph.
# for now we just log data and write stuff like sqrt k, switch point etc.
import math

import matplotlib.pyplot as plot
import numpy

from pylonsim import zirconlib


def show_stats(reserve0, reserve1, vab, anchor_k):
    price = reserve1/reserve0
    tpv = reserve1 * 2
    k = reserve0 * reserve1

    vfb = k/(vab * anchor_k)
    sqrt_k_factor = math.sqrt(anchor_k ** 2 - anchor_k)
    vab_multiplier = anchor_k - sqrt_k_factor if sqrt_k_factor < anchor_k else anchor_k + sqrt_k_factor
    reserve_switch = vab * vab_multiplier

    if reserve1 > reserve_switch:
        gamma = 1 - vab / tpv
    else:
        gamma = tpv/(4*vab*anchor_k)

    print("Price is {}, vfb is {}, reserve switch is {}, while gamma is {}".format(price, vfb, reserve_switch, gamma))


def plot_pylon(reserve0, reserve1, vab, vfb, p2x, p2y):
    (k, kv, p3x, a, b) = calculate_parameters(reserve0, reserve1, vab, vfb, p2x, p2y)

    end_price = reserve1/reserve0 * 5

    plot.scatter([0], [0])
    p2 = plot.scatter([p2x], [p2y])
    p3 = plot.scatter([p3x], vab)

    price = reserve1 / reserve0
    ftv = zirconlib.get_ftv_for_x(price, p2x, p2y, k, vab)
    gamma = ftv / (2 * reserve1)
    res = plot.scatter(price, ftv)

    x = numpy.linspace(0, end_price, 10000)
    y = [zirconlib.get_ftv_for_x(item, p2x, p2y, k, vab, True) for index, item in enumerate(x)]
    plot.plot(x, y)

    plot.legend((p2, p3, res),
                ('P2 ({:.2f}, {:.2f})'.format(p2x, p2y),
                 'P3 ({:.2f}, {:.2f})'.format(p3x, vab),
                 'P: {:.2f}, FTV: {:.2f}, gamma: {:.2f}, gamma2: {:.2f}'
                 .format(price, ftv, gamma, 1 - vab/(2*reserve1))),
                scatterpoints=1,
                loc='lower right',
                ncol=1,
                fontsize=8)
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
    reserve1 = numpy.sqrt(k*x)
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
