
import collections
import random

colorDict = {0: 'red', 1: 'yellow', 2: 'green', 3: 'blue', 4: 'white'}
colorsName = ['red', 'yellow', 'green', 'blue', 'white']
cardsNumber = {1: 3, 2: 2, 3: 2, 4: 2, 5: 1}
CARD_LIMIT = [3, 2, 2, 2, 1]


def ruleMatch(ruleNum: int, playerNum: int, hintTable: list, tableCards: dict, handSize: int, others: list, discards: list, players: list, usedNoteTokens: int) -> str:
    if ruleNum == None:
        ruleNum = random.choice(range(0, 22))
    playerToHint = None
    cardToHint = None
    cardToPlay = None
    cardToDiscard = None

    if ruleNum < 3:
        if ruleNum == 0:
            cardToPlay = rules[ruleNum](
                hintTable[playerNum], tableCards, handSize)
        elif ruleNum == 1:
            cardToPlay = rules[ruleNum](hintTable[playerNum], tableCards,
                                        handSize, others, discards)
        if ruleNum == 2:
            cardToPlay = rules[ruleNum](hintTable[playerNum], tableCards,
                                        handSize, others, discards, 0.8)
        if ruleNum == 3:
            cardToPlay = rules[ruleNum](hintTable[playerNum], tableCards,
                                        handSize, others, discards, 0.6)
        return 'play', [cardToPlay]
    elif 3 < ruleNum < 14 and usedNoteTokens < 8:
        if 3 < ruleNum < 9:
            playerToHint, cardToHint = rules[ruleNum](
                hintTable, tableCards, playerNum, players)
        if 9 < ruleNum < 13:
            playerToHint, cardToHint = rules[ruleNum](
                hintTable, playerNum, players)
        if ruleNum == 13:
            playerToHint, cardToHint = rules[ruleNum](playerNum, players)

        return 'hint', [playerToHint, cardToHint]
    elif 13 < ruleNum < 23 and usedNoteTokens > 0:
        if 13 < ruleNum < 16:
            cardToDiscard = rules[ruleNum](hintTable[playerNum], tableCards,
                                           discards, handSize)
        if ruleNum == 16:
            cardToDiscard = rules[ruleNum](
                hintTable[playerNum], discards, handSize)
        if 16 < ruleNum < 19:
            cardToDiscard = rules[ruleNum](
                hintTable[playerNum], tableCards, handSize)
        if ruleNum > 19:
            cardToDiscard = rules[ruleNum](hintTable[playerNum], handSize)
        return 'discard', [cardToDiscard]
    return None, None


def isPlayable(cardNum, cardColor, tableCards) -> bool:
    """Checks if the current card can be played at the moment. For the given color of the card, goes to the corresponding stack of cards
        and based on the amount of cards in it, sees if this new card can be placed on top.
        E.g. amount of cards = 3; card.value = 4 -> Can be placed"""

    if(len(tableCards[cardColor]) == cardNum-1):
        return True
    return False


def findKnown(hint):
    """Returns the value or color of a card if a hint of it is present in the hintTable passed as an argument"""
    for key, val in hint.items():
        if val == 1:
            return key
    return None

def playIfCertain(hintTable, tableCards, slots):
    """Tries to find a card with fully know information (value and color) in the hintTable. Then check if it isPlayable().
    If it passes this checks, it returns that card."""
    for slot in range(slots):
        val = findKnown(hintTable[slot].values)
        col = findKnown(hintTable[slot].colors)

        if val != None and col != None:
            if(isPlayable(val, col, tableCards)):
                return slot
            else:
                return None


def playSafeCard2(hintTable, tableCards, slots):
    cardsNum = []
    for slot in range(slots):
        try:
            possibleCards = list(
                hintTable[slot].values.values()).index(1)+1
            
            if(all(possibleCards == len(tableCards[colorDict[x]])+1 for x in range(5))):
                cardsNum.append(possibleCards)
        except ValueError:
            print(f"No known card value in slot: {slot}")
    if(cardsNum):
        # return the first card to be playable. There can be many, we may choose by some metric
        return cardsNum[0]
    else:
        return None

