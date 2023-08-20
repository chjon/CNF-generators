import sys
from pysat.solvers import Glucose3

def generateExactlyOneConstraint(varList):
    return [varList] + [
        [-varList[i], -varList[j]]
        for i in range(0, len(varList))
        for j in range(i + 1, len(varList))
    ]

def getLRUDChar(lrud):
    if lrud ==  0: return ' '
    if lrud ==  1: return '╷'
    if lrud ==  2: return '╵'
    if lrud ==  3: return '│'
    if lrud ==  4: return '╶'
    if lrud ==  5: return '┌'
    if lrud ==  6: return '└'
    if lrud ==  7: return '├'
    if lrud ==  8: return '╴'
    if lrud ==  9: return '┐'
    if lrud == 10: return '┘'
    if lrud == 11: return '┤'
    if lrud == 12: return '─'
    if lrud == 13: return '┬'
    if lrud == 14: return '┴'
    if lrud == 15: return '┼'

def getLRUDPad(lrud, spacing):
    if (lrud & 4) == 0: return ' ' * spacing
    else              : return '─' * spacing

class FlowFreeBoard:
    def __init__(self, width, height, numFlows, data):
        self.width = width
        self.height = height
        self.numFlows = numFlows
        self.data = data
        if len(data) == 0: return

        self.numColourVars = self.getColourVar(width - 1, height - 1, numFlows - 1)
        self.numVerticalEdgeVars = self.getVerticalEdgeVar(width - 2, height - 1) - self.numColourVars
        self.numHorizontalEdgeVars = self.getHorizontalEdgeVar(width - 1, height - 2) - self.numVerticalEdgeVars - self.numColourVars

    def generateConstraints(self):
        clauses = []

        # Generate clauses for 'at most 1 colour' in each cell
        clauses += [
            [-self.getColourVar(x, y, i), -self.getColourVar(x, y, j)]
            for y in range(self.height)
            for x in range(self.width)
            for i in range(0, self.numFlows)
            for j in range(i + 1, self.numFlows)
        ]

        # Generate clauses for 'at least 1 colour' in each cell
        clauses += [
            [self.getColourVar(x, y, i) for i in range(self.numFlows)]
            for y in range(self.height)
            for x in range(self.width)
        ]

        # Generate clauses for 'if there is a vertical edge between two cells, then their colours are the same'
        for y in range(self.height):
            for x in range(self.width - 1):
                for i in range(self.numFlows):
                    clauses.append([-self.getVerticalEdgeVar(x, y), +self.getColourVar(x, y, i), -self.getColourVar(x + 1, y, i)])
                    clauses.append([-self.getVerticalEdgeVar(x, y), -self.getColourVar(x, y, i), +self.getColourVar(x + 1, y, i)])

        # Generate clauses for 'if there is a horizontal edge between two cells, then their colours are the same'
        for y in range(self.height - 1):
            for x in range(self.width):
                for i in range(numFlows):
                    clauses.append([-self.getHorizontalEdgeVar(x, y), +self.getColourVar(x, y, i), -self.getColourVar(x, y + 1, i)])
                    clauses.append([-self.getHorizontalEdgeVar(x, y), -self.getColourVar(x, y, i), +self.getColourVar(x, y + 1, i)])

        for y in range(self.height):
            for x in range(self.width):
                # Get list of adjacent edge variables
                adjacentEdgeVars = []
                if 0 < x:          adjacentEdgeVars.append(self.getVerticalEdgeVar(x - 1, y))
                if x < self.width - 1:  adjacentEdgeVars.append(self.getVerticalEdgeVar(x, y))
                if 0 < y:          adjacentEdgeVars.append(self.getHorizontalEdgeVar(x, y - 1))
                if y < self.height - 1: adjacentEdgeVars.append(self.getHorizontalEdgeVar(x, y))

                # Generate clauses for 'non-root cells have either 0 or 2 edges'
                if self.data[y][x] == 0:
                    # 'At least 2 edges are disconnected'
                    clauses += [
                        [-adjacentEdgeVars[i], -adjacentEdgeVars[j], -adjacentEdgeVars[k]]
                        for i in range(0, len(adjacentEdgeVars))
                        for j in range(i + 1, len(adjacentEdgeVars))
                        for k in range(j + 1, len(adjacentEdgeVars))
                    ]

                    # 'If there is one connected edge, there must be another connected edge'
                    clauses += [
                        adjacentEdgeVars[:i] + [-adjacentEdgeVars[i]] + adjacentEdgeVars[i + 1:]
                        for i in range(len(adjacentEdgeVars))
                    ]

                # Generate clauses for 'the root cell has the given colour' and 'root cells have exactly 1 edge'
                else: clauses += [[self.getColourVar(x, y, self.data[y][x] - 1)]] + generateExactlyOneConstraint(adjacentEdgeVars)
        
        return self.numVars(), clauses

    def numVars(self):
        return self.numColourVars + self.numVerticalEdgeVars + self.numHorizontalEdgeVars

    def getColourVar(self, x, y, i):
        return 1 + y * self.width * self.numFlows + x * self.numFlows + i

    def getVerticalEdgeVar(self, x, y):
        return 1 + self.numColourVars + y * (self.width - 1) + x
    
    def getHorizontalEdgeVar(self, x, y):
        return 1 + self.numColourVars + self.numVerticalEdgeVars + y * self.width + x
    
    def outputBoard(self, spacing, model = None):
        print(' ' + ' ' * spacing + ('\'' + ' ' * spacing) * self.width)
        for y in range(self.height):
            print('-' + ' ' * spacing, end='')
            for x in range(self.width):
                lrud = 0x0
                if model != None:
                    if 0 < x:               lrud |= (model[self.getVerticalEdgeVar(x - 1, y) - 1] > 0) << 3
                    if x < self.width - 1:  lrud |= (model[self.getVerticalEdgeVar(x, y) - 1] > 0) << 2
                    if 0 < y:               lrud |= (model[self.getHorizontalEdgeVar(x, y - 1) - 1] > 0) << 1
                    if y < self.height - 1: lrud |= (model[self.getHorizontalEdgeVar(x, y) - 1] > 0) << 0
                
                outstr = ''
                if data[y][x] > 0:  outstr += chr(ord("A") + self.data[y][x] - 1)
                elif model == None: outstr += '0'
                else:               outstr += getLRUDChar(lrud)
                print(outstr + getLRUDPad(lrud, spacing), end='')

            print()

