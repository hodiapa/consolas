from src.model import *
from z3 import *
import yaml
from pprint import pprint

NUM_STATES = 10

class_in_yaml = """
-
  name: State
  reference:
  - {name: next, type: State}
  - {name: near, type: Object, multiple: true}
  - {name: far, type: Object, multiple: true}
-
  name: Object
  reference: [{name: eat, type: Object}]
"""

State, Object = load_all_classes(yaml.load(class_in_yaml))

s = ObjectVar(State, 's')
o = ObjectVar(Object, 'o')
o2 = ObjectVar(Object, 'o2')
Start = ObjectConst('Start', State)
Final = ObjectConst('Final', State)

generate_meta_constraints()
meta_fact(State.join(Object).forall([s, o], s['near'].contains(o) != s['far'].contains(o)))
meta_fact(Object.forall(o, Start['near'].contains(o)))
meta_fact(State.forall(s, Object.forall(o, s['far'].contains(o)) == (s == Final)))
meta_fact(And(Start.alive(), Final.alive()))
meta_fact(State.forall(s, And(s.alive(), s['next'].undefined()) == (s == Final)))

farmer = DefineObject('farmer', Object).get_constant()
fox = DefineObject('fox', Object).get_constant()
chicken = DefineObject('chicken', Object).get_constant()
grain = DefineObject('grain', Object).get_constant()
states = [DefineObject('state%d' % i, State, suspended=True).get_constant() for i in range(0,NUM_STATES)]

generate_config_constraints()
config_fact(And([fox['eat']==chicken, chicken['eat']==grain, grain['eat'].undefined(), farmer['eat'].undefined()]))
config_fact(And([Or(Not(states[i].alive()), states[i]==Final, states[i]['next']==states[i+1])
                 for i in range(0, len(states)-1)
                ]))
config_fact(Implies(states[-1].alive(), states[-1]['next'].undefined()))

config_fact(State.forall(s, Or(s == Final, If(
    s['near'].contains(farmer),
    And(s['next']['far'].contains(farmer), s['near'].exists(
        o, And(s['next']['far'].contains(o), Object.forall(
            o2, Or(o2==farmer, o2==o, s['next']['near'].contains(o2) == s['near'].contains(o2)))
               )
    )),
    And(s['next']['near'].contains(farmer), s['far'].exists(
        o, And(s['next']['near'].contains(o), Object.forall(
            o2, Or(o2==farmer, o2==o, s['next']['far'].contains(o2) == s['far'].contains(o2)))
               )
    ))
))))
config_fact(Start == states[0])


meta_fact(State.forall(s, If(
    s['near'].contains(farmer),
    s['far'].forall(o, Not(s['far'].contains(o['eat']))),
    s['near'].forall(o, Not(s['near'].contains(o['eat'])))
)))

solver = Solver()
solver.add(*get_all_meta_facts())
solver.add(*get_all_config_facts())
print solver.check()
result = cast_all_objects(solver.model())
# pprint(result)

print 'Here is how they move:'
for s in states:
    sname = str(s)
    if sname in result:
        print '%40s, %40s' % (result[sname]['near'], result[sname]['far'])
