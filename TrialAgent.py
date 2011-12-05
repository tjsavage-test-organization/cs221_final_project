'''
Created on Nov 29, 2011

@author: rorymacqueen
'''
from captureAgents import CaptureAgent
from captureAgents import AgentFactory
import distanceCalculator
import baselineAgents
from baselineAgents import OffensiveReflexAgent
from baselineAgents import DefensiveReflexAgent
from game import Directions
import regularMutation
import random, time, util, math
from featureHandler import FeatureHandler

class TrialAgentFactory(AgentFactory):
    "Returns one keyboard agent and offensive reflex agents"

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
            return TrialAgent(index)
        else:
            return DefensiveTrialAgent(index)

class TrialAgent(DefensiveReflexAgent):
    
    enemyPositions = util.Counter()
    legalPositions = list()
    legalNextPositions = util.Counter()
    firstTurn = True
    distancer = None
    manhattanDistancer = None
    enemyIndices = list()
    allyIndices = list()
    noisyDistances = util.Counter()
    lastSightings = util.Counter()
    discount = .99
    alpha = 0.0002
    featureHandler = FeatureHandler()
    agentType = 'basicQLearningAgent'
    #explorationRate = 0.3
    explorationRate = 0.0
    weights = None
    
    def __init__(self, index):
        DefensiveReflexAgent.__init__(self, index)
        
        
    def registerInitialState(self, gameState):
        DefensiveReflexAgent.registerInitialState(self, gameState)
        self.startingFood = len(self.getFoodYouAreDefending(gameState).asList())
        self.theirStartingFood = len(self.getFood(gameState).asList())
        if TrialAgent.firstTurn:
            TrialAgent.distancer = distanceCalculator.Distancer(gameState.data.layout)
            TrialAgent.manhattanDistancer = distanceCalculator.Distancer(gameState.data.layout)
            TrialAgent.manhattanDistancer.useManhattanDistances()
            TrialAgent.distancer.getMazeDistances()
            TrialAgent.legalPositions = gameState.getWalls().asList(False)
            for pos in TrialAgent.legalPositions:
                TrialAgent.legalNextPositions[pos] = self.getLegalNextPositions(gameState, pos)
            TrialAgent.enemyIndices = self.getOpponents(gameState)
            TrialAgent.allyIndices = self.getTeam(gameState)
            self.initializeUniformly(gameState)
            TrialAgent.firstTurn = False
            
        
    def initializeUniformly(self, gameState):
        
        
        #self.distancer.getMazeDistances()
        "Begin with a uniform distribution over ghost positions."
        
        for enemy in TrialAgent.enemyIndices:
            beliefs = util.Counter();
            for p in TrialAgent.legalPositions:
                beliefs[p] = 1.0
            beliefs.normalize()
            TrialAgent.enemyPositions[enemy] = beliefs
            
    def getPositionDistribution(self, gameState, p, agentIndex):
        
        posDist = util.Counter()
        for i in range(-1, 1):
            newPos = (p[0] + i, p[1])
            if newPos in self.legalPositions:
                posDist[newPos] = 0.001
            
        for j in range(-1, 1):
            newPos = (p[0], p[1] + j)
            if newPos in self.legalPositions:
                posDist[newPos] = 0.001
                
        #posDist.normalize()
        
        return posDist
    
    def getLegalNextPositions(self, gameState, position):
        legalNextPositions = list()
        legalNextPositions.append(position)
        nextPos = (position[0] + 1, position[1])
        if nextPos in TrialAgent.legalPositions: legalNextPositions.append(nextPos)
        nextPos = (position[0] - 1, position[1])
        if nextPos in TrialAgent.legalPositions: legalNextPositions.append(nextPos)
        nextPos = (position[0], position[1] + 1)
        if nextPos in TrialAgent.legalPositions: legalNextPositions.append(nextPos)
        nextPos = (position[0], position[1] - 1)
        if nextPos in TrialAgent.legalPositions: legalNextPositions.append(nextPos)
        
        return legalNextPositions
        
    def getClosestFood(self, gameState, position, foodList):
        distances = [self.getMazeDistance(position, food) for food in foodList]
        i = distances.index(min(distances))
        closestFood = foodList[i]
        return closestFood
    
    def getClosestFriendFood(self, gameState, position):
        foodList = (self.getFoodYouAreDefending(gameState)).asList() 
        return self.getClosestFood(gameState, position, foodList)                                                
    
    def getClosestEnemyFood(self, gameState, position):
        foodList = self.getFood(gameState).asList()
        return self.getClosestFood(gameState, position, foodList)   
    
    def getClosestFoodAll(self, gameState, position):
        foodList = self.getFood(gameState).asList()
        foodList.extend( (self.getFoodYouAreDefending(gameState)).asList() )
        return self.getClosestFood(gameState, position, foodList)  
    
    def nextPositionDist(self, gameState, position):
        allNextPos = util.Counter()
        nextPossiblePos = TrialAgent.getLegalNextPositions(self, gameState, position)
        for nextPos in nextPossiblePos:
            
            closestFoodOfNextPos = self.getClosestFood(gameState, nextPos)
            newDistance = self.getMazeDistance(nextPos, closestFoodOfNextPos)
            allNextPos[nextPos] = newDistance
            #allNextPos[nextPos] = 1
        allNextPos.normalize()
        return allNextPos
        
            
 

    def infer(self, gameState):
        newEnemyP = util.Counter()   
        for enemyIndex, belief in TrialAgent.enemyPositions.items():
            newEnemyP[enemyIndex] = util.Counter()
             
        for p in TrialAgent.legalPositions:
            
            for enemyIndex, beliefs in TrialAgent.enemyPositions.items():
                dist = list()
    
                for ally in TrialAgent.allyIndices:
                
                    myNoisyDistances = TrialAgent.noisyDistances[ally]
                    allyPos = gameState.getAgentPosition(ally)
                    trueDistance = TrialAgent.manhattanDistancer.getDistance(p, allyPos)
                        
                    noisyDistance = myNoisyDistances[enemyIndex]
                    distProb = gameState.getDistanceProb(trueDistance, noisyDistance)
                    if distProb == 0:
                        continue
                    prob =  math.log1p(distProb)  + math.log1p(beliefs[p])
                    
                    dist.append(prob)
                
                
                newEnemyP[enemyIndex][p] = sum(dist)
                
            
        newEnemyPos = util.Counter()
        for enemy, beliefs in newEnemyP.items():
            pos = gameState.getAgentPosition(enemy)
            newBeliefs = util.Counter()
            if pos is not None: 
                intPos = ( int(pos[0]), int(pos[1]) )
                newBeliefs[intPos] = 1
                
            else :    
                newBeliefs = beliefs
            newBeliefs.normalize()
            newEnemyPos[enemy] = newBeliefs
        TrialAgent.enemyPositions = newEnemyPos
            
                
    def trackLastPos(self, gameState):
        for enemy, dist in TrialAgent.enemyPositions.items():
            defPos = gameState.getAgentPosition(enemy)
            if defPos is not None:
                intDefPos = (int(defPos[0]), int(defPos[1]))
                posList = util.Counter()
                posList[intDefPos] = 1.0
                TrialAgent.lastSightings[enemy] = (posList, 0, intDefPos)
            elif TrialAgent.lastSightings[enemy] is not 0:
                posDist = TrialAgent.lastSightings[enemy][0]
                #if enemy is self.enemyIndices[0]: print posDist
                timeSinceObs = TrialAgent.lastSightings[enemy][1]
                posOriginalObs =  TrialAgent.lastSightings[enemy][2]
                newPosDist = util.Counter()
                for pos in posDist :
                    if timeSinceObs < 10:
                        legalNext = TrialAgent.legalNextPositions[pos]
                        probPerState = 1.0/(len(legalNext) + len(posDist))
                        
                        pacman = False
                        for ally in TrialAgent.allyIndices:
                            pacman = gameState.getAgentState(ally).isPacman
                            if pacman: break
                            
                        closestFood = 0
                        if pacman: closestFood = self.getClosestFoodAll(gameState, pos)
                        else: closestFood = self.getClosestFriendFood(gameState, pos)
                        
                        oldFoodDist = self.getMazeDistance(pos, closestFood)
                        for newPos in legalNext:
                            distance = self.getMazeDistance(newPos, closestFood)
                            if distance <= oldFoodDist :
                                newPosDist[newPos] += math.log1p(probPerState) + math.log1p(1.0/(distance + 0.0001))
                        newPosDist.normalize()
                        TrialAgent.lastSightings[enemy] = (newPosDist, timeSinceObs + 1,posOriginalObs )
                    elif timeSinceObs < 20 :
                        maxNumMoves = 1 + int(timeSinceObs/len(TrialAgent.enemyIndices))
                        maxXPos = posOriginalObs[0] + maxNumMoves
                        minXPos = posOriginalObs[0] - maxNumMoves
                        maxYPos = posOriginalObs[1] + maxNumMoves
                        minYPos = posOriginalObs[1] - maxNumMoves
                        for p in TrialAgent.legalPositions:
                            if p[0] < maxXPos + 1 and p[0] > minXPos - 1 and p[1] < maxYPos + 1 and p[1] > minYPos - 1 :
                                newPosDist[p] = 1.0
                        newPosDist.normalize()
                        
                        TrialAgent.lastSightings[enemy] = (newPosDist, timeSinceObs + 1, posOriginalObs)
                    else:
                        TrialAgent.enemyPositions[enemy][pos] += math.log1p(posDist[pos])
                        TrialAgent.enemyPositions[enemy].normalize()
                        TrialAgent.lastSightings[enemy] = 0
                
                    
    def observe(self, gameState):
      
        TrialAgent.noisyDistances[self.index] = gameState.getAgentDistances()
      

    """def getFeatures(self, gameState, action):
        features = self.getMutationFeatures(gameState, action)
        successor = self.getSuccessor(gameState, action)
        
        features['successorScore'] = self.getScore(successor)
        
         #computes territory
        #terr = self.getTerritoryAllies(successor)
        #features['homeTerritory'] = len(terr)
        netDist = self.netDistanceToFriends(successor)
        features['netDistance'] = netDist
        
        if action == Directions.STOP: features['stop'] = 1
        rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        if action == rev: features['reverse'] = 1
        
        # Compute distance to the nearest food
        foodList = self.getFood(successor).asList()
        features['numFood'] = len(foodList)
        if len(foodList) > 0: # This should always be True,  but better safe than sorry
          myPos = successor.getAgentState(self.index).getPosition()
          minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
          features['distanceToFood'] = minDistance
        return features

    def getWeights(self, gameState, action):
        weights = regularMutation.aggressiveDWeightsDict
        weights['successorScore'] = 1.5
        # Always eat nearby food
        weights['numFood'] = -1000
        # Favor reaching new food the most
        weights['distanceToFood'] = -5
        weights['homeTerritory'] = 5
        weights['netDistance'] = 5
        weights['stop'] = -10
        weights['reverse'] = -1
        return weights"""
    
    def netDistanceToFriends(self, gameState):
        friends = self.getTeamPositions(gameState)
        myPos = self.getPosition(gameState)
        netDistance = 0
        for ally in friends:
            netDistance += self.getMazeDistance(ally, myPos)
        return netDistance
        
    def getTerritoryAllies(self, gameState):
        friends = self.getTeamPositions(gameState)
        friendsDist = util.Counter()
        for i in range(len(friends)):
            pos = friends[i]
            dist = util.Counter()
            dist[pos] = 1.0
            friendsDist[i] = dist
        terr = self.getTerritory(gameState, friendsDist)
        return terr
    #Returns all food items (and capsules) that I am closer to than any of my enemies:
        
    def getTerritoryEnemies(self, gameState):
        terr = self.getTerritory(gameState, TrialAgent.enemyPositions)    
        return terr
    
    def getTerritory(self, gameState, others):
        foodList = self.getFood(gameState).asList()
        #foodList.extend( (self.getFoodYouAreDefending(gameState)).asList() )
        territory = list()
        myPos = self.getPosition(gameState)
        for food in foodList:
            myDistance = self.getMazeDistance(food, myPos)
            meClosest = True
            for otherIndex, dist in others.items():
                mostLikelyPos = dist.argMax()
                
                hisDistance = self.getMazeDistance(mostLikelyPos, food)
                #if hisDistance < 20: print "distance between " + str(mostLikelyPos) + " and " + str(food) + " is " + str(hisDistance) 
                
                if myDistance > hisDistance:
                    meClosest = False 
                    break
            if meClosest: territory.append(food)
            
        return territory
        
        
    def evaluateDeep(self, gameState, depth):
        actions = gameState.getLegalActions(self.index)
        values = list()
        maxValue = -9999999999999999
        bestAction = None
        for action in actions:
            valueForAction = 0
            if depth == 3:
                valueForAction = self.evaluate(gameState, action)
                print "action " + str(action) + " value " + str(valueForAction) 
        
            else:
                succ = self.getSuccessor(gameState, action)
                valueForAction = self.evaluateDeep(succ, depth+1)[1] 
                currentPosValue = self.evaluate(gameState, action)
                valueForAction += currentPosValue
                print "-------------------"
            if valueForAction >= maxValue:
                maxValue = valueForAction
                bestAction = action
               
        if depth==0: print "action " + str(bestAction) + " max value " + str(maxValue) 
        return (bestAction, maxValue)
    
    def getMostLikelyPositionForEnemy(self, enemy):
        return max([(p, TrialAgent.enemyPositions[enemy][p]) for p in TrialAgent.legalPositions], key = lambda x : x[1])[0]
    
    
    def getClosestEnemyDist(self, gameState):

        enemyPositions = [self.getMostLikelyPositionForEnemy(enemy) for enemy in TrialAgent.enemyIndices]
        closestEnemy = min(enemyPositions, key = lambda ePos : self.getMazeDistance(self.getPosition(gameState), ePos))
        return self.getMazeDistance(self.getPosition(gameState), closestEnemy)
        
        
    
    
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
        
        features['degreesOfFreedom'] = len(self.getLegalActions(successor))
        
        
        """avgFriendDist = 0.0
            for fpos in self.getTeamPositions(successor):
            avgFriendDist += self.getMazeDistance(position, fpos)
            
            avgFriendDist /= (len(self.getTeam(gameState)) - 1)
            """   
        #features['avgFriendDist'] = sum([self.getMazeDistance(position, fpos) for fpos in self.getTeamPositions(successor)]) / (len(self.getTeam(gameState)) - 1)
        
            
        features['successorScore'] = self.getScore(successor)
                
        #computes territory
        terr = self.getTerritoryAllies(successor)
        features['homeTerritory'] = len(terr)
        netDist = self.netDistanceToFriends(successor)
        #features['netDistance'] = netDist
                
        rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        features['reverse'] = 1.0 if action == rev else 0.0
                
            # Compute distance to the nearest food
        """foodList = self.getFood(successor).asList()
        features['numFood'] = len(foodList)
        if len(foodList) > 0: # This should always be True,  but better safe than sorry
            myPos = successor.getAgentState(self.index).getPosition()
            minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
            features['distanceToFood'] = minDistance"""
                
        defenseFoodDists = [self.getMazeDistance(nextPosition, foodPos) for foodPos in self.getFoodYouAreDefending(successor).asList()]        
        features['numberOfYourFoodsRemaining'] = len(self.getFoodYouAreDefending(successor).asList())
        
        #print 'OUR FOOD LEFT: ' + str(features['numberOfYourFoodsRemaining'])
        
        features['distanceToClosestYouFood'] = min(defenseFoodDists)
        
        features['eatingFood'] = 1.0 if self.isPacman(successor) and gameState.hasFood(nextPositionAsInt[0], nextPositionAsInt[1]) else 0.0
        
        features['notMoving'] = 1.0 if position == nextPosition else 0.0
        
        foodDists = [self.getMazeDistance(nextPosition, foodPos) for foodPos in self.getFood(successor).asList()]
        
        features['numberOfEnemyFoodsRemaining'] = len(self.getFood(successor).asList())
        
        features['distancetoClosestEnemyFood'] = 0 if features['eatingFood'] > 0 else min(foodDists)
        
        features['distanceToClosestEnemyAsGhost'] = self.getClosestEnemyDist(gameState) if self.isGhost(gameState) else 0.0
        
        features['distanceToClosestEnemyAsPacman'] = self.getClosestEnemyDist(gameState) if self.isPacman(gameState) else 0.0
        
        features['enemyGhostClose'] = 1.0 if features['distanceToClosestEnemyAsPacman'] < 4 and features['distanceToClosestEnemyAsPacman'] > 0 else 0.0
        
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
        
        if TrialAgent.weights == None:
            TrialAgent.weights = util.Counter()
                #for feature in self.getFeatures(gameState, 'Stop'):
            #TrialAgent.weights[feature] = self.getStartingWeight(feature)
            TrialAgent.weights = TrialAgent.featureHandler.getFeatureWeights('basicQlearningAgent')
            print 'WEIGHTS'
            print TrialAgent.weights
        
        return TrialAgent.weights
    
    def getReward(self, state):
        prevState = self.getPreviousObservation()
        
        if prevState == None: return 0
        
        reward = 0
        
        reward += (len(self.getFood(state).asList()) - len(self.getFood(prevState).asList())) * 25
        
        reward += (len(self.getCapsules(state)) - len(self.getCapsules(prevState))) * 25
        
        reward -= self.getScore(state)

        
        #reward -= (len(self.getFoodYouAreDefending(state).asList()) - len(self.getFoodYouAreDefending(prevState).asList())) * 5
        
        return reward
    
    
    def getValue(self, state):
        action = self.getBestAction(state)
        if action == None:
            return 0.0
        return self.evaluate(state, action)
    
    
    def getBestAction(self, state):
        return DefensiveReflexAgent.chooseAction(self, state)
    
    
    
    """ def chooseAction(self, state):
        #return random.choice( state.getLegalActions( self.index ) )
        if not self.firstTurnComplete:
            self.registerInitialState(state)
            self.firstTurnComplete = True
        
        
    
            #Picks among the actions with the highest Q(s,a).
            
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
        return action"""
    
    
    def getStartingWeight(self, feature):
        if feature in regularMutation.aggressiveDWeightsDict:
           return regularMutation.aggressiveDWeightsDict[feature]
        
        if feature == 'degreesOfFreedom': return 5
        if feature == 'numberOfYourFoodsRemaining': return 20
        if feature == 'numberOfEnemyFoodsRemaining': return -20
        if feature == 'distancetoClosestEnemyFood': return -25
        if feature == 'distanceToClosestYouFood': return -5
        if feature == 'eatingFood': return 250
        if feature == 'notMoving': return -25
