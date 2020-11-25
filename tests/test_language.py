import pytest
import sys

from draconic.exceptions import *


def test_comps(e):
    assert e('[a + 1 for a in [1,2,3]]') == [2, 3, 4]
    assert e('{a + 1 for a in [1,2,3]}') == {2, 3, 4}
    assert e('{a + 1: a - 1 for a in [1,2,3]}') == {2: 0, 3: 1, 4: 2}


def test_setcomp(e):
    assert e('{0 for a in [1,2,3]}') == {0}
    assert e('{a % 10 for a in [5,10,15,20]}') == {0, 5}


def test_genexp(e):
    assert e('list(a + 1 for a in [1,2,3])') == [2, 3, 4]


def test_bitwise_operators(e):
    assert e('4 << 1') == 8

    assert e('8 >> 1') == 4

    assert e('4 | 1') == 5

    assert e('5 ^ 6') == 3

    assert e('3 & 6') == 2


class TestAssignments:

    def test_names(self, e):
        e('a = 1')
        assert e('a') == 1

        e('b = c = 2')
        assert e('b') == 2
        assert e('c') == 2

        e('d = c + 1')
        assert e('d') == 3

        with pytest.raises(NotDefined):
            e('e = x')

    def test_augassign(self, e):
        e('a = 1')
        assert e('a') == 1

        e('a += 1')
        assert e('a') == 2

        e('a *= 2')
        assert e('a') == 4

        e('a <<= 1')
        assert e('a') == 8

        e('a >>= 1')
        assert e('a') == 4

        e('a |= 1')
        assert e('a') == 5

        e('a ^= 6')
        assert e('a') == 3

        e('a &= 6')
        assert e('a') == 2

        e('a /= 2')
        assert e('a') == 1

        e('a += a + 1')
        assert e('a') == 3

        e('a += -2')
        assert e('a') == 1

        with pytest.raises(NotDefined):
            e('b += 1')

        with pytest.raises(DraconicSyntaxError):
            e('a + 1 += 1')

    def test_assigning_expressions(self, e):
        e('a = 1')
        e('b = 2')
        e('c = "foo"')

        e('ab = a + b')
        assert e('ab') == 3

        e('cb = c * b')
        assert e('cb') == 'foofoo'

        e('cb *= 2')
        assert e('cb') == 'foofoofoofoo'

        e('cb = cb.upper()')
        assert e('cb') == 'FOOFOOFOOFOO'

        with pytest.raises(IterableTooLong):
            e('cb = cb * 1000000')


class TestCompoundAssignments:

    def test_unpack(self, i, e):
        i.builtins['x'] = (1, 2)
        i.builtins['y'] = (1, (2, 3), 4)

        e('a, b = (1, 2)')
        assert e('a') == 1
        assert e('b') == 2

        e('a, (b, c), d = (1, (2, 3), 4)')
        assert e('a') == 1
        assert e('b') == 2
        assert e('c') == 3
        assert e('d') == 4

        e('e = (1, (2, 3), 4)')
        assert e('e') == (1, (2, 3), 4)

        e('a, (b, c), d = (1, (a, (3, 3)), "foo")')
        assert e('a') == 1
        assert e('b') == 1
        assert e('c') == (3, 3)
        assert e('d') == 'foo'

    def test_bad_unpacks(self, e):
        with pytest.raises(DraconicValueError):
            e('a, b, c = (1, 2)')

        with pytest.raises(DraconicValueError):
            e('a, b = (1, 2, 3)')

        with pytest.raises(DraconicValueError):
            e('a, b = 1')

    def test_iterator_unpack(self, i, e):
        i.builtins['range'] = range
        e('a, b, c, d = range(4)')
        assert e('a') == 0
        assert e('b') == 1
        assert e('c') == 2
        assert e('d') == 3

        e('a, b, c, d = [i + 1 for i in range(4)]')
        assert e('a') == 1
        assert e('b') == 2
        assert e('c') == 3
        assert e('d') == 4

    def test_compound_assignments(self, e):
        e('a = [1, 2, 3]')
        e('b = {"foo": "bar"}')

        e('a[0] = 0')
        assert e('a') == [0, 2, 3]

        e('a[1] = (1, 2)')
        assert e('a') == [0, (1, 2), 3]

        e('a[2] = a')  # oh boy
        # this = [0, (1, 2), 0]
        # this[2] = this
        # assert e('a') == this  # this causes a RecursionError in comparison
        # but making a self-referencing list does not explode here, which is the real test
        assert e('a[2] is a') is True

        e('b[0] = 0')
        assert e('b') == {"foo": "bar", 0: 0}

        e('b["foo"] = "bletch"')
        assert e('b') == {"foo": "bletch", 0: 0}

    def test_compound_unpack(self, i, e):
        i.builtins['x'] = (1, 2)
        i.builtins['y'] = (1, (2, 3), 4)
        e('a = [1, 2, 3]')

        e('a[0], a[1] = (-1, -2)')
        assert e('a') == [-1, -2, 3]

        e('a[0], a[1], _ = y')
        assert e('a') == [1, (2, 3), 3]

    def test_assign_slice(self, i, e):
        e('a = [1, 2, 3]')
        i.builtins['range'] = range

        e('a[0:2] = range(2)')
        assert e('a') == [0, 1, 3]

    def test_deep_assign(self, e):
        e('a = [[[0]]]')
        e('b = {0:{0:{0: 0}}}')

        e('a[0][0][0] = 1')
        assert e('a') == [[[1]]]

        e('b[0][0][0] = 1')
        assert e('b') == {0: {0: {0: 1}}}

    def test_references(self, e):
        e('a = [1, 2, 3]')
        e('b = a')

        assert e('a is b') is True

        e('b[0] = 0')
        assert e('a') == [0, 2, 3]
        assert e('b') == [0, 2, 3]


class TestSetDictOperations:
    def test_set_operations(self, e):
        e('a = {1, 2, 3}')
        e('b = {3, 4, 5}')

        assert e('a | b') == {1, 2, 3, 4, 5}

        assert e('a & b') == {3}

        assert e('a - b') == {1, 2}

        assert e('a ^ b') == {1, 2, 4, 5}

    if hasattr(dict, "__or__"):
        def test_dict_operations(self, e):
            e('a = {"a": 1, "b": 2}')
            e('b = {"b": 3, "c": 4}')
            e('c = a.copy()')

            assert e('a | b') == {"a": 1, "b": 3, "c": 4}

            e('c |= b')
            assert e('c') == {"a": 1, "b": 3, "c": 4}


class TestNamedExpressions:
    def test_names(self, e):
        if sys.version_info < (3,8,0): return

        assert e('(a := 1)') == 1
        assert e('a') == 1

        assert e('(b := a + 1)') == 2
        assert e('b') == 2

        with pytest.raises(NotDefined):
            e('(c := x)')

        e("d = [1, 2, 3]")
        with pytest.raises(DraconicSyntaxError):
            e("(d[0] := 0)")

    def test_assigning_expressions(self, e):
        if sys.version_info < (3, 8, 0): return

        e('a = 1')
        e('b = 2')
        e('c = "foo"')

        assert e('(ab := a + b)') == 3
        assert e('ab') == 3

        assert e('(cb := c * b)') == 'foofoo'
        assert e('cb') == 'foofoo'

        assert e('(cb := cb.upper())') == 'FOOFOO'
        assert e('cb') == 'FOOFOO'

        with pytest.raises(IterableTooLong):
            e('(cb := cb * 1000000)')
