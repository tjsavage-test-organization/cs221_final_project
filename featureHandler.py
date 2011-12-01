import ast
from agentEnums import AgentEnums 
from highMutation import cautiousOWeightsDict
import util

class FeatureHandler:
    
    
    def readAllFeatureWeights(self):
        try:
            f = open('FeatureWeights.py', 'r')
            for line in f:
                partitionedLine = line.partition(' = ')
                name = partitionedLine[0]
                features = ast.literal_eval(util.Counter(partitionedLine[2]))
                self.allFeatureVectors[name] = features
            
            f.close()
        except:
            self.updateFeatureWeights(cautiousOWeightsDict, 'basicQlearningAgent')
            
    
    def __init__(self):
        self.allFeatureVectors = util.Counter()
        self.readAllFeatureWeights()
    
    def writeFeatureVector(self):
        
        f = open('FeatureWeights.py' , 'w')
        for name, features in self.allFeatureVectors.items():
            f.write(name + ' = ' + str(features))
        f.close()
    
    def nameForAgent(agentType):
        return str(AgentEnums(agentType))
            
    def updateFeatureWeights(self, features, agentType):
        self.allFeatureVectors[agentType] = features
        self.writeFeatureVector()
    
    def getFeatureWeights(self, agentType):
        return self.allFeatureVectors[agentType]
    
    
