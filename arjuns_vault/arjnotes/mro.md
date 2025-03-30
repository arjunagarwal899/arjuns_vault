Very good source to understand Method Resolution Order (MRO) in python i.e. how is multiple inheritance in python resolved: https://www.python.org/download/releases/2.3/mro/

One example:

```
>>> O = object
>>> class F(O): pass
>>> class E(O): pass
>>> class D(O): pass
>>> class C(D, F): pass
>>> class B(D, E): pass
>>> class A(B, C): pass
```

Inheritance graph:

```
                          6
                         ---
Level 3                 | O |                  (more general)
                      /  ---  \
                     /    |    \                      |
                    /     |     \                     |
                   /      |      \                    |
                  ---    ---    ---                   |
Level 2        3 | D | 4| E |  | F | 5                |
                  ---    ---    ---                   |
                   \  \ _ /       |                   |
                    \    / \ _    |                   |
                     \  /      \  |                   |
                      ---      ---                    |
Level 1            1 | B |    | C | 2                 |
                      ---      ---                    |
                        \      /                      |
                         \    /                      \ /
                           ---
Level 0                 0 | A |                (more specialized)
                           ---
```

The linearizations of O, D, E and F are trivial:

```
L[O] = O
L[D] = D O
L[E] = E O
L[F] = F O
```

The linearization of B can be computed as

```
L[B] = B + merge(DO, EO, DE)
```

We see that D is a good head, therefore we take it and we are reduced to compute merge(O, EO, E). Now O is not a good head, since it is in the tail of the sequence EO. In this case the rule says that we have to skip to the next sequence. Then we see that E is a good head; we take it and we are reduced to compute merge(O, O) which gives O. Therefore

```
L[B] =  B D E O
```

Using the same procedure one finds:

```
L[C] = C + merge(DO, FO, DF)
     = C + D + merge(O, FO, F)
     = C + D + F + merge(O, O)
     = C D F O
```

Now we can compute:

```
L[A] = A + merge(BDEO, CDFO, BC)
     = A + B + merge(DEO, CDFO, C)
     = A + B + C + merge(DEO, DFO)
     = A + B + C + D + merge(EO, FO)
     = A + B + C + D + E + merge(O, FO)
     = A + B + C + D + E + F + merge(O, O)
     = A B C D E F O
```

In this example, the linearization is ordered in a pretty nice way according to the inheritance level, in the sense that lower levels (i.e. more specialized classes) have higher precedence (see the inheritance graph). However, this is not the general case.
