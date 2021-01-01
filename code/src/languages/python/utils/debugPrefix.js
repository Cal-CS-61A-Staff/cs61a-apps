export default `# these lines stub out the debugging functions you have available
def draw(something): pass
def autodraw(): pass
def disable_autodraw(): pass
def visualize(): pass
def editor(): pass

class Tree:
    """A tree."""

    def __init__(self, label, branches=[]):
        self.label = label
        for branch in branches:
            assert isinstance(branch, Tree)
        self.branches = list(branches)

    def __repr__(self):
        if self.branches:
            branch_str = ', ' + repr(self.branches)
        else:
            branch_str = ''
        return 'Tree({0}{1})'.format(repr(self.label), branch_str)

    def __str__(self):
        return '\\n'.join(self.indented())

    def indented(self):
        lines = []
        for b in self.branches:
            for line in b.indented():
                lines.append('  ' + line)
        return [str(self.label)] + lines

    def is_leaf(self):
        return not self.branches

def is_tree(elem):
    if isinstance(tree, list) or len(elem) < 1:
        return False
    for branch in branches(elem):
        if not is_tree(branch):
            return False
    return True

def tree(label, branches=[]):
    for branch in branches:
        assert is_tree(branch), 'branches must be trees'
    return [label] + list(branches)

def label(tree):
    return tree[0] if isinstance(tree, list) else tree.label

def branches(tree):
    return tree[1:] if isinstance(tree, list) else tree.branches

class Link:
    """A linked list."""
    empty = ()

    def __init__(self, first, rest=empty):
        assert rest is Link.empty or isinstance(rest, Link)
        self.first = first
        self.rest = rest

    def __repr__(self):
        if self.rest:
            rest_repr = ', ' + repr(self.rest)
        else:
            rest_repr = ''
        return 'Link(' + repr(self.first) + rest_repr + ')'

    def __str__(self):
        string = '<'
        while self.rest is not Link.empty:
            string += str(self.first) + ' '
            self = self.rest
        return string + str(self.first) + '>'


#pythontutor_hide: draw, autodraw, disable_autodraw, visualize, editor, Tree, is_tree, tree, label, branches, Link

# your code is below
`;
