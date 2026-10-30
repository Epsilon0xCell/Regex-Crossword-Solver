# This file never looks inside a pattern. It builds one set of cell
# variables, hands each row and column string to RegexSolver, and
# reads characters back out of the finished model. When a solve goes
# wrong, the place to open follows from what went wrong: grid shape
# here, the parse tree in regex_parser, the Z3 terms in regex_solver.
import z3

from .regex_solver import RegexSolver

def solve_crossword(rows, cols, rows2=None, cols2=None):
    row_cnt = len(rows)
    col_cnt = len(cols)

    # I make one integer variable per cell, and the integer is a
    # character code. Rows and columns then constrain the same
    # variables, which is the whole trick: a cell has one value, and
    # both clue directions have to agree on it.
    x = [[None]*col_cnt for _ in range(row_cnt)]
    for i in range(row_cnt):
        for j in range(col_cnt):
            x[i][j] = z3.Int("x_%d_%d" % (i,j))

    solver = z3.Solver()
    for i in range(row_cnt):
        v = x[i]
        e = RegexSolver(col_cnt, rows[i], v).sat_expr()
        solver.add(e)
        # rows2 and cols2 are a second clue set for the same grid, used
        # by two sided puzzles. I add them beside the first set. They
        # narrow the answer, they never replace the first clues.
        if rows2:
            e = RegexSolver(col_cnt, rows2[i], v).sat_expr()
            solver.add(e)
    for j in range(col_cnt):
        # I rebuild each column as a flat list because RegexSolver takes
        # one list per line. The lambda parameter shadows the grid name
        # x on purpose here, and it only picks the j entry out.
        v = list(map(lambda x: x[j], x))
        e = RegexSolver(row_cnt, cols[j], v).sat_expr()
        solver.add(e)
        if cols2:
            e = RegexSolver(row_cnt, cols2[j], v).sat_expr()
            solver.add(e)
    check = solver.check()
    if check == z3.sat:
        model = solver.model()
        answer = [[0]*col_cnt for _ in range(row_cnt)]
        for i in range(row_cnt):
            for j in range(col_cnt):
                v = model[x[i][j]]
                answer[i][j] = chr(int(v.as_long()))
        return answer
    else:
        return None

def solve_regex(regex, length):
    # I name these variables x_00, x_01 and so on, apart from the grid
    # names in solve_crossword, so a printed Z3 term tells me which
    # entry point built it.
    unknowns = [z3.Int("x_%02d" % i) for i in range(length)]
    expr = RegexSolver(length, regex, unknowns).sat_expr()
    solver = z3.Solver()
    solver.add(expr)
    if solver.check() == z3.sat:
        model = solver.model()
        answer = [model[unknowns[i]].as_long() for i in range(length)]
        return ''.join(map(chr, answer))
    else:
        return None
