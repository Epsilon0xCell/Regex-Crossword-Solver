import z3

from . import regex_parser

# I keep one parser for the whole module. Sharing it is only safe
# because parse resets its group tables on every call, and in return I
# do not rebuild the PLY tables for every row and column of a grid.
_parser = regex_parser.RegexParser()

class RegexSolver:
    # This counter is class level and never resets, on purpose. A
    # crossword builds many RegexSolver objects that all feed one Z3
    # solver, and each group start variable needs a name no other
    # object has used. Letting the count climb for the life of the
    # process is how I get names that never collide inside one solve.
    scratch_var_cnt = 0

    def __init__(self, length, regex, x):
        self.length = length
        parse_result = _parser.parse(regex)
        self.regex = parse_result['root']
        self.groups = parse_result['groups']
        self.backrefs = parse_result['backrefs']
        self.x = x
        self.p = []
        self.possible_pos = [set() for _ in range(len(self.groups))]
        for i in range(len(self.groups)):
            self.p.append(z3.Int("p_%d" % RegexSolver.scratch_var_cnt))
            RegexSolver.scratch_var_cnt += 1

    def _set_sum(self, a, b):
        # I drop sums over the line length right here. A part that is
        # already too long can never shrink back, so keeping those
        # lengths would only grow every set built above this one.
        s = set()
        for i in a:
            for j in b:
                if (i + j) <= self.length:
                    s.add(i + j)
        return s

    def _len_set(self, r):
        ty = r[0]

        if ty == regex_parser.EMPTY:
            return set([0])

        elif ty == regex_parser.CHAR:
            return set([1])

        elif ty == regex_parser.DOT:
            return set([1])

        elif ty == regex_parser.STAR:
            # LEN(r) = { k * l <= MAX : k = 0,1,2,... && l in len_set(r) }
            l = self._len_set(r[1])
            s = set([0])
            while True:
                inc = self._set_sum(s, l)
                if s | inc == s:
                    break
                s = s | inc
            return s

        elif ty == regex_parser.BAR:
            # LEN(r1 | r2) = LEN(r1) union LEN(r2)
            l1 = self._len_set(r[1])
            l2 = self._len_set(r[2])
            return l1 | l2

        elif ty == regex_parser.CONCAT:
            # LEN(r1 r2) = { l1 + l2 <= MAX : l1 in LEN(r1) and l2 in LEN(r2) }
            s = set()
            l1 = self._len_set(r[1])
            l2 = self._len_set(r[2])
            return self._set_sum(l1, l2)

        elif ty == regex_parser.GROUP:
            return self._len_set(r[2])

        elif ty == regex_parser.BACKREF:
            # A backref is exactly as long as the group it points at. I
            # ask the group tree for its lengths instead of keeping a
            # second record that could disagree with it.
            idx = r[1] - 1
            return self._len_set(self.groups[idx])

        elif ty == regex_parser.CARET:
            return self._len_set(r[1])

        elif ty == regex_parser.DOLLAR:
            return self._len_set(r[1])

        else:
            raise ValueError("Unknown regex_parser type '%s'" % repr(ty))

    def _sat_expr(self, x, r, i, l):
        # I test the length set before I build anything. Most dead
        # branches die on this one test. Without it, the recursion
        # would build large Z3 terms for splits that can never fit the
        # line, and big grids would slow down for no gain.
        if l not in self._len_set(r):
            return z3.BoolVal(False)
        if i + l > self.length:
            return z3.BoolVal(False)

        ty = r[0]

        if ty == regex_parser.EMPTY:
            return z3.BoolVal(True)

        elif ty == regex_parser.CHAR:
            return (x[i] == ord(r[1]))

        elif ty == regex_parser.DOT:
            # A dot costs one Or branch per character in CHARSET. It is
            # the widest node I build, which is why dot heavy rows are
            # the slow ones in a real grid.
            expr = z3.BoolVal(False)
            for ch in regex_parser.CHARSET:
                expr = z3.Or(expr, x[i] == ord(ch))
            return expr

        elif ty == regex_parser.STAR:
            # SAT(r*, i, l) = Union for l' in LEN(r):
            #                   [ SAT(r, i, l') && SAT(r*, i+l', l-l') ]
            if l == 0:
                return z3.BoolVal(True)
            else:
                expr = z3.BoolVal(False)
                for l1 in self._len_set(r[1]):
                    expr = z3.Or(expr, z3.And(
                        self._sat_expr(x, r[1], i, l1),
                        self._sat_expr(x, r, i + l1, l - l1)
                    ))
                return expr

        elif ty == regex_parser.BAR:
            # SAT(r1 | r2, i, l) = SAT(r1, i, l) || SAT(r2, i, l)
            expr = z3.Or(
                    self._sat_expr(x, r[1], i, l),
                    self._sat_expr(x, r[2], i, l)
            )
            return expr

        elif ty == regex_parser.CONCAT:
            # SAT(r1 r2, i, l) = Union for l1 in LEN(r1):
            #                      [ SAT(r1, i, l1) && SAT(r2, i+l1, l-l1) ]
            expr = z3.BoolVal(False)
            for l1 in self._len_set(r[1]):
                expr = z3.Or(expr, z3.And(
                    self._sat_expr(x, r[1], i, l1),
                    self._sat_expr(x, r[2], i + l1, l - l1)
                ))
            return expr

        elif ty == regex_parser.GROUP:
            # This branch has a side effect I depend on. When the group
            # is used by a backref, I record where it can start in
            # possible_pos, and the BACKREF branch below reads that
            # list. It works because the walk reaches the group before
            # the backref in the patterns I feed it. A pattern that puts
            # the backref first gets an empty list and can never match.
            idx = r[1] - 1
            inner = r[2]
            if (idx+1) in self.backrefs:
                expr = z3.And(
                        (self.p[idx] == i),
                        self._sat_expr(x, inner, i, l)
                )
                self.possible_pos[idx].add(i)
            else:
                expr = self._sat_expr(x, inner, i, l)
            return expr

        elif ty == regex_parser.BACKREF:
            idx = r[1] - 1
            expr = z3.BoolVal(False)
            for j in self.possible_pos[idx]:
                clause = (self.p[idx] == j)
                for k in range(l):
                    clause = z3.And(clause, (x[i+k] == x[j+k]))
                expr = z3.Or(expr, clause)
            return expr

        elif ty == regex_parser.CARET:
            inner = r[1]
            if i == 0:
                return self._sat_expr(x, inner, i, l)
            else:
                return z3.BoolVal(False)

        elif ty == regex_parser.DOLLAR:
            inner = r[1]
            if i + l == self.length:
                return self._sat_expr(x, inner, i, l)
            else:
                return z3.BoolVal(False)

        else:
            raise ValueError("Unknown regex_parser type '%s'" % repr(ty))

    def sat_expr(self):
        # I simplify once, here at the end, instead of inside the
        # recursion. Simplifying at every node cost more time than it
        # saved on the grids I run.
        expr = self._sat_expr(self.x, self.regex, 0, self.length)
        return z3.simplify(expr)