# Plays a card that is known to be playable(even with partial information)


def playSafeCard(hintTable, tableCards, slots, others, discards):
    """Plays a card that is known to be playable (even with partial information).  """
    others = [card for cards in others for card in cards]
    # for a slot it can be placed, regardless of the color
    cardsNum = []
    for slot in range(slots):
        prob = calcprob(hintTable[slot],
                        others, discards, tableCards)
        if(prob == 1):
            return slot
    return None


def getNumCards(values: list, colors: list, deck, fireworks=None):
    """Returns how many cards are still present for that values and that colors in a certain deck.
        If fireworks is present, the fireworks will be accounted"""
    n = 0
    for v in values:
        for col in colors:
            n += cardsNumber[v]
            n -= sum(1 for c in deck if c.value ==
                     v and c.color == col)
            if fireworks:
                n -= fireworks[col].count(v)
    return n

# Prob that card in numslot with that hint is playable

def calcprob(hint, others, discards, fireworks):
    """Calculates the probability of a card in numSlot of being playable, given a certain hint"""
    prob = 0
    for col in fireworks:
        p = 0
        val = 1 if not fireworks[col] else int(fireworks[col][-1].value) + 1

        possibleValues = [k for k in hint.values if hint.values[k] == 0]
        possibleColors = [k for k in hint.colors if hint.colors[k] == 0]

        # Finiamo nel caso partiallyknown1-value o partiallyknown1-color
        if(not len(possibleValues)):
            possibleValues = [k for k in hint.values if hint.values[k] == 1]
        if(not len(possibleColors)):
            possibleColors = [k for k in hint.colors if hint.colors[k] == 1]

        # Se tra i valori possibili non è listato il colore o il valore corrente, la probabilità è 0
        if(val not in possibleValues or col not in possibleColors):
            num = 0
            tot = 1
        else:
            # Get the numbers of the cards value-color still present (not played, nor discarded, nor present in other players hand)
            num = getNumCards([val], [col], others + discards, fireworks)
            tot = getNumCards(possibleValues, possibleColors,
                              others + discards, fireworks)
            if tot == 0:
                tot = 1


        prob += num/tot
    return prob


#

def playProbablySafeCard(hintTable, tableCards, slots, others, discards, p):
    """Plays card most likely to be playable if the probability of being playable is greater than p"""
    others = [card for cards in others for card in cards]

    probs = []
    for slot in range(slots):
        prob = calcprob(hintTable[slot],
                        others, discards, tableCards)

        probs.append(prob)
    # Put a threshold and if not return false
    return probs.index(max(probs)) if max(probs) > p else None

# ------------ #
#  HINT RULES  #
# ------------ #

def hintPartiallyKnown(hintTable, tableCards, playerWhoHints, players):
    """Tells the missing information (color or value) of a partially known playable card to a player"""
    playersArr = [p for p in range(len(players))]
    playersArr = playersArr[playerWhoHints:] + playersArr[:playerWhoHints]
    playersArr.remove(playerWhoHints)

    for p in playersArr:
        for slot in range(len(players[p].hand)):
            foundValue = any(
                el == 1 for el in hintTable[p][slot].values.values())
            foundColor = any(
                el == 1 for el in hintTable[p][slot].colors.values())

            if(isPlayable(players[p].hand[slot].value, players[p].hand[slot].color, tableCards)):
                if foundValue and not foundColor:  # in hintTable and in the players hand
                    return p, players[p].hand[slot].color
                elif not foundValue and foundColor:
                    return p, players[p].hand[slot].value
                else:
                    continue
    return None, 0

