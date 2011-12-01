import ast
from agentEnums import AgentEnums 
class FeatureHandler:
    
    
    def readAllFeatureWeights(self):
        try:
            f = open('FeatureWeights.py', 'r')
            for line in f:
                partitionedLine = line.partition(' = ')
                name = partitionedLine[0]
                features = ast.literal_eval(partitionedLine[2])
                self.allFeatureVectors[name] = features
            
            f.close()
        except:
            print "No FeatureWeights.py file present"
            
    
    def __init__(self):
        self.allFeatureVectors = {}
        self.readAllFeatureWeights()
    
    def writeFeatureVector(self):
        
        f = open('FeatureWeights.py' , 'w')
        for name, features in self.allFeatureVectors.items():
            f.write(name + ' = ' + str(features))
        f.close()
    
    def nameForAgent(agentType):
        return str(AgentEnums(agentType))
            
    def updateFeatureWeights(self, features, agentType):
        self.allFeatureVectors[nameForAgent(agentType)] = features
        self.writeFeatureVector()
    
    def getFeatureWeights(self, agentType):
        return self.allFeatureVectors[nameForAgent(agentType)]
    
    