#if feature == 'avgFriendDist': return 0.25
        if feature == 'successorScore': return 1.25
        if feature == 'homeTerritory': return 10
        if feature == 'reverse': return -10
        if feature == 'distanceToClosestEnemyAsGhost': return -25
        if feature == 'distanceToClosestEnemyAsPacman': return 2.5
        if feature == 'enemyGhostClose': return 35
        
        return 0
    
    
    def update(self, state, action, nextState):
        features = self.getFeatures(state, action)
        weights = self.getWeights(state, action)
        
        correction = (self.getReward(state) + TrialAgent.discount * self.getValue(nextState)) - self.evaluate(state, action)
        """print 'CORRECTION: ' + str(correction)
        print 'REWARD: ' + str(self.getReward(state))
        print 'NEXT VALUE: ' + str(self.getValue(nextState))
        print 'EVAL: ' + str(self.evaluate(state, action))"""
        
        for feature in features.keys():
            weights[feature] = weights[feature] + correction * TrialAgent.alpha if feature in weights else self.getStartingWeight(feature)
        #weights[feature] = self.getStartingWeight(feature)
        #weights = self. dictNormalize(weights)
        
        TrialAgent.weights = weights
        TrialAgent.featureHandler.updateFeatureWeights(weights, 'basicQlearningAgent')
        
    def chooseAction(self, gameState):
        #print "index " + str(self.index)
        self.observe(gameState)
        if self.index == TrialAgent.allyIndices[len(TrialAgent.allyIndices) - 1] :
            start = time.time()
            self.infer(gameState)
            self.trackLastPos(gameState)
            
            counters = list()
        
            counters.append(TrialAgent.enemyPositions[self.enemyIndices[0]]) 
            if TrialAgent.lastSightings[self.enemyIndices[0]] is not 0 :
                timeSince = TrialAgent.lastSightings[self.enemyIndices[0]][1]
                if timeSince < 32:
                    toDisplay = TrialAgent.lastSightings[self.enemyIndices[0]][0].copy()
                    counters.append(toDisplay) 
            self.displayDistributionsOverPositions(counters)
            
            """actionValuePair = self.evaluateDeep(gameState, 0)
            print actionValuePair
            return actionValuePair[0]"""
        
        
        
        actions = gameState.getLegalActions(self.index)
            
        if util.flipCoin(TrialAgent.explorationRate):
            return random.choice(actions)
            
            # You can profile your evaluation time by uncommenting these lines
            # start = time.time()
        values = [(a, self.evaluate(gameState, a)) for a in actions]
            # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)
            
            
            #print 'VALUES: ' + str(values)  
        maxValue = max(values, key=lambda val : val[1])
        bestActions = [a for a, v in zip(actions, values) if v == maxValue]
            
        action = random.choice(bestActions)
            
        self.update(gameState, action, self.getSuccessor(gameState, action))
        return action
