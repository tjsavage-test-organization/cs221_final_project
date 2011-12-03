'''
Created on Nov 29, 2011

@author: rorymacqueen
'''
from captureAgents import CaptureAgent
from captureAgents import AgentFactory
import util
import distanceCalculator
import baselineAgents
from baselineAgents import OffensiveReflexAgent
import math
import time

class TrialAgentFactory(AgentFactory):
  "Returns one keyboard agent and offensive reflex agents"

  def __init__(self, **args):
    AgentFactory.__init__(self, **args)

  def getAgent(self, index):
    return TrialAgent(index)

class TrialAgent(OffensiveReflexAgent):
    
    enemyPositions = util.Counter()
    legalPositions = list()
    legalNextPositions = util.Counter()
    firstTurn = True
    distancer = None
    enemyIndices = list()
    allyIndices = list()
    noisyDistances = util.Counter()
    
    def __init__(self, index):
        OffensiveReflexAgent.__init__(self, index)
        
    def registerInitialState(self, gameState):
        OffensiveReflexAgent.registerInitialState(self, gameState)
        if TrialAgent.firstTurn:
            TrialAgent.distancer = distanceCalculator.Distancer(gameState.data.layout)
            TrialAgent.distancer.useManhattanDistances()
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
        
    def getClosestFood(self, gameState, position):
        foodList = self.getFood(gameState).asList()
        foodList.extend( (self.getFoodYouAreDefending(gameState)).asList() )
        distances = [self.getMazeDistance(position, food) for food in foodList]
        i = distances.index(min(distances))
        closestFood = foodList[i]
        return closestFood                                                
    
    def nextPositionDist(self, gameState, position):
        print 'given position ' + str(position)
        allNextPos = util.Counter()
        nextPossiblePos = TrialAgent.getLegalNextPositions(self, gameState, position)
        for nextPos in nextPossiblePos:
            
            closestFoodOfNextPos = self.getClosestFood(gameState, nextPos)
            print "closestFood " + str(closestFoodOfNextPos)
            newDistance = self.getMazeDistance(nextPos, closestFoodOfNextPos)
            print str(nextPos) + "     " + str(newDistance)
            #allNextPos[nextPos] = newDistance
            allNextPos[nextPos] = 1
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
                    trueDistance = TrialAgent.distancer.getDistance(p, allyPos)
                    
                        
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
            
                

    def observe(self, gameState):
      
        TrialAgent.noisyDistances[self.index] = gameState.getAgentDistances()
        
    def chooseAction(self, gameState):
        self.observe(gameState)
                 
        if self.index == TrialAgent.allyIndices[len(TrialAgent.allyIndices) - 1] :
            start = time.time()
            self.infer(gameState)
            #self.elapseTime(gameState)
            counters = list()
        
            counters.append(TrialAgent.enemyPositions[self.enemyIndices[0]])  
            self.displayDistributionsOverPositions(counters)
        
        return OffensiveReflexAgent.chooseAction(self, gameState)              
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
        
        
        
        
              