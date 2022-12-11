# Is fed data such as reserves, vab etc to draw the graph.
# for now we just log data and write stuff like sqrt k, switch point etc.
import math

import matplotlib.pyplot as plot
import numpy


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


def plot_pylon(reserve0, reserve1, vab, anchorK):
    params = calculate_parameters(reserve0, reserve1, vab, anchorK)

    x = numpy.linspace(0, 0.01, 10000)

    y = pylon_function(x, params[0], vab, anchorK, params[2])

    plot.plot(x, y)

    plot.show()



def calculate_parameters(reserve0, reserve1, vab, anchorK):
    price = reserve1 / reserve0
    tpv = reserve1 * 2
    k = reserve0 * reserve1

    vfb = k / (vab * anchorK)
    sqrtKFactor = math.sqrt(anchorK ** 2 - anchorK)
    vabMultiplier = anchorK - sqrtKFactor if sqrtKFactor < anchorK else anchorK + sqrtKFactor
    reserveSwitch = vab * vabMultiplier

    return [k, vfb, reserveSwitch]


def pylon_function(x, k, vab, anchorK, reserve_switch):
    reserve1 = numpy.sqrt(k*x)
    result = numpy.zeros_like(x)
    mask = reserve1 > reserve_switch
    result[mask] = 2 * reserve1[mask] - vab
    result[~mask] = k * x[~mask] / (vab * anchorK)
    return result
