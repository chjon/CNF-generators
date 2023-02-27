from pysat.solvers import Glucose3
from generate_multiplier import generate_forward_multiplication

if __name__ == '__main__':
    for x in range(0, 31):
        for y in range(0, 31):
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