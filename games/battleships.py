import sys
from pysat.card import *
from pysat.formula import *
from pysat.solvers import Glucose3

def parse_battleships_game(filepath: str):
    dim = 0
    data = []
    ships = []
    col_constraints = []
    row_constraints = []
    
    try:
        f = open(filepath)

        # Parse header
        line = f.readline().strip().split(' ')
        assert(len(line) == 4)
        assert(line[0] == 'n')
        dim = int(line[1])
        assert(line[2] == 's')
        ship_count = int(line[3])
        data = [['.'] * dim for i in range(dim)]

        # Parse board
        for y in range(dim):
            line = f.readline().strip()
            assert(len(line) == dim + 1)
            for x in range(dim):
                data[y][x] = line[x]
            row_constraints.append(int(line[dim]))
        line = f.readline().strip()
        for y in range(dim):
            col_constraints.append(int(line[y]))
            
        # Read ship types
        for s in range(ship_count):
            line = f.readline().strip().split(' ')
            assert(len(line) == 4)
            assert(line[0] == 'l')
            length = int(line[1])
            assert(line[2] == 'c')
            count = int(line[3])
            ships.append((length, count))

    except Exception as e:
        print(f"Failed to read file {filepath}")
        print(e)

    return data, ships, col_constraints, row_constraints

def print_battleships_game(data, col_constraints=None, row_constraints=None):
    dim = len(data)
    for y in range(dim):
        for x in range(dim):
            print(data[y][x], end='')
        if row_constraints != None:
            print(row_constraints[y])
        else: print()
    if col_constraints != None:
        for y in range(dim):
            print(col_constraints[y], end='')
        print()
    
class BattleshipsTile(Enum):
    EMPTY     = 0
    CIRCLE    = 1
    TRI_LEFT  = 2
    TRI_RIGHT = 3
    TRI_UP    = 4
    TRI_DOWN  = 5
    SQUARE    = 6

def encode_if_AND_then_OR(and_set, or_set):
    return [-a for a in and_set] + or_set

