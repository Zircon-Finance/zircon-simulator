# For the sim we make a few simplifying assumptions:
# - all liquidity is Pylon (no PTB/ptt etc.)
# - no fees
# - no deltaGamma, mu, fee calculations etc.
import math

from pylonsim import zirconlib
from pylonsim.pylontoken import PylonToken


class Pylon:
    def __init__(self, _uniswap, float_token, anchor_token):
        self.uniswap = _uniswap
        self.float_token = float_token
        self.anchor_token = anchor_token

        self.float_pool_token = PylonToken("{}/{}-fZPT".format(float_token.ticker, anchor_token.ticker), 0)
        self.anchor_pool_token = PylonToken("{}/{}-sZPT".format(float_token.ticker, anchor_token.ticker), 0)

        self.vab = 0
        self.anchor_k = 0
        self.vfb = 0
        self.p2x = 0
        self.p2y = 0
        self.sync_reserve0 = 0
        self.sync_reserve1 = 0

        self.gamma = 0
        self.is_line_formula = False

        self.address = "pylon"
        self.min_liquidity = 0.0000001
        self.max_sync = 0.40

        print("Initialized Pylon Class")

    def init_pylon(self, to, amount0, amount1):

        print("Launching pylon with amount0 {}, amount1 {}".format(amount0, amount1))
        self.float_token.transfer(to, self.address, amount0)
        self.anchor_token.transfer(to, self.address, amount1)

        # TODO: add force ratio match
        self.vab = amount1
        self.anchor_k = 1.0
        self.vfb = amount0

        # Would get recalculated after sync anyway
        self.p2x, self.p2y = zirconlib.calculate_p2(amount0 * amount1, self.vab, self.vfb)

        (self.gamma, self.is_line_formula) = zirconlib.calculate_gamma(self.vab,
                                                                       self.vfb,
                                                                       self.p2x,
                                                                       self.p2y,
                                                                       0,
                                                                       0,
                                                                       amount0,
                                                                       amount1)



        self.float_pool_token.mint("zero", self.min_liquidity)
        self.anchor_pool_token.mint("zero", self.min_liquidity)

        anchor_liquidity = amount1 - self.min_liquidity
        float_liquidity = (amount0 * 2 * self.gamma) - self.min_liquidity

        self.sync_minting()

        self.float_pool_token.mint(to, float_liquidity)
        self.anchor_pool_token.mint(to, anchor_liquidity)

        self._update(amount0)

    def mint_pool_tokens(self, to, amount_in, is_anchor):
        print("\n====MintSync====")
        self.sync()

        if not is_anchor:
            self.float_token.transfer(to, self.address, amount_in)
        else:
            self.anchor_token.transfer(to, self.address, amount_in)

        (reserve0, reserve1) = self.get_pair_reserves()

        (sync_reserve0, sync_reserve1) = self.get_sync_reserves()
        print("DEBUG: Sync0 before PTB: ", sync_reserve0)

        float_liquidity_owned = 0
        ptb_max = 0
        amount_out = 0
        liquidity = 0
        # records either existing ftv or ftv + new liquidity
        # used to match the parabola to the desired characteristic
        desired_ftv = 0
        ptb = self.uniswap.pool_token.total_supply

        if not is_anchor:
            float_liquidity_owned = (sync_reserve0 * ptb / (2 * reserve0)) + ptb * self.gamma

            ptb_max = amount_in * ptb / (2 * reserve0)
            print("MintPool: Liquidity val in ptb: ", ptb_max)

            amount_out, amount_pool = self.handle_sync_async(amount_in, reserve0, sync_reserve0, False)
            ftv = 2 * reserve0 * self.gamma
            print("Debug: Initial FTV: {}, AmountPool: {}".format(ftv * reserve1/reserve0, amount_pool))
            self.vfb += self.vfb * amount_out/(ftv + sync_reserve0)
            desired_ftv = (ftv + amount_pool) * reserve1/reserve0
        else:

            amount_out, _ = self.handle_sync_async(amount_in, reserve1, sync_reserve1, True)
            liquidity = amount_out * self.anchor_pool_token.total_supply / self.vab

            self.vab += amount_out
            desired_ftv = 2 * reserve1 * self.gamma
            self.anchor_pool_token.mint(to, liquidity)

        new_gamma, _ = self._update(desired_ftv)


        if not is_anchor:

            pair_reserve0, pair_reserve1 = self.get_pair_reserves()
            sync_reserve0, sync_reserve1 = self.get_sync_reserves()
            print("DEBUG: Sync0 for PTB: ", sync_reserve0)
            print("Debug: New FTV: ", 2 * pair_reserve1 * new_gamma)

            ptb_new = self.uniswap.pool_token.balance_of(self.address)

            new_float_liquidity = sync_reserve0 * ptb_new / (2 * pair_reserve0) + ptb_new * new_gamma

            if new_float_liquidity > float_liquidity_owned:

                liquidity = self.float_pool_token.total_supply * ((new_float_liquidity/float_liquidity_owned) - 1)
                print("Liquidity minted: {}, oldPTT: {}, newPTT: {}".format(liquidity, float_liquidity_owned,
                                                                            new_float_liquidity))

                kv = (self.vfb -sync_reserve0) * (self.vab - sync_reserve1)
                k = pair_reserve0 * pair_reserve1
                print("New VFB: {}, adjVfb: {} kv: {}, k: {}".format(self.vfb, self.vfb - sync_reserve0, kv, k))
                print("DEBUG: reserveOnly PTB old: {}, resOnly ptb new: {}".format(ptb * self.gamma, ptb_new * new_gamma))
                self.float_pool_token.mint(to, liquidity)
            else:
                print("Error VFB, Old Liq: {}, New Liq: {}".format(float_liquidity_owned, new_float_liquidity))



    def handle_sync_async(self, amount_in, pair_reserve, sync_reserve, is_anchor):

        max = pair_reserve * self.max_sync

        free_space = 0
        amount_out = 0

        # TODO: Clean this code for solidity
        res0, res1 = self.get_pair_reserves()
        max0 = res0 * self.max_sync / 2
        max1 = res1 * self.max_sync / 2
        px, py = zirconlib.get_maximum(res0,
                                       res1,
                                       self.float_token.balance_of(self.address) - max0,
                                       self.anchor_token.balance_of(self.address) - max1)
        if py < 0 or px < 0:
            py = 0
            px = 0
        sync_mint = 0
        if is_anchor:
            max = (res1 + py) * self.max_sync
            sync_mint = py
        else:
            max = (res0 + px) * self.max_sync
            sync_mint = px

        if max > sync_reserve:
            free_space = max + sync_mint - sync_reserve
            print("HandleSync:syncMint: {}, free_space: {}, AsyncIn: {}".format(sync_mint, free_space, (amount_in - free_space)))
            if free_space > 0:
                if amount_in <= free_space:
                    px, _ = self.sync_minting()
                    return amount_in, px
                else:
                    amount_out += free_space

        (new_reserve0, new_reserve1) = self.get_pair_reserves()

        async_amount_in = amount_in - free_space

        async_amount_out = 0
        if is_anchor:
            sqrtk = math.sqrt(new_reserve0 * new_reserve1)
            sqrtk_prime = math.sqrt(new_reserve0 * (new_reserve1 + async_amount_in))

            liq_percentage = (sqrtk_prime - sqrtk) / sqrtk

            async_amount_out = new_reserve1 * 2 * liq_percentage

            # self.anchor_k = zirconlib.calculate_anchor_factor(self.is_line_formula,
            #                                                   async_amount_out,
            #                                                   self.anchor_k,
            #                                                   self.vab - sync_reserve,
            #                                                   new_reserve0,
            #                                                   new_reserve1)

        else:
            sqrtk = math.sqrt(new_reserve0 * new_reserve1)
            sqrtk_prime = math.sqrt((new_reserve0 + async_amount_in) * new_reserve1)

            liq_percentage = (sqrtk_prime - sqrtk) / sqrtk

            async_amount_out = new_reserve0 * 2 * liq_percentage

            # self.anchor_k = zirconlib.anchor_factor_float_add(
            #     async_amount_out,
            #     self.anchor_k,
            #     new_reserve0,
            #     new_reserve1,
            #     self.gamma,
            #     True
            # )

        amount_out += async_amount_out

        px = 0
        if free_space > 0:
            px, _ = self.sync_minting()

        return amount_out, px + async_amount_out

    def mint_async(self, to, amount0, amount1, is_anchor):
        print("\n====MintAsync====")
        self.sync()

        self.float_token.transfer(to, self.address, amount0)
        self.anchor_token.transfer(to, self.address, amount1)

        float_liquidity_owned = 0
        ptb_max = 0
        amount_out = 0
        liquidity = 0
        ptb = self.uniswap.pool_token.total_supply

        (sync_reserve0, sync_reserve1) = self.get_sync_reserves()
        (reserve0, reserve1) = self.get_pair_reserves()

        total_amount = 0
        desired_ftv = 0
        if not is_anchor:
            float_liquidity_owned = (sync_reserve0 * ptb / (2 * reserve0)) + ptb * self.gamma

            ptb_max = amount0 * ptb / reserve0
            total_amount = min(amount1 * 2 * reserve0/reserve1, amount0 * 2)

            ftv = 2 * reserve1 * self.gamma
            ftv_f = 2 * reserve0 * self.gamma
            print("Debug: Ftv: {}, Vfb: {}, 2 * amount1: {}".format(ftv, self.vfb, 2 * amount1))
            self.vfb += self.vfb * (total_amount / (ftv_f + sync_reserve0))
            desired_ftv = ftv + 2 * amount1

            #
            # self.anchor_k = zirconlib.anchor_factor_float_add(
            #     total_amount * reserve1 / reserve0,
            #     self.anchor_k,
            #     reserve0,
            #     reserve1,
            #     self.gamma,
            #     False
            # )

        else:
            total_amount = min(amount0 * 2 * reserve1/reserve0, amount1 * 2)

            # self.anchor_k = zirconlib.calculate_anchor_factor(self.is_line_formula,
            #                                                   total_amount,
            #                                                   self.anchor_k,
            #                                                   self.vab - sync_reserve1,
            #                                                   reserve0, reserve1)
            liquidity = total_amount * self.anchor_pool_token.total_supply / self.vab
            self.vab += total_amount
            desired_ftv = 2 * reserve1 * self.gamma
            self.anchor_pool_token.mint(to, liquidity)

        print("Debug: Old PTT: {}, Fl_liq: {}".format(self.uniswap.pool_token.total_supply, float_liquidity_owned))
        print("Debug: Fpt supply: {}".format(self.float_pool_token.total_supply))
        self.uniswap.mint(amount0, amount1, self.address)

        new_gamma, _ = self._update(desired_ftv)

        if not is_anchor:
            (sync_reserve0, sync_reserve1) = self.get_sync_reserves()
            (reserve0, reserve1) = self.get_pair_reserves()

            ptb_new = self.uniswap.pool_token.balance_of(self.address)
            new_float_liquidity = ((sync_reserve0 * ptb_new)/(2 * reserve0)) + (ptb_new * new_gamma)

            print("Debug: New PTT: {}, Fl_liq: {}".format(self.uniswap.pool_token.total_supply, new_float_liquidity))

            if new_float_liquidity > float_liquidity_owned:
                liquidity = self.float_pool_token.total_supply * ((new_float_liquidity/float_liquidity_owned) - 1)
                self.float_pool_token.mint(to, liquidity)
            else:
                print("VFB Error")

    def burn(self, to, liquidity, is_anchor):
        print("\n====Burn====")
        self.sync()

        reserve_pt, amount = self.burn_pylon_reserves(is_anchor, liquidity)
        if is_anchor:
            self.anchor_token.transfer(self.address, to, amount)
        else:
            self.float_token.transfer(self.address, to, amount)

        reserve0, reserve1 = self.get_pair_reserves()
        desired_ftv = 2 * reserve1 * self.gamma

        if reserve_pt < liquidity:

            liquidity_adjusted = liquidity - reserve_pt
            ptu = self.calculate_lptu(is_anchor, liquidity)


            sync_reserve0, sync_reserve1 = self.get_pair_reserves()
            # large simplification here, we simply slash ptu by omega and that's it
            if is_anchor:
                omega = min(1, ((1 - self.gamma) * reserve1 * 2)/(self.vab - sync_reserve1))

                ptu = ptu * omega

                # self.anchor_k = zirconlib.calculate_anchor_factor_burn(
                #     self.is_line_formula,
                #     self.vab * liquidity_adjusted / self.anchor_pool_token.total_supply,
                #     ptu,
                #     self.uniswap.pool_token.balance_of(self.address),
                #     self.anchor_k,
                #     self.vab - sync_reserve1,
                #     reserve1
                # )

                return_amount = self.uniswap.burn_one_side(self.address, to, ptu, False)

                desired_ftv = 2 * reserve1 * self.gamma


            else:

                # the adjustment for slippage is done later, in theory
                removed_amount = ptu * reserve1 * 2 / self.uniswap.pool_token.total_supply
                desired_ftv = 2 * reserve1 * self.gamma - removed_amount
                # self.anchor_k = zirconlib.anchor_factor_float_burn(
                #     removed_amount,
                #     self.anchor_k,
                #     ptu,
                #     self.uniswap.pool_token.balance_of(self.address),
                #     reserve1,
                #     self.gamma)

                self.uniswap.burn_one_side(self.address, to, ptu, True)

        if not is_anchor:
            self.vfb -= self.vfb * liquidity / self.float_pool_token.total_supply
            self.float_pool_token.burn(to, liquidity)
        else:
            self.vab -= self.vab * liquidity / self.anchor_pool_token.total_supply
            self.anchor_pool_token.burn(to, liquidity)

        self._update(desired_ftv)

    def burn_async(self, to, liquidity, is_anchor):
        print("\n====BurnAsync====")
        self.sync()

        ptu = self.calculate_lptu(is_anchor, liquidity)

        reserve0, reserve1 = self.get_pair_reserves()
        sync_reserve0, sync_reserve1 = self.get_sync_reserves()
        max_pool_tokens = 0
        if is_anchor:
            max_pool_tokens = self.anchor_pool_token.total_supply * (1 - (sync_reserve1/self.vab))
        else:
            max_pool_tokens = self.float_pool_token.total_supply * (1 - (sync_reserve0 / (reserve0 * 2 * self.gamma + sync_reserve0)))

        if liquidity > max_pool_tokens:
            print("BurnAsync: Max Liquidity error, maxPT: ", max_pool_tokens)
            return -1

        ptb = self.uniswap.pool_token.balance_of(self.address)
        desired_ftv = 0

        if is_anchor:
            omega = min(1, ((1 - self.gamma) * reserve1 * 2) / (self.vab - sync_reserve1))

            ptu = ptu * omega

            # self.anchor_k = zirconlib.calculate_anchor_factor_burn(
            #     self.is_line_formula,
            #     self.vab * liquidity / self.anchor_pool_token.total_supply,
            #     ptu,
            #     ptb,
            #     self.anchor_k,
            #     self.vab - sync_reserve1,
            #     reserve1
            # )

            self.vab -= self.vab * liquidity / self.anchor_pool_token.total_supply
            desired_ftv = 2 * reserve1 * self.gamma
            self.anchor_pool_token.burn(to, liquidity)

        else:

            removed_amount = ptu * reserve1 * 2 / self.uniswap.pool_token.total_supply

            desired_ftv = 2 * reserve1 * self.gamma - removed_amount
            # self.anchor_k = zirconlib.anchor_factor_float_burn(
            #     removed_amount,
            #     self.anchor_k,
            #     ptu,
            #     self.uniswap.pool_token.balance_of(self.address),
            #     reserve1,
            #     self.gamma)
            self.vfb -= self.vfb * liquidity/self.float_pool_token.total_supply
            self.float_pool_token.burn(to, liquidity)

        self.uniswap.burn(ptu, self.address, to)

        self._update(desired_ftv)

    def sync(self):

        (reserve0, reserve1) = self.get_pair_reserves()

        (pylon_reserve0, pylon_reserve1) = self.get_sync_reserves()

        max0 = reserve0 * self.max_sync
        max1 = reserve1 * self.max_sync

        self.update_reserves_removing_excess(pylon_reserve0, pylon_reserve1, max0, max1)

        (reserve0, reserve1) = self.get_pair_reserves()
        (pylon_reserve0, pylon_reserve1) = self.get_sync_reserves()

        (self.gamma, self.is_line_formula) = zirconlib.calculate_gamma(self.vab,
                                                                       self.vfb,
                                                                       self.p2x,
                                                                       self.p2y,
                                                                       pylon_reserve0,
                                                                       pylon_reserve1,
                                                                       reserve0,
                                                                       reserve1)
        print("PylonSync: Gamma: {}, is_line: {}, vfb: {}, vab: {}".format(self.gamma, self.is_line_formula, self.vfb, self.vab))

    def sync_minting(self):

        (balance0, balance1) = self.get_balances()

        (reserve0, reserve1) = self.get_pair_reserves()

        if reserve0 == 0 and reserve1 == 0:
            reserve0 = balance0
            reserve1 = balance1

        max0 = reserve0 * self.max_sync / 2
        max1 = reserve1 * self.max_sync / 2

        if balance0 > max0 and balance1 > max1:
            (px, py) = zirconlib.get_maximum(reserve0, reserve1, balance0 - max0, balance1 - max1)

            self.uniswap.mint(px, py, self.address)
            print("sync minted {} {} and {} {}".format(px, self.float_token.ticker, py, self.anchor_token.ticker))
            return px, py
        return 0, 0

    def burn_pylon_reserves(self, is_anchor, liquidity):

        (reserve0, reserve1) = self.get_pair_reserves()
        (sync_reserve0, sync_reserve1) = self.get_sync_reserves()

        if is_anchor:

            reserve_pt = sync_reserve1 * self.anchor_pool_token.total_supply / self.vab

            ptu_amount = min(reserve_pt, liquidity)

            amount = self.vab * ptu_amount / self.anchor_pool_token.total_supply

            return reserve_pt, amount

        else:

            float_balance = sync_reserve0 + reserve0 * 2 * self.gamma
            reserve_pt = sync_reserve0 * self.float_pool_token.total_supply / float_balance

            ptu_amount = min(reserve_pt, liquidity)

            amount = float_balance * ptu_amount / self.float_pool_token.total_supply

            return reserve_pt, amount

    def calculate_lptu(self, is_anchor, liquidity):

        (reserve0, reserve1) = self.get_pair_reserves()
        (sync_reserve0, sync_reserve1) = self.get_sync_reserves()

        pylon_share = 0
        ptb = self.uniswap.pool_token.balance_of(self.address)
        max_pool_tokens = 0


        if is_anchor:
            pylon_share = ptb * (self.vab - sync_reserve1) / (reserve1 * 2)
            max_pool_tokens = self.anchor_pool_token.total_supply * (1 - sync_reserve1/self.vab)
        else:
            pylon_share = self.gamma * ptb
            max_pool_tokens = self.float_pool_token.total_supply * (1 - sync_reserve0 / (reserve0 * 2 * self.gamma + sync_reserve0))

        return liquidity * pylon_share/max_pool_tokens



    def _update(self, desired_ftv):

        (balance0, balance1) = self.get_balances()

        (reserve0, reserve1) = self.get_pair_reserves()

        max0 = reserve0 * self.max_sync
        max1 = reserve1 * self.max_sync

        # only point where price might change so can record price before
        self.update_reserves_removing_excess(balance0, balance1, max0, max1)

        # desired ftv represents a target ftv that we have to fit for
        # an important adjustment to make is price, since async100 mints could change it


        (sync0, sync1) = self.get_sync_reserves()
        (new_reserve0, new_reserve1) = self.get_pair_reserves()
        adjusted_ftv = desired_ftv
        if reserve1 / reserve0 != new_reserve1/new_reserve0:
            adjusted_ftv = desired_ftv * (reserve0 / reserve1) * new_reserve1/new_reserve0
        print("Debug: Adjusted FTV: {}, desired FTV: {}".format(adjusted_ftv, desired_ftv))

        # the ftv can help us define p2. we only really care about it when kv > k
        # Ideally the deviation from constantly shifting p2 should be very small,
        # so we should be able to reset it to default value without too many issues when not in is_line formula

        kv = (self.vab - sync1) * (self.vfb - sync0)
        k = new_reserve1 * new_reserve0
        adjusted_vab = self.vab - sync1
        adjusted_vfb = self.vfb - sync0
        x = new_reserve1/new_reserve0

        # p2 can't be placed later than p3
        if kv > k and (x < (adjusted_vab ** 2)/k):
            self.p2y = adjusted_ftv
            self.p2x = new_reserve1/new_reserve0

        else:
            # resets p2 to its default value
            self.p2y = (2 * k/adjusted_vfb) - adjusted_vab
            self.p2x = self.p2y/adjusted_vfb

        new_gamma = zirconlib.calculate_gamma(self.vab,
                                              self.vfb,
                                              self.p2x,
                                              self.p2y,
                                              sync0,
                                              sync1,
                                              new_reserve0,
                                              new_reserve1)

        print("PylonUpdate: New Gamma: {}, new Sync0: {}, new Sync1 {}, new Res0: {}, new Res1: {}".format(new_gamma, sync0, sync1, reserve0, reserve1))
        print("PylonUpdate: Vfb: {}, Vab: {},".format(self.vfb, self.vab))
        ptb_new = self.uniswap.pool_token.total_supply
        print("PylonUpdate: FloatPTB: {}".format(((sync0 * ptb_new)/(2 * reserve0)) + (ptb_new * new_gamma[0])))
        return new_gamma

    def update_reserves_removing_excess(self, new_reserve0, new_reserve1, max0, max1):
        if max0 < new_reserve0:
            self.uniswap.mint_one_side(new_reserve0 - max0, 0, self.address)
            self.sync_reserve0 = max0
            print("PylonExcess: Thrown {} {}".format(new_reserve0 - max0, self.float_token.ticker))
        else:
            self.sync_reserve0 = new_reserve0

        if max1 < new_reserve1:
            self.uniswap.mint_one_side(0, new_reserve1 - max1, self.address)
            self.sync_reserve1 = max1
            print("PylonExcess: Thrown {} {}".format(new_reserve1 - max1, self.anchor_token.ticker))
        else:
            self.sync_reserve1 = new_reserve1

    def get_pair_reserves(self):
        return self.uniswap.reserve0, self.uniswap.reserve1

    def get_balances(self):
        return self.float_token.balance_of(self.address), self.anchor_token.balance_of(self.address)

    def get_sync_reserves(self):
        return self.sync_reserve0, self.sync_reserve1

    def my_method(self):
        print("This is my method")