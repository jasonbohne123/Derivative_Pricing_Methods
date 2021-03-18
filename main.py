from Execution.ImmediateExecutionModel import ImmediateExecutionModel
from Portfolio.EqualWeightingPortfolioConstructionModel import EqualWeightingPortfolioConstructionModel
from QuantConnect.Securities.Option import OptionPriceModels
from QuantConnect.Securities.Option import ConstantQLRiskFreeRateEstimator
from QuantConnect.Securities.Option import Option
import optionsalpha

class OptionDataGenerator(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2020,11,16)  # Set Start Date
        self.SetEndDate(2021,1,15)
        self.SetCash(100000)  # Set Strategy Cash
        self.SetTimeZone(TimeZones.Chicago)
        self.SetSecurityInitializer(self.CustomSecurityInitializer) #Set our custom security intializer below
        self.variable=True
        self.endOfDay=False
        
        self.SetExecution(NullExecutionModel())
        self.SetPortfolioConstruction(NullPortfolioConstructionModel())
        self.SetRiskManagement(NullRiskManagementModel())
        self.AddAlpha(optionsalpha.alpha(self)) #Add our Options Alpha Model

        symbols = [ Symbol.Create("SPY", SecurityType.Equity, Market.USA) ]
        self.SetUniverseSelection( ManualUniverseSelectionModel(symbols) )
        self.UniverseSettings.Resolution = Resolution.Minute #Minute resolution for options
        self.UniverseSettings.FillForward = True 
        self.UniverseSettings.ExtendedMarketHours = False #Does not takes in account after hours data
        self.UniverseSettings.MinimumTimeInUniverse = 1 
        self.UniverseSettings.Leverage=2 
        self.Settings.FreePortfolioValuePercentage = 0.5
  
        
        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.At(14,59), self.checktwo)
        if self.ObjectStore.ContainsKey("MyObject"):
            self.ObjectStore.Delete("MyObject")
    
    def checktwo(self):
        self.endOfDay=True
        
    def OnData(self, slice):
        if self.IsWarmingUp: return
    
    def CustomSecurityInitializer(self, security):
        #Intialize each security's prices 
        security.SetDataNormalizationMode(DataNormalizationMode.Raw)
        if security.Type == SecurityType.Equity:
            #for equity intialize volatility model and perform history call
            security.VolatilityModel = StandardDeviationOfReturnsVolatilityModel(60)
            history = self.History(security.Symbol, 61, Resolution.Daily)
            if history.empty or 'close' not in history.columns:
                return
            for time, row in history.loc[security.Symbol].iterrows():
                trade_bar = TradeBar(time, security.Symbol, row.open, row.high, row.low, row.close, row.volume)    
                security.VolatilityModel.Update(security, trade_bar)
        elif security.Type == SecurityType.Option:
            #Intialize pricing method for backtest
            security.PriceModel = OptionPriceModels.BinomialCoxRossRubinstein()