def hintUseful(hintTable, tableCards, playerWhoHints, players):
    """Tells a player some new information about one of their playable cards,
    prioritizing value if card is completely unknown."""

    playersArr = [p for p in range(len(players))]
    playersArr = playersArr[playerWhoHints:] + playersArr[:playerWhoHints]
    playersArr.remove(playerWhoHints)
    random.shuffle(playersArr)

    for p in playersArr:
        for slot in range(len(players[p].hand)):
            foundValue = any(
                el == 1 for el in hintTable[p][slot].values.values())
            foundColor = any(
                el == 1 for el in hintTable[p][slot].colors.values())

            if isPlayable(players[p].hand[slot].value, players[p].hand[slot].color, tableCards):
                if not foundValue and foundColor:  # in hintTable and in the players hand
                    return p, players[p].hand[slot].value
                elif foundValue and not foundColor:
                    return p, players[p].hand[slot].color
                elif not foundColor and not foundValue:
                    return p, players[p].hand[slot].value
            else:
                continue

    return None, 0


def hintOld(hintTable, tableCards, playerWhoHints, players):
    """Chooses a random player and hints him the oldest card it has"""

    playersArr = [p for p in range(len(players))]
    playersArr.remove(playerWhoHints)
    random.shuffle(playersArr)
    hint = 1
    age = 0

    break_out_flag = False
    found = False
    for p in playersArr:
        for slot in range(len(players[p].hand)):
            if isPlayable(players[p].hand[slot].value, players[p].hand[slot].color, tableCards):
                if hintTable[p][slot].age > age:
                    age = hintTable[p][slot].age
                    foundValue = any(
                        el == 1 for el in hintTable[p][slot].values.values())
                    foundColor = any(
                        el == 1 for el in hintTable[p][slot].colors.values())

                    # Added this part to avoid to hint a completely known card
                    if not foundValue:
                        hint = players[p].hand[slot].value
                        found = True
                    elif not foundColor:
                        found = True
                        hint = players[p].hand[slot].color
                    else:
                        continue
        if found:
            break
    if found:
        return p, hint
    return None, 0


def hintPlayable(hintTable, tableCards, playerWhoHints, players):
    """Hints a playable card, randomly chooses between color or value,
    even if it already partially knows it"""

    playersArr = [p for p in range(len(players))]
    playersArr.remove(playerWhoHints)
    random.shuffle(playersArr)

    for p in playersArr:
        for slot in range(len(players[p].hand)):
            if(isPlayable(players[p].hand[slot].value, players[p].hand[slot].color, tableCards)):
                foundValue = any(
                    el == 1 for el in hintTable[p][slot].values.values())
                foundColor = any(
                    el == 1 for el in hintTable[p][slot].colors.values())
                if foundValue and foundColor:
                    continue  # At least not hint a completely known card
                return p, random.choice([players[p].hand[slot].value,
                                        players[p].hand[slot].color])

    return None, 0


def hintUseless(hintTable, tableCards, playerWhoHints, players):
    """Hints a useless card. A card who's value is below the stack's (tableCard) top one for the given color"""""

    playersArr = [p for p in range(len(players))]
    playersArr.remove(playerWhoHints)
    random.shuffle(playersArr)

    for p in playersArr:
        for slot in range(len(players[p].hand)):
            # checks for the pile of the cards color if the amount (len()) of cards
            if len(tableCards[players[p].hand[slot].color]) >= players[p].hand[slot].value:
                # its higher than the card's number. If True > card won't be played
                if not any(el == 1 for el in hintTable[p][slot].values.values()):
                    # if the players doesn't know the value, I hint it
                    return p, players[p].hand[slot].value
                elif not any(el == 1 for el in hintTable[p][slot].colors.values()):
                    # if the players doesn't know the color, I hint it
                    return p, players[p].hand[slot].color
    return None, 0


def hintOnes(hintTable, playerWhoHints, players):
    """Hints cards with value one to the player that has the most of them"""
    playersArr = [p for p in range(len(players))]
    playersArr = playersArr[playerWhoHints:] + playersArr[:playerWhoHints]

    playersArr.remove(playerWhoHints)

    # First value: player number, Second value: amount of one cards in his hand
    maxOnePlayer = [None, 0]

    for p in playersArr:
        onesCount = 0
        for slot in range(len(players[p].hand)):
            # position number 0 in hintTable has the info of card value 1
            if hintTable[p][slot].values[1] == 1:
                continue  # The player p already knows about this one. See other slots
            if players[p].hand[slot].value == 1:
                onesCount += 1
        if onesCount > maxOnePlayer[1]:
            maxOnePlayer[0] = p
            maxOnePlayer[1] = onesCount
    if maxOnePlayer[1] > 0:
        return maxOnePlayer[0], 1
    else:
        return None, 0  # no player with one-value cards found


