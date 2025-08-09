import sys
from pysat.card import *
from pysat.formula import *
from pysat.solvers import Glucose3

def parse_diamond25_game(filepath: str):
    dim = 0
    data = []
    
    try:
        f = open(filepath)
        data = [line.strip() for line in f.readlines()]
        assert(len(data) == 8)
        for i in range(len(data) // 2):
            assert(len(data[i]) == 3 + 2 * i)
            assert(len(data[-i-1]) == 3 + 2 * i)

    except Exception as e:
        print(f"Failed to read file {filepath}")
        print(e)

    return data

def print_diamond25_game(data):
    spacing = ' '
    dim = len(data) // 2
    for i, line in enumerate(data):
        indent = (' ' + spacing) * (dim - i - 1) if i < dim else (' ' + spacing) * (i - dim)
        print(indent, end=spacing)
        for c in line:
            print(c, end=spacing)
        print()

def get_cell_vars(vpool, x, y):
    return [vpool.id(f'v_{x}_{y}_{v}') for v in range(9)]

if __name__ == '__main__':
    # Validate input
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <PROBLEM_FILE> <MODE[0,1]>")
        exit()
    filepath = sys.argv[1]
    mode = int(sys.argv[2])
        
    # Parse file
    data = parse_diamond25_game(filepath)
    if len(data) == 0:
        print(f"Failed to parse {filepath}")
        exit()
    # print_diamond25_game(data)
    
    # Encode rules
    cnf = CNF()
    vpool = IDPool()

    # Rule 1: every cell can only have one value (identified by the MSB)
    for y, line in enumerate(data):
        for x, c in enumerate(line):
            for v in range(1, 9):
                # v_{i} => v_{i-1}
                cnf.append([
                    -vpool.id(f'v_{x}_{y}_{v}'),
                    +vpool.id(f'v_{x}_{y}_{v-1}')
                ])
            cnf.append([vpool.id(f'v_{x}_{y}_{0}')])
                
    # 1.1: one-hot encode the number in a hexagon for comparison
    for y, line in enumerate(data):
        for x, c in enumerate(line):
            for v in range(0, 8):
                # o_i <=> (v_{i} ^ -v_{i+1})
                # o_i => v_{i}
                cnf.append([
                    -vpool.id(f'o_{x}_{y}_{v}'),
                    +vpool.id(f'v_{x}_{y}_{v}')
                ])
                # o_i => -v_{i+1}
                cnf.append([
                    -vpool.id(f'o_{x}_{y}_{v}'),
                    -vpool.id(f'v_{x}_{y}_{v+1}')
                ])
                # (v_{i} ^ -v_{i+1}) => o_i
                cnf.append([
                    -vpool.id(f'v_{x}_{y}_{v}'),
                    +vpool.id(f'v_{x}_{y}_{v+1}'),
                    +vpool.id(f'o_{x}_{y}_{v}')
                ])
                
            # o_8 <=> v_8
            cnf.append([
                -vpool.id(f'o_{x}_{y}_{8}'),
                +vpool.id(f'v_{x}_{y}_{8}')
            ])
            cnf.append([
                +vpool.id(f'o_{x}_{y}_{8}'),
                -vpool.id(f'v_{x}_{y}_{8}')
            ])
    
    # Rule 2: every hexagon should sum to 24
    dim = len(data) // 2
    for y in range(dim - 1):
        for x in range(0, 2 * (y + 1), 2):
            hex_vars = []
            hex_vars.extend(get_cell_vars(vpool, x+0, y+0))
            hex_vars.extend(get_cell_vars(vpool, x+1, y+0))
            hex_vars.extend(get_cell_vars(vpool, x+2, y+0))
            hex_vars.extend(get_cell_vars(vpool, x+1, y+1))
            hex_vars.extend(get_cell_vars(vpool, x+2, y+1))
            hex_vars.extend(get_cell_vars(vpool, x+3, y+1))
            cnf.extend(CardEnc.equals(hex_vars, 24, vpool=vpool).clauses)
    y = dim - 1
    for x in range(0, 2 * (y + 1), 2):
        hex_vars = []
        hex_vars.extend(get_cell_vars(vpool, x+0, y+0))
        hex_vars.extend(get_cell_vars(vpool, x+1, y+0))
        hex_vars.extend(get_cell_vars(vpool, x+2, y+0))
        hex_vars.extend(get_cell_vars(vpool, x+0, y+1))
        hex_vars.extend(get_cell_vars(vpool, x+1, y+1))
        hex_vars.extend(get_cell_vars(vpool, x+2, y+1))
        cnf.extend(CardEnc.equals(hex_vars, 24, vpool=vpool).clauses)
    for y in range(dim, 2 * dim - 1):
        for x in range(1, 2 * (2 * dim - y - 1), 2):
            hex_vars = []
            hex_vars.extend(get_cell_vars(vpool, x+0, y+0))
            hex_vars.extend(get_cell_vars(vpool, x+1, y+0))
            hex_vars.extend(get_cell_vars(vpool, x+2, y+0))
            hex_vars.extend(get_cell_vars(vpool, x-1, y+1))
            hex_vars.extend(get_cell_vars(vpool, x+0, y+1))
            hex_vars.extend(get_cell_vars(vpool, x+1, y+1))
            cnf.extend(CardEnc.equals(hex_vars, 24, vpool=vpool).clauses)
            
    # Rule 3: numbers cannot repeat within a hexagon
    for y in range(dim - 1):
        for x in range(0, 2 * (y + 1), 2):
            for v in range(9):
                hex_vars = [
                    vpool.id(f'o_{x+0}_{y+0}_{v}'),
                    vpool.id(f'o_{x+1}_{y+0}_{v}'),
                    vpool.id(f'o_{x+2}_{y+0}_{v}'),
                    vpool.id(f'o_{x+1}_{y+1}_{v}'),
                    vpool.id(f'o_{x+2}_{y+1}_{v}'),
                    vpool.id(f'o_{x+3}_{y+1}_{v}')
                ]
                cnf.extend(CardEnc.atmost(hex_vars, 1, vpool=vpool).clauses)
    y = dim - 1
    for x in range(0, 2 * (y + 1), 2):
        for v in range(9):
            hex_vars = [
                vpool.id(f'o_{x+0}_{y+0}_{v}'),
                vpool.id(f'o_{x+1}_{y+0}_{v}'),
                vpool.id(f'o_{x+2}_{y+0}_{v}'),
                vpool.id(f'o_{x+0}_{y+1}_{v}'),
                vpool.id(f'o_{x+1}_{y+1}_{v}'),
                vpool.id(f'o_{x+2}_{y+1}_{v}')
            ]
            cnf.extend(CardEnc.atmost(hex_vars, 1, vpool=vpool).clauses)
    for y in range(dim, 2 * dim - 1):
        for x in range(1, 2 * (2 * dim - y - 1), 2):
            for v in range(9):
                hex_vars = [
                    vpool.id(f'o_{x+0}_{y+0}_{v}'),
                    vpool.id(f'o_{x+1}_{y+0}_{v}'),
                    vpool.id(f'o_{x+2}_{y+0}_{v}'),
                    vpool.id(f'o_{x-1}_{y+1}_{v}'),
                    vpool.id(f'o_{x+0}_{y+1}_{v}'),
                    vpool.id(f'o_{x+1}_{y+1}_{v}')
                ]
                cnf.extend(CardEnc.atmost(hex_vars, 1, vpool=vpool).clauses)
            
    # Encode board
    for y, line in enumerate(data):
        for x, c in enumerate(line):
            if c == '.': continue
            num = int(c) - 1
            cnf.append([vpool.id(f'v_{x}_{y}_{num}')])
            cnf.append([-vpool.id(f'v_{x}_{y}_{num+1}')])
    
    if mode == 1:
        print(cnf.to_dimacs())
    else:
        print("Solving...")

        # Solve instance
        g = Glucose3()
        for clause in cnf.clauses:
            g.add_clause(clause)
        if g.solve():
            # Decode model into human readable format
            model = g.get_model()
            soln = []
            for y, line in enumerate(data):
                soln.append([])
                for x, c in enumerate(line):
                    max_val = 0
                    for v in range(1, 9):
                        if model[vpool.id(f'v_{x}_{y}_{v}') - 1] > 0:
                            max_val = v
                    soln[y].append(max_val + 1)
            print_diamond25_game(soln)
        else:
            print("UNSAT")