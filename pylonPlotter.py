# Is fed data such as reserves, vab etc to draw the graph.
# for now we just log data and write stuff like sqrt k, switch point etc.
import math

import matplotlib.pyplot as plot
import numpy


def show_stats(reserve0, reserve1, vab, anchor_k):
    price = reserve1 / reserve0
    tpv = reserve1 * 2

    (k, vfb, reserve_switch) = calculate_parameters(reserve0, reserve1, vab, anchor_k)

    if reserve1 > reserve_switch:
        gamma = 1 - vab / tpv
    else:
        gamma = tpv/(4*vab*anchor_k)

    print("Price is {}, vfb is {}, reserve switch is {}, while gamma is {}".format(price, vfb, reserve_switch, gamma))


def plot_pylon(reserve0, reserve1, vab, anchor_k):
    (k, vfb, reserve_switch) = calculate_parameters(reserve0, reserve1, vab, anchor_k)

    x = numpy.linspace(0, 0.01, 10000)

    y = pylon_function(x, k, vab, anchor_k, reserve_switch)

    plot.plot(x, y)

    plot.show()


def calculate_parameters(reserve0, reserve1, vab, anchor_k):
    k = reserve0 * reserve1

    vfb = k / (vab * anchor_k)
    sqrt_k_factor = math.sqrt(anchor_k ** 2 - anchor_k)
    vab_multiplier = anchor_k - sqrt_k_factor if sqrt_k_factor < anchor_k else anchor_k + sqrt_k_factor
    reserve_switch = vab * vab_multiplier

    return k, vfb, reserve_switch


def pylon_function(x, k, vab, anchor_k, reserve_switch):
    reserve1 = numpy.sqrt(k*x)
    result = numpy.zeros_like(x)
    mask = reserve1 > reserve_switch
    result[mask] = 2 * reserve1[mask] - vab
    result[~mask] = k * x[~mask] / (vab * anchor_k)
    return result
