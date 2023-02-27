import sys
from typing import List

# Generate clauses encoding x <=> XOR(a, b, c)
def generate_3xor(x: int, a: int, b: int, c: int) -> List[List[int]]:
    return [
        [-x, a, b, c], [-x,-a,-b, c], [-x,-a, b,-c], [-x, a,-b,-c],
        [ x,-a,-b,-c], [ x, a, b,-c], [ x, a,-b, c], [ x,-a, b, c],
    ]

# Generate clauses encoding x <=> a + b + c > 1
def generate_3gt1(x: int, a: int, b: int, c: int) -> List[List[int]]:
    return [
        [ x,-a,-b], [ x,-a,-c], [ x,-b,-c],
        [-x, a, b], [-x, a, c], [-x, b, c],
    ]

def generate_multiplier_cnf(n: int, offset: int = 1):
    original_offset = offset

    # Step 0: define variables for the inputs
    x_vars = [ i + offset for i in range(n) ]
    offset += len(x_vars)
    y_vars = [ i + offset for i in range(n) ]
    offset += len(y_vars)

    # Step 1: generate all the bitwise multiplication variables
    mult_vars = [] # index by row, then column
    for row in range(n):
        row_vars = []
        for col in range(n):
            row_vars.append(offset + col)
        offset += len(row_vars)
        mult_vars.append(row_vars)

    # Step 2: generate all the bitwise multiplication clauses
    clauses = []
    for row, x_var in enumerate(x_vars):
        for col, y_var in enumerate(y_vars):
            # z <=> x AND y
            z = mult_vars[row][col]
            clauses += [
                [ z, -x_var, -y_var],
                [-z,  x_var],
                [-z,  y_var],
            ]

    # Step 3: generate all the output variables for the adders
    # note that the output of row 0 is just the multiplication variables
    adder_out_vars = []
    adder_out_vars.append(mult_vars[0])
    for row in range(n - 1):
        row_vars = []
        for col in range(n):
            row_vars.append(offset + col)
        offset += len(row_vars)
        adder_out_vars.append(row_vars)

    # Step 4: generate variable representing all the carries (starting from carry-in)
    adder_carry_vars = []
    for row in range(n):
        row_vars = []
        for col in range(n + 1): # Index n indicates an overflow
            row_vars.append(offset + col)
        offset += len(row_vars)
        adder_carry_vars.append(row_vars)

    # Step 5: set the carry bits of row 0 and column 0 to zero
    clauses += [ [-adder_carry_vars[0][col]] for col in range(n + 1) ]
    clauses += [ [-adder_carry_vars[row][0]] for row in range(1, n) ]

    # Step 5: generate all the adder output clauses
    for row in range(1, n):
        for col in range(n - 1):
            in_1  = mult_vars       [row    ][col    ]
            in_2  = adder_out_vars  [row - 1][col + 1]
            out   = adder_out_vars  [row    ][col    ]
            c_in  = adder_carry_vars[row    ][col    ]
            c_out = adder_carry_vars[row    ][col + 1]
            clauses += generate_3xor(  out, in_1, in_2, c_in)
            clauses += generate_3gt1(c_out, in_1, in_2, c_in)

        # Map each adder's overflow carry bit to the input of the adder below
        col   = n - 1
        in_1  = mult_vars       [row    ][col    ]
        in_2  = adder_carry_vars[row - 1][col + 1]
        out   = adder_out_vars  [row    ][col    ]
        c_in  = adder_carry_vars[row    ][col    ]
        c_out = adder_carry_vars[row    ][col + 1]
        clauses += generate_3xor(  out, in_1, in_2, c_in)
        clauses += generate_3gt1(c_out, in_1, in_2, c_in)

    # Step 6: get a list of the output variables
    out_vars = [ adder_out_vars[row][0] for row in range(n) ]
    out_vars += adder_out_vars[-1][1:] + [ adder_carry_vars[-1][n] ]

    return offset - original_offset, clauses, x_vars, y_vars, out_vars

def generate_forward_multiplication(x: int, y: int):
    n = max(1, x.bit_length(), y.bit_length())
    
    # Generate multiplier
    nvars, clauses, x_vars, y_vars, out_vars = generate_multiplier_cnf(n)

    # Set input bits
    for i in range(n):
        clauses += [
            [x_vars[i] * (1 if x & 1 == 1 else -1)],
            [y_vars[i] * (1 if y & 1 == 1 else -1)],
        ]
        x >>= 1
        y >>= 1

    return nvars, clauses, x_vars, y_vars, out_vars

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <N>")
        exit(1)

    n = int(sys.argv[1])
    nvars, clauses, x_vars, y_vars, out_vars = generate_multiplier_cnf(n)

    # Output CNF
    print(f'p cnf {nvars} {len(clauses)}')
    for clause in clauses:
        print(' '.join(str(lit) for lit in clause) + ' 0')
    print(f"c input vars (x): {' '.join(str(x) for x in x_vars)}")
    print(f"c input vars (y): {' '.join(str(y) for y in y_vars)}")
    print(f"c output vars: {' '.join(str(o) for o in out_vars)}")