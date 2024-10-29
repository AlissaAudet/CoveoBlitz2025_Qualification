import heapq

from game_message import *
import random


class Bot:
    def __init__(self):
        print("Initializing your super mega duper bot")

    def get_next_move(self, game_message: TeamGameState):
        """
        Here is where the magic happens, for now the moves are not very good. I bet you can do better ;)
        """
        actions = []
        threats = game_message.threats
        current_position = game_message.yourCharacter.position
        map_width = game_message.map.width
        map_height = game_message.map.height

        directions = {
            "MOVE_UP": Position(current_position.x, current_position.y - 1),
            "MOVE_DOWN": Position(current_position.x, current_position.y + 1),
            "MOVE_LEFT": Position(current_position.x - 1, current_position.y),
            "MOVE_RIGHT": Position(current_position.x + 1, current_position.y)
        }

        valid_moves = []
        for action, position in directions.items():
            if 0 <= position.x < map_width and 0 <= position.y < map_height:
                if game_message.map.tiles[position.y][position.x] != TileType.WALL:
                    valid_moves.append((action, position))

        if not valid_moves:
            return []

        move_distances = []
        for action, position in valid_moves:
            min_distance = float("inf")
            for threat in threats:
                distance = abs(position.x - threat.position.x) + abs(position.y - threat.position.y)
                if distance < min_distance:
                    min_distance = distance
            heapq.heappush(move_distances, (-min_distance, action))


        _, best_action = heapq.heappop(move_distances)

        if best_action == "MOVE_UP":
            actions.append(MoveUpAction())
        elif best_action == "MOVE_DOWN":
            actions.append(MoveDownAction())
        elif best_action == "MOVE_LEFT":
            actions.append(MoveLeftAction())
        elif best_action == "MOVE_RIGHT":
            actions.append(MoveRightAction())

        return actions

