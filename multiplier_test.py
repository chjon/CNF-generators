import sys
from pysat.solvers import Glucose3
from generate_multiplier import *

def test_multiplication():
    def test(x: int, y: int):
        # Generate instance
        nvars, clauses, x_vars, y_vars, out_vars = generate_forward_multiplication(x, y)
        g = Glucose3()
        for clause in clauses:
            g.add_clause(clause)
        
        # Perform multiplication by sat solving
        assert(g.solve())
        model = g.get_model()
        result = 0
        for i, o in enumerate(out_vars):
            result |= (1 << i) if model[o - 1] > 0 else 0

        # Perform multiplication normally
        expected = x * y
        assert(result == expected)

    for x in range(0, 31):
        for y in range(0, 31):
            test(x, y)

def test_factoring():
    def test(c: int):
        # Generate instance
        nvars, clauses, x_vars, y_vars, out_vars = generate_backward_multiplication(c)
        g = Glucose3()
        for clause in clauses:
            g.add_clause(clause)
        
        # Perform factoring by sat solving
        sat = g.solve()
        if sat:
            model = g.get_model()
            x = 0
            for i, v in enumerate(x_vars):
                x |= (1 << i) if model[v - 1] > 0 else 0
            y = 0
            for i, v in enumerate(y_vars):
                y |= (1 << i) if model[v - 1] > 0 else 0

            return (y, x) if x > y else (x, y)
        else:
            return None

    assert(test(1)  == None)
    assert(test(2)  == None)
    assert(test(3)  == None)
    assert(test(5)  == None)
    assert(test(8)  == (2, 4))
    assert(test(13) == None)
    assert(test(21) == (3, 7))
    assert(test(44) != None)
    assert(test(65) == (5, 13))

def test_commutativity():
    def test(n: int):
        # Generate instance
        nvars, clauses = generate_commutativity(n)
        g = Glucose3()
        for clause in clauses:
            g.add_clause(clause)
        
        # Must be commutative
        assert(not g.solve())
    
    test(1)
    test(2)
    test(3)
    test(4)

if __name__ == '__main__':
    test_multiplication()
    test_factoring()
    test_commutativity()