def hintFives(hintTable, playerWhoHints, players):
    """Tells a player about all their cards with value five"""

    playersArr = [p for p in range(len(players))]
    playersArr.remove(playerWhoHints)
    random.shuffle(playersArr)

    # First value: player number, Second value: amount of one cards in his hand
    maxOnePlayer = [None, 0]

    for p in playersArr:
        fivesCount = 0
        for slot in range(len(players[p].hand)):
            if hintTable[p][slot].values[5] == 1:
                continue  # The player p already knows about this five. See other slots
            if players[p].hand[slot].value == 5:
                fivesCount += 1
        if fivesCount > maxOnePlayer[1]:
            maxOnePlayer[0] = p
            maxOnePlayer[1] = fivesCount

    if maxOnePlayer[1] > 0:
        return maxOnePlayer[0], 5
    else:
        return None, 0  # no player with five-value cards found


def hintMostInfo(hintTable, playerWhoHints, players):
    """Hint whatever gives the most information to the player. Randomly chooses a player.
     It searches the hintTable for the least known info of the cards the player has in its hand.
     Then selects the most repeated information (color or value) and hints it."""

    # (given by amount of cards with same color or value)
    playersArr = [p for p in range(len(players))]
    playersArr.remove(playerWhoHints)
    p = random.choice(playersArr)

    color = {c: 0 for c in colorsName}  # (color name, #repetitions)
    value = {v: 0 for v in range(1, 6)}  # (value, #repetitions)

    for slot in range(len(players[p].hand)):
        # checks if the card's value/color the player p has in its hand has not been hinted yet
        if hintTable[p][slot].values[players[p].hand[slot].value] == 0:
            value[players[p].hand[slot].value] += 1

        if hintTable[p][slot].colors[players[p].hand[slot].color] == 0:
            color[players[p].hand[slot].color] += 1

    sortedColor = collections.OrderedDict({k: v for k, v in sorted(
        color.items(), key=lambda item: item[1], reverse=True)})
    sortedValue = collections.OrderedDict({k: v for k, v in sorted(
        value.items(), key=lambda item: item[1], reverse=True)})

    if next(iter(sortedColor.values())) >= next(iter(sortedValue.values())):
        return p, next(iter(sortedColor.keys()))
    else:
        return p, next(iter(sortedValue.keys()))  




def hintMostInfo2(hintTable, playerWhoHints, players):
    """Hint whatever gives the most information to the player"""
    playersArr = [p for p in range(len(players))]
    playersArr.remove(playerWhoHints)
    p = random.choice(playersArr)
    mi = 0
    maxCnt = 0
    maxInfo = None
    for col in colorsName:
        mi = len([card.value for slot, card in enumerate(players[p].hand)
                   if card.color == col and hintTable[p][slot].colors[card.color] == 0])
        if mi > maxCnt:
            maxInfo = col
            maxCnt = mi
    mi = 0
    for v in range(1, 6):
        mi = len([card.value for slot, card in enumerate(players[p].hand)
                   if card.value == v and hintTable[p][slot].values[card.value] == 0])
        if mi > maxCnt:
            maxInfo = v
            maxCnt = mi
    if maxInfo != None:
        return p, maxInfo
    return None, None


def hintUnkown(hintTable, playerWhoHints, players):
    """Hints to a random player unknown information about its cards."""
    playersArr = [p for p in range(len(players))]
    playersArr.remove(playerWhoHints)
    random.shuffle(playersArr)

    for p in playersArr:
        for slot in range(len(players[p].hand)):
            foundValue = any(
                el == 1 for el in hintTable[p][slot].values.values())
            foundColor = any(
                el == 1 for el in hintTable[p][slot].colors.values())
            if not foundValue and foundColor:
                return p, players[p].hand[slot].value
            elif foundValue and not foundColor:
                return p, players[p].hand[slot].color
            elif not foundColor and not foundValue:
                return p, players[p].hand[slot].value
            else:
                continue

    return None, 0