def parse_flow_free(filepath):
    width = 0
    height = 0
    numFlows = 0
    data = []

    try:
        f = open(filepath)

        # Parse header
        line = f.readline().strip().split(' ')
        assert(len(line) == 4)
        assert(line[0] == 'd')
        width, height, numFlows = (int(i) for i in line[1:]) 
        data = [[0] * width for i in range(height)]

        # Parse pairs of points
        for i in range(1, numFlows + 1):
            line = f.readline().strip().split(' ')
            assert(len(line) == 5)
            assert(line[0] == 'p')
            x1, y1, x2, y2 = (int(i) for i in line[1:])
            assert(0 < x1 and x1 <= width)
            assert(0 < x2 and x2 <= width)
            assert(0 < y1 and y1 <= height)
            assert(0 < y2 and y2 <= height)
            data[y1 - 1][x1 - 1] = i
            data[y2 - 1][x2 - 1] = i

    except Exception as e:
        print(f"Failed to read file {filepath}")
        print(e)

    return width, height, numFlows, data

if __name__ == '__main__':
    # Validate input
    if len(sys.argv) != 3:
    	print(f"Usage: {sys.argv[0]} <PROBLEM_FILE> <MODE[0,1]>")
    	exit()

    mode = int(sys.argv[2])

    # Parse file
    if mode > 0: print("Parsing...")
    width, height, numFlows, data = parse_flow_free(sys.argv[1])
    if len(data) == 0:
        print(f"Failed to parse {sys.argv[1]}")
        exit()

    # Generate instance
    if mode > 0: print("Encoding...")
    board = FlowFreeBoard(width, height, numFlows, data)
    numVars, clauses = board.generateConstraints()

    if mode == 0:
        # Output clauses as DIMACS
        print(f"p cnf {numVars} {len(clauses)}")
        for clause in clauses:
            for i in clause: print(f'{i} ', end='')
            print('0')
    elif mode == 1:
        print("Solving...")

        # Solve instance
        g = Glucose3()
        for clause in clauses:
            g.add_clause(clause)
        
        if g.solve():
            model = g.get_model()
            board.outputBoard(1, model)

        else:
            print("UNSAT")
    else:
        print(f"Mode '{mode}' is not supported")