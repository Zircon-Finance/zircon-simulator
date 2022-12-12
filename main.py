# This is a sample Python script.
import sys

from pylonPlotter import show_stats, plot_pylon
from pylonsim import controller
from pylonsim.pylon import Pylon
from pylonsim.pylontoken import PylonToken
from pylonsim.uniswapv2 import Uniswap


# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

def start():

    debug = True
    # Use a breakpoint in the code line below to debug your script.
    float_token = PylonToken("ETH", 1000)
    anchor_token = PylonToken("USDC", 1)

    uniswap = Uniswap(float_token, anchor_token)
    pylon = Pylon(uniswap, float_token, anchor_token)

    float_token.mint("self", 1000)
    anchor_token.mint("self", 10000000)

    pylon.init_pylon("self", 10, 10000)

    pylon.mint_pool_tokens("self", 1, False)

    pylon.burn("self", 1, False)

    pylon.mint_async("self", 0.5, 500, False)

    pylon.burn_async("self", 1, False)

    pylon.mint_pool_tokens("self", 1, False)

    while True:

        if not debug:
            try:
                command = controller.parse_command()

                if command == "exit":
                    break
                if command == "debug":
                    debug = not debug
                eval(command)
                print("posteval", command)
            except Exception as e:
                print("Error executing command: ", e)
        else:
            command = controller.parse_command()
            if command == "exit":
                break
            if command == "debug":
                debug = not debug
            eval(command)
            print("posteval ", command)


    show_stats(38897447*0.995, 10915*0.995, 29417-2488, 1.055)  # Press ⌘F8 to toggle the breakpoint.
    plot_pylon(38897447*0.995, 10915*0.995, 29417-2488, 1.055)



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    start()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
