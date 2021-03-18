from datetime import datetime, timedelta
from QuantConnect.Securities.Option import OptionPriceModels
from QuantConnect.Securities.Option import ConstantQLRiskFreeRateEstimator
from QuantConnect.Securities.Option import IOptionPriceModel 
from QuantConnect.Securities import Option
import json

class alpha(AlphaModel):   
    def __init__(self,algorithm):
        self.algorithm=algorithm
        self.symbolDataBySymbol ={} 
        self.day=None
        self.optionDataBySymbol={} #Keyed by symbol, valued by Theoretical Price/Bid/Ask/ Volume
        self.LastPrice={} 
      
    def Update(self, algorithm, slice):
        insights=[]
        for symbol, symbolData in self.symbolDataBySymbol.items():
            for chain in slice.OptionChains:
                volatility = algorithm.Securities[chain.Key.Underlying].VolatilityModel.Volatility
                for contract in chain.Value:
                    if str(contract.Expiry.date())!='2021-01-15':
                        continue
                    #Specificy Contract Expiration Date of interest
                    if contract.Symbol.Value not in self.optionDataBySymbol:
                        #First instance of contract append key-value pair
                        self.optionDataBySymbol[contract.Symbol.Value]=[[
                        contract.TheoreticalPrice,
                        contract.BidPrice, 
                        contract.AskPrice ,
                        contract.Volume
                        ]]
                        #Initialize the first instance of our LastPrice Dict 
                        self.LastPrice[contract.Symbol.Value]=[
                        #str(algorithm.Time),
                        contract.TheoreticalPrice,
                        contract.BidPrice, 
                        contract.AskPrice,
                          contract.Volume
                        ]
                    else:
                        #If we have already saved our contract append the new datapoint 
                        self.optionDataBySymbol[contract.Symbol.Value].append([ 
                        contract.TheoreticalPrice,
                        contract.BidPrice,
                       contract.AskPrice,
                         contract.Volume
                        ])
                        #Update our LastPrice Dictionary 
                        self.LastPrice[contract.Symbol.Value]=[
                        contract.TheoreticalPrice,
                        contract.BidPrice, 
                        contract.AskPrice ,
                          contract.Volume
                        ]
                #Time-Adjusts for stale data
                k=0
                for x in self.optionDataBySymbol:
                        temp=(len(self.optionDataBySymbol[x]))
                        if temp>k:
                            k=temp
                for x in self.optionDataBySymbol:
                    while len(self.optionDataBySymbol[x])<k:
                        self.optionDataBySymbol[x].append(self.LastPrice[x])
                    
         #Save all of our Price data to ObjectStore which we can analyze in a research notebook                
        if self.algorithm.endOfDay==True:
            dump=json.dumps(self.optionDataBySymbol)
            algorithm.ObjectStore.Save("MyObject", dump)    
            self.algorithm.endOfDay=False
        return insights
        
    def OnSecuritiesChanged(self, algorithm, changes):
        addedSymbols = [ x.Symbol for x in changes.AddedSecurities if (x.Symbol not in self.symbolDataBySymbol and x.Symbol.SecurityType ==SecurityType.Equity)]
        if len(addedSymbols) == 0: return
        for symbol in addedSymbols:
            self.symbolDataBySymbol[symbol] = SymbolData(symbol, algorithm)
            self.option = algorithm.AddOption(symbol)
            self.option.SetFilter(lambda universe: universe.Strikes(-2, 2).Expiration(timedelta(0), timedelta(180)))
            #Sets option filter to 2 strikes each direction, expiration 180 days out
class SymbolData:  
     def __init__(self, symbol, algorithm):
         self.Symbol = symbol