# Hint a random hint


def hintRandom(playerWhoHints, players):
    """Give a hint to a random player"""
    playersArr = [p for p in range(len(players))]
    playersArr.remove(playerWhoHints)
    p = random.choice(playersArr)

    # Check that chosen player
    if not players[p].hand:
        return None, 0

    # The hint could be of a card already known
    availableColors = list(dict.fromkeys(
        [card.color for card in players[p].hand]))
    availableValues = list(dict.fromkeys(
        [card.value for card in players[p].hand]))

    randomColor = random.choice(availableColors)
    randomValue = random.choice(availableValues)

    if randomColor and randomValue:
        return p, random.choice([randomColor, randomValue])
    return None, 0


# --------------- #
#  DISCARD RULES  #
# --------------- #



def discardUselessSafe(hintTable, tableCards, discards, slots):
    """Discards a card that is useless or safe.
        Useless card: one with a color/value for which there higher value/color cards have been already discarded"
        Safe Usless: the tableCards stack for the card's color has a higher value card on top that the one in question"""

    for slot in range(slots):
        val = findKnown(hintTable[slot].values)
        col = findKnown(hintTable[slot].colors)
        safe = False
        if val != None:
            # value 1 doesn't have prerequisites..
            if val == 1:
                continue
            prereq = val-1
            if col == None:
                n = getNumCards(
                    [prereq], [col for col in colorDict.values()], discards)
                safe = all([len(tableCards[col]) >= val for col in colorsName])
            else:
                n = getNumCards(
                    [prereq], [col], discards)
                safe = len(tableCards[col]) >= val
            if n == 0 or safe:
                return slot
    return None


def discardLeastLikelyToBeNecessary2(hintTable, tableCards, slots, discards):
    for slot in range(slots):
        val = findKnown(hintTable[slot].values)
        col = findKnown(hintTable[slot].colors)
        safe = False
        # Osawa
        if val != None:
            # value 1 doesn't have prerequisites..
            if val == 1:
                continue
            prereq = val-1
            if col == None:
                n = getNumCards(
                    [prereq], [col for col in colorDict.values()], discards)
                safe = all([len(tableCards[col]) >= val for col in colorsName])

            else:
                n = getNumCards(
                    [prereq], [col], discards)
                remaining = getNumCards(
                    [val], [col], discards)

                safe = len(tableCards[col]) >= val
            if n == 0 or safe:
                return slot
        # Cerca tra le carte quella giocabile con più occorrenze
    return None


def discardLeastLikelyToBeNecessary(handSize, hintTable, tableCards, discardedCards):
    return None
    _slots = [s for s in range(handSize)]
    necessarySlots = []
    notPlayableSlots = []
    for slot in _slots:
        if(any(el == 1 for el in hintTable[slot].values.values())
                and any(el == 1 for el in hintTable[slot].colors.values())):
            try:
                cardNum = list(hintTable
                               [slot].values.values()).index(1)+1
                cardColor = colorDict[list(
                    hintTable[slot].colors.values()).index(1)]

                # Card may be playable in the future
                if len(tableCards[cardColor]) < cardNum:
                    # Test if the card is the last of its kind.
                    if discardedCards[cardColor][cardNum]+1 == CARD_LIMIT[cardNum-1]:
                        # For this, I see if the discardedCards of that card are one from being all discarded/used
                        necessarySlots.append(slot)
                else:
                    notPlayableSlots.append(slot)
                    continue
            except ValueError:
                print(
                    f"discardLeastLikelyToBeNecessary: No known card value in slot: {slot}")
                continue

    notNecessarySlots = [s for s in _slots if s not in [
        *necessarySlots, *notPlayableSlots]]

    if (notPlayableSlots):
        return random.choice(notPlayableSlots)
    else:
        return None

