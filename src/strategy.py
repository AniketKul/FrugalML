#Copyright 2020 Lingjiao Chen, version 0.1.
#All rights reserved.
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.

import numpy as np
import pandas as pd
import jsonpickle
class Strategy(object):
    """ Strategy for calling ML services
    """
    def  __init__(self ):
        self.MLAPIsoutput = dict()
        self.MLAPIperformance = dict()
        self.strategy = list()
        self.num_test = 0
        self.num_train = 0
    def trainstrategy(self):
        raise NotImplementedError # TODO
    
    def loadstrategy(self,strategypath,
                     budgetpath):
        policy_handle = open(strategypath,'r')
        data = policy_handle.readlines()
        policy_list = list()
        for www in range(len(data)):
            policy_list.append(jsonpickle.decode(data[www]))
        policy_handle.close() 
        self.budgetlist = np.loadtxt(budgetpath)
        self.strategy = policy_list
        return policy_list
    
    def setbudget(self,budget):
        if(budget>self.budgetlist[-1]):
            self.policyid = len(self.budgetlist)-1
        for i in range(len(self.budgetlist)):
            if(budget<self.budgetlist[i]):
                self.policyid = i       
                break
        s = self.strategy[self.policyid]
        self.s = s
        if(s[4]=='one_model'):
            baseindex = s[3] # base service index
            self.baseid = self.indexIDDict[baseindex]
        else:
            print('model approach is',s)
            raise NotImplementedError # TODO

    def savestrategy(self, strategypath):
        raise NotImplementedError # TODO

    def evalperformance(self):
        policyid = self.policyid
        s = self.strategy[policyid]
        avg_acc = 0
        avg_cost = 0
        print('model is',s)
        if(s[4]=='one_model'): # Always use one model as the base
            baseindex = s[3] # base service index
            baseID = self.indexIDDict[baseindex]
            self.baseid = baseID
            for i in range(self.num_test):
                avg_cost += self.MLAPIsoutput[baseID]['cost']
                baseconf = self.MLAPIsoutput[baseID]['confidence'][i]
                baselabel = int(self.MLAPIsoutput[baseID]['predlabel'][i])
                basereward = self.MLAPIsoutput[baseID]['reward'][i]
                thres = s[0][baselabel][2] # the confidence threshold
                if(thres<baseconf):
                    avg_acc += basereward
                else:
                    dist = s[0][baselabel][0]
                    dist = [ (j>0) * j for j in dist ]
                    #print('prob is', dist)
                    addonindex = np.random.choice(np.arange(0,0+len(dist)),p=dist)
                    if(addonindex>=baseindex):
                        addonindex += 1
                    addonID = self.indexIDDict[addonindex]
                    #print('add-on id is',addonID)
                    #print('add on id',addonID)
                    avg_acc += self.MLAPIsoutput[addonID]['reward'][i]
                    avg_cost += self.MLAPIsoutput[addonID]['cost']
            avg_cost /= self.num_test
            avg_acc /= self.num_test
            return avg_acc, avg_cost
        else:
            raise NotImplementedError # TODO
        return 0, 0
        
    def loadtestdata(self, testpath):
        path1 = testpath+'/Model'
        path3 = '_PredictedLabel.txt'
        path5 = '_Reward.txt'
        path7 = '_Confidence.txt'
        loadpath = testpath+'/meta.csv'
        metainfo = pd.read_csv(loadpath)
        self.indexIDDict = dict()
        for i in range(len(metainfo)):
            data = dict()
            modelID = metainfo.iloc[i]['Index']
            self.indexIDDict[i] = metainfo.iloc[i]['Index']
            c = metainfo.iloc[i]['Cost per 10k images']
            data['cost'] = float(c)
            loadpath = path1+str(modelID)+path3
            data['predlabel'] = np.loadtxt(loadpath)
            loadpath = path1+str(modelID)+path5
            data['reward'] = np.loadtxt(loadpath)
            loadpath = path1+str(modelID)+path7
            data['confidence'] = np.loadtxt(loadpath)
            self.MLAPIsoutput[modelID] = data   
            self.num_test = len(data['predlabel'])
        return 0
    
    def getbaseid(self):
        return self.baseid

    def getdecision(self,base_pred):
        decision = dict()
        baseconf = base_pred['confidence']
        baselabel = base_pred['label']
        baseindex = self.s[3] # base service index
        thres = self.s[0][baselabel][2]
        if(thres<baseconf):
            decision['accept_base'] = True
        else:
            decision['accept_base'] = False
            dist = self.s[0][baselabel][0]
            addonindex = np.random.choice(np.arange(0,0+len(dist)),p=dist)
            if(addonindex>=baseindex):
                addonindex += 1
            addonID = self.indexIDDict[addonindex]
            decision['addon_API'] = addonID
        return decision
        
    def loadtraindata(self, trainpath):
        raise NotImplementedError # TODO

def main():
    MyStrategy = Strategy()
    MyStrategy.loadtestdata(testpath='../dataset/mlserviceperformance_CONLL_single')
    MyStrategy.loadstrategy(strategypath='../output/CONLL_split_True_trainratio_0.5_randseed_1_testeval_True_optname_FrugalML_policy.txt',
                            budgetpath='../output/CONLl_split_True_trainratio_0.5_randseed_1_testeval_True_optname_FrugalML_budget.txt')
    MyStrategy.setbudget(29)
    print( 'base API is', MyStrategy.getbaseid())
    base_pred = dict()
    base_pred['label'] = 1
    base_pred['confidence'] = 0.9
    print('decision is', MyStrategy.getdecision(base_pred))
    print('policy id is',MyStrategy.policyid)
    print(MyStrategy.evalperformance())
    return 0
        
if __name__== "__main__":
    main()