# captureAgents.py
# ----------------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html

"""
  Interfaces for capture agents and agent factories
"""

from game import Agent
from game import Actions
import distanceCalculator
from util import nearestPoint
import util
import random

class AgentFactory:
  "Generates agents for a side"

  def __init__(self, isRed, **args):
    self.isRed = isRed

  def getAgent(self, index):
    "Returns the agent for the provided index."
    util.raiseNotDefined()

class RandomAgent( Agent ):
  """
  A random agent that abides by the rules.
  """
  def __init__( self, index ):
    self.index = index

  def getAction( self, state ):
    return random.choice( state.getLegalActions( self.index ) )

class CaptureAgent(Agent):
  """
  A base class for capture agents.  The convenience methods herein handle
  some of the complications of a two-team game.

  Recommended Usage:  Subclass CaptureAgent and override chooseAction.
  """

  #############################
  # Methods to store key info #
  #############################

  def __init__( self, index, timeForComputing = 0.9 ):
    """
    Lists several variables you can query:
    self.index = index for this agent
    self.red = true if you're on the red team, false otherwise
    self.agentsOnTeam = a list of agent objects that make up your team
    self.distancer = distance calculator (contest code provides this)
    self.observationHistory = list of GameState objects that correspond
        to the sequential order of states that have occurred so far this game
    self.timeForComputing = an amount of time to give each turn for computing maze distances
    """
    # Agent index for querying state
    self.index = index

    # Whether or not you're on the red team
    self.red = None

    # Agent objects controlling you and your teammates
    self.agentsOnTeam = None

    # Maze distance calculator
    self.distancer = None

    # A history of observations
    self.observationHistory = []

    # Time to spend each turn on computing maze distances
    self.timeForComputing = timeForComputing

    # Access to the graphics
    self.display = None

  def registerInitialState(self, gameState):
    """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).
    
    If you want initialization any items a single time for a team
    (i.e. the first agent that gets created does the work) you'll
    need to create your own team class and only let it initialize
    once.
    
    A distanceCalculator instance caches the maze distances 
    between each pair of positions, so your agents can use:
    self.distancer.getDistance(p1, p2)
    """
    self.red = gameState.isOnRedTeam(self.index)
    # Even though there are up to 6 agents creating a distancer, the distances
    # will only actually be computed once, before the start of the game 
    self.distancer = distanceCalculator.Distancer(gameState.data.layout)
    
    # comment this out to forgo maze distance computation and use manhattan distances
    self.distancer.getMazeDistances()
    
    # or uncomment this to forget maze distances and just use manhattan distances for this agent
    #self.distancer.useManhattanDistances()
    
    import __main__
    if '_display' in dir(__main__):
      self.display = __main__._display

  def final(self, gameState):
    self.observationHistory = []

  def registerTeam(self, agentsOnTeam):
    """
    Fills the self.agentsOnTeam field with a list of the
    indices of the agents on your team.
    """
    self.agentsOnTeam = agentsOnTeam

  def observationFunction(self, gameState):
    " Changing this won't affect pacclient.py, but will affect capture.py "
    return gameState.makeObservation(self.index)

  #################
  # Action Choice #
  #################

  def getAction(self, gameState):
    """
    Calls chooseAction on a grid position, but continues on half positions.
    If you subclass CaptureAgent, you shouldn't need to override this method.  It
    takes care of appending the current gameState on to your observation history
    (so you have a record of the game states of the game) and will call your
    choose action method if you're in a state (rather than halfway through your last
    move - this occured because Pacman agents used to move half as quickly as ghost agents).

    """
    self.observationHistory.append(gameState)

    myState = gameState.getAgentState(self.index)
    myPos = myState.getPosition()
    if myPos != nearestPoint(myPos):
      # We're halfway from one position to the next
      return gameState.getLegalActions(self.index)[0]
    else:
      return self.chooseAction(gameState)

  def chooseAction(self, gameState):
    """
    Override this method to make a good agent. It should return a legal action within
    the time limit (otherwise a random legal action will be chosen for you).
    """
    util.raiseNotDefined()

  #######################
  # Convenience Methods #
  #######################
  
  def getLayoutWidth(self, gameState):
    """
    Returns the width of the layout
    """
    return gameState.data.layout.width
  
  def getLayoutHeight(self, gameState):
    """
    Returns the height of the layout
    """
    return gameState.data.layout.height

  def getLayoutDimensions(self, gameState):
    """
    Returns a tuple of (width, height)
    """
    return (self.getLayoutWidth(gameState), self.getLayoutHeight(gameState))

  # Left as getFood instead of getFoodYouAreAttacking for backwards compatibility
  def getFood(self, gameState):
    """
    Returns the food you're meant to eat. This is in the form of a matrix
    where m[x][y]=true if there is food you can eat (based on your team) in that square.
    """
    if self.red:
      return gameState.getBlueFood()
    else:
      return gameState.getRedFood()

  def getFoodYouAreDefending(self, gameState):
    """
    Returns the food you're meant to protect (i.e., that your opponent is
    supposed to eat). This is in the form of a matrix where m[x][y]=true if
    there is food at (x,y) that your opponent can eat.
    """
    if self.red:
      return gameState.getRedFood()
    else:
      return gameState.getBlueFood()

  # Left as getCapsules instead of getCapsulesYouAreAttacking for backwards compatibility
  def getCapsules(self, gameState):
    if self.red:
      return gameState.getBlueCapsules()
    else:
      return gameState.getRedCapsules()

  def getCapsulesYouAreDefending(self, gameState):
    if self.red:
      return gameState.getRedCapsules()
    else:
      return gameState.getBlueCapsules()

  def getOpponents(self, gameState):
    """
    Returns agent indices of your opponents. This is the list of the numbers
    of the agents (e.g., red might be "1,3,5")
    """
    if self.red:
      return gameState.getBlueTeamIndices()
    else:
      return gameState.getRedTeamIndices()
    
  def getOpponentPositions(self, gameState):
    """
    Returns a list of the position of all your enemy's agents.
    NOTE: This returns None for agents at distances > 5
    """
    return [gameState.getAgentPosition(enemy) for enemy in self.getOpponents(gameState)]

  def getTeam(self, gameState):
    """
    Returns agent indices of your team. This is the list of the numbers
    of the agents (e.g., red might be the list of 1,3,5)
    """
    if self.red:
      return gameState.getRedTeamIndices()
    else:
      return gameState.getBlueTeamIndices()
    
  def getTeamPositions(self, gameState):
    """
    Returns a list of the position of all your team's agents.
    """
    return [gameState.getAgentPosition(ally) for ally in self.getTeam(gameState)]
  
  def getPosition(self, gameState):
    """
    Returns the position of this particular agent.
    """
    return gameState.getAgentState(self.index).getPosition()
  
  def getPositionAsInt(self, gameState):
    """
    Returns the position of this particular agent as an integer.
    The game defaults to using floating point because it has mechanics
    that were designed when agents could move at speed < 1.0 -- which
    is confusing when agents only move 1 square at a time. This returns
    new positions as integers.
    """
    pos = self.getPosition(gameState)
    return (int(pos[0]), int(pos[1]))
  
  def getScaredTimer(self, gameState):
    """
    Returns the time left for which the Agent is scared. Note that when the 
    agent is a Pacman he can still be scared, but it doesn't affect him in 
    any way -- unless he comes back to ghost land without being eaten.
    """
    return gameState.getAgentState(self.index).scaredTimer
  
  def isPacman(self, gameState):
    """
    Returns true if the agent is a Pacman.
    """
    return gameState.getAgentState(self.index).isPacman
  
  def isGhost(self, gameState):
    """
    Returns true if the agent is a Ghost.
    """
    return not self.isPacman(gameState)
  
  def getLegalActions(self, gameState):
    """
    Returns the actions which are legal for this particular agent to make.
    """
    return gameState.getLegalActions(self.index)
  
  def getDirectionalVector(self, action):
    """
    Returns the (dx, dy) directional movement from a particular action.
    """
    return Actions.directionToVector(action)
  
  def getNextPositionAsInt(self, gameState, action):
    """
    Returns the next position for the agent as an int.
    The game defaults to using floating point because it has mechanics
    that were designed when agents could move at speed < 1.0 -- which
    is confusing when agents only move 1 square at a time. This returns
    new positions as integers.
    If the action is illegal it returns a tuple of (None, None)
    """
    if action in self.getLegalActions(gameState):
      pos = self.getPosition(gameState)
      dx, dy = self.getDirectionalVector(action)
      return (int(pos[0]+dx),int(pos[1]+dy))
    else:
      return (None, None)

  def isPositionInTeamTerritory(self, gameState, position):
    """
    Returns true if the given position is in your team's territory.
    """
    width = self.getLayoutWidth(gameState)
    return (position[0] < width/2 and self.red) or (position[0] >= width/2 and not self.red)
  
  def isPositionInEnemyTerritory(self, gameState, position):
    """
    Returns true if the given position is in your enemy's territory.
    """
    return not self.isPositionInTeamTerritory(gameState, position)

  def getScore(self, gameState):
    """
    Returns how much you are beating the other team by in the form of a number
    that is the difference between your score and the opponents score.  This number
    is negative if you're losing.
    """
    if self.red:
      return gameState.getScore()
    else:
      return gameState.getScore() * -1

  def getMazeDistance(self, pos1, pos2):
    """
    Returns the distance between two points; These are calculated using the provided
    distancer object.

    If distancer.getMazeDistances() has been called, then maze distances are available.
    Otherwise, this just returns Manhattan distance.
    """
    d = self.distancer.getDistance(pos1, pos2)
    return d

  def getPreviousObservation(self):
    """
    Returns the GameState object corresponding to the last state this agent saw
    (the observed state of the game last time this agent moved - this may not include
    all of your opponent's agent locations exactly).
    """
    if len(self.observationHistory) == 1: return None
    else: return self.observationHistory[-2]

  def getCurrentObservation(self):
    """
    Returns the GameState object corresponding this agent's current observation
    (the observed state of the game - this may not include
    all of your opponent's agent locations exactly).
    """
    return self.observationHistory[-1]

  def displayDistributionsOverPositions(self, distributions):
    """
    Overlays a distribution over positions onto the pacman board that represents
    an agent's beliefs about the positions of each agent.

    The arg distributions is a tuple or list of util.Counter objects, where the i'th
    Counter has keys that are board positions (x,y) and values that encode the probability
    that agent i is at (x,y). The distribution should look like 
    [(1, Counter1), (2, Counter2), etc...].

    If some elements are None, then they will be ignored.  If a Counter is passed to this
    function, it will be displayed. This is helpful for figuring out if your agent is doing
    inference correctly, and does not affect gameplay.
    """
    dists = []
    for dist in distributions:
      if dist != None:
        if not isinstance(dist, util.Counter): raise Exception("Wrong type of distribution")
        dists.append(dist)
      else:
        dists.append(util.Counter())
    if self.display != None and 'updateDistributions' in dir(self.display):
      self.display.updateDistributions(dists)
    else:
      self._distributions = dists # These can be read by pacclient.py


class TimeoutAgent( Agent ):
  """
  A random agent that takes too much time. Taking
  too much time results in penalties and random moves.
  """
  def __init__( self, index ):
    self.index = index
    
  def getAction( self, state ):
    import random, time
    time.sleep(2.0)
    return random.choice( state.getLegalActions( self.index ) )
