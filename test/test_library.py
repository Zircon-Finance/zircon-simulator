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


# this function calculates the y point given the 3 points in parabola
@pytest.mark.parametrize("coefficients", [
    ((10, 100, 2, 5), (0.9375, 0.625)),
    ((20, 5, 100, 2), (-0.002875, 0.3075)),
    ((20, 100, 20, 20), (0, 1.0)) # test for p3x == p2x
])
def test_parabola_coefficient(coefficients):
    (args, expected_results) = coefficients
    results = zirconlib.calculate_parabola_coefficients(*args)
    assert results == expected_results


# @pytest.mark.parametrize("coefficients", [
#     ((10, 100, 2, 5), (0.9375, 0.625)),
#     ((20, 5, 100, 2), (-0.002875, 0.3075)),
#     ((20, 100, 20, 20), (0, 1.0))
#     # test for p3x == p2x
# ])
# def test_get_ftv_for_x(coefficients):
#     (args, expected_results) = coefficients
#     results = zirconlib.get_ftv_for_x(*args)
#     assert results == expected_results

# def test_calculate_gamma(plt):
#     values = list(range(0, 200))
#     rectified = [v if v > 0 else 0 for v in values]
#     assert all(v >= 0 for v in rectified)
#     plt.plot(values, label="Original")
#     plt.plot(rectified, label="Rectified")
#     plt.legend()
#     plt.saveas = "test_rec.png"