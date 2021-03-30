#!/bin/sh

clang -Xclang -ast-dump=json -fsyntax-only -fno-color-diagnostics $1 > $1.json
test=$(< $2)
python3 test.py $1.json $1 "$test"
