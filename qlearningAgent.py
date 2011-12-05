from captureAgents import CaptureAgent, AgentFactory
from baselineAgents import ReflexCaptureAgent
from featureHandler import FeatureHandler
from capture import GameState
import util, random
import highMutation

class QLearningAgentFactory(AgentFactory):
    def __init__(self, isRed, first='offense', second='defense', third='offense', rest='offense', **args):
        AgentFactory.__init__(self, isRed)
        self.agents = [first, second, third]
        self.rest = rest

    def getAgent(self, index):
        if len(self.agents) > 0:
            return self.choose(self.agents.pop(0), index)
        else:
            return self.choose(self.rest, index)

    def choose(self, agentStr, index):
        if agentStr == 'offense':
            return QLearningAgent(index)
        else:
            return DefensiveQLearningAgent(index)

class QLearningAgent(ReflexCaptureAgent):
    targetedLocations = []
    
    def __init__(self, index):
        CaptureAgent.__init__(self, index)
        self.firstTurnComplete = False
        self.startingFood = 0
        self.theirStartingFood = 0
        self.discount = .9
        self.alpha = 0.002
        self.featureHandler = FeatureHandler()
        self.agentType = 'basicQLearningAgent'
        self.weights = None
        self.explorationRate = 0.3
    
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
        nextPosition = self.getPosition(successor)
        nextPositionAsInt = self.getPositionAsInt(successor)
        
        
        #oldFeatures = self.getMutationFeatures(gameState, action)
        
        #features['isAgentInEnemyTerritory'] = self.isPositionInEnemyTerritory(successor, position)
        #features['isAgentAPacman'] = self.isPacman(successor)
        
        features = util.Counter()
        #for oldFeature, value in oldFeatures.items():
            #features[oldFeature] = value
        
        #features['degreesOfFreedom'] = len(self.getLegalActions(successor))
        
    
        """avgFriendDist = 0.0
        for fpos in self.getTeamPositions(successor):
            avgFriendDist += self.getMazeDistance(position, fpos)
        
        avgFriendDist /= (len(self.getTeam(gameState)) - 1)
         """   
        features['avgFriendDist'] = sum([self.getMazeDistance(position, fpos) for fpos in self.getTeamPositions(successor)]) / (len(self.getTeam(gameState)) - 1)
        
        """features['numberOfEnemies'] = 0
            #for enemy in self.getOpponents(successor):
        features['numberOfEnemies'] += 1"""
          
        
       # defenseFoodDists = [self.getMazeDistance(nextPosition, foodPos) for foodPos in self.getFoodYouAreDefending(successor).asList()]        
        #features['numberOfYourFoodsRemaining'] = len(self.getFoodYouAreDefending(successor).asList())
        #features['distanceToClosestYouFood'] = min(defenseFoodDists)
        
        features['eatingFood'] = 1.0 if self.isPacman(successor) and gameState.hasFood(nextPositionAsInt[0], nextPositionAsInt[1]) else 0.0
        
        #features['notMoving'] = 1.0 if position == nextPosition else 0.0
        
        foodDists = [self.getMazeDistance(nextPosition, foodPos) for foodPos in self.getFood(successor).asList()]
        
        features['numberOfEnemyFoodsRemaining'] = len(self.getFood(successor).asList())
        features['distancetoClosestEnemyFood'] = 0 if features['eatingFood'] > 0 else min(foodDists)
        #features['distanceToClosestFoodSquared'] = min(foodDists) ** 2
        print "FEATURES: ", features
        return features
    
    def getWeights(self, gameState, action):
        """
            Normally, weights do not depend on the gamestate.    They can be either
            a counter or a dictionary.
            """
        #self.weights['numberOfEnemyFoodsRemaining'] = -10
        #self.weights['distancetoClosestEnemyFood'] = -150
        #self.weights['degreesOfFreedom'] = 25
        
        if self.weights == None:
            self.weights = util.Counter()
                #for feature in self.getFeatures(gameState, 'Stop'):
            #self.weights[feature] = self.getStartingWeight(feature)
            self.weights = self.featureHandler.getFeatureWeights('basicQlearningAgent')
            print 'WEIGHTS'
            print self.weights
        
        return self.weights
    
    def getReward(self, state):
        prevState = self.getPreviousObservation()
        
        if prevState == None: return 0
        
        reward = 0
        if self.getPosition(state) in self.getFood(prevState).asList():
            reward += 10
            
        #reward += (len(self.getFood(state).asList()) - len(self.getFood(prevState).asList()))
        
        prevPosition = self.getPosition(prevState)
        currPosition = self.getPosition(state)
        if self.getMazeDistance(prevPosition, currPosition) > 1:
            reward -= 40
        
        return reward
    
    
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
        

        """
        Picks among the actions with the highest Q(s,a).
        """
        actions = state.getLegalActions(self.index)
    
        if util.flipCoin(self.explorationRate):
            return random.choice(actions)
        
        # You can profile your evaluation time by uncommenting these lines
        # start = time.time()
        values = [(a, self.evaluate(state, a)) for a in actions]
        # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)
    
    
        #print 'VALUES: ' + str(values)  
        maxValue = max(values, key=lambda val : val[1])
        bestActions = [a for a, v in zip(actions, values) if v == maxValue]
    
        action = random.choice(bestActions)
                
        self.update(state, action, self.getSuccessor(state, action))
      
                
        #print 'Features: ' + str(self.getFeatures)
        #print 'Weights: ' + str(self.weights)
        #print 'Action: ' + str(action) + ' - ' + str(self.getPosition(state)) + '--->' + str(self.getPosition(self.getSuccessor(state, action)))
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
            
        if feature == 'degreesOfFreedom': return 0.5
        if feature == 'numberOfYourFoodsRemaining': return 0.25
        if feature == 'numberOfEnemyFoodsRemaining': return -0.25
        if feature == 'distancetoClosestEnemyFood': return -0.5
        if feature == 'distanceToClosestYouFood': return -0.4
        if feature == 'eatingFood': return 1
        if feature == 'notMoving': return -1
        if feature == 'avgFriendDist': return 0.25
        
        return 0
        
    
    def update(self, state, action, nextState):
        features = self.getFeatures(state, action)
        weights = self.getWeights(state, action)
        
        correction = (self.getReward(state) + self.discount * self.getValue(nextState)) - self.evaluate(state, action)
        #print 'CORRECTION: ' + str(correction)
        #print 'REWARD: ' + str(self.getReward(state))
        #print 'NEXT VALUE: ' + str(self.getValue(nextState))
        #print 'EVAL: ' + str(self.evaluate(state, action))
                             
        for feature in features.keys():
            weights[feature] = weights[feature] + correction * self.alpha if feature in weights else self.getStartingWeight(feature)
        #weights[feature] = self.getStartingWeight(feature)
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

