## @file
## @brief powered by `metaL`

MODULE = 'webook'
TITLE = 'book writing platform /web+kb/'
ABOUT = '''
* standalone web interface server /Flask/
* graph knowledge database
* markup render engine
* powered by `metaL`'''
AUTHOR = 'Dmitry Ponyatov'
EMAIL = 'dponyatov@gmail.com'
YEAR = 2020
LICENSE = 'MIT'
GITHUB = 'https://github.com/ponyatov/%s' % MODULE
LOGO = 'logo.png'


import os, sys

## @defgroup persist Persistence

import xxhash, json

## @defgroup object Object

## @brief base object graph node
## @ingroup object
class Object:

    ## construct object
    ## @param[in] V given scalar value
    def __init__(self, V):
        ## name / scalar value
        self.val = V
        ## attributes = dict = env
        self.slot = {}
        ## nested AST = vector = stack = queue
        self.nest = []
        ## global storage id
        ## @ingroup persist
        self.gid = self.sync().gid

    ## @name storage/hot-update
    ## @{

    ## this method must be called on any object update
    ## (compute hash, update persistent memory,..)
    ##
    ## mostly used in operator methods in form of `return self.sync()`
    ## @ingroup persist
    ## @returns self
    def sync(self):
        # update global hash
        self.gid = hash(self)
        ## sync with storage
        #storage.put(self)
        return self

    ## fast object hashing for global storage id
    ## @ingroup persist
    def __hash__(self):
        hsh = xxhash.xxh32()
        hsh.update(self._type())
        hsh.update('%s' % self.val)
        for i in self.slot:
            hsh.update(i)
            hsh.update(self.slot[i].gid.to_bytes(8, 'little'))
        for j in self.nest:
            hsh.update(j.gid.to_bytes(8, 'little'))
        return hsh.intdigest()

    ## @}

    ## @name dump
    ## @{

    ## `print` callback
    def __repr__(self): return self.dump()

    def dump(self, cycle=None, depth=0, prefix='', test=False):
        # header
        tree = self._pad(depth) + self.head(prefix, test)
        # cycles
        if not depth:
            cycle = []
        if self in cycle:
            return tree + ' _/'
        else:
            cycle.append(self)
        # slot{}s
        for i in sorted(self.slot.keys()):
            tree += self.slot[i].dump(cycle, depth + 1, '%s = ' % i, test)
        # nest[]ed
        idx = 0
        for j in self.nest:
            tree += j.dump(cycle, depth + 1, '%s: ' % idx, test)
            idx += 1
        # subtree
        return tree

    ## paddig for @ref dump
    def _pad(self, depth): return '\n' + '\t' * depth

    ## short `<T:V>` header only
    ## @param[in] prefix optional prefix in `<T:V>` header
    ## @param[in] test test dump option @ref test
    def head(self, prefix='', test=False):
        hdr = '%s<%s:%s>' % (prefix, self._type(), self._val())
        if not test:
            hdr += ' #%x @%x' % (self.gid, id(self))
        return hdr

    def _type(self): return self.__class__.__name__.lower()

    def _val(self): return '%s' % self.val

    ## @}

    ## @name operator
    ## @{

    ## `A[key] ~> A.slot[key:str] | A.nest[key:int] `
    def __getitem__(self, key):
        if isinstance(key, int):
            return self.nest[key]
        elif isinstance(key, str):
            return self.slot[key]
        else:
            raise TypeError(that)

    ## `A[key] = B`
    def __setitem__(self, key, that):
        if isinstance(that, str):
            that = String(that)
        self.slot[key] = that
        return self.sync()

    ## `A << B ~> A[B.type] = B`
    def __lshift__(self, that):
        return self.__setitem__(that._type(), that)

    ## `A >> B ~> A[B.val] = B`
    def __rshift__(self, that):
        return self.__setitem__(that.val, that)

    ## `A // B -> A.push(B)`
    def __floordiv__(self, that):
        if isinstance(that, str):
            that = String(that)
        self.nest.append(that)
        return self.sync()

    ## @}


## primitive

class Primitive(Object):
    def eval(self, ctx): return self

class String(Primitive):
    def _val(self):
        s = ''
        for c in self.val:
            if c == '\n':
                s += r'\n'
            elif c == '\t':
                s += r'\t'
            else:
                s += c
        return s

## I/O

class IO(Object):
    pass

class File(IO):
    def __init__(self, V):
        IO.__init__(self, V)
        self.fh = open(V, 'w')

    def __floordiv__(self, that):
        if isinstance(that, str):
            that = String(that)
        IO.__floordiv__(self, that)
        if self.fh:
            self.fh.write('%s\n' % that.val)
        return self


readme = File('README.md')
readme // ('#  `%s`' % MODULE)
readme // ('## %s' % TITLE)
readme // (ABOUT)
readme // ''
readme // ('(c) %s <<%s>> %s %s' % (AUTHOR, EMAIL, YEAR, LICENSE))
readme // ''
readme // ('github: %s' % GITHUB)
# print(readme)

import flask
