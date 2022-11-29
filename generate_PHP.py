import sys
import itertools

def PigeonholePrinciple(numPigeons: int, numHoles: int, functional=False, extensionMode = 0):
    """
    Map m pigeons into n holes

    @param numPigeons: the number of pigeons
    @param numHoles  : the number of holes
    @param functional: True if each pigeon can only be assigned to one hole
    @param extensionMode : True if extension variables should be generated (according to Cook's short ER method)
    """

    def getVar(pigeon: int, hole: int, nPigeons=numPigeons, nHoles=numHoles) -> int:
        """
        Get the variable corresponding to assigning a pigeon to a hole

        @param pigeon: the pigeon to assign
        @param hole  : the hole to which the pigeon should be assigned
        """
        return 1 + pigeon * nHoles + hole
    
    def getExtDefVars(pigeon: int, hole: int, nPigeons: int, nHoles: int):
        """
        Get the variables required for defining an extension variable
        """
        Q_ij = getVar(pigeon, hole, nPigeons - 1, nHoles - 1)
        P_ij = getVar(pigeon, hole, nPigeons, nHoles)
        P_im = getVar(pigeon, nHoles - 1, nPigeons, nHoles)
        P_nj = getVar(nPigeons - 1, hole, nPigeons, nHoles)

        return (Q_ij, P_ij, P_im, P_nj)

    def getExtDefClauses(Q_ij: int, P_ij: int, P_im: int, P_nj: int, level_size: int):
        """
        Generate extension definition clauses for a single extension variable according to Cook's short ER method
        """
        q_ij = Q_ij + level_size
        if extensionMode == 1: return [
            [ Q_ij, -P_ij],
            [ Q_ij, -P_im, -P_nj],
            [-Q_ij,  P_ij,  P_im],
            [-Q_ij,  P_ij,  P_nj],
        ], {P_ij, P_im, P_nj}
        elif extensionMode == 2: return [
            [ -q_ij, -P_im, -P_nj ], [ q_ij,  P_im ], [ q_ij, P_nj ],
            [ -Q_ij,  P_ij, -q_ij ], [ Q_ij, -P_ij ], [ Q_ij, q_ij ],
        ], {q_ij, P_ij, P_im, P_nj}

    def generateExtLayer(nPigeons, nHoles, prev_nVars: int, curr_nVars: int):
        """
        Generate a layer of extension variables over a given instance of PHP

        @param nPigeons the number of pigeons in the new layer
        @param nHoles   the number of holes in the new layer
        @param prev_nVars number of variables below the base layer
        @param curr_nVars number of variables including the base layer
        """

        clauses = []
        covered = set()
        for pigeon in range(nPigeons):
            for hole in range(nHoles):
                (Q_ij, P_ij, P_im, P_nj) = getExtDefVars(pigeon, hole, nPigeons + 1, nHoles + 1)
                (cs, vs) = getExtDefClauses(
                    curr_nVars + Q_ij,
                    prev_nVars + P_ij,
                    prev_nVars + P_im,
                    prev_nVars + P_nj,
                    (nPigeons) * (nHoles)
                )
                clauses += cs
                covered |= vs
        return clauses, covered

    ### Execution entry point ###

    # Initialize clause array
    clauses = []

    # Generate pigeon clause: every pigeon must be assigned to a hole
    clauses += [
        [
            getVar(pigeon, hole) for hole in range(numHoles)
        ] for pigeon in range(numPigeons)
    ]

    # Generate hole clauses: every hole can contain at most 1 pigeon
    clauses += [
        [ -p1, -p2 ] for (p1, p2) in list(itertools.chain.from_iterable([
            itertools.combinations([
                getVar(pigeon, hole) for pigeon in range(numPigeons)
            ], 2) for hole in range(numHoles)
        ]))
    ]

    # Generate functional PHP clauses: every pigeon can be in at most 1 hole
    if functional: clauses += [
        [ -h1, -h2 ] for (h1, h2) in list(itertools.chain.from_iterable([
            itertools.combinations([
                getVar(pigeon, hole) for hole in range(numHoles)
            ], 2) for pigeon in range(numPigeons)
        ]))
    ]

    # Generate extension variable definition clauses according to Cook's short ER proof
    prev_nVars = 0
    curr_nVars = getVar(numPigeons - 1, numHoles - 1)
    extLevels = [0] * curr_nVars
    covered = set()
    if extensionMode > 0:
        for layer in range(1, numHoles):
            # Generate clauses
            nPigeons = numPigeons - layer
            nHoles   = numHoles - layer
            (cs, vs) = generateExtLayer(nPigeons, nHoles, prev_nVars, curr_nVars)
            clauses += cs
            covered |= vs

            layer_size = nPigeons * nHoles
            prev_nVars = curr_nVars

            # Populate extension level array
            if extensionMode == 1:
                curr_nVars += layer_size
                extLevels += [layer] * layer_size
            elif extensionMode == 2:
                curr_nVars += 2 * layer_size
                extLevels += [2 * layer] * layer_size + [2 * layer - 1] * layer_size

    return (curr_nVars, clauses, extLevels, covered)

def printCNF(numVars, clauses):
    """
    Output a CNF in DIMACS format
    """

    # Output DIMACS header
    print(f"p cnf {numVars} {len(clauses)}")

    # Output clauses
    for clause in clauses:
        for lit in clause: print(f"{lit}", end=' ')
        print("0")

def printExtLvl(extLevels, covered):
    for i, lvl in enumerate(extLevels):
        print(f"c extlvl {i + 1} {lvl} {1 if i + 1 in covered else 0}")

if __name__ == '__main__':
    # Validate input
    if len(sys.argv) != 6:
    	print(f"Usage: {sys.argv[0]} <NUM_PIGEONS> <NUM_HOLES> <FUNCTIONAL?> <EXTENSION_MODE> <OUTPUT_EXT_LVL?>")
    	exit()

    [ numPigeons, numHoles, functional, extensionMode, output_extLvl ] = [ int(arg) for arg in sys.argv[1:] ]
    assert(numPigeons > 0)
    assert(numHoles > 0)
    assert(0 <= functional and functional <= 1)
    assert(0 <= extensionMode and extensionMode <= 2)
    assert(0 <= output_extLvl and output_extLvl <= 1)

    # Generate encoding
    (numVars, clauses, extLevels, covered) = PigeonholePrinciple(numPigeons, numHoles, functional, extensionMode)
    
    # Output formula
    printCNF(numVars, clauses)
    if output_extLvl == 1: printExtLvl(extLevels, covered)