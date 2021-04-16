import sys
from z3 import *

# checking arguments
args = sys.argv
if len(args) != 3:
    print('[usage]: python3 main.py input output')
    sys.exit()
input_filepath, output_filepath = args[1:]

# input format check and reading
def check_args(args, l, n):
    if len(args) != n:
        print('input error at line %d: The number of arguments is incorrect. (given %d, expected %d)' % (l, len(args), n))
        sys.exit()
    for s in args:
        if not s.isalnum():
            print('input error at line %d: %s is not a non-negative integer.' % (l, s))
            sys.exit()
with open(input_filepath) as input_file:
    input_str = input_file.read()
input_data_raw = input_str.split('\n')
args = input_data_raw[0].split()
# read the first line
check_args(args, 1, 2)
H, W = map(lambda s: int(s), args)
if max(H, W) > 100:
    print('input error: The board size is too large.')
    sys.exit()
# read the second line and after
board_data = [[[-2, False] for j in range(W)] for i in range(H)]
id_set = set()
for l in range(1, len(input_data_raw)):
    args = input_data_raw[l].split()
    if not args: continue
    check_args(args, l+1, 3)
    i, j, idx = map(lambda s: int(s), args)
    if not 0 <= i < H or not 0 <= j < W:
        print('input error at line %d: The specified position is out of range.' % (l+1))
        sys.exit()
    board_data[i][j] = [idx, idx not in id_set]
    id_set.add(idx)
id_set.add(-1)

# enumeration of requirements
solver = Solver()
heights = [[Int('h_%s_%s' % (i, j)) for j in range(W)] for i in range(H)]
ids = [[Int('id_%s_%s' % (i, j)) for j in range(W)] for i in range(H)]
use_v = [[Bool('use_%s_%s_%s_%s' % (i, j, i + 1, j)) for j in range(W)] for i in range(H - 1)]
use_h = [[Bool('use_%s_%s_%s_%s' % (i, j, i, j + 1)) for j in range(W - 1)] for i in range(H)]
def surroundings(i, j):
    ret = []
    if i > 0: ret.append([heights[i - 1][j], ids[i - 1][j], use_v[i - 1][j]])
    if j > 0: ret.append([heights[i][j - 1], ids[i][j - 1], use_h[i][j - 1]])
    if i < H - 1: ret.append([heights[i + 1][j], ids[i + 1][j], use_v[i][j]])
    if j < W - 1: ret.append([heights[i][j + 1], ids[i][j + 1], use_h[i][j]])
    return ret

for i in range(H):
    for j in range(W):
        surr = surroundings(i, j)
        idx, root = board_data[i][j]

        # the idx is either given by input or -1
        solver.add(Or([ids[i][j] == idx for idx in id_set]))
        
        # when not using point (i,j)
        solver.add(And([Or(ids[i][j] != -1, edge == False) for *_, edge in surr]))
        
        # when the idx of point (i,j) is/isn't specified
        if idx != -2:
            solver.add(ids[i][j] == idx)
        else:
            # pass
            solver.add(Or(ids[i][j] == -1, Sum([If(edge, 1, 0) for *_, edge in surr]) >= 2))

        # when the point (i,j) is/isn't specified as the root of a connected component
        if root:
            solver.add(heights[i][j] == 0)
        else:
            solver.add(heights[i][j] > 0)
            for h_surr, idx_surr, edge in surr:
                solver.add(Or(ids[i][j] == -1, Not(edge), And(ids[i][j] == idx_surr, heights[i][j] != h_surr)))
            solver.add(Or(ids[i][j] == -1, Sum([If(And(edge, heights[i][j] > h_surr), 1, 0) for h_surr, idx_surr, edge in surr]) == 1))

# solve
print(solver.check())
if solver.check() == unsat:
    sys.exit()

# debug output
model = solver.model()
for i in range(H):
    for j in range(W):
        print('x' if board_data[i][j][0] != -2 else '.', end='')
        print(('-' if model[use_h[i][j]] else ' ') if j < W - 1 else '\n', end='')
    if i == H - 1: break
    for j in range(W):
        print('|' if model[use_v[i][j]] else ' ', end='')
        print(' ' if j < W - 1 else '\n', end='')

# output
# output_file = open(output_filepath, 'w')
# output_file.close()