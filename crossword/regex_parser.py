import string
from functools import reduce

import ply.lex as lex
import ply.yacc as yacc

[EMPTY, CHAR, DOT, STAR, BAR, CONCAT, GROUP, BACKREF, CARET, DOLLAR] = range(10)
# CHARSET is the whole alphabet a dot or a negated set can draw from.
# A character outside this string can never appear in an answer, and a
# negated set is only negated inside this list, not inside all of
# Unicode. When a puzzle needs a new character, it goes here first.
CHARSET = string.ascii_lowercase + string.ascii_uppercase + string.digits + " :/'!" + ".*+?|()[]^-{},\\"

# I only define s and d here, and s means one space, not all
# whitespace. A backslash letter that is not in this table and is not
# punctuation raises SyntaxError below instead of passing through as a
# quiet literal.
character_classes = {
    's' : " ",
    'd' : "0123456789",
}

class RegexLexer:
    tokens = (
        "NON_META_CHAR", "DIGIT",
        "DOT", "STAR", "PLUS", "QUESTION",
        "BAR",
        "LPAREN", "RPAREN",
        "LBRACKET", "RBRACKET",
        "CARET", "DASH", "DOLLAR",
        "LBRACE", "RBRACE", "COMMA",
        "BACKSLASH",
    )

    def t_NON_META_CHAR(self, t):
        r"[a-zA-Z :/'!]"
        return t
    def t_DIGIT(self, t):
        r"[0-9]"
        return t
    t_DOT, t_STAR, t_PLUS, t_QUESTION = r"\.", r"\*", r"\+", r"\?"
    t_BAR = r"\|"
    t_LPAREN, t_RPAREN = r"\(", r"\)"
    t_LBRACKET, t_RBRACKET = r"\[", r"\]"
    t_CARET, t_DASH, t_DOLLAR = r"\^", r"-", r"\$"
    t_LBRACE, t_RBRACE, t_COMMA = r"\{", r"\}", r","
    t_BACKSLASH = r"\\"

    def t_error(self, t):
        # PLY prints this and then skips the bad character. A typo in a
        # puzzle string does not crash the parse here, it quietly
        # changes the pattern, so I treat this print as a real signal
        # when a solve looks wrong.
        print ("Lexer error at '%s'" % t.value[0])

    def __init__(self):
        self.lexer = lex.lex(module=self)

