# test_pylon.py
import pytest

from pylonsim.pylon import Pylon
from pylonsim.pylontoken import PylonToken
from pylonsim.uniswapv2 import Uniswap


@pytest.fixture(autouse=True)
def run_before_and_after_tests(tmpdir):
    """Fixture to execute asserts before and after a test is run"""
    # Setup: fill with any logic you want

    float_token = PylonToken("ZRG", 0.0001)
    anchor_token = PylonToken("USDC", 1)

    uniswap = Uniswap(float_token, anchor_token)
    pylon = Pylon(uniswap, float_token, anchor_token)

    float_token.mint("self", 100000000)
    anchor_token.mint("self", 10000000)

    pylon.init_pylon("self", 10000000, 10000)

    liquidity = pylon.mint_pool_tokens("self", 10000, False)

    pylon.burn("self", liquidity, False)

    liquidity_async = pylon.mint_async("self", 5000000, 1000, False)

    pylon.burn_async("self", liquidity_async, False)

    pylon.mint_pool_tokens("self", 100, True)

    # this is where the testing happens
    yield

    # Teardown : fill with any logic you want


def test_mint_pool_tokens():

    assert True
