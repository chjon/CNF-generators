from vec3 import Vec3
from matn import Mat, Vec

class Line3:
    def __init__(self, p1: Vec3, p2: Vec3):
        assert(p1 != p2)
        self.p1 = p1
        self.p2 = p2
        self.d = p2 - p1

def is_point_on_line(p: Vec3, l: Line3):
    crossprod = (l.p1 - p).cross(l.p2 - p)
    return crossprod.x == 0 and crossprod.y == 0 and crossprod.z == 0

def is_point_on_line_seg(p: Vec3, l: Line3):
    if not is_point_on_line(p, l): return False
    dotprod1 = (l.p1 - p).dot(l.d)
    dotprod2 = (l.p2 - p).dot(l.d)
    return (
        (dotprod1 == 0) or 
        (dotprod2 == 0) or
        (dotprod1 > 0) ^ (dotprod2 > 0)
    )

def line_eq(l1: Line3, l2: Line3):
    return is_point_on_line(l1.p1, l2) and is_point_on_line(l1.p2, l2)

def line_seg_eq(l1: Line3, l2: Line3):
    return (
        (l1.p1 == l2.p1 and l1.p2 == l2.p2) or
        (l1.p1 == l2.p2 and l1.p2 == l2.p1)
    )

def do_lines_cross(l1: Line3, l2: Line3):
    if line_eq(l1, l2): return True
    # Find scalars λ1 and λ2 satisfying:
    # l1.p1 + λ1 * l1.d = l2.p1.x + λ2 * l2.d
    # l1.p1 - l2.p1.x = λ2 * l2.d - λ1 * l1.d
    #
    # Equivalently:
    # l1.p1.x - l2.p1.x = λ2 * l2.d.x - λ1 * l1.d.x
    # l1.p1.y - l2.p1.y = λ2 * l2.d.y - λ1 * l1.d.y
    # l1.p1.z - l2.p1.z = λ2 * l2.d.z - λ1 * l1.d.z
    #
    # We will solve using the first two equations and use the third to verify:
    # [l1.p1.x - l2.p1.x] = [l1.d.x  l2.d.x][-λ1]
    # [l1.p1.y - l2.p1.y]   [l1.d.y  l2.d.y][+λ2]
    #
    # [-λ1] = [l1.d.x  l2.d.x]^-1 * [l1.p1.x - l2.p1.x]
    # [+λ2]   [l1.d.y  l2.d.y]      [l1.p1.y - l2.p1.y]
    #
    # Determinant is zero when the lines do not cross
    # https://en.wikipedia.org/wiki/Line%E2%80%93line_intersection
    mat = Mat([
        [l1.d.x, l2.d.x],
        [l1.d.y, l2.d.y]
    ])
    
    det = mat.determinant()
    if det == 0: return False
    
    # det * [-λ1] = adj([l1.d.x  l2.d.x]) * [l1.p1.x - l2.p1.x]
    #       [+λ2]      ([l1.d.y  l2.d.y])   [l1.p1.y - l2.p1.y]
    vec = Vec([l1.p1.x - l2.p1.x, l1.p1.y - l2.p1.y])
    det_λ = mat.adjoint() * vec
    
    # Recall:      l1.p1.z - l2.p1.z = λ2 * l2.d.z - λ1 * l1.d.z
    # Then:   det * (l1.p1.z - l2.p1.z) = det * λ2 * l2.d.z - det * λ1 * l1.d.z
    lhs = det * (l1.p1.z - l2.p1.z)
    rhs = det_λ(0) * l1.d.z + det_λ(1) * l2.d.z
    return lhs == rhs
    
if __name__ == '__main__':
    def test_is_point_on_line():    
        l1 = Line3(Vec3((1, 2, 3)), Vec3((3, 6, 9)))
        assert(is_point_on_line(Vec3((0, 0,  0)), l1) == True )
        assert(is_point_on_line(Vec3((1, 2,  3)), l1) == True )
        assert(is_point_on_line(Vec3((2, 4,  6)), l1) == True )
        assert(is_point_on_line(Vec3((3, 6,  9)), l1) == True )
        assert(is_point_on_line(Vec3((4, 8, 12)), l1) == True )
        assert(is_point_on_line(Vec3((1, 1,  1)), l1) == False)
    test_is_point_on_line()
    
    def test_is_point_on_line_seg():
        l1 = Line3(Vec3((1, 2, 3)), Vec3((3, 6, 9)))
        assert(is_point_on_line_seg(Vec3((0, 0,  0)), l1) == False)
        assert(is_point_on_line_seg(Vec3((1, 2,  3)), l1) == True )
        assert(is_point_on_line_seg(Vec3((2, 4,  6)), l1) == True )
        assert(is_point_on_line_seg(Vec3((3, 6,  9)), l1) == True )
        assert(is_point_on_line_seg(Vec3((4, 8, 12)), l1) == False)
        assert(is_point_on_line_seg(Vec3((1, 1,  1)), l1) == False)
    test_is_point_on_line_seg()
        
    def test_do_lines_cross():
        l1 = Line3(Vec3(( 0, 0, 0)), Vec3((1, 1, 1)))
        l2 = Line3(Vec3(( 2, 2, 2)), Vec3((3, 3, 3)))
        l3 = Line3(Vec3(( 1, 2, 3)), Vec3((3, 2, 1)))
        l4 = Line3(Vec3(( 1, 2, 3)), Vec3((2, 3, 4)))
        assert(do_lines_cross(l1, l1) == True)
        assert(do_lines_cross(l1, l2) == True)
        assert(do_lines_cross(l1, l3) == True)
        assert(do_lines_cross(l1, l4) == False)
        assert(do_lines_cross(l2, l3) == True)
        assert(do_lines_cross(l2, l4) == False)
        assert(do_lines_cross(l3, l4) == True)
    test_do_lines_cross()