# pip install ply z3-solver
# I hardcode the puzzle in this file instead of reading it from a file
# or from flags. I edit the lists, run the file, and read the grid. For
# a one shot puzzle that flow is faster than building an input format
# I would use once.
# https://regexcrossword.com/playerpuzzles/595e8c8e86584
# https://www.bbc.co.uk/programmes/articles/5LCB3rN2dWLqsmGMy5KYtBf/puzzle-for-today
from crossword import solve_crossword

# The row list holds one regex per grid row and the column list one
# per column, 5 and 14 here. solve_crossword trusts those counts, so a
# list I type short does not fail cleanly. It solves the wrong shape.
rows = [
    r'[^XZVCHFJLQM]+',
    r'[^PZVJG]{4}(.)[EFUG]{6}\1[^\sPZVJI]{2}',
    r'[^\sPQFB]{7}[^MGVAJNZ\s]+[^MVZJ]',
    r'N[OYSRU]{5}[NICE]{6}\s\-',
    r'.A[A\sDL]{4}O[AECLV\s]+',
]

cols = [
    r'.*\sA?(SA|PE|N\s){2}',
    r'([XYZ])(P|GO|EL)\1.',
    r'(LS|CA|OS)[L\sP][DO]{2}',
    r'(U)(T)\2\1[AOB?]',
    r'(.)\1\1\1\s',
    r'(FF|BE|QU|OS){2}L',
    r'ES?F?(OBZ|UCO|PTE)',
    r'S[MVU]B(TZ|BP|IV)',
    r'T[GLMV]{2}(E)\1',
    r'(JK|AE|EN|MG){2}L',
    r'N(XN|ZB|CA|FS){2}',
    r'[XHDJ]R[MZVIJ]EC',
    r'X?W(\sE|OS|PE){2}',
    r'[VIMZJ]{3}\-\s',
]

answer = solve_crossword(rows, cols)
# If this puzzle had no solution, solve_crossword would give back None
# and the loop below would fail on it. I leave that failure as the
# signal. It means the puzzle, or my typing of it above, is wrong.
for line in answer:
    print ('  '.join(line))

print('Bonus: I have updated this to also solve Beginner Level 1 Beatles, below is the answer:')
# I keep this tiny grid after the big one as a smoke check. It solves
# at once, so if the big grid ever hangs I can still tell whether the
# solver itself works.
answer = solve_crossword(["HE|LL|O+","[PLEASE]+"], ["[^SPEAK]+","EP|IP|EF"])
for line in answer:
    print ('  '.join(line))
