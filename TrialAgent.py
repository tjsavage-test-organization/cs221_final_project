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
            return TrialAgent(index, True)
        else:
            return TrialAgent(index, False)



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
    discount = .999
    alpha = 0.0003
    featureHandler = FeatureHandler()
    agentType = 'basicQLearningAgent'
    explorationRate = 0.03
    #explorationRate = 0.0
    weights = None
    currentGoal = util.Counter()
    lastAgent = None
    numAllies = None
    targetedFoods = {}
    defenseIndex = list()
    
    def __init__(self, index, offense):
        DefensiveReflexAgent.__init__(self, index)
        if offense:
            self.myNotFeatures = [ 'eatingEnemy','distanceToClosestEnemyAsGhostSquared', 'attackingEnemyAsGhost',
                               'numberOfYourFoodsRemaining', 'homeTerritory', 'distanceToClosestEnemyAsGhost', 'isPacman']
        else:
            TrialAgent.defenseIndex.append(index)
            self.myNotFeatures = [ 'distancetoClosestEnemyFoodSquared', 'gettingEaten'
                                   'distanceToClosestEnemyAsPacmanSquared', 'attackingEnemyAsPacman',
                                   'numberOfEnemyFoodsRemaining','distancetoClosestEnemyFood','enemyTerritory',
                                   'distanceToClosestEnemyAsPacman','enemyGhostClose', 'distanceToFriends']
        
        
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
            TrialAgent.lastAgent = TrialAgent.allyIndices[len(TrialAgent.allyIndices) -1]
            TrialAgent.numAllies = len(TrialAgent.allyIndices)
            for ally in TrialAgent.allyIndices:
                TrialAgent.currentGoal[ally] = (-1, -1)
            TrialAgent.defenseIndex = list()
            
        
    def initializeUniformly(self, gameState):
        
        
        #self.distancer.getMazeDistances()
        "Begin with a uniform distribution over ghost positions."
        
        for enemy in TrialAgent.enemyIndices:
            beliefs = util.Counter();
            for p in TrialAgent.legalPositions:
                beliefs[p] = 1.0
            beliefs.normalize()
            TrialAgent.enemyPositions[enemy] = beliefs
            

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
                
                total = sum(dist)
                if total is not 0:
                    newEnemyP[enemyIndex][p] = total
                
            
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
        for enemy in TrialAgent.enemyIndices:
            defPos = gameState.getAgentPosition(enemy)
            dist = TrialAgent.enemyPositions[enemy]
            if defPos is not None:
                intDefPos = (int(defPos[0]), int(defPos[1]))
                posList = util.Counter()
                posList[intDefPos] = 1.0
                TrialAgent.lastSightings[enemy] = (posList, 0, intDefPos)
            elif TrialAgent.lastSightings[enemy] is not 0:
                posDist = TrialAgent.lastSightings[enemy][0]
                timeSinceObs = TrialAgent.lastSightings[enemy][1]
                posOriginalObs =  TrialAgent.lastSightings[enemy][2]
                newPosDist = util.Counter()
                for pos in posDist :
                    if timeSinceObs < 20:
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
                                newPosDist[newPos] += math.log1p(probPerState) + math.log1p(1.0/(distance + 0.0001)) + math.log1p(posDist[pos])
                                TrialAgent.enemyPositions[enemy][newPos] += math.log1p(probPerState) + math.log1p(1.0/(distance + 0.0001)) + math.log1p(posDist[pos]) 
                        newPosDist.normalize()
                        TrialAgent.enemyPositions[enemy].normalize()
                        TrialAgent.lastSightings[enemy] = (newPosDist, timeSinceObs + 1,posOriginalObs )
                    else:
                        TrialAgent.enemyPositions[enemy][pos] += math.log1p(posDist[pos])
                        TrialAgent.enemyPositions[enemy].normalize()
                        TrialAgent.lastSightings[enemy] = 0
            elif len(dist) < 50:
                newPosDist = util.Counter()
                for pos in dist:
                    legalNext = TrialAgent.legalNextPositions[pos]
                    probPerState = 1.0/(len(legalNext) + len(dist))
                        
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
                            newPosDist[newPos] += math.log1p(probPerState) + math.log1p(1.0/(distance + 0.0001)) + math.log1p(dist[pos])
                newPosDist.normalize()
                TrialAgent.enemyPositions[enemy] = newPosDist
