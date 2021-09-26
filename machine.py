#!/usr/bin/env python3

import json

OPS = {
    0: ('halt', 0),
    1: ('set', 2),
    2: ('push', 1),
    3: ('pop', 1),
    4: ('eq', 3),
    5: ('gt', 3),
    6: ('jmp', 1),
    7: ('jt', 2),
    8: ('jf', 2),
    9: ('add', 3),
    10: ('mult', 3),
    11: ('mod', 3),
    12: ('and', 3),
    13: ('or', 3),
    14: ('not', 2),
    15: ('rmem', 2),
    16: ('wmem', 2),
    17: ('call', 1),
    18: ('ret', 0),
    19: ('out', 1),
    20: ('in', 1),
    21: ('noop', 0),
}

memory = [0 for _ in range(32768)]
registers = [0 for _ in range(8)]
stack = []
buffer = []

with open('challenge.bin', 'rb') as f:
    cur = 0
    two_bytes = f.read(2)
    while two_bytes:
        memory[cur] = int.from_bytes(two_bytes, 'little')
        cur += 1
        two_bytes = f.read(2)

def value(x):
    return registers[x - 32768] if 32768 <= x <= 32775 else x

def decompile():
    cur = 0
    with open('challenge.asm', 'w') as f:
        while cur < len(memory):
            f.write('{:>5}: '.format(cur))
            if memory[cur] in OPS:
                op, args = OPS.get(memory[cur])
                f.write(' '.join([op] + [str(a) for a in memory[cur + 1:cur + 1 + args]]) + '\n')
                cur += 1 + args
            else:
                f.write('>> ' + str(memory[cur]) + '\n')
                cur += 1

cur = 0
while True:
    op, args = OPS.get(memory[cur])
    # print('OP', op, memory[cur + 1], memory[cur + 2], memory[cur + 3])
    if op == 'halt':
        break
    elif op == 'set':
        registers[memory[cur + 1] - 32768] = value(memory[cur + 2])
        cur += args + 1
    elif op == 'push':
        stack.append(value(memory[cur + 1]))
        cur += args + 1
    elif op == 'pop':
        if not stack:
            raise Exception('empty stack')
        registers[memory[cur + 1] - 32768] = stack.pop()
        cur += args + 1
    elif op == 'eq':
        registers[memory[cur + 1] - 32768] = 1 if value(memory[cur + 2]) == value(memory[cur + 3]) else 0
        cur += args + 1
    elif op == 'gt':
        registers[memory[cur + 1] - 32768] = 1 if value(memory[cur + 2]) > value(memory[cur + 3]) else 0
        cur += args + 1
    elif op == 'jmp':
        cur = value(memory[cur + 1])
    elif op == 'jt':
        if value(memory[cur + 1]) != 0:
            cur = value(memory[cur + 2])
        else:
            cur += args + 1
    elif op == 'jf':
        if value(memory[cur + 1]) == 0:
            cur = value(memory[cur + 2])
        else:
            cur += args + 1
    elif op == 'add':
        registers[memory[cur + 1] - 32768] = (value(memory[cur + 2]) + value(memory[cur + 3])) % 32768
        cur += args + 1
    elif op == 'mult':
        registers[memory[cur + 1] - 32768] = (value(memory[cur + 2]) * value(memory[cur + 3])) % 32768
        cur += args + 1
    elif op == 'mod':
        registers[memory[cur + 1] - 32768] = value(memory[cur + 2]) % value(memory[cur + 3])
        cur += args + 1
    elif op == 'and':
        registers[memory[cur + 1] - 32768] = value(memory[cur + 2]) & value(memory[cur + 3])
        cur += args + 1
    elif op == 'or':
        registers[memory[cur + 1] - 32768] = value(memory[cur + 2]) | value(memory[cur + 3])
        cur += args + 1
    elif op == 'not':
        registers[memory[cur + 1] - 32768] = ~value(memory[cur + 2]) & 0x7fff
        cur += args + 1
    elif op == 'rmem':
        registers[memory[cur + 1] - 32768] = memory[value(memory[cur + 2])]
        cur += args + 1
    elif op == 'wmem':
        memory[value(memory[cur + 1])] = value(memory[cur + 2])
        cur += args + 1
    elif op == 'call':
        stack.append(cur + 2)
        cur = value(memory[cur + 1])
    elif op == 'ret':
        if not stack:
            break
        cur = stack.pop()
    elif op == 'out':
        print(chr(value(memory[cur + 1])), end='')
        cur += args + 1
    elif op == 'in':
        while not buffer:
            s = input('>>> ')
            if s.startswith('save'):
                with open('save.json', 'w') as f:
                    json.dump({'cur': cur, 'registers': registers, 'stack': stack, 'memory': memory}, f)
                print('Saved.\n')
            elif s.startswith('load'):
                with open('save.json', 'r') as f:
                    saved = json.load(f)
                cur = saved['cur']
                memory = saved['memory']
                registers = saved['registers']
                stack = saved['stack']
                print('Loaded.\n')
            elif s.startswith('reg7'):
                reg7 = int(s.split(' ')[-1])
                registers[7] = reg7
                print('Set register 7 to', reg7, '\n')
            else:
                buffer = list(s + '\n')
        if memory[cur + 1] >= 32768:
            registers[memory[cur + 1] - 32768] = ord(buffer.pop(0))
        else:
            memory[memory[cur + 1]] = ord(buffer.pop(0))
        cur += args + 1
    elif op == 'noop':
        cur += args + 1
    else:
        print('unknown op', op)
        break

