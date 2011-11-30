import ast
import AgentEnums

class FeatureHandler:
    
    
    def readAllFeatureWeights(self):
        f = open('FeatureWeights.py', 'r')
        for line in f:
            partitionedLine = line.partition(' = ')
            name = partitionedLine[0]
            features = ast.literal_eval(partitionedLine[2])
            self.allFeatureVectors[name] = features
        
        f.close()
            
    
    def __init__(self):
        self.allFeatureVectors = {}
        self.agentType = AgentEnums(agentType)
        self.readAllFeatureWeights()
    
    def updateFeatureWeights(self, features):
        self.allFeatureVectors[str(self.agentType)] = features
        self.writeFeatureVector()
    
    def getFeatureWeights(self, agentType):
        return self.allFeatureVectors[self.agentName]
    
    def writeFeatureVector(self):
        
        f = open('FeatureWeights.py' , 'w')
        for name, features in self.allFeatureVectors.items():
            f.write(name + ' = ' + str(features))
        f.close()