#                counters = list()
#                newCounter = newPosDist.copy()
#                counters.append(newCounter)
#                self.displayDistributionsOverPositions(counters)
                
                
                    
    def observe(self, gameState):
      
        TrialAgent.noisyDistances[self.index] = gameState.getAgentDistances()
      
    
    def netDistanceToFriends(self, gameState):
        positions = [(index, gameState.getAgentPosition(index)) for index in self.allyIndices]
    
        friends = self.getTeamPositions(gameState)
        myPos = self.getPosition(gameState)
        netDistance = 0
        for index, pos in positions:
            if index in TrialAgent.defenseIndex: continue
            netDistance += self.getMazeDistance(pos, myPos)
        return netDistance
    
    def getListOfEnemyPos(self, gameState):
        enemyPos = list()
        for enemy in TrialAgent.enemyIndices:
            beliefs = TrialAgent.enemyPositions[enemy]
            enemyPos.append(beliefs.argMax())
        return enemyPos
        
        
    def evaluateDeep(self, gameState, depth):
        actions = gameState.getLegalActions(self.index)
        actions.remove(Directions.STOP)
        
        values = list()
        maxValue = -9999999999999999
        bestAction = None
        for action in actions:
            valueForAction = 0
            if depth == 0:
                valueForAction = self.evaluate(gameState, action)
                for ally, pos in TrialAgent.currentGoal.items():
                    if gameState.getAgentPosition(self.index) is pos:
                        valueForAction = -99999
        
            else:
                succ = self.getSuccessor(gameState, action)
                valueForAction = self.evaluateDeep(succ, depth+1)[1] 
                currentPosValue = self.evaluate(gameState, action)
                valueForAction = (0.5*valueForAction) + currentPosValue
            if valueForAction >= maxValue:
                maxValue = valueForAction
                bestAction = action
                if depth == 0:
                    succ = self.getSuccessor(gameState, action)
                    pos = succ.getAgentPosition(self.index)
                    TrialAgent.currentGoal[self.index] = pos
               
        return (bestAction, maxValue)
    
    def getMostLikelyPositionForEnemy(self, enemy):
        beliefs = TrialAgent.enemyPositions[enemy]
        return beliefs.argMax()
    
    
    def getClosestEnemyPos(self, gameState):
        enemyPositions = [self.getMostLikelyPositionForEnemy(enemy) for enemy in TrialAgent.enemyIndices]
        return min(enemyPositions, key = lambda ePos : self.getMazeDistance(self.getPosition(gameState), ePos))
    
    def getClosestEnemyDist(self, gameState):

        return self.getMazeDistance(self.getPosition(gameState), self.getClosestEnemyPos(gameState))  
        
    def updateFoodFeatures(self, gameState, successor, features):
        nextPositionD = self.getPosition(successor)
        nextPosition = ( int(nextPositionD[0]), int(nextPositionD[1]) )
        
        ourFood = self.getFoodYouAreDefending(successor).asList()
        foodsTargetedByNotMe = [foodPos for index, foodPos in TrialAgent.targetedFoods.items() if index != self.index]
        foodDistDict = {}
        for foodPos in self.getFood(successor).asList():
            distancesFromFoodToTargetedFood = [self.getMazeDistance(foodPos, tfoodPos) for tfoodPos in foodsTargetedByNotMe]
            if not len(distancesFromFoodToTargetedFood) or min(distancesFromFoodToTargetedFood) > 3:
                foodDistDict[foodPos] = self.getMazeDistance(nextPosition, foodPos)
        
        enemyFood = foodDistDict.keys()
        oldEnemyFood = self.getFood(gameState).asList()
        
        numEnemyFood = 0
        numOurFood = 0
        numOldFood = 0
        
        defenseFoodDists = list()
        enemyFoodDists = list()
        oldEnemyFoodDists = list()
        
        minOldDistance = 10000
        closest = None
        for oldFood in oldEnemyFood:
            if nextPosition == oldFood and self.isPacman(successor):
                features['eatingFood'] = 1.0
            
            numOldFood += 1
            distance = self.getMazeDistance(nextPosition, oldFood)
            if distance < minOldDistance:
                minOldDistance = distance
                closest = oldFood
            oldEnemyFoodDists.append(self.getMazeDistance(nextPosition, oldFood))
        

        others = self.getListOfEnemyPos(successor)
        #others.extend(self.getTeamPositions(successor))
        homeTerritoryCount = 0
        
        closest = None
        minMyDistance = 10000
        for myFood in ourFood:
            
            numOurFood += 1
            distance = self.getMazeDistance(nextPosition, myFood)
            if distance < minMyDistance:
                minMyDistance = distance
                closest = myFood
            defenseFoodDists.append(self.getMazeDistance(nextPosition, myFood))
            
            meClosest = True
            for otherPos in others:
                hisDistance = self.getMazeDistance(otherPos, myFood)
                if distance > hisDistance:
                    meClosest = False 
                    break
            if meClosest: homeTerritoryCount += 1
            
            
        closest = None    
        minTheirDistance = 10000  
        enemyTerritoryCount = 0  
        for food in enemyFood:
            
            numEnemyFood += 1
            distance = self.getMazeDistance(nextPosition, food)
            if distance < minTheirDistance:
                minTheirDistance = distance
                closest = food
            enemyFoodDists.append(self.getMazeDistance(nextPosition, food))
            
            meClosest = True
            for otherPos in others:
                hisDistance = self.getMazeDistance(otherPos, food)
                if distance > hisDistance:
                    meClosest = False 
                    break
            if meClosest: enemyTerritoryCount +=1
        
        if closest:
            TrialAgent.targetedFoods[self.index] = closest
            
        for capsule in self.getCapsules(successor):
            distance = self.getMazeDistance(nextPosition, capsule)
            meClosest = True
            for otherPos in others:
                hisDistance = self.getMazeDistance(otherPos, capsule)
                if distance > hisDistance:
                    meClosest = False 
                    break
            if meClosest: enemyTerritoryCount +=5

        
        features['numberOfEnemyFoodsRemaining'] = numEnemyFood
        features['numberOfYourFoodsRemaining'] = numOurFood
        features['distancetoClosestEnemyFoodSquared'] = minTheirDistance ** 2
        
        features['homeTerritory'] = homeTerritoryCount
        
        
        if features['eatingFood'] > 0:
            features['distancetoClosestEnemyFoodSquared'] = 0
            enemyTerritoryCount *= 5
        features['enemyTerritory'] = enemyTerritoryCount
        if minTheirDistance < 4: features['enemyTerritory'] *= (5 - minTheirDistance)
        
    
    def getFeatures(self, gameState, action):
        """
            Returns a counter of features for the state
            """
        
        successor = self.getSuccessor(gameState, action)
        position = self.getPosition(gameState)
        nextPosition = self.getPosition(successor)
        nextPositionAsInt = self.getPositionAsInt(successor)
        
        features = util.Counter()
        
        features['degreesOfFreedom'] = len(self.getLegalActions(successor)) - 1
        
        closestFriend = min(  [self.getMazeDistance(position, fpos) for fpos in self.getTeamPositions(successor)] )
        features['closestFriend'] = closestFriend 
            
        features['successorScore'] = self.getScore(successor)
                
        rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        features['reverse'] = 1.0 if action == rev else 0.0     
        
        self.updateFoodFeatures(gameState, successor, features)
        
        features['notMoving'] = 1.0 if position == nextPosition else 0.0
        
        closestEnemyPos = self.getClosestEnemyPos(gameState)
        closestEnemy = self.getClosestEnemyDist(gameState)
        
        if closestEnemy < 3: features['homeTerritory'] *= (4 - closestEnemy)
        
        features['eatingEnemy'] = 0.0
        features['gettingEaten'] = 0.0
        for enemyIndex in TrialAgent.enemyIndices:
            oldEnemyPos = gameState.getAgentPosition(enemyIndex)
            if oldEnemyPos == nextPosition:
                if self.isGhost(successor) and self.getScaredTimer(successor) <= 0:
                    features['eatingEnemy'] = 1.0
                    features['homeTerritory'] *= 4
                
        if self.getMazeDistance(position, nextPosition) > 1:
            features['gettingEaten'] = 1.0

        attackingEnemy = closestEnemyPos ==  nextPosition
        
        features['attackingEnemyAsGhost'] = 1.0 if self.isGhost(successor) and attackingEnemy else 0.0
        features['attackingEnemyAsPacman'] = 1.0 if self.isPacman(successor) and attackingEnemy else 0.0
        
        if attackingEnemy:
            features['distanceToClosestEnemyAsGhostSquared'] = 0        
            features['distanceToClosestEnemyAsPacmanSquared'] = 0
        else:
            features['distanceToClosestEnemyAsGhostSquared'] = closestEnemy ** 2
            features['distanceToClosestEnemyAsPacmanSquared'] = closestEnemy ** 2
            if features['distanceToClosestEnemyAsPacmanSquared'] <= 9:
                features['enemyGhostClose'] = 1.0 
                
        
        if self.isPacman(successor): features['isPacman'] = 1.0
        else: features['isPacman'] = 0
        
        netDist = self.netDistanceToFriends(successor)
        features['distanceToFriends'] = netDist
        
        features = self.pruneFeatures(features)
        
        return features
    
    def pruneFeatures(self, features):
        for feature, value in features.items():
            if feature in self.myNotFeatures:
                features[feature] = 0
                
        return features
    
    def getWeights(self, gameState, action):
        """
            Normally, weights do not depend on the gamestate.    They can be either
            a counter or a dictionary.
            """
        if TrialAgent.weights == None:
            TrialAgent.weights = util.Counter()
            for feature in self.getFeatures(gameState, 'Stop'):
                TrialAgent.weights[feature] = self.getStartingWeight(feature)
            #TrialAgent.weights = TrialAgent.featureHandler.getFeatureWeights('basicQlearningAgent')
        
        return TrialAgent.weights
    
    def getReward(self, state):
        prevState = self.getPreviousObservation()
        
        if prevState == None: return 0
        
        reward = 0
        
        reward += 25 if self.getPosition(state) in self.getFood(prevState).asList() else 0
        reward += (len(self.getCapsules(state)) - len(self.getCapsules(prevState))) * 25
        
        for enemyIndex in TrialAgent.enemyIndices:
            oldEnemyPos = prevState.getAgentPosition(enemyIndex)
            if oldEnemyPos == self.getPosition(state):
                if self.isGhost(state) and self.getScaredTimer(state) <= 0:
                    reward += 25
        
        
        if(self.getMazeDistance(self.getPosition(state), self.getPosition(prevState)) > 1):
            reward -= 100
                    
        return reward
    
    def getValue(self, state):
        action = self.getBestAction(state)
        if action == None:
            return 0.0
        return self.evaluate(state, action)
    
    
    def getBestAction(self, state):
        return DefensiveReflexAgent.chooseAction(self, state)
    
    
    def getStartingWeight(self, feature):
        if feature in regularMutation.aggressiveDWeightsDict:
           return regularMutation.aggressiveDWeightsDict[feature]
        
        if feature == 'degreesOfFreedom': return 0
        if feature == 'distancetoClosestEnemyFoodSquared': return -1
        if feature == 'eatingFood': return 100
        if feature == 'eatingEnemy': return 100
        if feature == 'gettingEaten': return -100
        if feature == 'notMoving': return -1.0
        if feature == 'avgFriendDist': return 1.0
        if feature == 'successorScore': return 0
        if feature == 'reverse': return -1.0
        if feature == 'distanceToClosestEnemyAsGhostSquared': return -1.0
        if feature == 'distanceToClosestEnemyAsPacmanSquared': return 1.0
        if feature == 'isPacman': return -1000000
        if feature == 'attackingEnemyAsGhost': return 1.0
        if feature == 'attackingEnemyAsPacman': return -1.0
        if feature == 'numberOfYourFoodsRemaining': return 1.0
        if feature == 'numberOfEnemyFoodsRemaining': return -1.0
        if feature == 'distancetoClosestEnemyFood': return -1.0
        if feature == 'homeTerritory': return 10
        if feature == 'enemyTerritory': return 10
        if feature == 'distanceToClosestEnemyAsGhost': return -1.0
        if feature == 'distanceToClosestEnemyAsPacman': return 1.0
        if feature == 'enemyGhostClose': return -1.0
        if feature == 'closestFriend': return 1.0
        if feature == 'distanceToFriends': return 1.0
        
        return 0
    
    
    def update(self, state, action, nextState):
        features = self.getFeatures(state, action)
        weights = self.getWeights(state, action)
        
        correction = self.getReward(nextState) + (TrialAgent.discount * self.getValue(nextState)) - self.evaluate(state, action)
        #print 'CORRECTION: ' + str(correction)
        #print 'REWARD: ' + str(self.getReward(state))
        #print 'NEXT VALUE: ' + str(self.getValue(nextState))
        #print 'EVAL: ' + str(self.evaluate(state, action))
        
        for feature in features.keys():
            weights[feature] = weights[feature] + correction * TrialAgent.alpha if feature in weights else self.getStartingWeight(feature)
        #weights[feature] = self.getStartingWeight(feature)
        #weights = self. dictNormalize(weights)
        
        TrialAgent.weights = weights
        TrialAgent.featureHandler.updateFeatureWeights(weights, 'basicQlearningAgent')
        
    def chooseAction(self, gameState):
        start = time.time()
        self.observe(gameState)
        if self.index == TrialAgent.lastAgent :
            self.infer(gameState)
            self.trackLastPos(gameState)
            
       
        valueActionPair = self.evaluateDeep(gameState, 0)
        action = valueActionPair[0]
        actions = self.getLegalActions(gameState)
        #action = random.choice(bestActions)    
            
        #self.update(gameState, action, self.getSuccessor(gameState, action))
        
        while action == Directions.STOP:
            action = random.choice(actions)
            print "random"
        succ = self.getSuccessor(gameState, action)
        myPosition = succ.getAgentPosition(self.index)
        for enemy, dist in TrialAgent.enemyPositions.items():
            defPos = gameState.getAgentPosition(enemy)
            
            if defPos == myPosition:
                TrialAgent.lastSightings[enemy] = 0
        
        if time.time() - start >= 0.95: print "too long!!!!!!!!"
        return action
        