def discardUseless(hintTable, discarded, slots):
    """Discards cards whose pre-requisites have been discarded.
        Assumption: I need to know the value to know the prerequisite"""
    for slot in range(slots):
        val = findKnown(hintTable[slot].values)
        col = findKnown(hintTable[slot].colors)
        if val != None:
            # value 1 doesn't have prerequisites..
            if val == 1:
                continue
            prereq = val-1
            if col == None:
                n = getNumCards(
                    [prereq], [col for col in colorDict.values()], discarded)
            else:
                n = getNumCards(
                    [prereq], [col], discarded)
            if n == 0:
                return slot
    return None


def discardSafe(hintTable, tableCards, slots):
    """Discards that is no longer playable. A card is not playable if 
        the tableCards stack for the card's color has a higher value card on top that the one in question """
    safe = False
    for slot in range(slots):
        val = findKnown(hintTable[slot].values)
        col = findKnown(hintTable[slot].colors)
        if val != None and col == None:
            safe = all([len(tableCards[col]) >= val for col in colorsName])
        elif val != None and col != None:
            safe = (len(tableCards[col]) >= val)
        if safe:
            return slot
    return None


def discardIfCertain(hintTable, tableCards, slots):
    """Discards a card that with fully known information and no longer playable
        (same as discardSafe but with just fully known information)"""
    for slot in range(slots):
        val = findKnown(hintTable[slot].values)
        col = findKnown(hintTable[slot].colors)
        if val != None and col != None:
            if(len(tableCards[col]) >= val):
                return slot
    return None


def discardHighest(hintTable, slots):
    """Discards card in hand with highest known value"""
    slotToDiscard = None
    highestValue = 0
    for slot in range(slots):
        val = findKnown(hintTable[slot].values)
        if val == None:
            continue
        if val > highestValue:
            slotToDiscard = slot
    return slotToDiscard



def discardOldest(hintTable, slots):
    """Discards oldest card in hand."""
    slotToDiscard = None
    age = 0
    for slot in range(slots):
        if hintTable[slot].age > age:
            age = hintTable[slot].age
            slotToDiscard = slot

    if slotToDiscard == None:
        return None
    else:
        return slotToDiscard


def discardNoInfo(hintTable, slots):
    """Discards a card with no known information"""
    slotsToDiscard = []
    for slot in range(slots):
        val = findKnown(hintTable[slot].values)
        col = findKnown(hintTable[slot].colors)
        if val == None and col == None:
            return slot
    return None


def discardNoInfoOldest(hintTable, slots):
    """Discards oldest card with no known information"""
    slotToDiscard = None
    age = 0
    for slot in range(slots):
        val = findKnown(hintTable[slot].values)
        col = findKnown(hintTable[slot].colors)
        if val == None and col == None:
            if hintTable[slot].age > age:
                age = hintTable[slot].age
                slotToDiscard = slot
    if slotToDiscard == None:
        return None
    else:
        return slotToDiscard


# Array of rule functions
rules = [playIfCertain, playSafeCard, playProbablySafeCard, playProbablySafeCard,
         hintPartiallyKnown, hintUseful, hintOld, hintPlayable,
         hintUseless, hintOnes, hintFives, hintMostInfo2, hintUnkown, hintRandom,
         discardUselessSafe, discardLeastLikelyToBeNecessary, discardUseless, discardSafe, discardIfCertain,
         discardHighest, discardOldest, discardNoInfo, discardNoInfoOldest]


""" rules2 = {0: playIfCertain, 1: playSafeCard, 2: playProbablySafeCard,
          3: hintPartiallyKnown, 4: hintUseful, 5: hintOld,
          6: hintPlayable, 7: hintUseless, 8: hintOnes,
          9: hintFives, 10: hintMostInfo, 11: hintUnkown, 12: hintRandom,
          13: discardUselessSafe,
          14: discardLeastLikelyToBeNecessary,
          15: discardUseless,
          16: discardSafe,
          17: discardIfCertain,
          18: discardHighest,
          19: discardOldest,
          20: discardNoInfo,
          21: discardNoInfoOldest}
 """