class DefensiveQLearningAgent(QLearningAgent):
    def getFeatures(self, gameState, action):
        """
            Returns a counter of features for the state
            """
        
        successor = self.getSuccessor(gameState, action)
        position = self.getPosition(gameState)
        nextPosition = self.getPosition(successor)
        nextPositionAsInt = self.getPositionAsInt(successor)
        
        features = util.Counter()
        #oldFeatures = self.getMutationFeatures(gameState, action)
        
        features['isAgentInEnemyTerritory'] = self.isPositionInEnemyTerritory(successor, position)
        #features['isAgentAPacman'] = self.isPacman(successor)
        
        features = util.Counter()
        #for oldFeature, value in oldFeatures.items():
            #features[oldFeature] = value
        
        #features['degreesOfFreedom'] = len(self.getLegalActions(successor))
        
    
        """avgFriendDist = 0.0
        for fpos in self.getTeamPositions(successor):
            avgFriendDist += self.getMazeDistance(position, fpos)
        
        avgFriendDist /= (len(self.getTeam(gameState)) - 1)
         """   
        features['avgFriendDist'] = sum([self.getMazeDistance(position, fpos) for fpos in self.getTeamPositions(successor)]) / (len(self.getTeam(gameState)) - 1)
        
        """features['numberOfEnemies'] = 0
            #for enemy in self.getOpponents(successor):
        features['numberOfEnemies'] += 1"""
          
        
        defenseFoodDists = [self.getMazeDistance(nextPosition, foodPos) for foodPos in self.getFoodYouAreDefending(successor).asList()]        
        features['numberOfYourFoodsRemaining'] = len(self.getFoodYouAreDefending(successor).asList())
        features['distanceToClosestYouFood'] = min(defenseFoodDists)
        
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
        
        #features['notMoving'] = 1.0 if position == nextPosition else 0.0
        
        
        #features['distanceToClosestFoodSquared'] = min(foodDists) ** 2
        print "FEATURES: ", features
        return features

    def getWeights(self, gameState, action):
        """
            Normally, weights do not depend on the gamestate.    They can be either
            a counter or a dictionary.
            """
        #self.weights['numberOfEnemyFoodsRemaining'] = -10
        #self.weights['distancetoClosestEnemyFood'] = -150
        #self.weights['degreesOfFreedom'] = 25
        
        if self.weights == None:
            self.weights = util.Counter()
                #for feature in self.getFeatures(gameState, 'Stop'):
            #self.weights[feature] = self.getStartingWeight(feature)
            self.weights = self.featureHandler.getFeatureWeights('defensiveQLearningAgent')
            print self.weights
        
        return self.weights