class DefensiveTrialAgent(TrialAgent):

    def __init__(self, index):
        DefensiveReflexAgent.__init__(self, index)
        self.agentName = 'defensiveQLearningAgent' 
        self.weights = None

    def getReward(self, state):

        prevState = self.getPreviousObservation()
        if prevState == None: return 0
        reward = 0
        reward -= (len(self.getFoodYouAreDefending(prevState).asList()) - len(self.getFoodYouAreDefending(state).asList())) * 100

        reward -= (len(self.getCapsulesYouAreDefending(prevState)) - len(self.getCapsulesYouAreDefending(state))) * 200


        for index in self.getOpponents(state):

            if prevState.getAgentPosition(index) == self.getPosition(state) and state.getAgentPosition(index) == None:

                reward += 500
        if(self.getMazeDistance(self.getPosition(state), self.getPosition(prevState)) > 1):

            reward -= 500
        return reward

    def getStartingWeight(self, feature):
        

        if feature == 'degreesOfFreedom': return 5

        if feature == 'numOurFoodsLeft': return 10

        if feature == 'successorScore': return 1.25

        if feature == 'homeTerritory': return 10

        if feature == 'reverse': return -2

        if feature == 'distanceToClosestEnemy': return -100

        if feature == 'distanceToClosestEnemySquared': return -100

        if feature == 'closestOfOurFood': return -2

        #if feature == 'enemyGhostClose': return -50
        if feature == 'attackingEnemyAsGhost': return 500

        if feature == 'attackingEnemyAsPacman': return -500

        if feature == 'isPacman': return -50000

        if feature == 'totalFoodDist': return -35

        return 0
        
              