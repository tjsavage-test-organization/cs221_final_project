from captureAgents import CaptureAgent, AgentFactory
from baselineAgents import ReflexCaptureAgent, OffensiveReflexAgent
from featureHandler import FeatureHandler
from capture import GameState
from game import Directions

import util, random
import highMutation, regularMutation

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
            return AggressiveQLearningAgent(index)
        elif agentStr == 'defense':
            return DefensiveQLearningAgent(index)
        else:
            raise Exception("No staff agent identified by " + agentStr)


class QLearningAgent(ReflexCaptureAgent):
    def __init__(self, index):
        ReflexCaptureAgent.__init__(self, index)
        self.discount = .9
        self.featureHandler = FeatureHandler()
        self.agentType = 'basicQlearningAgent'
        self.prevState = None
        self.prevAction = None
        
    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        self.prevState = gameState
        self.prevAction = None

    def getFeatures(self, gameState, action):
        """
        Returns a counter of features for the state
        """
        features = self.getMutationFeatures(gameState, action)
        return features

    def getWeights(self, gameState, action):
        """
        Normally, weights do not depend on the gamestate.    They can be either
        a counter or a dictionary.
        """
        weights = self.featureHandler.getFeatureWeights(self.agentType)
        return weights
    
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
        action = ReflexCaptureAgent.chooseAction(self, state)

        self.update(state, action)
    
        return action
        
        
    def update(self, state, action):
        nextState = state.generateSuccessor(self.index, action)
        features = self.getFeatures(state, action)
        weights = util.Counter(self.getWeights(state, action))
        
        correction = .01 * (self.getReward(state) + self.discount * self.getValue(nextState)) - self.evaluate(state, action)
        for feature in features.keys():
            weights[feature] += correction * self.getFeatures(state, action)[feature]
        if self.index == 2:
            print weights
        weights.normalize()
        self.featureHandler.updateFeatureWeights(weights, self.agentType)

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

class AggressiveQLearningAgent(QLearningAgent):
    def getFeatures(self, gameState, action):
        features = self.getMutationFeatures(gameState, action)
        successor = self.getSuccessor(gameState, action)
    
        features['successorScore'] = self.getScore(successor)
        
        # Compute distance to the nearest food
        foodList = self.getFood(successor).asList()
        features['numFood'] = len(foodList)
        if len(foodList) > 0: # This should always be True,  but better safe than sorry
            myPos = successor.getAgentState(self.index).getPosition()
            minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
            features['distanceToFood'] = minDistance
        return features
    
    def getWeights(self, gameState, action):
        """
        Normally, weights do not depend on the gamestate.    They can be either
        a counter or a dictionary.
        """
        weights = self.featureHandler.getFeatureWeights(self.agentType)
        weights['successorScore'] = 1.5
        # Always eat nearby food
        weights['numFood'] = -1000
        # Favor reaching new food the most
        weights['distanceToFood'] = -5
        return weights

class DefensiveQLearningAgent(QLearningAgent):
    def getFeatures(self, gameState, action):
        features = self.getMutationFeatures(gameState, action)
        successor = self.getSuccessor(gameState, action)
    
        myState = successor.getAgentState(self.index)
        myPos = myState.getPosition()
    
        # Computes whether we're on defense (1) or offense (0)
        features['onDefense'] = 1
        if myState.isPacman: features['onDefense'] = 0
    
        # Computes distance to invaders we can see
        enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
        invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
        features['numInvaders'] = len(invaders)
        if len(invaders) > 0:
            dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
            features['invaderDistance'] = min(dists)
    
        if action == Directions.STOP: features['stop'] = 1
        rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        if action == rev: features['reverse'] = 1
        
        foodList = self.getFoodYouAreDefending(successor).asList()
        distance = 0
        for food in foodList:
            distance = distance + self.getMazeDistance(myPos, food)
        features['totalDistancesToFood'] = distance
    
        return features

    def getWeights(self, gameState, action):
        weights = regularMutation.goalieDWeightsDict
        weights['numInvaders'] = -100
        weights['onDefense'] = 100
        weights['invaderDistance'] = -1.5
        weights['totalDistancesToFood'] = -0.1
        weights['stop'] = -1
        weights['reverse'] = -1
        return weights
    