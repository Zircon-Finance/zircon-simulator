class PylonToken:
    def __init__(self, _ticker, price_usd):
        self.ticker = _ticker
        self.price_usd = price_usd
        self.total_supply = 0
        self.balances = {"zero": 0}  # first one is "address", second is amount

    def mint(self, to, amount):
        self._set_zero(to)
        self.balances[to] += amount
        self.total_supply += amount
        print("ERC: Minted {} {} to: {}".format(amount, self.ticker, to))

    def burn(self, _from, amount):
        self.balances[_from] -= amount
        self.total_supply -= amount
        print("ERC: Burned {} {} from: {}".format(amount, self.ticker, _from))

    def transfer(self, _from, to, amount):
        if self.balances[_from] < amount:
            return -1  # it's an error

        self.balances[_from] -= amount
        self._set_zero(to)
        self.balances[to] += amount

        print("ERC: Transferred {} {} from: {} to: {}".format(amount, self.ticker, _from, to))

    def balance_of(self, to):
        return self.balances.get(to)

    def _set_zero(self, to):
        if to not in self.balances:
            self.balances[to] = 0