#        positions = util.Counter()
#        for enemy in TrialAgent.enemyPositions:
#            ghost = enemy[1]
#            mostLikelyPos = ghost.argMax()
#            #print mostLikelyPos
#            distance = TrialAgent.distancer.getDistance(self.getPosition(gameState), mostLikelyPos)
#            #print distance
#            positions[mostLikelyPos] = -1*distance
#        
#        closestGhost = positions.argMax()
#        #print closestGhost
#        closestGhost = (29, 13)
#        allActions = util.Counter();
#        for action in self.getLegalActions(gameState):
#            successorState = gameState.generateSuccessor(self.index, action)
#            successorPosition = self.getPosition(successorState)
#            newDistance = TrialAgent.distancer.getDistance(successorPosition, closestGhost)
#            #print str(self.getPosition(gameState)) +  action + str(newDistance)
#            allActions[action] = -1*newDistance
#        
#        #print (time.time() - start)
#        return allActions.argMax()
        
class DefensiveTrialAgent(TrialAgent):
       def getFeatures(self, gameState, action):
        """
            Returns a counter of features for the state
            """
        
        successor = self.getSuccessor(gameState, action)
        position = self.getPosition(gameState)
        nextPosition = self.getPosition(successor)
        nextPositionAsInt = self.getPositionAsInt(successor)
        
        features = util.Counter()
  
        features['avgFriendDist'] = sum([self.getMazeDistance(position, fpos) for fpos in self.getTeamPositions(successor)]) / (len(self.getTeam(gameState)) - 1)
        
            
        features['successorScore'] = self.getScore(successor)
                
        #computes territory
        terr = self.getTerritoryAllies(successor)
        features['homeTerritory'] = len(terr)
        netDist = self.netDistanceToFriends(successor)
        #features['netDistance'] = netDist
                
        rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        features['reverse'] = 1.0 if action == rev else 0.0
                
            # Compute distance to the nearest food
        """foodList = self.getFood(successor).asList()
        features['numFood'] = len(foodList)
        if len(foodList) > 0: # This should always be True,  but better safe than sorry
            myPos = successor.getAgentState(self.index).getPosition()
            minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
            features['distanceToFood'] = minDistance"""
                
        defenseFoodDists = [self.getMazeDistance(nextPosition, foodPos) for foodPos in self.getFoodYouAreDefending(successor).asList()]        
        features['numberOfYourFoodsRemaining'] = len(self.getFoodYouAreDefending(successor).asList())
        
        #print 'OUR FOOD LEFT: ' + str(features['numberOfYourFoodsRemaining'])
        
        features['distanceToClosestYouFood'] = min(defenseFoodDists)
        
        features['eatingFood'] = 1.0 if self.isPacman(successor) and gameState.hasFood(nextPositionAsInt[0], nextPositionAsInt[1]) else 0.0
        
        #features['notMoving'] = 1.0 if position == nextPosition else 0.0
        
        foodDists = [self.getMazeDistance(nextPosition, foodPos) for foodPos in self.getFood(successor).asList()]
        
        #features['numberOfEnemyFoodsRemaining'] = len(self.getFood(successor).asList())
        
        #features['distancetoClosestEnemyFood'] = 0 if features['eatingFood'] > 0 else min(foodDists)
        
        features['distanceToClosestEnemyAsGhost'] = self.getClosestEnemyDist(gameState) if self.isGhost(gameState) else 0.0
        
        #features['distanceToClosestEnemyAsPacman'] = self.getClosestEnemyDist(gameState) if self.isPacman(gameState) else 0.0
        
        #features['enemyGhostClose'] = 1.0 if features['distanceToClosestEnemyAsPacman'] < 4 and features['distanceToClosestEnemyAsPacman'] > 0 else 0.0
        
        #features['distanceToClosestFoodSquared'] = min(foodDists) ** 2
        
        return features
        
        
              