#!/usr/bin/env python

'''
Base classes and tools to simulate servicing of a requests' flow by a forwarding company
'''
__author__  = 'Vitalii Naumov'
__email__   = 'vitalii.naumov@pk.edu.pl'
__version__ = '1.0'


import numpy as np


class Stochastic:

    def __init__(self, law:str='rect', loc:float=0, scale:float=1):
        self.__law = law
        self.__loc = loc
        self.__scale = scale
    
    def __rect(self):
        return self.__loc + self.__scale * np.random.random()

    def __expon(self):
        return -self.__scale * np.log(np.random.random())

    def __norm(self):
        return np.random.normal(self.__loc, self.__scale)

    def value(self):
        if self.__law == 'expon':
            return self.__expon()
        elif self.__law == 'norm':
            return self.__norm()
        else:
            return self.__rect()


class Request:

    def __init__(self):
        self.appear_time = 0
        self.serviced = False


class RequestsFlow:

    def __init__(self, s_itv:Stochastic=Stochastic(), model_time:float=1):
        self.interval = s_itv
        self.model_time = model_time
        self.requests = []

    @property
    def size(self):
        return len(self.requests)

    def generate(self):
        # reset flow
        self.requests = []
        # generate requests
        t = self.interval.value()
        while t < self.model_time:
            request = Request()
            request.appear_time = t
            self.requests.append(request)
            t += self.interval.value()


class Dispatcher:

    def __init__(self, name:str='Dispatcher', srv_time:Stochastic=Stochastic()):
        self.name = name
        self.service_time = srv_time
        self.requests = []
        self.ready_time = 0

    def is_available(self, t:float) -> bool:
        return self.ready_time <= t
    
    def serve(self, request:Request) -> None:
        request.serviced = True
        self.requests.append(request)
        self.ready_time = request.appear_time + self.service_time.value()


class FreightForwarder:

    rates = {'vat': 0.23, 'profit': 0.12}

    def __init__(self):
        self.dispatchers = []
        self.costs_1h = 0
        self.costs_1h_paid = 0
        self.tariff = 0

    def reset(self) -> None:
        for d in self.dispatchers:
            d.requests = []
            d.ready_time = 0

    def get_dispatcher(self, t:float) -> Dispatcher:
        available = [d for d in self.dispatchers if d.is_available(t)]
        if len(available) == 0: return None
        least_busy = available[0]
        served_requests = len(least_busy.requests)
        for d in available[1:]:
            if len(d.requests) < served_requests:
                served_requests = len(d.requests)
                least_busy = d
        return least_busy

    def serve(self, rf:RequestsFlow) -> dict:
        # simulate servicing process
        for request in rf.requests:
            dispatcher = self.get_dispatcher(request.appear_time)
            if dispatcher: dispatcher.serve(request)
        # calculate finances
        result = {}
        result['income'] = self.tariff * sum([len(d.requests) for d in self.dispatchers])
        result['expenses'] = rf.model_time * self.costs_1h * len(self.dispatchers)
        result['expenses_paid'] = rf.model_time * self.costs_1h_paid # * len(self.dispatchers)
        result['vat_tax'] = self.rates['vat'] * (result['income'] - \
                            result['expenses_paid']) / (1 + self.rates['vat'])
        result['net_profit'] = result['income'] - result['expenses'] - result['vat_tax'] + \
                            self.rates['vat'] * result['expenses_paid'] / (1 + self.rates['vat'])
        result['profit_tax'] = self.rates['profit'] * result['net_profit'] if result['net_profit'] > 0 else 0
        result['profit'] = result['income'] - result['expenses'] - result['vat_tax'] - result['profit_tax']
        return result

