import math

import pytest

from pylonsim.pylontoken import PylonToken
from pylonsim.uniswapv2 import Uniswap


@pytest.fixture(autouse=True)
def run_before_and_after_tests(tmpdir):
    """Fixture to execute asserts before and after a test is run"""
    # Setup: fill with any logic you want

    pytest.float_token = PylonToken("ZRG", 0.0001)
    pytest.anchor_token = PylonToken("USDC", 1)

    pytest.uniswap = Uniswap(pytest.float_token, pytest.anchor_token)
    pytest.address = "tester"

    pytest.float_token.mint(pytest.address, 1000)
    pytest.anchor_token.mint(pytest.address, 10000000)

    # this is where the testing happens
    yield

    # Teardown : fill with any logic you want

# //   const swapTestCases = [
# //     [1, 5, 10, '1662497915624478906'],
# //     [1, 10, 5, '453305446940074565'],
# //
# //     [2, 5, 10, '2851015155847869602'],
# //     [2, 10, 5, '831248957812239453'],
# //
# //     [1, 10, 10, '906610893880149131'],
# //     [1, 100, 100, '987158034397061298'],
# //     [1, 1000, 1000, '996006981039903216']
# //   ].map(a => a.map(n => (typeof n === 'string' ? ethers.BigNumber.from(n) : expandTo18Decimals(n))))
# //   swapTestCases.forEach((swapTestCase, i) => {
# //     it(`getInputPrice:${i}`, async () => {
# //       const [swapAmount, token0Amount, token1Amount, expectedOutputAmount] = swapTestCase
# //       await addLiquidity(token0Amount, token1Amount)
# //
# //       await token0.transfer(pair.address, swapAmount)
# //       await expect(pair.swap(0, expectedOutputAmount.add(1), account.address, '0x')).to.be.revertedWith(
# //           'UniswapV2: K'
# //       )
# //       await pair.swap(0, expectedOutputAmount, account.address, '0x')
# //     })
# //   })


@pytest.mark.parametrize("swaps", [
    ((2, -3), (3/4, -1/8)),
    ((-4, 6), (3/4, 13/4)),
    ((0.5, 1), (-1, 1/2))
])
def test_swap(swaps):
    (args, expected_results) = swaps
    uniswap: Uniswap = pytest.uniswap
    results = uniswap.swap(*args)
    assert results == expected_results



def test_mint_one_side():
    token_0_amount = 1
    token_1_amount = 100
    address = pytest.address
    uniswap: Uniswap = pytest.uniswap

    liquidity = uniswap.mint(token_0_amount, token_1_amount, address)

    first_liq = pytest.approx(10 - uniswap.min_liquidity)
    assert liquidity == first_liq

    # it should be some infinite ∑
    # but we approx as only the first and last one
    calculated_liquidity = ((token_0_amount/2) * uniswap.pool_token.total_supply) / uniswap.reserve0
    calculated_liquidity_2 = (uniswap.get_amount_out(token_0_amount/2, True) * uniswap.pool_token.total_supply) / uniswap.reserve1

    second_liquidity = uniswap.mint_one_side(token_0_amount, 0, address)
    assert second_liquidity == pytest.approx((calculated_liquidity+calculated_liquidity_2)/2, abs=2e-2)


def test_mint():

    token_0_amount = 1
    token_1_amount = 4
    address = pytest.address
    float_token: PylonToken = pytest.float_token
    anchor_token: PylonToken = pytest.anchor_token
    uniswap: Uniswap = pytest.uniswap

    # seeing if liquidity is minted correctly

    # float_token.transfer(address, uniswap.address, token_0_amount)
    # anchor_token.transfer(address, uniswap.address, token_1_amount)

    liquidity = uniswap.mint(token_0_amount, token_1_amount, address)
    expected_liquidity = liquidity - uniswap.min_liquidity
    assert liquidity == pytest.approx(expected_liquidity)
    assert uniswap.pool_token.total_supply == 2

    # checking pair/token balances
    tester_balance = uniswap.pool_token.balance_of(address)
    assert tester_balance == pytest.approx(expected_liquidity)

    pair_balance_token0 = float_token.balance_of(uniswap.address)
    assert pair_balance_token0 == token_0_amount

    pair_balance_token1 = anchor_token.balance_of(uniswap.address)
    assert pair_balance_token1 == token_1_amount

    # checking pair reserves
    assert uniswap.reserve0 == token_0_amount
    assert uniswap.reserve1 == token_1_amount
