import sys


class FeatureWriter:
    
    def __init__(self, agentName):
        self.agentName = agentName
    
    def writeFeatureVector(self, features):
        f = open(self.agentName + '.py' , 'w')
        f.write(self.agentName + 'Weights = ' + str(features))
        f.close()
