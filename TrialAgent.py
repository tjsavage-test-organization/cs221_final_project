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

class TrialAgentFactory(AgentFactory):
  "Returns one keyboard agent and offensive reflex agents"

  def __init__(self, **args):
    AgentFactory.__init__(self, **args)

  def getAgent(self, index):
    return TrialAgent(index)

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
        print 'given position ' + str(position)
        allNextPos = util.Counter()
        nextPossiblePos = TrialAgent.getLegalNextPositions(self, gameState, position)
        for nextPos in nextPossiblePos:
            
            closestFoodOfNextPos = self.getClosestFood(gameState, nextPos)
            print "closestFood " + str(closestFoodOfNextPos)
            newDistance = self.getMazeDistance(nextPos, closestFoodOfNextPos)
            print str(nextPos) + "     " + str(newDistance)
            allNextPos[nextPos] = newDistance
            #allNextPos[nextPos] = 1
        allNextPos.normalize()
        print '----------end-----------'
        return allNextPos
        
            
        #minDistance = min([self.getMazeDistance(position, food) for food in foodList])
    
    def elapseTime(self, gameState):
        newEnemiesP = util.Counter()
        for enemyIndex, beliefs in TrialAgent.enemyPositions.items():
            newEnemyP = util.Counter()
            for p, probP in beliefs.items():
                newPosDist = self.nextPositionDist(gameState, p)
                for newPos, probNewPositionGivenP in newPosDist.items():
                    newEnemyP[newPos] += math.log1p(probNewPositionGivenP) +  math.log1p(probP)
            newEnemyP.normalize()
            newEnemiesP[enemyIndex] = newEnemyP

        TrialAgent.enemyPositions = newEnemiesP

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
                #print "pos " + str(pos)
                #print "me " + str(self.getPosition(gameState))
                if self.getPosition(gameState) is pos:print "same"
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
                TrialAgent.lastSightings[enemy] = (posList, 0)
            elif TrialAgent.lastSightings[enemy] is not 0:
                posDist = TrialAgent.lastSightings[enemy][0]
                #if enemy is self.enemyIndices[0]: print posDist
                timeSinceObs = TrialAgent.lastSightings[enemy][1]
                timeFactor = math.exp(-3*timeSinceObs)
                newPosDist = util.Counter()
                for pos in posDist :
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
                TrialAgent.lastSightings[enemy] = (newPosDist, timeSinceObs + 1)
                
                
                    
    def observe(self, gameState):
      
        TrialAgent.noisyDistances[self.index] = gameState.getAgentDistances()
      

    def getFeatures(self, gameState, action):
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
        return weights
    
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
        
        
    def chooseAction(self, gameState):
        
        #print "index " + str(self.index)
        self.observe(gameState)
        if self.index == TrialAgent.allyIndices[len(TrialAgent.allyIndices) - 1] :
            start = time.time()
            self.infer(gameState)
            #self.elapseTime(gameState)
            self.trackLastPos(gameState)
            
            counters = list()
        
            counters.append(TrialAgent.enemyPositions[self.enemyIndices[0]]) 
            if TrialAgent.lastSightings[self.enemyIndices[0]] is not 0 :
                timeSince = TrialAgent.lastSightings[self.enemyIndices[0]][1]
                if timeSince < 32:
                    toDisplay = TrialAgent.lastSightings[self.enemyIndices[0]][0].copy()
                    counters.append(toDisplay) 
            self.displayDistributionsOverPositions(counters)
            
            actionValuePair = self.evaluateDeep(gameState, 0)
            print actionValuePair
            return actionValuePair[0] 
        
        
        
        print self.index
        return DefensiveReflexAgent.chooseAction(self, gameState) 
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
        
        
        
        
              