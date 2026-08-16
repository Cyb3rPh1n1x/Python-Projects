database =  [
    "Arsenal;Chelsea;win",
    "Liverpool;Manchester City;draw",
    "Manchester United;Tottenham;loss",
    "Newcastle;Aston Villa;win",
    "Everton;West Ham;draw",

    "Chelsea;Liverpool;loss",
    "Manchester City;Manchester United;win",
    "Tottenham;Newcastle;draw",
    "Aston Villa;Everton;win",
    "West Ham;Arsenal;loss",

    "Liverpool;Tottenham;win",
    "Manchester United;Newcastle;draw",
    "Chelsea;Aston Villa;loss",
    "Manchester City;Everton;win",
    "West Ham;Liverpool;draw",

    "Arsenal;Manchester City;win",
    "Tottenham;Aston Villa;loss",
    "Newcastle;West Ham;win",
    "Everton;Chelsea;draw",
    "Manchester United;Liverpool;loss"
]
class Team:
    def __init__(self,name):
        self.name = name
        self.MP = 0
        self.W = 0
        self.L = 0
        self.D = 0
        self.P = 0
    def win(self):                 #setting the class of teams
        self.W += 1
        self.MP += 1
        self.P += 3
    def draw(self):
        self.D += 1
        self.MP += 1
        self.P += 1
    def loss(self):
        self.L += 1
        self.MP += 1

clubs = {}

for item in database:
    TeamA,TeamB,score = item.split(";")
    if not TeamA in clubs:
        clubs[TeamA] = Team(TeamA)
    if not TeamB in clubs:
        clubs[TeamB]= Team(TeamB)
    if score == "win":
        clubs[TeamA].win()
        clubs[TeamB].loss()
    elif score == "draw":
        clubs[TeamA].draw()
        clubs[TeamB].draw()
    else:
        clubs[TeamA].loss()
        clubs[TeamB].win()
clubs = dict(sorted(clubs.items(), key=lambda item: item[1].P, reverse=True))
print("   Team                         MP  |  W  |  D  |  L  |  P")
position = 0
for item in clubs:
    position += 1
    if position>=10:
        jump = " "
    else:
        jump = "  "
    team = clubs[item]
    space = ""
    for i in range(30-len(team.name)):
        space += " "
    print(str(position)+jump+team.name +space+str(team.MP)+"  |  " +str(team.W) +"  |  " + str(team.D)+"  |  "  + str(team.L)+"  |  "  + str(team.P))




