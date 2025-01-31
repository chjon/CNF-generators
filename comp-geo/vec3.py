class Vec3:
    def __init__(self, xyz: tuple[int,int,int] = (0, 0, 0)):
        self.x = xyz[0]
        self.y = xyz[1]
        self.z = xyz[2]
    
    def __eq__(self, other: "Vec3"):
        return self.x == other.x and self.y == other.y and self.z == other.z
    
    def __add__(self, other: "Vec3"):
        return Vec3((
            self.x + other.x,
            self.y + other.y,
            self.z + other.z
        ))
        
    def __sub__(self, other: "Vec3"):
        return Vec3((
            self.x - other.x,
            self.y - other.y,
            self.z - other.z
        ))
    
    def __mul__(self, scalar: int):
        return Vec3((
            self.x * scalar,
            self.y * scalar,
            self.z * scalar
        ))
        
    def __rmul__(self, scalar: int):
        return Vec3((
            self.x * scalar,
            self.y * scalar,
            self.z * scalar
        ))
    
    def dot(self, other: "Vec3"):
        return self.x * other.x + self.y * other.y + self.z * other.z
        
    def cross(self, other: "Vec3"):
        return Vec3((
            self.y * other.z - other.y * self.z,
            self.z * other.x - other.z * self.x,
            self.x * other.y - other.x * self.y
        ))
    
    def len2(self):
        return self.dot(self)
    
    def __str__(self):
        return f"({self.x},{self.y},{self.z})"