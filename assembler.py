#!/usr/bin/python

# Small8 assembler
# Copyright 2014 Forrest Voight

import sys

def resolve(x):
    if x.startswith('$'):
        return int(x[1:], 16)
    elif set(x).issubset('0123456789'):
        return int(x)
    elif x in equs:
        return resolve(equs[x])
    elif x in labels:
        return labels[x]
    elif '+' in x:
        a, b = map(str.strip, x.split('+', 1))
        return resolve(a) + resolve(b)
    else:
        assert False, x

instructions = {
    # format:
    # (mnemonic, number_of_nonconstant_arguments, *constant_matched_arguments):
    #     (opcode, *lengths_of_nonconstant_arguments_in_bytes),
    
    ('ldai', 1): (0x84, 1),
    ('ldaa', 1): (0x88, 2),
    ('ldad', 0): (0x81,),
    ('staa', 1): (0xF6, 2),
    ('star', 0, 'd'): (0xF1,),

    ('adcr', 0, 'd'): (0x01,),
    ('sbcr', 0, 'd'): (0x11,),
    ('cmpr', 0, 'd'): (0x91,),
    ('andr', 0, 'd'): (0x21,),
    ('orr' , 0, 'd'): (0x31,),
    ('xorr', 0, 'd'): (0x41,),
    ('slrl', 0): (0x51,),
    ('srrl', 0): (0x61,),
    ('rolc', 0): (0x52,),
    ('rorc', 0): (0x62,),

    ('bcca', 1): (0xB0, 2),
    ('bcsa', 1): (0xB1, 2),
    ('beqa', 1): (0xB2, 2),
    ('bmia', 1): (0xB3, 2),
    ('bnea', 1): (0xB4, 2),
    ('bpla', 1): (0xB5, 2),
    ('bvca', 1): (0xB6, 2),
    ('bvsa', 1): (0xB7, 2),

    ('deca', 0): (0xFB,),
    ('inca', 0): (0xFA,),
    ('setc', 0): (0xF8,),
    ('clrc', 0): (0xF9,),
    
    ('ldsi', 1): (0x89, 2),
    ('call', 1): (0xC8, 2),
    ('ret', 0): (0xC0,),
    
    ('ldxi', 1): (0x8A, 2),
    ('ldaa', 1, 'x'): (0xBC, 1),
    ('staa', 1, 'x'): (0xEC, 1),
    ('incx', 0): (0xFC,),
    ('decx', 0): (0xFD,),
    
    ('mulr', 0, 'd'): (0x71,),
}

def range_checker(val_func, length):
    def f(x=val_func, l=length):
        if x() < 0 or x() >= 256**l:
            print >>sys.stderr, "value %i exceeded representable range" % (x(),)
            sys.exit(1)
    return f

res = []
equs = {} # equ name -> string
labels = {} # label name -> address
checks = []
with open(sys.argv[1], 'rb') as f:
    for line in f:
        if '*' in line:
            # comment
            line, _ = line.split('*', 1)
        
        line = line.strip()
        
        if ':' in line:
            # label
            label, line = line.split(':', 1)
            labels[label] = len(res)
            line = line.strip()
        
        if not line: continue
        
        split = line.split(None)
        
        if len(split) == 2 and split[0].lower() == 'include':
            pass #print >>sys.stderr, 'ignoring include', split[1]
            continue
        
        if len(split) == 3 and split[1].lower() == 'equ':
            equs[split[0]] = split[2]
            continue
        
        split1 = line.split(None, 1)
        split1args = map(str.strip, split1[1].split(',')) if len(split1) == 2 else []
        
        found = False
        for varargs in xrange(0, len(split1args)+1):
            key = (split1[0].lower(), varargs) + tuple(map(str.lower, split1args[varargs:]))
            if key in instructions:
                inst = instructions[key]
                res.append(lambda x=inst[0]: x)
                assert varargs == len(inst[1:])
                for i, length in zip(xrange(varargs), inst[1:]):
                    val_func = lambda x=split1args[i]: resolve(x)
                    checks.append(range_checker(val_func, length))
                    for j in xrange(length):
                        res.append(lambda x=val_func, y=j: (x() >> (8 * y)) & 0xFF)
                found = True
                break
        if found:
            continue
        
        if split1[0].lower() == 'dc.b':
            val_func = lambda x=split1[1]: resolve(x)
            checks.append(range_checker(val_func, 1))
            res.append(val_func)
            continue
        if split1[0].lower() == 'ds.b':
            for i in xrange(resolve(split1[1])):
                res.append(lambda: 0)
            continue
        if split1[0].lower() == 'ds.w':
            for i in xrange(2*resolve(split1[1])):
                res.append(lambda: 0)
            continue
        
        if split1[0].lower() == 'end':
            continue # ignored
        
        print >>sys.stderr, "don't understand", repr(line), split1
        sys.exit(1)

for check in checks:
    check()

print '''Depth = 256;
Width = 8;
Address_radix = hex;
Data_radix = hex;
% Program RAM Data %
Content'''
print '  Begin'
for i, x in enumerate(res):
    print '%04X : %02X;' % (i, x())
print '[%04X..00FF] : 00;' % (len(res),)
print 'End;'
print
