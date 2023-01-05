# test_library.py
from pylonsim import zirconlib
import pytest


@pytest.mark.parametrize("maximums", [
    ((10, 100, 2, 5), (0.5, 5)),
    ((100, 10, 2, 5), (2, 0.2)),
    ((30, 1, 3, 5), (3, 0.1)),
    ((50.5, 100, 0.5, 0.5), (0.2525, 0.5)),
])
def test_get_max(maximums):
    (args, expected_results) = maximums
    results = zirconlib.get_maximum(*args)
    assert results == expected_results


def test_gamma(plt):
    values = list(range(0, 200))
    rectified = [v if v > 0 else 0 for v in values]
    assert all(v >= 0 for v in rectified)
    plt.plot(values, label="Original")
    plt.plot(rectified, label="Rectified")
    plt.legend()
    plt.saveas = "test_rec.png"

#
# def test_calculate_anchor_factor():
#     assert False
#
# def test_calculate_anchor_factor_burn():
#     assert False
#
# def test_anchor_factor_float_add():
#     assert False
#
# def test_anchor_factor_float_burn():
#     assert False
#
#
#
