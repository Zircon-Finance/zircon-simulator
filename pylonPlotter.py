# Is fed data such as reserves, vab etc to draw the graph.
# for now we just log data and write stuff like sqrt k, switch point etc.
import math

import matplotlib.pyplot as plot
import numpy

from pylonsim import zirconlib


def show_stats(reserve0, reserve1, vab, anchorK):
    price = reserve1/reserve0
    tpv = reserve1 * 2
    k = reserve0 * reserve1

    vfb = k/(vab * anchorK)
    sqrtKFactor = math.sqrt(anchorK ** 2 - anchorK)
    vabMultiplier = anchorK - sqrtKFactor if sqrtKFactor < anchorK else anchorK + sqrtKFactor
    reserveSwitch = vab * vabMultiplier

    if reserve1 > reserveSwitch:
        gamma = 1 - vab / tpv
    else:
        gamma = tpv/(4*vab*anchorK)

    print("Price is {}, vfb is {}, reserve switch is {}, while gamma is {}".format(price, vfb, reserveSwitch, gamma))


def plot_pylon(reserve0, reserve1, vab, vfb, p2x, p2y):
    params = calculate_parameters(reserve0, reserve1, vab, vfb, p2x, p2y)

    end_price = reserve1/reserve0 * 5

    x = numpy.linspace(0, end_price, 10000)

    y = pylon_function(x, params[0], vab, vfb, params[2], params[3], params[4])

    plot.plot(x, y)

    plot.show()


def calculate_parameters(reserve0, reserve1, vab, vfb, p2x, p2y):
    price = reserve1 / reserve0
    tpv = reserve1 * 2
    k = reserve0 * reserve1
    kv = vab * vfb

    p3x = 0
    if kv <= k:
        p3x = ((math.sqrt(k) - math.sqrt(k - kv))/vfb) ** 2
    else:
        p3x = vab ** 2 / k

    a, b = zirconlib.calculate_parabola_coefficients(p2x, p2y, p3x, vab)

    return [k, kv, p3x, a, b]


def pylon_function(x, k, vab, vfb, p3x, a, b):
    reserve1 = numpy.sqrt(k*x)
    result = numpy.zeros_like(x)

    kv = vab * vfb

    for index, item in enumerate(x):
        if x[index] >= p3x:
            result[index] = 2 * reserve1[index] - vab
        else:
            if kv <= k:
                result[index] = vfb * x[index]
            else:
                result[index] = (a * (x[index] ** 2) + b * x[index])

    return result
