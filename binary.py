import sys
from pysat.card import *
from pysat.formula import *
from pysat.solvers import Glucose3

def parse_binary_game(filepath: str):
    dim = 0
    data = []
    
    try:
        f = open(filepath)

        # Parse header
        line = f.readline().strip().split(' ')
        assert(len(line) == 2)
        assert(line[0] == 'n')
        dim = 2 * int(line[1])
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

def print_binary_game(data):
    for line in data:
        for c in line:
            print(c, end='')
        print()

if __name__ == '__main__':
    # Validate input
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <PROBLEM_FILE> <MODE[0,1]>")
        exit()
    filepath = sys.argv[1]
    mode = int(sys.argv[2])
        
    # Parse file
    data = parse_binary_game(filepath)
    if len(data) == 0:
        print(f"Failed to parse {filepath}")
        exit()
    # print_binary_game(data)
    dim = len(data)
    n = dim // 2
    cnf = CNF()
    vpool = IDPool()
    
    # Encode rules
    # Rule 1: every row and column should have n 0s and n 1s
    for y in range(dim):
        row_vars = [vpool.id(f'v_{x}_{y}') for x in range(dim)]
        cnf.extend(CardEnc.equals(row_vars, n, vpool=vpool).clauses)
    for x in range(dim):
        col_vars = [vpool.id(f'v_{x}_{y}') for y in range(dim)]
        cnf.extend(CardEnc.equals(col_vars, n, vpool=vpool).clauses)
    
    # Rule 2: numbers cannot appear in more than 2 consecutive squares
    for y in range(dim):
        for x in range(dim - 2):
            row_seg_vars = [vpool.id(f'v_{x + i}_{y}') for i in range(3)]
            cnf.extend(CardEnc.atleast(row_seg_vars, 1, vpool=vpool).clauses)
            cnf.extend(CardEnc.atmost(row_seg_vars, 2, vpool=vpool).clauses)
    for x in range(dim):
        for y in range(dim - 2):
            row_seg_vars = [vpool.id(f'v_{x}_{y + i}') for i in range(3)]
            cnf.extend(CardEnc.atleast(row_seg_vars, 1, vpool=vpool).clauses)
            cnf.extend(CardEnc.atmost(row_seg_vars, 2, vpool=vpool).clauses)
            
    # Encode board
    for y in range(dim):
        for x in range(dim):
            v = vpool.id(f'v_{x}_{y}')
            if data[y][x] == '0':
                cnf.append([-v])
            elif data[y][x] == '1':
                cnf.append([v])
    
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
            for y in range(dim):
                for x in range(dim):
                    value = 1 if model[vpool.id(f'v_{x}_{y}') - 1] > 0 else 0
                    print(value, end=' ')
                print()
        else:
            print("UNSAT")