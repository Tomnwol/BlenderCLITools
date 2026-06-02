import trimesh
import sys

path = sys.argv[1]

trimesh.load(path).show()