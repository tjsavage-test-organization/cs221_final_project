import sys
import game

class ExtendedGameState(GameState):

    def __init__(self, state = None):
        GameState.__init__(self, state)
        self.positions = []

        for i in range(self.getNumAgents()):
            self.positions[i] = GameState.getAgentPosition(self, i) if state != None else state.positions[i]

    def getAgentPosition(self, index):
        actualPos = GameState.getAgentPosition(self, index)
        if actualPos != None:
            return actualPos

        return self.positions[index]

    
    def setBelievedPositionForAgent(self, index, position):
        self.positions[index] = position

    
    def agentIsObservable(self, index):
        return GameState.getAgentPosition(index) != None
            
    
    def generateSuccessor(self, agentIndex, action):
        if self.agentIsObservable(agentIndex):
            return ExtendedGameState(GameState.generateSuccessor(self, agentIndex, action))
        
        nextPosForAgent = Actions.getSuccessor(self.positions[i], action)
        
        if nextPosForAgent in Actions.getLegalNeighbors(self.positions[agentIndex], self.getWalls()):
            return self
        
        nextState = ExtendedGameState(self)
        nextState.positions[agentIndex] = nextPosForAgent
        return nextState

    
        

        

        