### Simulation de l'IA ###
from bourse import *


class AI:
    
    def __init__(self, wallet : dict, portfolio : dict, global_value : float):
        self.wallet = wallet # {id : [buy_price, quantity],...}
        self.portfolio = portfolio # dict of all stock bought by AI 
        self.global_value = global_value # value of the portolio (o(1) complexity)

    def strategy(self, market : Market):
        for action_list in self.wallet.values():   
            

        pass