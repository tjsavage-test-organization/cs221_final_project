class AgentEnums:
    Offensive = 1
    Defensive = 2
    Goalie = 3
    Hunter = 4

    def __init__(self, type):
        self.value = type
    
    def __str__(self):
        if self.value == AgentEnums.Offensive:
            return 'Offensive'

        if self.value == AgentEnums.Defensive:
            return 'Defensive'

        if self.value == AgentEnums.Goalie:
            return 'Goalie'

        if self.value == AgentEnums.Hunter:
            return 'Hunter'

    def __eq__(self, other):
        return self.value == other.value