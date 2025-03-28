#!/usr/bin/env python
__author__ = "Boris Verwoerd"

from abc import abstractmethod
import csv
from datetime import datetime
from operator import add
import os
import sys

PLAYER_DATABASE_FILE_SINGLES = "players.csv"
PLAYER_DATABASE_FILE_SINGLES_UPDATE = "players_temp.csv"
RAW_GAME_DATA_FILE_SINGLES = "raw_games_data.csv"

PLAYER_DATABASE_FILE_DOUBLES = "players_doubles.csv"
PLAYER_DATABASE_FILE_DOUBLES_UPDATE = "players_doubles_temp.csv"
RAW_GAME_DATA_FILE_DOUBLES = "raw_games_doubles_data.csv"

STARTING_RATING = 1000
K_VALUE = 40

class Game:
    def __init__(self, player_database_file, player_database_file_update, raw_game_data_file, teamSize):
        self.player_database_file        = player_database_file
        self.player_database_file_update = player_database_file_update
        self.raw_game_data_file          = raw_game_data_file
        self.teamSize                    = teamSize
        self.score                       = -1
        self.playerNames                 = []
        self.playerRatingsOld            = []
        self.teamRatingsOld              = []
        self.expectedTeamScore           = []
        self.teamScoreGain               = []
        self.playerRatingsNew            = []
    
    def playerExists(self, playerName):
        playerExists = False
        with open(self.player_database_file) as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in reader:
                if row[0] == playerName:
                    playerExists = True
        return playerExists

    def addNewPlayer(self):
        playerName = input("Please provide the shortened name of the player to add: (ex. boverwoe)\n")
        if self.playerExists(playerName):
            print("Player already exists!")
            exit(1)
        # Now add the player (with default score 1000)
        with open(self.player_database_file, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            writer.writerow([playerName, STARTING_RATING, 0])
            print("Player", playerName, "succesfully added to the database with a rating of", STARTING_RATING)

    def getRatingFromPlayer(self, playerName):
        playerRating = int()
        playerExists = False
        with open(self.player_database_file) as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in reader:
                # Names: row[0], Rating: row[1]
                if row[0] == playerName:
                    playerExists = True
                    playerRating = int(float(row[1]))
        if not playerExists:
            print("Player '", playerName, "' does not exist yet!")
        return playerRating
    
    def updateRankingFileWithNewScores(self):
        # First copy with new ratings
        with open(self.player_database_file_update, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            with open(self.player_database_file) as csvfile2:
                reader = csv.reader(csvfile2, delimiter=',', quotechar='|')
                for row in reader:
                    playerFound = False
                    for i in range(len(self.playerNames)):
                        if row[0] == self.playerNames[i]:
                            writer.writerow([row[0], self.playerRatingsNew[i], int(row[2]) + 1])
                            playerFound = True
                    if not playerFound:
                        writer.writerow([row[0], row[1], row[2]])
        # Now remove original rating file and rename the temp file
        os.remove(self.player_database_file)
        os.rename(self.player_database_file_update, self.player_database_file)
        print("New player ratings have been succesfully processed!")
    
    def determineUpdateScoresOfTeams(self):
        expectedTeamScore = []
        expectedTeamScore.append(1/(1 + 10**((self.teamRatingsOld[1]-self.teamRatingsOld[0])/400)))
        expectedTeamScore.append(1/(1 + 10**((self.teamRatingsOld[0]-self.teamRatingsOld[1])/400)))
        self.expectedTeamScore = expectedTeamScore
        teamScoreGain = []
        teamScoreGain.append(int(K_VALUE*(self.score - self.expectedTeamScore[0])))
        teamScoreGain.append(int(K_VALUE*((1-self.score) - self.expectedTeamScore[1])))
        self.teamScoreGain = teamScoreGain

    def queryPlayerNames(self):
        playerNames = []
        for j in range(2):
            for i in range(self.teamSize):
                playerName = 'test_dummy_non_existent'
                while True:
                    string = "\nPlease provide the shortened name of player " + str(i+1) + " of team " + str(j+1) + ": (ex. boverwoe)\n"
                    playerName = input(string)
                    if not self.playerExists(playerName):
                        print("The player",playerName,"does not exist!")
                    else:
                        break
                playerNames.append(playerName)
        self.playerNames = playerNames
        if len(self.playerNames) > len(set(self.playerNames)):
            print("Please provide",2*self.teamSize,"different names!")
            exit(1)
    
    @abstractmethod
    def setTeamRatings(self):
        pass

    def updatePlayerRatings(self):
        playerRatingsNew = []
        numberOfTeams = int(len(self.playerNames)/self.teamSize)
        for t in range(numberOfTeams):
            for p in range(self.teamSize):
                playerIndex = (t * self.teamSize) + p
                playerRatingsNew.append(int(self.playerRatingsOld[playerIndex] + self.teamScoreGain[t]))
        self.playerRatingsNew = playerRatingsNew
    
    def writeResults(self):
        rawDataRow = []
        rawDataRow.append(datetime.today().strftime('%Y-%m-%d'))
        rawDataRow.extend(self.playerNames)
        rawDataRow.extend(self.playerRatingsOld)
        rawDataRow.extend(self.expectedTeamScore)
        rawDataRow.append(self.score)
        rawDataRow.append(K_VALUE)
        rawDataRow.extend(self.playerRatingsNew)

        with open(self.raw_game_data_file, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(rawDataRow)
        
        self.updateRankingFileWithNewScores()
    
    def addNewGameResult(self):
        playerRatingsOld = []
        for i in range(len(self.playerNames)):
            playerRatingsOld.append(self.getRatingFromPlayer(self.playerNames[i]))
        self.playerRatingsOld = playerRatingsOld
        
        self.setTeamRatings()

        self.score = int(input("\nWhat was the score of the game? (1 if team 1 won, 0 if team 1 lost)\n"))
        if self.score not in [0,1]:
            print("Please either give a score of 1 or 0.")
            exit(1)
        
        self.determineUpdateScoresOfTeams()
        self.updatePlayerRatings()
        self.writeResults()

    def printRanking(self):
        ratingList = []
        playerList = []
        gamesList = []
        with open(self.player_database_file) as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in reader:
                # Sort based on row[1]
                ratingOfPlayer = int(row[1])
                playerName = row[0]
                numberOfGames = int(float(row[2]))
                if numberOfGames > 0:
                    if len(ratingList) == 0:
                        ratingList.append(ratingOfPlayer)
                        playerList.append(playerName)
                        gamesList.append(numberOfGames)
                    else:
                        worstPlayer = True
                        for i in range(len(ratingList)):
                            ratingListElement = ratingList[i]
                            if ratingOfPlayer > ratingListElement:
                                ratingList.insert(i, ratingOfPlayer)
                                playerList.insert(i, playerName)
                                gamesList.insert(i, numberOfGames)
                                worstPlayer = False
                                break
                        if worstPlayer:
                            ratingList.append(ratingOfPlayer)
                            playerList.append(playerName)
                            gamesList.append(numberOfGames)
        print("\nThe current ranking is given by: (Only players with more than 0 games are shown)")
        whiteSpaceBuffer = 8
        for i in range(len(ratingList)):
            whiteSpaceLength = whiteSpaceBuffer - len(playerList[i])
            whiteSpace = ' '*whiteSpaceLength
            ranking = str(i+1) + '.'
            extraWhiteSpace = ""
            if ratingList[i] < 1000:
                extraWhiteSpace = " "
            print(ranking, playerList[i], whiteSpace, "(" + str(ratingList[i]) + ", " + extraWhiteSpace + str(gamesList[i]) + " games)")
        print()


class SingleGame(Game):
    def __init__(self):
        self.teamSize = 1
        Game.__init__(self, PLAYER_DATABASE_FILE_SINGLES, PLAYER_DATABASE_FILE_SINGLES_UPDATE, RAW_GAME_DATA_FILE_SINGLES, self.teamSize)
    
    def setTeamRatings(self):
        self.teamRatingsOld = self.playerRatingsOld


class DoubleGame(Game):
    def __init__(self):
        self.teamSize = 2
        Game.__init__(self, PLAYER_DATABASE_FILE_DOUBLES, PLAYER_DATABASE_FILE_DOUBLES_UPDATE, RAW_GAME_DATA_FILE_DOUBLES, self.teamSize)

    def setTeamRatings(self):
        team1Average = (self.playerRatingsOld[0] + self.playerRatingsOld[1] )/2
        team2Average = (self.playerRatingsOld[2] + self.playerRatingsOld[3] )/2
        self.teamRatingsOld = [team1Average, team2Average]

if __name__ == '__main__':
    typeOfGame = input("\nWelcome!\nAre you interested in Singles (press S) or Doubles (press D)?\n")
    if typeOfGame == 'S':
        game = SingleGame()
    elif typeOfGame == 'D':
        game = DoubleGame()
    else:
        print("\nNot a valid option chosen, exiting now.\n")
        exit(1)

    functionality = input("\nPlease choose one of the following options:\n1. Add a new player (press P)\n2. Add a new game result (press G)\n3. Show the current ranking (press R)\n")
    if functionality == 'P':
        game.addNewPlayer()
    elif functionality == 'G':
        game.queryPlayerNames()
        while(True):
            game.addNewGameResult()
            print("\nYou could add a new game result if you want, you can at all times exit by ctrl-C or entering an invalid option.")
    elif functionality == 'R':
        game.printRanking()
    else:
        print("Not a valid option chosen, exiting now.")
        exit(1)
