from pyswip import Prolog
import argparse
import json
import re

FUNCTION_TYPE_PATTERN = r"([^\(\)\s]+)\s*\(([^\(\)]*)\).*"

TYPE_CLASS = 'class'
TYPE_METHOD = 'method'

declared_methods = {}

parser = argparse.ArgumentParser(description='Tests OOP program structure.')
parser.add_argument('ast', type=str, help='Json file of CLang AST')
parser.add_argument('src_name', type=str, help='Name of source code file')
parser.add_argument('test', type=str, help='Prolog test query')

args = parser.parse_args()

def create_object(parent, obj_type, name):
    return {
        'parent': parent,
        'type': obj_type,
        'name': name
    }

def collect_facts(prolog, parent, ast):
    node_kind = ast['kind']
    facts = []
    if node_kind == 'CXXRecordDecl':
        class_name = ast['name']
        facts.append("class('{}')".format(class_name))
        parent = create_object(parent, TYPE_CLASS, class_name)
        if 'bases' in ast:
            for base in ast['bases']:
                base_class_name = base['type']['qualType']
                facts.append("parent('{}','{}',{})".format(
                        base_class_name, class_name, base['access']
                    ))
    if node_kind == 'FieldDecl' \
            and parent != None and parent['type'] == TYPE_CLASS:
        class_name = parent['name']
        property_name = ast['name']
        facts.append("property('{}','{}')".format(class_name, property_name))
    if node_kind == 'CXXConstructorDecl' \
            and parent != None and parent['type'] == TYPE_CLASS \
            and ('isImplicit' not in ast or not ast['isImplicit']):
            # and 'type' in ast and 'qualType' in ast['type'] \
        match = re.match(FUNCTION_TYPE_PATTERN, ast['type']['qualType'])
        assert(match.lastindex == 2)
        parameter_types = match.group(2)
        if parameter_types.strip() == '':
            parameter_types = []
        else:
            parameter_types = parameter_types.split(', ')
        class_name = parent['name']
        facts.append("constructor('{}',{})".format(class_name, str(parameter_types)))
    if node_kind == 'CXXDestructorDecl' \
            and parent != None and parent['type'] == TYPE_CLASS \
            and ('isImplicit' not in ast or not ast['isImplicit']):
        class_name = parent['name']
        facts.append("destructor('{}')".format(class_name))
    if node_kind == 'CXXMethodDecl':
        method_name = ast['name']
        match = re.match(FUNCTION_TYPE_PATTERN, ast['type']['qualType'])
        assert(match.lastindex == 2)
        return_type = match.group(1)
        parameter_types = match.group(2)
        if parameter_types.strip() == '':
            parameter_types = []
        else:
            parameter_types = parameter_types.split(', ')
        # parent = create_object(parent, TYPE_METHOD, method_name)
        if parent is not None and parent['type'] == TYPE_CLASS:
            class_name = parent['name']
            facts.append("method_declaration('{}','{}','{}',{})".format(
                    class_name, method_name, return_type, str(parameter_types)
                ))
            if 'inner' in ast:
                facts.append("method_implementation('{}','{}',inside,'{}',{})".format(
                    class_name, method_name, return_type, str(parameter_types)
                ))
            declared_methods[ast['id']] = parent
        elif 'previousDecl' in ast and ast['previousDecl'] in declared_methods \
                and 'inner' in ast:
            class_obj = declared_methods[ast['previousDecl']]
            facts.append("method_implementation('{}','{}',outside,'{}',{})".format(
                    class_obj['name'], method_name, return_type, str(parameter_types)
                ))
        else:
            print('Warning: Invalid CXXMethodDecl node: {}'.format(ast['id']))



    if len(facts) > 0:
        print('Collected facts: {}'.format(str(facts)))
        for fact in facts:
            prolog.assertz(fact)

    if 'inner' in ast:
        for children in ast['inner']:
            collect_facts(prolog, parent, children)

prolog = Prolog()
with open(args.ast, 'r') as f:
    try:
        ast = json.loads(f.read())
    except:
        print("Can't read ast file!")
        exit()

prolog.assertz('use_module(library(clpfd))')
prolog.assertz('all_diff(L) :- \+ (append(_,[X|R],L), memberchk(X,R))')

if ast['kind'] == 'TranslationUnitDecl':
    items = ast['inner']
    current_file = ''
    for item in items:
        if 'loc' in item and 'file' in item['loc'] and item['loc']['file'] != '':
            current_file = item['loc']['file']
            # print('Handling file: {}'.format(current_file))

        if current_file == args.src_name:
            collect_facts(prolog, None, item)
else:
    print('Invalid root declaration')
    exit()

# collect_facts(prolog, None, ast)

solutions = prolog.query(args.test)
try:
    specific_solution = next(solutions)
    print('PASSED')
except:
    print('FAILED')

solutions.close()


