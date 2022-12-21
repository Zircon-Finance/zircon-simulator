import math

from pylonsim.pylontoken import PylonToken


def get_amount_out_manual(reserve_in, reserve_out, amount_in):
    return amount_in * reserve_out / (reserve_in + amount_in)


class Uniswap:
    def __init__(self, float_token, anchor_token):
        self.float_token = float_token
        self.anchor_token = anchor_token
        self.pool_token = PylonToken("UNI-{}{}".format(float_token.ticker, anchor_token.ticker), 0)

        self.reserve0 = 0
        self.reserve1 = 0

        self.min_liquidity = 0.000000001
        self.address = "uniswap"

    def mint(self, amount0, amount1, to):

        # replicates the router as a transferFrom
        self.float_token.transfer(to, self.address, amount0)
        self.anchor_token.transfer(to, self.address, amount1)

        if self.pool_token.total_supply == 0:
            liquidity = math.sqrt(amount0 * amount1) - self.min_liquidity
            self.pool_token.mint("zero", self.min_liquidity)
        else:
            liquidity = min(amount0 * self.pool_token.total_supply / self.reserve0,
                            amount1 * self.pool_token.total_supply / self.reserve1)

        self.pool_token.mint(to, liquidity)
        self._update(self.reserve0 + amount0, self.reserve1 + amount1)

        #print("Uniswap: Minted {} {} to {}".format(liquidity, self.pool_token.ticker, to))
        return liquidity

    def _update(self, balance0, balance1):
        self.reserve0 = balance0
        self.reserve1 = balance1

    def burn(self, liquidity, _from, to):
        amount0 = liquidity * self.reserve0 / self.pool_token.total_supply
        amount1 = liquidity * self.reserve1 / self.pool_token.total_supply

        self.pool_token.burn(_from, liquidity)
        self.float_token.transfer(self.address, to, amount0)
        self.anchor_token.transfer(self.address, to, amount1)

        balance0 = self.float_token.balance_of(self.address)
        balance1 = self.anchor_token.balance_of(self.address)

        self._update(balance0, balance1)

    def swap(self, amount0_in, amount1_in, amount0_out, amount1_out, to):

        # since we can't revert stuff here, need to do an initial k check
        balance0 = self.float_token.balance_of(self.address) + amount0_in - amount0_out
        balance1 = self.anchor_token.balance_of(self.address) + amount1_in - amount1_out

        # print("Balance0: {}, Balance1: {}, reserve0: {}, reserve1: {}"
          #    .format(balance0, balance1, self.reserve0, self.reserve1))
        # print("Kp, k", balance0 * balance1, self.reserve0 * self.reserve1)
        if balance0 * balance1 + 0.1 >= self.reserve0 * self.reserve1:


            self.float_token.transfer(to, self.address, amount0_in)
            self.anchor_token.transfer(to, self.address, amount1_in)

            # sending tokens out
            self.float_token.transfer(self.address, to, amount0_out)
            self.anchor_token.transfer(self.address, to, amount1_out)

            self._update(balance0, balance1)
            return amount0_out, amount1_out
        else:
            print("Uniswap: K")
            return -1, -1

    def get_amount_out(self, amount_in, float_is_in):
        if float_is_in:
            reserve_in = self.reserve0
            reserve_out = self.reserve1
        else:
            reserve_in = self.reserve1
            reserve_out = self.reserve0

        return amount_in * reserve_out / (reserve_in + amount_in)

    def mint_one_side(self, amount0, amount1, to):

        self.float_token.transfer(to, self.address, amount0)
        self.anchor_token.transfer(to, self.address, amount1)

        balance0 = self.float_token.balance_of(self.address)
        balance1 = self.anchor_token.balance_of(self.address)

        sqrtk = math.sqrt(balance0 * balance1)
        sqrtk_init = math.sqrt(self.reserve0 * self.reserve1)

        liquidity = (sqrtk - sqrtk_init) * self.pool_token.total_supply / sqrtk_init

        self.pool_token.mint(to, liquidity)
        self._update(balance0, balance1)

        return liquidity

    def burn_one_side(self, _from, to, liquidity, get_float):

        total_supply = self.pool_token.total_supply
        self.pool_token.burn(_from, liquidity)

        balance0 = self.float_token.balance_of(self.address)
        balance1 = self.anchor_token.balance_of(self.address)

        amount0 = liquidity * balance0 / total_supply
        amount1 = liquidity * balance1 / total_supply

        amount = 0
        if get_float:
            amount = amount0 + get_amount_out_manual(balance1-amount1, balance0-amount0, amount1)
            print("Debug: BurnOne: amount0: {}, amount1: {}, amount: {}".format(amount0, amount1, amount))
            self.float_token.transfer(self.address, to, amount)
        else:
            amount = amount1 + get_amount_out_manual(balance0-amount0, balance1-amount1, amount0)
            self.anchor_token.transfer(self.address, to, amount)

        balance0 = self.float_token.balance_of(self.address)
        balance1 = self.anchor_token.balance_of(self.address)

        self._update(balance0, balance1)

        return amount

    def price(self):
        price = self.reserve1/self.reserve0
        print("Price: ", price)
        return self.reserve1/self.reserve0

    # Calculates amount of tokens to pump/dump and executes swap to arrive at the desired price
    def set_price(self, price, to):

        res_in = 0
        res_out = 0
        adjusted_price = 0
        dump = price < self.price()
        if dump:
            res_in = self.reserve0
            res_out = self.reserve1
            adjusted_price = 1/price
        else:
            res_in = self.reserve1
            res_out = self.reserve0
            adjusted_price = price

        # x is amount of res_in token to dump
        x = math.sqrt(adjusted_price * res_in * res_out) - res_in
        print("X: ", x)
        out = self.get_amount_out(x, dump)
        if dump:
            # res in is 0
            self.swap(x, 0, 0, out, to)
        else:
            self.swap(0, x, out, 0, to)
