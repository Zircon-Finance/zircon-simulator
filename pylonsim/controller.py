import difflib
# TODO: inherit from click.options to do this more user friendly
# https://stackoverflow.com/questions/49186376/how-to-create-a-command-line-prompt-that-displays-options-next-to-integers-and-a

functions = [
    "pylon.mint_pool_tokens",
    "pylon.mint_async",
    "pylon.burn",
    "pylon.burn_async",
    "pylon.init_pylon",
    "uniswap.price",
    "uniswap.set_price",
    "exit",
    "debug"]

_bool = ["True", "False"]

aliases = ["sync", "async", "price", "setprice", "burn", "burnasync"]
alias_key = {
    "sync": "mint_pool_tokens",
    "async": "mint_async",
    "price": "uniswap.price",
    "setprice": "uniswap.set_price",
    "burn": "pylon.burn",
    "burnasync": "pylon.burn_async"
}


def parse_command():

    command = input("Input Next Command: ")

    params = command.split(" ")

    params = [x.strip('') for x in params]

    print(params)

    selector = params[0]
    alias = difflib.get_close_matches(selector, aliases)
    if len(alias) > 0:
        selector = alias_key[alias[0]]

    function = difflib.get_close_matches(selector, functions)[0]

    print("Debug: Function: " + function)

    if function == "exit" or function == "debug":
        return function

    calldata = "{}(".format(function)

    for index, item in enumerate(params):
        if index > 0:

            if index > 1:
                calldata = calldata + ", "

            if is_number(item):
                calldata = calldata + item
            else:
                match = difflib.get_close_matches(item, _bool)

                if len(match) > 0:
                    calldata = calldata + match[0]
                else:
                    calldata = calldata + "\"" + item + "\""

    calldata = calldata + ")"

    print(calldata)
    return calldata


def is_number(num):
    try:
        if isinstance(int(num), int):
            return True
    except:
        try:
            if isinstance(float(num), float):
                return True

        except:
            return False