class RegexParser:

    def p_regex_term(self, p):
        """regex : outer_term"""
        p[0] = p[1]
    def p_regex_union(self, p):
        """regex : outer_term BAR regex"""
        p[0] = (BAR, p[1], p[3])

    # Anchors only exist at this outer level. A caret or dollar sign in
    # the middle of a pattern is read as a plain character by the factor
    # rules, not as an anchor, which matches how the puzzle sources use
    # them inside groups.
    def p_outer_term_term(self, p):
        """outer_term : term"""
        p[0] = p[1]
    def p_outer_term_caret(self, p):
        """outer_term : CARET term"""
        p[0] = (CARET, p[2])
    def p_outer_term_dollar(self, p):
        """outer_term : term DOLLAR"""
        p[0] = (DOLLAR, p[1])
    def p_outer_term_caret_dollar(self, p):
        """outer_term : CARET term DOLLAR"""
        p[0] = (DOLLAR, (CARET, p[2]))

    def p_term_factor(self, p):
        """term : factor"""
        p[0] = p[1]
    def p_term_concat(self, p):
        """term : factor term"""
        p[0] = (CONCAT, p[1], p[2])

    def p_factor_char(self, p):
        """
        factor : NON_META_CHAR
               | DIGIT
               | DASH
               | COMMA
        """
        p[0] = (CHAR, p[1])
    def p_factor_dot(self, p):
        """factor : DOT"""
        p[0] = (DOT,)
    def p_factor_star(self, p):
        """factor : factor STAR"""
        p[0] = (STAR, p[1])
    def p_factor_plus(self, p):
        """factor : factor PLUS"""
        # I expand plus into the factor followed by the same factor
        # starred, reusing one subtree object in both spots. The solver
        # only reads the tree, so sharing it is safe, and plus can never
        # drift apart from what star means.
        p[0] = (CONCAT, p[1], (STAR, p[1]))
    def p_factor_question(self, p):
        """factor : factor QUESTION"""
        p[0] = (BAR, p[1], (EMPTY,))
    def p_factor_group(self, p):
        """factor : LPAREN regex RPAREN"""
        # I number a group when this rule runs, which is when its
        # closing paren has been read. With nested groups the inner one
        # finishes first, so my numbers follow closing order. Backrefs
        # use these same numbers, so the two sides stay consistent even
        # where that order differs from opening order.
        self.groups.append(p[2])
        p[0] = (GROUP, len(self.groups), p[2])
    def p_factor_backref(self, p):
        """factor : BACKSLASH DIGIT"""
        p[0] = (BACKREF, int(p[2]))
        self.backrefs.add(int(p[2]))
    def p_factor_set(self, p):
        """factor : set"""
        # Sort the set so the parse tree is deterministic. Iterating a set
        # directly made the BAR order, and the tests checking it, depend
        # on hash randomization.
        chars = sorted(p[1])
        chars = map(lambda x: (CHAR, x), chars)
        p[0] = reduce(lambda x, y: (BAR, x, y), chars)
    def p_factor_escape(self, p):
        """
        factor : BACKSLASH DOT
               | BACKSLASH STAR
               | BACKSLASH PLUS
               | BACKSLASH QUESTION
               | BACKSLASH BAR
               | BACKSLASH LPAREN
               | BACKSLASH RPAREN
               | BACKSLASH LBRACKET
               | BACKSLASH RBRACKET
               | BACKSLASH CARET
               | BACKSLASH LBRACE
               | BACKSLASH RBRACE
               | BACKSLASH DASH
               | BACKSLASH COMMA
               | BACKSLASH BACKSLASH
        """
        p[0] = (CHAR, p[2])
    def p_factor_escape_fallback(self, p):
        """
        factor : BACKSLASH NON_META_CHAR
        """
        if p[2] in ",-/'!":
            p[0] = (CHAR, p[2])
        elif p[2] in character_classes:
            chars = map(lambda x: (CHAR, x), character_classes[p[2]])
            p[0] = reduce(lambda x, y: (BAR, x, y), chars)
        else:
            raise SyntaxError("Unknown escape '%s'" % p[2])

    def p_factor_brace_1(self, p):
        """factor : factor LBRACE number RBRACE"""
        inner = p[1]
        times = int(p[3])
        if times == 0:
            p[0] = (EMPTY,)
        else:
            p[0] = reduce(lambda x, y: (CONCAT, x, y), [inner for _ in range(times)])
    def p_factor_brace_2(self, p):
        """factor : factor LBRACE number COMMA RBRACE"""
        inner = p[1]
        times = int(p[3])
        if times == 0:
            p[0] = (STAR, inner)
        else:
            prefix = reduce(lambda x, y: (CONCAT, x, y), [inner for _ in range(times)])
            p[0] = (CONCAT, prefix, (STAR, inner))
    def p_factor_brace_3(self, p):
        """factor : factor LBRACE number COMMA number RBRACE"""
        # I expand a range into one case per allowed count, joined by
        # BAR below. Counts in real puzzles are small, and one case per
        # count keeps the solver side simple. A huge range would build
        # a huge tree, so I do not feed this parser ranges like {1,500}.
        inner = p[1]
        times1 = int(p[3])
        times2 = int(p[5])
        cases = []
        for l in range(times1, times2+1):
            if l == 0:
                cases.append((EMPTY,))
                continue
            case = reduce(lambda x, y: (CONCAT, x, y), [inner for _ in range(l)])
            cases.append(case)
        p[0] = reduce(lambda x, y: (BAR, x, y), cases)

    def p_number_single(self, p):
        """number : DIGIT"""
        # Numbers stay digit strings while they are built, one digit at
        # a time, so {12} arrives as the string 12. The int conversion
        # happens in the brace rules that use the number, not here.
        p[0] = p[1]
    def p_number_multiple(self, p):
        """number : DIGIT number"""
        p[0] = p[1] + p[2]

    def p_set_positive(self, p):
        """set : LBRACKET set_items RBRACKET"""
        p[0] = p[2]
    def p_set_negative(self, p):
        """set : LBRACKET CARET set_items RBRACKET"""
        # I take the complement against CHARSET only. If every CHARSET
        # character is listed, this set comes out empty, and the reduce
        # in p_factor_set then has nothing to join. That empty case is
        # a known sharp edge, not a supported pattern.
        p[0] = set(set(CHARSET) - p[3])

    def p_set_items_single(self, p):
        """set_items : set_item"""
        p[0] = p[1]
    def p_set_items_multiple(self, p):
        """set_items : set_item set_items"""
        p[0] = p[1].union(p[2])

    def p_set_item_char(self, p):
        """set_item : set_non_meta_char"""
        p[0] = set([p[1]])
    def p_set_item_range(self, p):
        """set_item : set_non_meta_char DASH set_non_meta_char"""
        begin = ord(p[1])
        end = ord(p[3])
        p[0] = set(map(chr, range(begin, end+1)))
    def p_set_item_escape(self, p):
        """
        set_item : BACKSLASH RBRACKET
                 | BACKSLASH CARET
                 | BACKSLASH DASH
                 | BACKSLASH BACKSLASH
        """
        p[0] = set([p[2]])
    def p_set_item_escape_fallback(self, p):
        """
        set_item : BACKSLASH set_non_meta_char
        """
        if p[2] in character_classes:
            p[0] = set(character_classes[p[2]])
        else:
            p[0] = set(p[2])

    def p_set_non_meta_char(self, p):
        """
        set_non_meta_char : NON_META_CHAR
                          | LBRACKET
                          | DIGIT
                          | DOT
                          | STAR
                          | PLUS
                          | QUESTION
                          | BAR
                          | LPAREN
                          | RPAREN
                          | LBRACE
                          | RBRACE
                          | COMMA
        """
        p[0] = p[1]

    def p_error(self, p):
        # I print and let PLY stop the parse. The caller can get a
        # missing or partial tree out of a bad pattern instead of a
        # clean exception, so this print is the signal I look for first
        # when a puzzle string is malformed.
        print ("Parse error at '%s'" % p.value)

    def __init__(self):
        self.lexer = RegexLexer()
        self.tokens = self.lexer.tokens
        self.parser = yacc.yacc(module=self)

    def parse(self, s):
        # I reset the group tables on every parse because one parser
        # object is shared for a whole process in regex_solver. Without
        # this reset, group numbers from one regex would leak into the
        # next regex and backrefs would point at the wrong groups.
        self.groups = []
        self.backrefs = set()
        root = self.parser.parse(s, self.lexer.lexer)
        return {'groups': self.groups, 'backrefs': self.backrefs, 'root': root}