if __name__ == '__main__':
    # Validate input
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <PROBLEM_FILE> <MODE[0,1]>")
        exit()
    filepath = sys.argv[1]
    mode = int(sys.argv[2])
        
    # Parse file
    data, ships, col_constraints, row_constraints = \
        parse_battleships_game(filepath)
    if len(data) == 0:
        print(f"Failed to parse {filepath}")
        exit()
    # print_battleships_game(data, col_constraints, row_constraints)
    dim = len(data)
    cnf = CNF()
    vpool = IDPool()
    
    # Encode rules
    # Rule 1: every cell should have exactly one value
    for y in range(dim):
        for x in range(dim):
            cell_vars = [vpool.id(f'v_{x}_{y}_{t.value}') for t in BattleshipsTile]
            cnf.extend(CardEnc.equals(cell_vars, 1, vpool=vpool).clauses)
            
    # Rule 2: the number of ship segments in each row/col matches the contraints
    for y in range(dim):
        row_vars = [
            -vpool.id(f'v_{x}_{y}_{BattleshipsTile.EMPTY.value}')
            for x in range(dim)
        ]
        cnf.extend(CardEnc.equals(row_vars, row_constraints[y], vpool=vpool).clauses)
    for x in range(dim):
        col_vars = [
            -vpool.id(f'v_{x}_{y}_{BattleshipsTile.EMPTY.value}')
            for y in range(dim)
        ]
        cnf.extend(CardEnc.equals(col_vars, col_constraints[x], vpool=vpool).clauses)
        
    # Rule 3: The ship segments are surrounded by water
    for y in range(dim):
        for x in range(dim):
            shape_constraints = [
                (BattleshipsTile.CIRCLE,    [(1,0), (1,1), (0,1), (-1,1), (-1,0), (-1,-1), (0,-1), (1,-1)]),
                (BattleshipsTile.TRI_LEFT,  [       (1,1), (0,1), (-1,1), (-1,0), (-1,-1), (0,-1), (1,-1)]),
                (BattleshipsTile.TRI_RIGHT, [(1,0), (1,1), (0,1), (-1,1),         (-1,-1), (0,-1), (1,-1)]),
                (BattleshipsTile.TRI_UP,    [(1,0), (1,1),        (-1,1), (-1,0), (-1,-1), (0,-1), (1,-1)]),
                (BattleshipsTile.TRI_DOWN,  [(1,0), (1,1), (0,1), (-1,1), (-1,0), (-1,-1),         (1,-1)]),
                (BattleshipsTile.SQUARE,    [       (1,1),        (-1,1),         (-1,-1),         (1,-1)]),
            ]
            
            for constraint in shape_constraints:
                tile, directions = constraint
                for d in directions:
                    pos = (x + d[0], y + d[1])
                    if pos[0] == -1 or pos[0] == dim: continue
                    if pos[1] == -1 or pos[1] == dim: continue
                    cnf.append([
                        -vpool.id(f'v_{x}_{y}_{tile.value}'),
                        +vpool.id(f'v_{pos[0]}_{pos[1]}_{BattleshipsTile.EMPTY.value}')
                    ])
                    
    # Rule 4: ship segments must be connected
    for y in range(dim):
        for x in range(dim):
            # TRI_LEFT
            if x < dim-1:
                cnf.append([
                    -vpool.id(f'v_{x+0}_{y}_{BattleshipsTile.TRI_LEFT.value}'),
                    +vpool.id(f'v_{x+1}_{y}_{BattleshipsTile.TRI_RIGHT.value}'),
                    +vpool.id(f'v_{x+1}_{y}_{BattleshipsTile.SQUARE.value}'),
                ])
            else:
                cnf.append([-vpool.id(f'v_{x}_{y}_{BattleshipsTile.TRI_LEFT.value}')])
            # TRI_RIGHT
            if x > 0:
                cnf.append([
                    -vpool.id(f'v_{x+0}_{y}_{BattleshipsTile.TRI_RIGHT.value}'),
                    +vpool.id(f'v_{x-1}_{y}_{BattleshipsTile.TRI_LEFT.value}'),
                    +vpool.id(f'v_{x-1}_{y}_{BattleshipsTile.SQUARE.value}'),
                ])
            else:
                cnf.append([-vpool.id(f'v_{x}_{y}_{BattleshipsTile.TRI_RIGHT.value}')])
            # TRI_UP
            if y < dim-1:
                cnf.append([
                    -vpool.id(f'v_{x}_{y+0}_{BattleshipsTile.TRI_UP.value}'),
                    +vpool.id(f'v_{x}_{y+1}_{BattleshipsTile.TRI_DOWN.value}'),
                    +vpool.id(f'v_{x}_{y+1}_{BattleshipsTile.SQUARE.value}'),
                ])
            else:
                cnf.append([-vpool.id(f'v_{x}_{y}_{BattleshipsTile.TRI_UP.value}')])
            # TRI_DOWN
            if y > 0:
                cnf.append([
                    -vpool.id(f'v_{x}_{y+0}_{BattleshipsTile.TRI_DOWN.value}'),
                    +vpool.id(f'v_{x}_{y-1}_{BattleshipsTile.TRI_UP.value}'),
                    +vpool.id(f'v_{x}_{y-1}_{BattleshipsTile.SQUARE.value}'),
                ])
            else:
                cnf.append([-vpool.id(f'v_{x}_{y}_{BattleshipsTile.TRI_DOWN.value}')])
            # SQUARE
            if x == 1:
                cnf.append([
                    -vpool.id(f'v_{x+0}_{y}_{BattleshipsTile.SQUARE.value}'),
                    -vpool.id(f'v_{x-1}_{y}_{BattleshipsTile.SQUARE.value}'),
                ])
                cnf.append([
                    -vpool.id(f'v_{x+0}_{y}_{BattleshipsTile.TRI_RIGHT.value}'),
                    -vpool.id(f'v_{x-1}_{y}_{BattleshipsTile.SQUARE.value}'),
                ])
            if x == dim-2:
                cnf.append([
                    -vpool.id(f'v_{x+0}_{y}_{BattleshipsTile.SQUARE.value}'),
                    -vpool.id(f'v_{x+1}_{y}_{BattleshipsTile.SQUARE.value}'),
                ])
                cnf.append([
                    -vpool.id(f'v_{x+0}_{y}_{BattleshipsTile.TRI_LEFT.value}'),
                    -vpool.id(f'v_{x+1}_{y}_{BattleshipsTile.SQUARE.value}'),
                ])
            if y == 1:
                cnf.append([
                    -vpool.id(f'v_{x}_{y+0}_{BattleshipsTile.SQUARE.value}'),
                    -vpool.id(f'v_{x}_{y-1}_{BattleshipsTile.SQUARE.value}'),
                ])
                cnf.append([
                    -vpool.id(f'v_{x}_{y+0}_{BattleshipsTile.TRI_DOWN.value}'),
                    -vpool.id(f'v_{x}_{y-1}_{BattleshipsTile.SQUARE.value}'),
                ])
            if y == dim-2:
                cnf.append([
                    -vpool.id(f'v_{x}_{y+0}_{BattleshipsTile.SQUARE.value}'),
                    -vpool.id(f'v_{x}_{y+1}_{BattleshipsTile.SQUARE.value}'),
                ])
                cnf.append([
                    -vpool.id(f'v_{x}_{y+0}_{BattleshipsTile.TRI_UP.value}'),
                    -vpool.id(f'v_{x}_{y+1}_{BattleshipsTile.SQUARE.value}'),
                ])
            if x > 0 and x < dim-1:
                cnf.append(encode_if_AND_then_OR(
                    [+vpool.id(f'v_{x+0}_{y}_{BattleshipsTile.SQUARE.value}'),
                     +vpool.id(f'v_{x-1}_{y}_{BattleshipsTile.SQUARE.value}')],
                    [+vpool.id(f'v_{x+1}_{y}_{BattleshipsTile.SQUARE.value}'),
                     +vpool.id(f'v_{x+1}_{y}_{BattleshipsTile.TRI_RIGHT.value}')]
                ))
                cnf.append(encode_if_AND_then_OR(
                    [+vpool.id(f'v_{x+0}_{y}_{BattleshipsTile.SQUARE.value}'),
                     +vpool.id(f'v_{x-1}_{y}_{BattleshipsTile.TRI_LEFT.value}')],
                    [+vpool.id(f'v_{x+1}_{y}_{BattleshipsTile.SQUARE.value}'),
                     +vpool.id(f'v_{x+1}_{y}_{BattleshipsTile.TRI_RIGHT.value}')]
                ))
                cnf.append(encode_if_AND_then_OR(
                    [+vpool.id(f'v_{x+0}_{y}_{BattleshipsTile.SQUARE.value}'),
                     +vpool.id(f'v_{x+1}_{y}_{BattleshipsTile.SQUARE.value}')],
                    [+vpool.id(f'v_{x-1}_{y}_{BattleshipsTile.SQUARE.value}'),
                     +vpool.id(f'v_{x-1}_{y}_{BattleshipsTile.TRI_LEFT.value}')]
                ))
                cnf.append(encode_if_AND_then_OR(
                    [+vpool.id(f'v_{x+0}_{y}_{BattleshipsTile.SQUARE.value}'),
                     +vpool.id(f'v_{x-1}_{y}_{BattleshipsTile.TRI_RIGHT.value}')],
                    [+vpool.id(f'v_{x+1}_{y}_{BattleshipsTile.SQUARE.value}'),
                     +vpool.id(f'v_{x+1}_{y}_{BattleshipsTile.TRI_LEFT.value}')]
                ))
            if y > 0 and y < dim-1:
                cnf.append(encode_if_AND_then_OR(
                    [+vpool.id(f'v_{x}_{y+0}_{BattleshipsTile.SQUARE.value}'),
                     +vpool.id(f'v_{x}_{y-1}_{BattleshipsTile.SQUARE.value}')],
                    [+vpool.id(f'v_{x}_{y+1}_{BattleshipsTile.SQUARE.value}'),
                     +vpool.id(f'v_{x}_{y+1}_{BattleshipsTile.TRI_DOWN.value}')]
                ))
                cnf.append(encode_if_AND_then_OR(
                    [+vpool.id(f'v_{x}_{y+0}_{BattleshipsTile.SQUARE.value}'),
                     +vpool.id(f'v_{x}_{y-1}_{BattleshipsTile.TRI_UP.value}')],
                    [+vpool.id(f'v_{x}_{y+1}_{BattleshipsTile.SQUARE.value}'),
                     +vpool.id(f'v_{x}_{y+1}_{BattleshipsTile.TRI_DOWN.value}')]
                ))
                cnf.append(encode_if_AND_then_OR(
                    [+vpool.id(f'v_{x}_{y+0}_{BattleshipsTile.SQUARE.value}'),
                     +vpool.id(f'v_{x}_{y+1}_{BattleshipsTile.SQUARE.value}')],
                    [+vpool.id(f'v_{x}_{y-1}_{BattleshipsTile.SQUARE.value}'),
                     +vpool.id(f'v_{x}_{y-1}_{BattleshipsTile.TRI_UP.value}')]
                ))
                cnf.append(encode_if_AND_then_OR(
                    [+vpool.id(f'v_{x}_{y+0}_{BattleshipsTile.SQUARE.value}'),
                     +vpool.id(f'v_{x}_{y+1}_{BattleshipsTile.TRI_DOWN.value}')],
                    [+vpool.id(f'v_{x}_{y-1}_{BattleshipsTile.SQUARE.value}'),
                     +vpool.id(f'v_{x}_{y-1}_{BattleshipsTile.TRI_UP.value}')]
                ))
            neighbours = []
            if x > 0:
                neighbours.append(-vpool.id(f'v_{x-1}_{y}_{BattleshipsTile.EMPTY.value}'))
            if x < dim-1:
                neighbours.append(-vpool.id(f'v_{x+1}_{y}_{BattleshipsTile.EMPTY.value}'))
            if y > 0:
                neighbours.append(-vpool.id(f'v_{x}_{y-1}_{BattleshipsTile.EMPTY.value}'))
            if y < dim-1:
                neighbours.append(-vpool.id(f'v_{x}_{y+1}_{BattleshipsTile.EMPTY.value}'))
            cnf.append(encode_if_AND_then_OR(
                [vpool.id(f'v_{x}_{y}_{BattleshipsTile.SQUARE.value}')],
                neighbours))
    
    # Rule 5: Ship counts should match the provided ship counts
    
    # Encode board
    for y in range(dim):
        for x in range(dim):
            if data[y][x] == 'o':
                cnf.append([vpool.id(f'v_{x}_{y}_{BattleshipsTile.CIRCLE.value}')])
            elif data[y][x] == '<':
                cnf.append([vpool.id(f'v_{x}_{y}_{BattleshipsTile.TRI_LEFT.value}')])
            elif data[y][x] == '>':
                cnf.append([vpool.id(f'v_{x}_{y}_{BattleshipsTile.TRI_RIGHT.value}')])
            elif data[y][x] == '^':
                cnf.append([vpool.id(f'v_{x}_{y}_{BattleshipsTile.TRI_UP.value}')])
            elif data[y][x] == 'v':
                cnf.append([vpool.id(f'v_{x}_{y}_{BattleshipsTile.TRI_DOWN.value}')])
            elif data[y][x] == 's':
                cnf.append([vpool.id(f'v_{x}_{y}_{BattleshipsTile.SQUARE.value}')])
    
    if mode == 1:
        print(cnf.to_dimacs())
    else:
        print("Solving...")

        # Solve instance
        g = Glucose3()
        for clause in cnf.clauses:
            g.add_clause(clause)
        if g.solve():
            # Decode model into solution
            model = g.get_model()
            soln = [['.'] * dim for y in range(dim)]
            for y in range(dim):
                for x in range(dim):
                    for t in BattleshipsTile:
                        if model[vpool.id(f'v_{x}_{y}_{t.value}') - 1] > 0:
                            soln[y][x] = '.o<>^vs'[t.value]
            print_battleships_game(soln)
        else:
            print("UNSAT")