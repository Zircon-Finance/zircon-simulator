import math


def calculate_gamma(vab, vfb, p2x, p2y, sync_reserve0, sync_reserve1, reserve0, reserve1):

    # Parabolic VFB

    # We simply have a very open parabola defined by three points:
    # P1 = (0,0)
    # P2 = (y/VFB, 2k/vfb - vab) or (custom point based on fitting to liquidity changes)
    # P3 = TPV = 2 sqrt(kx) = vab (principle behing kx/vab formula)

    # P2 is in the base case a point defined as having the same Y as the point of closest approach
    # between 2kx and vfbx, which is conveniently found as d(2kx)/dx = vfb

    # P2 may be stored in memory if an addition/removal of float liquidity
    # doesn't satisfy the principle ftv' = ftv + amIn
    #
    # We then fit a parabola with these three points.

    adjusted_vab = vab - sync_reserve1
    adjusted_vfb = vfb - sync_reserve0

    k = reserve0 * reserve1
    kv = adjusted_vfb * adjusted_vab
    p3x = 0

    print("Debug: Gamma inputs: vab: {}, vfb: {}, p2x: {}, p2y: {}".format(adjusted_vab, adjusted_vfb, p2x, p2y))
    print("Debug: Gamma kv: {}, k: {}".format(kv, k))
    # if kv <= k:
    # p3x = ((math.sqrt(k) - math.sqrt(k - kv))/adjusted_vfb) ** 2
    # else:
    p3x = adjusted_vab ** 2 / k

    print("Debug: Gamma p3x: {}, p3y: {}".format(p3x, adjusted_vab))

    if reserve1/reserve0 > p3x:
        return 1 - adjusted_vab / (reserve1 * 2), False
    else:
        # if kv <= k:
        #     # Just good ole y = vfbx
        #     return (adjusted_vfb / (2 * reserve0)), True
        # else:
        # Here we must make the parabola
        # p3y is simply vab
        a, b = calculate_parabola_coefficients(p2x, p2y, p3x, adjusted_vab)
        x = reserve1/reserve0
        return ((a * (x ** 2) + b * x)/(2 * reserve1)), True


def calculate_parabola_coefficients(p2x, p2y, p3x, p3y):
    # returns a and b to construct the ftv parabola

    if p3x - p2x == 0:
        return 0, p3y/p3x # this is basically vfb
    a_num = p3y * p2x - p3x * p2y
    a_den = p2x * p3x * (p3x - p2x)
    a = a_num/a_den

    b = p2y/p2x - p2x * a

    print("Parabola a: {}, b: {}".format(a, b))

    return a, b


def calculate_p2(k, vab, vfb):
    print("Debug: ZirconLib: P2 calc k: {}, vab: {}, vfb: {}".format(k, vab, vfb))
    p2y = (2 * k/vfb) - vab
    p2x = p2y/vfb
    return p2x, p2y
def get_maximum(reserve0, reserve1, b0, b1):
    px = reserve0 * b1/reserve1

    if px > b0:
        return b0, b0 * reserve1 / reserve0
    else:
        return px, b1

def calculate_anchor_factor(is_line_formula, amount, old_kfactor, adjusted_vab, reserve0, reserve1):

    sqrtk_factor = math.sqrt(old_kfactor ** 2 - old_kfactor)
    vab_multiplier = old_kfactor - sqrtk_factor if sqrtk_factor < old_kfactor else old_kfactor + sqrtk_factor

    amount_threshold_multiplier = reserve1 / (adjusted_vab * vab_multiplier)

    if is_line_formula or amount_threshold_multiplier > 1:
        if not is_line_formula and 1 + amount/adjusted_vab < amount_threshold_multiplier:
            return old_kfactor

        initial_half_k = reserve0

        if not is_line_formula:
            initial_half_k = reserve0 + ((amount_threshold_multiplier - 1) * adjusted_vab/2 * reserve0/reserve1)

        initial_tail_k = reserve1

        if not is_line_formula:
            initial_tail_k = reserve1 + ((amount_threshold_multiplier - 1) * adjusted_vab/2)

        initial_vab = adjusted_vab

        if not is_line_formula:
            initial_vab = amount_threshold_multiplier * adjusted_vab

        k_prime = (reserve0 + (amount * reserve0 / (2 * reserve1))) * (reserve1 + amount/2) / initial_half_k

        anchor_k = k_prime * initial_vab/initial_tail_k
        anchor_k = anchor_k * old_kfactor / (adjusted_vab + amount)

        if anchor_k < 1:
            anchor_k = 1

        return anchor_k
    else:
        return old_kfactor


