import time
import random
import heapq
from itertools import count
from game_message import (
    TeamGameState,
    Position,
    MoveLeftAction,
    MoveRightAction,
    MoveUpAction,
    MoveDownAction,
    MoveToAction,
    TileType,
)
"""  Problème Le bot détecte mal les mur.
"""
class Bot:
    def __init__(self):
        self.tick = 0
        self.counter = count()
        self.last_move = None
        self.previous_positions = []

    def get_next_move(self, game_state: TeamGameState):
        start_time = time.perf_counter()
        self.tick += 1
        your_car = game_state.yourCharacter
        threats = game_state.threats
        position = your_car.position

        tiles = game_state.map.tiles

        # Convertir la carte en une grille
        grid = self.create_grid(tiles)

        # Obtenir les dimensions réelles de la grille
        height = len(grid)
        width = len(grid[0]) if height > 0 else 0

        # Afficher la position du bot
        print(f"Tick {self.tick}: Position du bot: ({position.x}, {position.y})")

        # Afficher les positions réelles des menaces
        print(
            f"Tick {self.tick}: Positions réelles des menaces : {[(threat.position.x, threat.position.y) for threat in threats]}")

        # Afficher les directions des menaces
        print(f"Tick {self.tick}: Directions des menaces : {[threat.direction for threat in threats]}")

        # Prédire les positions des menaces
        threat_positions = self.predict_threat_positions(threats, width, height)

        # Afficher les positions des menaces prédites pour le débogage
        print(
            f"Tick {self.tick}: Positions des menaces (prédites) : {[(t_pos.x, t_pos.y) for t_pos in threat_positions]}")

        # Mettre à jour la grille avec les menaces prédites
        for t_pos in threat_positions:
            if 0 <= t_pos.y < height and 0 <= t_pos.x < width:
                grid[t_pos.y][t_pos.x] = 1  # Marquer comme obstacle

        # Trouver le meilleur mouvement d'évasion
        move_action = self.evade_threats(position, threats, grid)

        # Mesurer le temps d'exécution
        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000  # Convertir en millisecondes
        print(f"Tick {self.tick}: Temps d'exécution = {execution_time:.2f} ms")

        # Enregistrer le dernier mouvement pour éviter les allers-retours
        if move_action:
            self.last_move = move_action.type

        return [move_action]

    def create_grid(self, tiles):
        # Conversion des tuiles en une grille binaire
        grid = []
        for y, row in enumerate(tiles):
            grid_row = []
            for x, tile in enumerate(row):
                if tile == TileType.WALL:
                    grid_row.append(1)
                    print(f"Mur détecté à la position ({x}, {y})")  # Log pour vérifier chaque mur détecté
                else:
                    grid_row.append(0)
            grid.append(grid_row)

        # Affichage des dimensions réelles de la grille
        height = len(grid)
        width = len(grid[0]) if height > 0 else 0
        print(f"Dimensions de la grille générée: largeur = {width}, hauteur = {height}")

        print("Grille générée:")
        for row in grid:
            print("".join(["#" if cell == 1 else "." for cell in row]))

        return grid

    def predict_threat_positions(self, threats, width, height):
        threat_positions = []
        for threat in threats:
            t_pos = threat.position
            direction = threat.direction.upper()
            dx, dy = 0, 0
            if direction == 'UP':
                dy = -1
            elif direction == 'DOWN':
                dy = 1
            elif direction == 'LEFT':
                dx = -1
            elif direction == 'RIGHT':
                dx = 1
            else:
                dx, dy = 0, 0
            predicted_x = t_pos.x + dx
            predicted_y = t_pos.y + dy
            # Vérifier si la position prédite est dans les limites
            if 0 <= predicted_x < width and 0 <= predicted_y < height:
                predicted_pos = Position(x=predicted_x, y=predicted_y)
            else:
                predicted_pos = Position(x=t_pos.x, y=t_pos.y)
            threat_positions.append(predicted_pos)
        return threat_positions

    def will_threat_move_to(self, threat, x, y):
        direction = threat.direction.upper()
        dx, dy = 0, 0
        if direction == 'UP':
            dy = -1
        elif direction == 'DOWN':
            dy = 1
        elif direction == 'LEFT':
            dx = -1
        elif direction == 'RIGHT':
            dx = 1
        next_x = threat.position.x + dx
        next_y = threat.position.y + dy
        return next_x == x and next_y == y

    def find_safest_point(self, start: Position, grid, threat_positions):
        positions = []
        max_distance = -1
        height = len(grid)
        width = len(grid[0]) if height > 0 else 0
        for y in range(height):
            for x in range(width):
                if grid[y][x] == 0:
                    min_threat_distance = min(
                        abs(x - t_pos.x) + abs(y - t_pos.y) for t_pos in threat_positions
                    )
                    if min_threat_distance > max_distance:
                        max_distance = min_threat_distance
                        positions = [Position(x=x, y=y)]
                    elif min_threat_distance == max_distance:
                        positions.append(Position(x=x, y=y))
        if positions:
            safest_point = min(positions, key=lambda pos: abs(pos.x - start.x) + abs(pos.y - start.y))
            print(f"Point le plus sûr choisi: ({safest_point.x}, {safest_point.y}) avec distance {max_distance}")
            return safest_point
        else:
            # Si aucune position sûre n'est trouvée, rester sur place
            return start

    def find_safest_path(self, start_pos, grid, threat_positions):
        # Fonction  l'algorithme A*
        def heuristic(a: Position, b: Position):
            return abs(a.x - b.x) + abs(a.y - b.y)

        start = Position(x=start_pos.x, y=start_pos.y)
        goal = self.find_safest_point(start, grid, threat_positions)

        open_set = []
        heapq.heappush(open_set, (0, next(self.counter), start))
        came_from = {}
        g_score = {(start.x, start.y): 0}
        f_score = {(start.x, start.y): heuristic(start, goal)}

        while open_set:
            current = heapq.heappop(open_set)[2]  # Récupérer l'élément Position

            if current.x == goal.x and current.y == goal.y:
                # Reconstruire le chemin
                path = [current]
                while (current.x, current.y) in came_from:
                    current = came_from[(current.x, current.y)]
                    path.append(current)
                path.reverse()
                return path

            neighbors = self.get_neighbors(current, grid)
            for neighbor in neighbors:
                tentative_g_score = g_score[(current.x, current.y)] + 1
                neighbor_pos = (neighbor.x, neighbor.y)
                if neighbor_pos not in g_score or tentative_g_score < g_score[neighbor_pos]:
                    came_from[neighbor_pos] = current
                    g_score[neighbor_pos] = tentative_g_score
                    f_score[neighbor_pos] = tentative_g_score + heuristic(neighbor, goal)
                    heapq.heappush(
                        open_set,
                        (f_score[neighbor_pos], next(self.counter), neighbor)
                    )

        print("Aucun chemin trouvé vers le point le plus sûr.")
        return None  # Aucun chemin trouvé

    def get_neighbors(self, pos: Position, grid):
        height = len(grid)
        width = len(grid[0]) if height > 0 else 0
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        neighbors = []
        for dx, dy in directions:
            nx, ny = pos.x + dx, pos.y + dy
            if 0 <= ny < height and 0 <= nx < width:
                if grid[ny][nx] == 0:
                    neighbors.append(Position(x=nx, y=ny))
        return neighbors

    def get_move_action(self, current_pos: Position, next_pos: Position):
        dx = next_pos.x - current_pos.x
        dy = next_pos.y - current_pos.y
        if dx == 1:
            return MoveRightAction()
        elif dx == -1:
            return MoveLeftAction()
        elif dy == 1:
            return MoveDownAction()
        elif dy == -1:
            return MoveUpAction()
        else:
            # Rester en place si aucun mouvement
            return MoveToAction(position=current_pos)

    def evade_threats(self, position: Position, threats, grid):
        height = len(grid)
        width = len(grid[0]) if height > 0 else 0
        directions = [
            ('MOVE_UP', (0, -1)),
            ('MOVE_DOWN', (0, 1)),
            ('MOVE_LEFT', (-1, 0)),
            ('MOVE_RIGHT', (1, 0)),
        ]
        moves = []
        for move_type, (dx, dy) in directions:
            nx, ny = position.x + dx, position.y + dy
            print(f"Position cible envisagée pour {move_type}: ({nx}, {ny})")

            # Vérifier les limites de la carte en premier lieu
            if not (0 <= nx < width and 0 <= ny < height):
                print(f"Position ({nx}, {ny}) est en dehors des limites. Mouvement {move_type} impossible.")
                continue

            # Vérifier s'il s'agit d'un mur
            if grid[ny][nx] == 1:
                print(f"Position ({nx}, {ny}) est un mur. Mouvement {move_type} impossible.")
                continue

            # Vérifier la présence d'une menace à cette position
            if any(threat.position.x == nx and threat.position.y == ny for threat in threats):
                print(f"Position ({nx}, {ny}) occupée par une menace. Mouvement {move_type} ignoré.")
                continue

            # Vérifier si une menace va se déplacer vers cette position
            if any(self.will_threat_move_to(threat, nx, ny) for threat in threats):
                print(f"Une menace va se déplacer vers ({nx}, {ny}). Mouvement {move_type} ignoré.")
                continue

            # Éviter le retour immédiat en arrière

            # Calculer la distance minimale aux menaces pour ce mouvement
            min_threat_distance = min(
                abs(nx - threat.position.x) + abs(ny - threat.position.y) for threat in threats
            )
            moves.append((min_threat_distance, move_type))
            print(
                f"Position ({nx}, {ny}) est libre. Mouvement {move_type} possible avec distance minimale aux menaces {min_threat_distance}.")

        if moves:
            # Choisir le mouvement avec la distance maximale aux menaces
            max_distance, best_move = max(moves)
            print(f"Mouvement d'évasion choisi: {best_move} avec distance minimale aux menaces {max_distance}.")
            if best_move == 'MOVE_UP':
                return MoveUpAction()
            elif best_move == 'MOVE_DOWN':
                return MoveDownAction()
            elif best_move == 'MOVE_LEFT':
                return MoveLeftAction()
            elif best_move == 'MOVE_RIGHT':
                return MoveRightAction()
        else:
            print("Aucun mouvement d'évasion possible. Le bot reste sur place.")
            return MoveToAction(position=position)
