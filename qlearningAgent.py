from captureAgents import CaptureAgent, AgentFactory
from baselineAgents import ReflexCaptureAgent
from featureHandler import FeatureHandler
from capture import GameState
import util, random
import highMutation

class QLearningAgentFactory(AgentFactory):
    def getAgent(self, index):
        return QLearningAgent(index)

class QLearningAgent(ReflexCaptureAgent):
    def __init__(self, index):
        CaptureAgent.__init__(self, index)
        self.firstTurnComplete = False
        self.startingFood = 0
        self.theirStartingFood = 0
        self.discount = .9
        self.alpha = 0.002
        self.featureHandler = FeatureHandler()
        self.agentType = 'basicQLearningAgent'
        self.weights = util.Counter()
    
    def registerInitialState(self, state):
        CaptureAgent.registerInitialState(self, state)
        self.startingFood = len(self.getFood(state).asList())
        self.theirStartingFood = len(self.getFoodYouAreDefending(state).asList())

                                
    
    def getFeatures(self, gameState, action):
        """
            Returns a counter of features for the state
            """
        
        successor = self.getSuccessor(gameState, action)
        position = self.getPosition(gameState)
        
        
        features = self.getMutationFeatures(gameState, action)
        
        #features['isAgentInEnemyTerritory'] = self.isPositionInEnemyTerritory(successor, position)
        #features['isAgentAPacman'] = self.isPacman(successor)
        
        features = util.Counter()
        
        features['degreesOfFreedom'] = len(self.getLegalActions(successor))
        
        
        """features['numberOfEnemies'] = 0
            #for enemy in self.getOpponents(successor):
        features['numberOfEnemies'] += 1"""
          
        
        defenseFoodDists = [self.getMazeDistance(position, foodPos) for foodPos in self.getFoodYouAreDefending(successor).asList()]        
        features['numberOfYourFoodsRemaining'] = len(self.getFoodYouAreDefending(successor).asList())
        features['distanceToClosestYouFood'] = min(defenseFoodDists)
        
        
        foodDists = [self.getMazeDistance(position, foodPos) for foodPos in self.getFood(successor).asList()]
        
        features['numberOfEnemyFoodsRemaining'] = len(self.getFood(successor).asList())
        features['distancetoClosestEnemyFood'] = min(foodDists)
        #features['distanceToClosestFoodSquared'] = min(foodDists) ** 2
        
        return features
    
    def getWeights(self, gameState, action):
        """
            Normally, weights do not depend on the gamestate.    They can be either
            a counter or a dictionary.
            """
        #self.weights['numberOfEnemyFoodsRemaining'] = -10
        #self.weights['distancetoClosestEnemyFood'] = -150
        #self.weights['degreesOfFreedom'] = 25
        return self.weights
    
    def getReward(self, state):
        return self.getScore(state)
    
    
    def getValue(self, state):
        action = self.getBestAction(state)
        if action == None:
            return 0.0
        return self.evaluate(state, action)
    
    
    def getBestAction(self, state):
        return ReflexCaptureAgent.chooseAction(self, state)
    
    
    
    def chooseAction(self, state):
        #return random.choice( state.getLegalActions( self.index ) )
        if not self.firstTurnComplete:
            self.registerInitialState(state)
            self.firstTurnComplete = True
        
        action = ReflexCaptureAgent.chooseAction(self, state)
    
        self.update(state, action, self.getSuccessor(state, action))
      
                
        print 'Features: ' + str(self.getFeatures)
        print 'Weights: ' + str(self.weights)
        print 'Action: ' + str(action) + ' - ' + str(self.getPosition(state)) + '--->' + str(self.getPosition(self.getSuccessor(state, action)))
        return action
    
    
    def dictNormalize(self, dict):
        total = float(sum(dict.values()))
        if total == 0: return
        for key in dict.keys():
            dict[key] = dict[key] / total
    
        return dict
    
    def getStartingWeight(self, feature):
        if feature in highMutation.cautiousOWeightsDict:
            return highMutation.cautiousOWeightsDict[feature]
            
        if feature == 'degreesOfFreedom': return 50
        if feature == 'numberOfYourFoodsRemaining': return 20
        if feature == 'numberOfEnemyFoodsRemaining': return -50
        if feature == 'distancetoClosestEnemyFood': return -100
        if feature == 'distancetoClosestYouFood': return -50
    
        return 0
        
    
    def update(self, state, action, nextState):
        features = self.getFeatures(state, action)
        weights = self.getWeights(state, action)
        
        correction = (self.getReward(state) + self.discount * self.getValue(nextState)) - self.evaluate(state, action)
        print 'CORRECTION: ' + str(correction)
        print 'REWARD: ' + str(self.getReward(state))
        print 'NEXT VALUE: ' + str(self.getValue(nextState))
        print 'EVAL: ' + str(self.evaluate(state, action))
                             
        for feature in features.keys():
            weights[feature] = weights[feature] + correction * self.alpha if feature in weights else self.getStartingWeight(feature)
        
        #weights = self. dictNormalize(weights)
        
        self.weights = weights
        self.featureHandler.updateFeatureWeights(weights, 'basicQlearningAgent')
    
    
    def getMutationFeatures(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        position = self.getPosition(gameState)
        
        
        
        distances = 0.0
        for tpos in self.getTeamPositions(successor):
            distances = distances + abs(tpos[0] - position[0])
        features['xRelativeToFriends'] = distances
    
        enemyX = 0.0
        for epos in self.getOpponentPositions(successor):
            if epos is not None:
                enemyX = enemyX + epos[0]
        features['avgEnemyX'] = distances
        
        foodLeft = len(self.getFoodYouAreDefending(successor).asList())
        features['percentOurFoodLeft'] = foodLeft / self.startingFood
        
        foodLeft = len(self.getFood(successor).asList())
        features['percentTheirFoodLeft'] = foodLeft / self.theirStartingFood
        
        features['IAmAScaredGhost'] = 1.0 if self.isPacman(successor) and self.getScaredTimer(successor) > 0 else 0.0
        
        features['enemyPacmanNearMe'] = 0.0
        minOppDist = 10000
        minOppPos = (0, 0)
        for ep in self.getOpponentPositions(successor):
            # For a feature later on
            if ep is not None and self.getMazeDistance(ep, position) < minOppDist:
                minOppDist = self.getMazeDistance(ep, position)
                minOppPos = ep
            if ep is not None and self.getMazeDistance(ep, position) <= 1 and self.isPositionInTeamTerritory(successor, ep):
                features['enemyPacmanNearMe'] = 1.0
        
        features['numSameFriends'] = 0
        for friend in self.getTeam(successor):
            if successor.getAgentState(self.index).isPacman is self.isPacman(successor):
                features['numSameFriends'] = features['numSameFriends'] + 1
        
        # Compute distance to the nearest food
        foodList = self.getFood(successor).asList()
        if len(foodList) > 0: # This should always be True,    but better safe than sorry
            minDiffDistance = min([1000] + [self.getMazeDistance(position, food) - self.getMazeDistance(minOppPos, food) for food in foodList if minOppDist < 1000])
            features['blockableFood'] = 1.0 if minDiffDistance < 1.0 else 0.0
        return features