def calculate_anchor_factor_burn(is_line_formula, amount, ptu, ptb, old_kfactor, adjusted_vab, reserve1):

    if is_line_formula or old_kfactor > 1:

        factor_anchor_amount = amount

        if is_line_formula:

            sqrtk_factor = math.sqrt(old_kfactor ** 2 - old_kfactor)
            vab_multiplier = old_kfactor - sqrtk_factor if sqrtk_factor < old_kfactor else old_kfactor + sqrtk_factor

            amount_threshold_multiplier = reserve1 / (adjusted_vab * vab_multiplier)

            factor_anchor_amount = min((1 - amount_threshold_multiplier) * adjusted_vab, amount)

        ptu = ptu * factor_anchor_amount / amount

        k_ratio = (1 - ptu/ptb) ** 2

        anchor_k = old_kfactor * k_ratio * adjusted_vab / (adjusted_vab - factor_anchor_amount)

        if anchor_k < 1:
            anchor_k = 1

    else:
        anchor_k = old_kfactor

    return anchor_k


def anchor_factor_float_add(amount, old_kfactor, reserve0, reserve1, gamma, async100):

    ftv = 0
    anchor_k = 0

    if async100:
        ftv = reserve0 * 2 * gamma
        anchor_k = (reserve0 + amount) * (reserve1) / (amount + ftv)

    else:
        ftv = reserve1 * 2 * gamma
        anchor_k = (reserve0 + (amount * reserve0 / (2 * reserve1))) * (reserve1 + amount/2) / (amount + ftv)

    anchor_k = anchor_k * ftv / reserve1
    anchor_k = anchor_k * old_kfactor / reserve0

    if anchor_k < 1:
        anchor_k = 1

    return anchor_k


def anchor_factor_float_burn(amount, old_kfactor, ptu, ptb, reserve1, gamma):

    k_ratio = (1 - ptu/ptb) ** 2

    ftv = reserve1 * 2 * gamma

    anchor_k = old_kfactor * k_ratio * ftv / (ftv - amount)

    if anchor_k < old_kfactor:
        anchor_k = old_kfactor

    if anchor_k < 1:
        anchor_k = 1

    return anchor_k

#  function anchorFactorFloatBurn(uint amount, uint oldKFactor, uint ptu, uint ptb, uint _reserveTranslated1, uint _gamma) pure public returns (uint anchorKFactor) {
#         // we know that ptu is proportional to sqrt(deltaK)
#         // so our Kprime is just k - (ptu/ptb * (sqrtK))**2
#         // while Kprime/k is simply 1 - ptu**2/ptb**2
#
#         uint kRatio = ((1e18 - uint(1e18).mul(ptu)/ptb)**2)/1e18;
#
#         uint ftv = _reserveTranslated1.mul(2 * _gamma)/1e18;
#         //kprime/amount + ftv, 1e18 final result
#         uint _anchorK = kRatio.mul(ftv)/(ftv - amount);
#
#         _anchorK = oldKFactor.mul(_anchorK)/1e18;
#
#         //console.log("akFR", _anchorK);
#
#         //We don't accept reductions of anchorK when removing Float
#         //This can only happen with large changes in liquidity
#         if(_anchorK < oldKFactor) {
#             return oldKFactor;
#         }
#         //No reason this should ever be below 1
#         require(_anchorK >= 1e18, "ZL: AK");
#
#         anchorKFactor = _anchorK;
#     }