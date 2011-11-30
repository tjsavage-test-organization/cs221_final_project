from captureAgents import CaptureAgent
from baselineAgents import ReflexCaptureAgent
from featureHandler import FeatureHandler
import util

class QLearningAgent(ReflexCaptureAgent):
    def __init__(self, index):
        CaptureAgent.__init__(self, index)
        self.firstTurnComplete = False
        self.startingFood = 0
        self.theirStartingFood = 0
        self.discount = .9
        self.featureHandler = FeatureHandler()
        self.agentType = 'basicQLearningAgent'

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
        return self.featureHandler.getFeatureWeights[self.agentType]
    
    def getReward(self, state):
        return 0
        
    def getValue(self, state);
        action = self.chooseAction(state)
        if action == None:
            return 0.0
        return self.evaluate(state, self.getBestAction(state))
    
    def getBestAction(self, state):
        return CaptureAgent.chooseAction(self, state)
    
    def chooseAction(self, state):
        action = CaptureAgent.chooseAction(self, state)
        self.update(state, action, 
        
    def update(self, state, action):
    """
       Should update your weights based on transition
    """
        "*** YOUR CODE HERE ***"
        nextState = 
        features = self.getFeatures(state, action)
        weights = self.getWeights(self, state, action)
        
        correction = (self.getReward(state) + self.discount * self.getValue(nextState)) - self.evaluate(state, action)
        for feature in features.keys():
            weights[feature] += correction * self.getFeatures(state, action)[feature]

        self.featureHandler.updateFeatureWeights(weights)
    """
    Features (not the best features) which have learned weight values stored.
    """
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