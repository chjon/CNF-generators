import sys
from typing import List
from pysat.card import IDPool, CNF, CardEnc
from pysat.formula import *
from pysat.solvers import Glucose3

vpool: IDPool = IDPool()
Lit = int
Clause = List[Lit]

def encode_equal(e: Lit, a: Lit, b: Lit) -> List[Clause]:
    """
    Encodes e <-> (a = b)
    """
    return [
        [+e, +a, +b],
        [+e, -a, -b],
        [-e, +a, -b],
        [-e, -a, +b],
    ]

def encode_hamming_distance_eq(
    a_lits: List[Lit],
    b_lits: List[Lit],
    distance: int,
) -> List[Clause]:
    assert len(a_lits) == len(b_lits)
    assert 0 <= distance and distance <= len(a_lits)

    # Define helper variables to check whether the literals at each index in
    # a and b are equal
    eq_lits: List[Lit] = []
    clauses: List[Clause] = []
    for ai, bi in zip(a_lits, b_lits):
        ei = vpool.id(f"eq({ai},{bi})")
        eq_lits.append(-ei)
        clauses.extend(encode_equal(ei, ai, bi))

    # Encode that a and b differ at exactly one location
    clauses.extend(CardEnc.equals(eq_lits, 1, vpool=vpool).clauses)
    return clauses

def encode_hamming_distance_ge(
    a_lits: List[Lit],
    b_lits: List[Lit],
    distance: int
) -> List[Clause]:
    assert len(a_lits) == len(b_lits)
    assert 0 <= distance and distance <= len(a_lits)

    # Define helper variables to check whether the literals at each index in
    # a and b are equal
    eq_lits: List[Lit] = []
    clauses: List[Clause] = []
    for ai, bi in zip(a_lits, b_lits):
        ei = vpool.id(f"eq({ai},{bi})")
        eq_lits.append(-ei)
        clauses.extend(encode_equal(ei, ai, bi))

    # Encode that the hamming distance is at least the given distance
    clauses.extend(CardEnc.atleast(eq_lits, distance, vpool=vpool).clauses)
    return clauses

def encode_snake_in_box(hypercube_dimension: int, snake_length: int) -> List[Clause]:
    # The path follows edges of the hypercube
    # i.e. Hamming distance = 1 between vertices adjacent on the path
    clauses: List[Clause] = []
    for i in range(snake_length - 1):
        a = [vpool.id(f"d({i+0},{j})") for j in range(hypercube_dimension)]
        b = [vpool.id(f"d({i+1},{j})") for j in range(hypercube_dimension)]
        clauses.extend(encode_hamming_distance_eq(a, b, 1))

    # Hamming distance >= 2 between vertices non-adjacent on the path
    for i in range(0, snake_length - 1):
        for j in range(i + 2, snake_length):
            a = [vpool.id(f"d({i},{k})") for k in range(hypercube_dimension)]
            b = [vpool.id(f"d({j},{k})") for k in range(hypercube_dimension)]
            clauses.extend(encode_hamming_distance_ge(a, b, 2))

    # The path starts from the origin
    clauses.extend([[-vpool.id(f"d(0,{i})")] for i in range(hypercube_dimension)])
    return clauses

def print_dimacs(clauses: List[Clause], file = sys.stdout) -> None:
    print(f"p cnf {vpool._next() + 1} {len(clauses)}", file=file)
    for clause in clauses:
        print(f"{' '.join([str(l) for l in clause])} 0", file=file)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <HYPERCUBE_DIMENSION> <SNAKE_LENGTH>")
        exit(1)

    hypercube_dimension = int(sys.argv[1])
    snake_length = int(sys.argv[2]) + 1

    assert hypercube_dimension >= 1
    assert 1 <= snake_length
    assert snake_length <= 2 ** hypercube_dimension

    clauses = encode_snake_in_box(hypercube_dimension, snake_length)
    print_dimacs(clauses)
