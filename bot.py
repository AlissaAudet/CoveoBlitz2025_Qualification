from game_message import *
import random
import heapq
from collections import deque

class Bot:
    def __init__(self):
        print("Initializing your super mega duper bot")
        self.last_move = None
        self.repeated_moves = 0
        self.visited_positions = deque(maxlen=10)  # Memory of last 10 positions
        self.safe_zones = []  # Pre-calculated safe zones

    def get_next_move(self, game_message: TeamGameState):
        actions = []
        threats = game_message.threats
        current_position = game_message.yourCharacter.position
        map_width = game_message.map.width
        map_height = game_message.map.height

        # Update safe zones
        self.update_safe_zones(game_message)

        directions = {
            "MOVE_UP": Position(current_position.x, current_position.y - 1),
            "MOVE_DOWN": Position(current_position.x, current_position.y + 1),
            "MOVE_LEFT": Position(current_position.x - 1, current_position.y),
            "MOVE_RIGHT": Position(current_position.x + 1, current_position.y)
        }

        valid_moves = []
        for action, position in directions.items():
            if 0 <= position.x < map_width and 0 <= position.y < map_height:
                if game_message.map.tiles[position.y][position.x] != TileType.WALL and position not in self.visited_positions:
                    valid_moves.append((action, position))

        if not valid_moves:
            return []

        move_scores = []
        for action, position in valid_moves:
            safety_score = self.evaluate_position_safety(position, threats, game_map=game_message.map, ticks_ahead=3)
            move_scores.append((safety_score, action))

        best_move = max(move_scores, key=lambda x: x[0])[1]

        if self.last_move is not None and best_move == self.last_move:
            self.repeated_moves += 1
        else:
            self.repeated_moves = 0
        self.last_move = best_move

        if self.repeated_moves > 3:
            alternative_moves = [move for move in valid_moves if move[0] != best_move]
            if alternative_moves:
                best_move = max(alternative_moves, key=lambda x: self.evaluate_position_safety(x[1], threats, game_map=game_message.map, ticks_ahead=3))[0]
            self.repeated_moves = 0

        # Add the current position to visited positions
        self.visited_positions.append(current_position)

        if best_move == "MOVE_UP":
            actions.append(MoveUpAction())
        elif best_move == "MOVE_DOWN":
            actions.append(MoveDownAction())
        elif best_move == "MOVE_LEFT":
            actions.append(MoveLeftAction())
        elif best_move == "MOVE_RIGHT":
            actions.append(MoveRightAction())

        return actions

    def evaluate_position_safety(self, position, threats, game_map, ticks_ahead=3):
        """
        Evaluate the safety of a position by considering the distance to threats over multiple ticks.
        """
        map_width = game_map.width
        map_height = game_map.height
        safety_score = 0

        for tick in range(1, ticks_ahead + 1):
            min_threat_distance = float("inf")
            for threat in threats:
                predicted_threat_position = self.predict_threat_position(threat, tick)
                if 0 <= predicted_threat_position.x < map_width and 0 <= predicted_threat_position.y < map_height:
                    distance = abs(position.x - predicted_threat_position.x) + abs(position.y - predicted_threat_position.y)
                    min_threat_distance = min(min_threat_distance, distance)
            safety_score += min_threat_distance

        # Add a bonus if the position is in a pre-calculated safe zone
        if position in self.safe_zones:
            safety_score += 10

        return safety_score

    def predict_threat_position(self, threat, ticks):
        position = threat.position
        for _ in range(ticks):
            if threat.direction == "UP":
                position = Position(position.x, max(0, position.y - 1))
            elif threat.direction == "DOWN":
                position = Position(position.x, min(position.y + 1, game_map.height - 1))
            elif threat.direction == "LEFT":
                position = Position(max(0, position.x - 1), position.y)
            elif threat.direction == "RIGHT":
                position = Position(min(position.x + 1, game_map.width - 1), position.y)
        return position

    def update_safe_zones(self, game_message):
        """
        Update the list of safe zones based on the current game state.
        """
        self.safe_zones.clear()
        map_width = game_message.map.width
        map_height = game_message.map.height

        for y in range(map_height):
            for x in range(map_width):
                position = Position(x, y)
                if game_message.map.tiles[y][x] != TileType.WALL:
                    # A position is considered safe if it's far from threats and not recently visited
                    if all(abs(position.x - threat.position.x) + abs(position.y - threat.position.y) > 3 for threat in game_message.threats):
                        if position not in self.visited_positions:
                            self.safe_zones.append(position)

        # Sort safe zones by distance from current position to prioritize closer zones
        current_position = game_message.yourCharacter.position
        self.safe_zones.sort(key=lambda pos: abs(pos.x - current_position.x) + abs(pos.y - current_position.y))
