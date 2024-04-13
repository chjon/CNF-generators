from enum import Enum
import sys
from pysat.card import *
from pysat.formula import *
from pysat.solvers import Glucose3

def parse_bridges_game(filepath: str):
    dim = 0
    data = []
    
    try:
        f = open(filepath)

        # Parse header
        line = f.readline().strip().split(' ')
        assert(len(line) == 2)
        assert(line[0] == 'n')
        dim = int(line[1])
        data = [['.'] * dim for i in range(dim)]

        # Parse board
        for y in range(dim):
            line = f.readline().strip()
            assert(len(line) == dim)
            for x in range(dim):
                data[y][x] = line[x]

    except Exception as e:
        print(f"Failed to read file {filepath}")
        print(e)

    return data

def encode_if_AND_then_OR(and_set, or_set):
    return [-a for a in and_set] + or_set

def print_bridges_game(data):
    for line in data:
        for c in line:
            print(c, end='')
        print()

class BridgeTile(Enum):
    EMPTY     = 0
    ISLAND    = 1
    SINGLE_H  = 2
    SINGLE_V  = 3
    DOUBLE_H  = 4
    DOUBLE_V  = 5

if __name__ == '__main__':
    # Validate input
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <PROBLEM_FILE> <MODE[0,1]>")
        exit()
    filepath = sys.argv[1]
    mode = int(sys.argv[2])
        
    # Parse file
    data = parse_bridges_game(filepath)
    if len(data) == 0:
        print(f"Failed to parse {filepath}")
        exit()
    # print_bridges_game(data)
    dim = len(data)
    
    # Encode rules
    cnf = CNF()
    vpool = IDPool()
    
    # Rule 1: every cell can be exactly one type of tile
    for y in range(dim):
        for x in range(dim):
            cell_vars = [vpool.id(f'v_{x}_{y}_{t.value}') for t in BridgeTile]
            cnf.extend(CardEnc.equals(cell_vars, 1, vpool=vpool).clauses)
            
    # Rule 2: bridges must be connected to islands
    for y in range(dim):
        for x in [0, dim-1]:
            for t in [BridgeTile.SINGLE_H, BridgeTile.DOUBLE_H]:
                cnf.append([-vpool.id(f'v_{x}_{y}_{t.value}')])
    for x in range(dim):
        for y in [0, dim-1]:
            for t in [BridgeTile.SINGLE_V, BridgeTile.DOUBLE_V]:
                cnf.append([-vpool.id(f'v_{x}_{y}_{t.value}')])
    for y in range(0, dim):
        for x in range(0, dim-1):
            for t in [BridgeTile.SINGLE_H, BridgeTile.DOUBLE_H]:
                cnf.append([
                    -vpool.id(f'v_{x}_{y}_{t.value}'),
                    +vpool.id(f'v_{x+1}_{y}_{BridgeTile.ISLAND.value}'),
                    +vpool.id(f'v_{x+1}_{y}_{t.value}'),
                ])
                cnf.append([
                    -vpool.id(f'v_{x+1}_{y}_{t.value}'),
                    +vpool.id(f'v_{x}_{y}_{BridgeTile.ISLAND.value}'),
                    +vpool.id(f'v_{x}_{y}_{t.value}'),
                ])
    for y in range(0, dim-1):
        for x in range(0, dim):
            for t in [BridgeTile.SINGLE_V.value, BridgeTile.DOUBLE_V.value]:
                cnf.append([
                    -vpool.id(f'v_{x}_{y}_{t}'),
                    +vpool.id(f'v_{x}_{y+1}_{BridgeTile.ISLAND.value}'),
                    +vpool.id(f'v_{x}_{y+1}_{t}'),
                ])
                cnf.append([
                    -vpool.id(f'v_{x}_{y+1}_{t}'),
                    +vpool.id(f'v_{x}_{y}_{BridgeTile.ISLAND.value}'),
                    +vpool.id(f'v_{x}_{y}_{t}'),
                ])
    
    # Rule 3: Islands must have the correct number of bridges
    for y in range(dim):
        for x in range(dim):
            if data[y][x] == '.':
                cnf.append([-vpool.id(f'v_{x}_{y}_{BridgeTile.ISLAND.value}')])
                continue
            else:
                cnf.append([+vpool.id(f'v_{x}_{y}_{BridgeTile.ISLAND.value}')])
            
            bridge_count_vars = []
            if (x > 0):
                b0 = vpool.id(f'b_{x}_{y}_l_{0}')
                b1 = vpool.id(f'b_{x}_{y}_l_{1}')
                bridge_count_vars.extend([b0, b1])
                t_single = vpool.id(f'v_{x-1}_{y}_{BridgeTile.SINGLE_H.value}')
                t_double = vpool.id(f'v_{x-1}_{y}_{BridgeTile.DOUBLE_H.value}')
                cnf.append(encode_if_AND_then_OR([-b0, -b1], [-t_single]))
                cnf.append(encode_if_AND_then_OR([-b0, -b1], [-t_double]))
                cnf.append(encode_if_AND_then_OR([+b0, -b1], [+t_single]))
                cnf.append(encode_if_AND_then_OR([-b0, +b1], [+t_single]))
                cnf.append(encode_if_AND_then_OR([+b0, +b1], [+t_double]))
            if (x < dim - 1):
                b0 = vpool.id(f'b_{x}_{y}_r_{0}')
                b1 = vpool.id(f'b_{x}_{y}_r_{1}')
                bridge_count_vars.extend([b0, b1])
                t_single = vpool.id(f'v_{x+1}_{y}_{BridgeTile.SINGLE_H.value}')
                t_double = vpool.id(f'v_{x+1}_{y}_{BridgeTile.DOUBLE_H.value}')
                cnf.append(encode_if_AND_then_OR([-b0, -b1], [-t_single]))
                cnf.append(encode_if_AND_then_OR([-b0, -b1], [-t_double]))
                cnf.append(encode_if_AND_then_OR([+b0, -b1], [+t_single]))
                cnf.append(encode_if_AND_then_OR([-b0, +b1], [+t_single]))
                cnf.append(encode_if_AND_then_OR([+b0, +b1], [+t_double]))
            if (y > 0):
                b0 = vpool.id(f'b_{x}_{y}_u_{0}')
                b1 = vpool.id(f'b_{x}_{y}_u_{1}')
                bridge_count_vars.extend([b0, b1])
                t_single = vpool.id(f'v_{x}_{y-1}_{BridgeTile.SINGLE_V.value}')
                t_double = vpool.id(f'v_{x}_{y-1}_{BridgeTile.DOUBLE_V.value}')
                cnf.append(encode_if_AND_then_OR([-b0, -b1], [-t_single]))
                cnf.append(encode_if_AND_then_OR([-b0, -b1], [-t_double]))
                cnf.append(encode_if_AND_then_OR([+b0, -b1], [+t_single]))
                cnf.append(encode_if_AND_then_OR([-b0, +b1], [+t_single]))
                cnf.append(encode_if_AND_then_OR([+b0, +b1], [+t_double]))
            if (y < dim - 1):
                b0 = vpool.id(f'b_{x}_{y}_d_{0}')
                b1 = vpool.id(f'b_{x}_{y}_d_{1}')
                bridge_count_vars.extend([b0, b1])
                t_single = vpool.id(f'v_{x}_{y+1}_{BridgeTile.SINGLE_V.value}')
                t_double = vpool.id(f'v_{x}_{y+1}_{BridgeTile.DOUBLE_V.value}')
                cnf.append(encode_if_AND_then_OR([-b0, -b1], [-t_single]))
                cnf.append(encode_if_AND_then_OR([-b0, -b1], [-t_double]))
                cnf.append(encode_if_AND_then_OR([+b0, -b1], [+t_single]))
                cnf.append(encode_if_AND_then_OR([-b0, +b1], [+t_single]))
                cnf.append(encode_if_AND_then_OR([+b0, +b1], [+t_double]))
            
            # Bridge count should match
            num_bridges = int(data[y][x])
            cnf.extend(CardEnc.equals(
                bridge_count_vars, num_bridges, vpool=vpool).clauses)
            
    # Rule 4: Islands must form a connected graph
    # Encoded using variables d_x_y_i meaning that (x,y) can be reached by a
    # path of length <= i from some starting point
    
    # 4.1: There is exactly one starting point
    starting_point_vars = []
    for y in range(dim):
        for x in range(dim):
            starting_point_vars.append(vpool.id(f'd_{x}_{y}_0'))
    cnf.extend(CardEnc.equals(starting_point_vars, 1, vpool=vpool).clauses)
    
    # 4.2 If a vertex can be reached by a path of length \leq i, it can be
    # reached by a path of length \leq i+1
    num_vertices = dim * dim
    for y in range(dim):
        for x in range(dim):
            for i in range(num_vertices - 1):
                cnf.append([
                    -vpool.id(f'd_{x}_{y}_{i}'),
                    vpool.id(f'd_{x}_{y}_{i+1}')
                ])
                    
    # 4.3 If a vertex u can be reached by a path of length \leq i, there is some
    # vertex v that can be reached by a path of length \leq i-1 s.t. u=v or u is
    # a neighbour of v
    for y in range(dim):
        for x in range(dim):
            for i in range(1, num_vertices - 1):
                neighbours = [vpool.id(f'd_{x}_{y}_{i-1}')]
                if (x > 0):
                    neighbours.append(vpool.id(f'd_{x-1}_{y}_{i-1}'))
                if (x < dim - 1):
                    neighbours.append(vpool.id(f'd_{x+1}_{y}_{i-1}'))
                if (y > 0):
                    neighbours.append(vpool.id(f'd_{x}_{y-1}_{i-1}'))
                if (y < dim - 1):
                    neighbours.append(vpool.id(f'd_{x}_{y+1}_{i-1}'))
                cnf.append(encode_if_AND_then_OR(
                    [vpool.id(f'd_{x}_{y}_{i}')],neighbours))
                
    # 4.4 A vertex can be reached iff it is not empty
    for y in range(dim):
        for x in range(dim):
            cnf.append([
                -vpool.id(f'v_{x}_{y}_{BridgeTile.EMPTY.value}'),
                -vpool.id(f'd_{x}_{y}_{num_vertices - 2}')])
            cnf.append([
                vpool.id(f'v_{x}_{y}_{BridgeTile.EMPTY.value}'),
                vpool.id(f'd_{x}_{y}_{num_vertices - 2}')])
                
    if mode == 1:
        print(cnf.to_dimacs())
    else:
        print("Solving...")

        # Solve instance
        g = Glucose3()
        for clause in cnf.clauses:
            g.add_clause(clause)
        if g.solve():
            model = g.get_model()
            spacing = '  '
            for y in range(dim):
                for x in range(dim):
                    for t in BridgeTile:
                        if model[vpool.id(f'v_{x}_{y}_{t.value}') - 1] > 0:
                            if   t == BridgeTile.EMPTY: print(' ', end=spacing)
                            elif t == BridgeTile.ISLAND: print(data[y][x], end=spacing)
                            elif t == BridgeTile.SINGLE_H: print('-', end=spacing)
                            elif t == BridgeTile.SINGLE_V: print('|', end=spacing)
                            elif t == BridgeTile.DOUBLE_H: print('=', end=spacing)
                            elif t == BridgeTile.DOUBLE_V: print('‖', end=spacing)
                            else: assert(False)
                print()
            print()
        else:
            print("UNSAT")