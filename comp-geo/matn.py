class Mat:
    def __init__(self, rows: list[list[int]]):
        self.m = len(rows)
        self.n = len(rows[0])
        self.rows = rows
        assert self.m > 0
        assert self.n > 0
        for row in rows: assert len(row) == self.n
    
    def row(self, i):
        assert(i >= 0 and i < self.m)
        return Mat([self.rows[i]])
    
    def col(self, i):
        assert(i >= 0 and i < self.n)
        return Mat([[self.rows[j][i]] for j in range(self.n)])
    
    def transpose(self):
        return Mat([
            [
                self.rows[r][c]
                for r in range(self.m)
            ] for c in range(self.n)
        ])
    
    def minor(self, r: int, c: int, sign = 1):
        assert(self.n == self.m)
        rows = []
        for i in range(self.n):
            row = []
            if i == r: continue
            for j in range(self.n):
                if j == c: continue
                row.append(sign * self.rows[i][j])
            rows.append(row)
        return Mat(rows).determinant()
    
    def cofactor(self, r: int, c: int):
        assert(self.n == self.m)
        return self.minor(r, c, -1 if (r + c) & 0x1 == 1 else 1)

    def determinant(self) :
        assert(self.n == self.m)
        if self.n == 1: return self.rows[0][0]
        return sum(self.rows[i][0] * self.cofactor(i, 0) for i in range(self.n))
    
    def cofactor_matrix(self):
        assert(self.n == self.m)
        return Mat([
            [
                self.cofactor(r, c)
                for c in range(self.n)
            ] for r in range(self.n)
        ])
    
    def adjoint(self):
        assert(self.n == self.m)
        return self.cofactor_matrix().transpose()
    
    def __mul__(self, other: "Mat"):
        assert(self.n == other.m)
        return Mat([
            [
                (
                    sum(self.rows[r][i] * other.rows[i][c]
                        for i in range(self.n))
                ) for c in range(other.n)
            ] for r in range(self.m)
        ])
    
    def __call__(self, r: int, c: int = 0):
        return self.rows[r][c]
    
def Vec(xs: list[int]):
    return Mat([xs]).transpose()