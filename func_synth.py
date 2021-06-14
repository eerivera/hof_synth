from __future__ import annotations

from typing import List, Type
from random import choice # note that choice actually accepts weights, see documentation for details

# TODO: need a "can_synthesize" function which determines if we have enough raw components for synthesizing a specific component

class AbstractSynth:
    @classmethod
    def synthesize(cls, 
                   depth: int,
                   input_args: List[SynthArg],
                   output_type: Type[AbstractSynth],
                   int_literals: List[int],
                   int_ops: List[Type[SynthInt]],
                   bool_literals: List[bool],
                   bool_ops: List[Type[SynthBool]],
                   str_literals: List[str],
                   str_ops: List[Type[SynthStr]]):
        raise NotImplementedError

    def evaluate(self, env):
        raise NotImplementedError

class SynthArg(AbstractSynth):
    def __init__(self, name, argtype):
        self.name = name
        self.argtype = argtype

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{self.__class__.__name__}(\"{str(self)}\")"

    def synthesize(self, # type: ignore 
                   depth: int,
                   input_args: List[SynthArg],
                   output_type: Type[AbstractSynth],
                   int_literals: List[int],
                   int_ops: List[Type[SynthInt]],
                   bool_literals: List[bool],
                   bool_ops: List[Type[SynthBool]],
                   str_literals: List[str],
                   str_ops: List[Type[SynthStr]]):
        return self

    def evaluate(self, env):
        if self.name not in env:
            raise KeyError(f"arg {self.name} not in env")
        return env[self.name]



class SynthInt(AbstractSynth):
    @classmethod
    def synthesize(cls, 
                   depth: int,
                   input_args: List[SynthArg],
                   output_type: Type[AbstractSynth],
                   int_literals: List[int],
                   int_ops: List[Type[SynthInt]],
                   bool_literals: List[bool],
                   bool_ops: List[Type[SynthBool]],
                   str_literals: List[str],
                   str_ops: List[Type[SynthStr]]):
        int_args = [a for a in input_args if a.argtype == SynthInt]
        valid_int_ops = [op for op in int_ops if (op == SynthIntConst and int_literals) or (op != SynthIntConst and depth > 1)]
        class_choices: List[Type[SynthInt]] = valid_int_ops + int_args # type: ignore
        return choice(class_choices).synthesize(depth, input_args, output_type, 
                                                       int_literals, int_ops,
                                                       bool_literals, bool_ops,
                                                       str_literals, str_ops)


class SynthIntConst(SynthInt):
    def __init__(self, val: int):
        self.val: int = val

    def __str__(self):
        return str(self.val)

    def __repr__(self):
        return f"{self.__class__.__name__}({str(self)})"

    @classmethod
    def synthesize(cls, 
                   depth: int,
                   input_args: List[SynthArg],
                   output_type: Type[AbstractSynth],
                   int_literals: List[int],
                   int_ops: List[Type[SynthInt]],
                   bool_literals: List[bool],
                   bool_ops: List[Type[SynthBool]],
                   str_literals: List[str],
                   str_ops: List[Type[SynthStr]]):
        if not int_literals:
            raise ValueError("not enough int literals to use for synthesis")
        return SynthIntConst(choice(int_literals))

    def evaluate(self, env):
        return self.val


class SynthIntAdd(SynthInt):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __str__(self):
        return f"({str(self.left)} + {str(self.right)})"

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.left)}, {repr(self.right)})"

    @classmethod
    def synthesize(cls, 
                   depth: int,
                   input_args: List[SynthArg],
                   output_type: Type[AbstractSynth],
                   int_literals: List[int],
                   int_ops: List[Type[SynthInt]],
                   bool_literals: List[bool],
                   bool_ops: List[Type[SynthBool]],
                   str_literals: List[str],
                   str_ops: List[Type[SynthStr]]):
        if depth <= 1:
            raise RuntimeError("attempting to synthesize SynthIntAdd without enough depth")
        left = SynthInt.synthesize(depth - 1, input_args, output_type, 
                                              int_literals, int_ops,
                                              bool_literals, bool_ops,
                                              str_literals, str_ops)
        right = SynthInt.synthesize(depth - 1, input_args, output_type, 
                                               int_literals, int_ops,
                                               bool_literals, bool_ops,
                                               str_literals, str_ops)
        return SynthIntAdd(left, right)

    def evaluate(self, env):
        return self.left.evaluate(env) + self.right.evaluate(env)

class SynthListLen(SynthInt):
    def __init__(self, inner):
        self.inner = inner

    def __str__(self):
        return f"len({str(self.inner)})"

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.inner)})"

    @classmethod
    def synthesize(cls, 
                   depth: int,
                   input_args: List[SynthArg],
                   output_type: Type[AbstractSynth],
                   int_literals: List[int],
                   int_ops: List[Type[SynthInt]],
                   bool_literals: List[bool],
                   bool_ops: List[Type[SynthBool]],
                   str_literals: List[str],
                   str_ops: List[Type[SynthStr]]):
        if depth <= 1:
            raise RuntimeError("attempting to synthesize SynthListLen without enough depth")
        inner = SynthList.synthesize(depth - 1, input_args, output_type, 
                                              int_literals, int_ops,
                                              bool_literals, bool_ops,
                                              str_literals, str_ops)
        return SynthListLen(inner)

    def evaluate(self, env):
        return len(self.inner.evaluate(env))



class SynthBool(AbstractSynth):
    @classmethod
    def synthesize(cls, 
                   depth: int,
                   input_args: List[SynthArg],
                   output_type: Type[AbstractSynth],
                   int_literals: List[int],
                   int_ops: List[Type[SynthInt]],
                   bool_literals: List[bool],
                   bool_ops: List[Type[SynthBool]],
                   str_literals: List[str],
                   str_ops: List[Type[SynthStr]]):
        bool_args = [a for a in input_args if a.argtype == SynthBool]
        valid_bool_ops = [op for op in bool_ops if op == SynthBoolConst or depth > 1]
        class_choices: List[Type[SynthBool]] = valid_int_ops + int_args # type: ignore
        return choice(class_choices).synthesize(depth, input_args, output_type, 
                                                       int_literals, int_ops,
                                                       bool_literals, bool_ops,
                                                       str_literals, str_ops)

    def evaluate(self, env):
        return self.val

class SynthBoolConst(SynthBool):
    def __init__(self, val: bool):
        self.val: bool = val

    def __str__(self):
        return str(self.val)

    def __repr__(self):
        return f"{self.__class__.__name__}({str(self)})"

    @classmethod
    def synthesize(cls, 
                   depth: int,
                   input_args: List[SynthArg],
                   output_type: Type[AbstractSynth],
                   int_literals: List[int],
                   int_ops: List[Type[SynthInt]],
                   bool_literals: List[bool],
                   bool_ops: List[Type[SynthBool]],
                   str_literals: List[str],
                   str_ops: List[Type[SynthStr]]):
        if not bool_literals:
            raise ValueError("not enough int literals to use for synthesis")
        return SynthIntConst(choice(bool_literals))

    def evaluate(self, env):
        return self.val

class SynthBoolAnd(SynthBool):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __str__(self):
        return f"({str(self.left)} and {str(self.right)})"

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.left)}, {repr(self.right)})"

    @classmethod
    def synthesize(cls, 
                   depth: int,
                   input_args: List[SynthArg],
                   output_type: Type[AbstractSynth],
                   int_literals: List[int],
                   int_ops: List[Type[SynthInt]],
                   bool_literals: List[bool],
                   bool_ops: List[Type[SynthBool]],
                   str_literals: List[str],
                   str_ops: List[Type[SynthStr]]):
        if depth <= 1:
            raise RuntimeError("attempting to synthesize SynthBoolAnd without enough depth")
        left = SynthBool.synthesize(depth - 1, input_args, output_type, 
                                              int_literals, int_ops,
                                              bool_literals, bool_ops,
                                              str_literals, str_ops)
        right = SynthBool.synthesize(depth - 1, input_args, output_type, 
                                               int_literals, int_ops,
                                               bool_literals, bool_ops,
                                               str_literals, str_ops)
        return SynthBoolAnd(left, right)

    def evaluate(self, env):
        return self.left.evaluate(env) and self.right.evaluate(env)

class SynthStr(AbstractSynth):
    @classmethod
    def synthesize(cls, 
                   depth: int,
                   input_args: List[SynthArg],
                   output_type: Type[AbstractSynth],
                   int_literals: List[int],
                   int_ops: List[Type[SynthInt]],
                   bool_literals: List[bool],
                   bool_ops: List[Type[SynthBool]],
                   str_literals: List[str],
                   str_ops: List[Type[SynthStr]]):
        str_args = [a for a in input_args if a.argtype == SynthStr]
        valid_str_ops = [op for op in str_ops if (op == SynthStrConst and str_literals) or (op != SynthStrConst and depth > 1)]
        class_choices: List[Type[SynthStr]] = valid_str_ops + str_args # type: ignore
        return choice(class_choices).synthesize(depth, input_args, output_type, 
                                                       int_literals, int_ops,
                                                       bool_literals, bool_ops,
                                                       str_literals, str_ops)

class SynthStrConst(SynthStr):
    def __init__(self, val: str):
        self.val: str = val

    def __str__(self):
        return f"\"{self.val}\""

    def __repr__(self):
        return f"{self.__class__.__name__}(\"{str(self)}\")"

    @classmethod
    def synthesize(cls, 
                   depth: int,
                   input_args: List[SynthArg],
                   output_type: Type[AbstractSynth],
                   int_literals: List[int],
                   int_ops: List[Type[SynthInt]],
                   bool_literals: List[bool],
                   bool_ops: List[Type[SynthBool]],
                   str_literals: List[str],
                   str_ops: List[Type[SynthStr]]):
        if not str_literals:
            raise ValueError("no string literals to use for synthesis")
        return SynthStrConst(choice(str_literals))

    def evaluate(self, env):
        return self.val

class SynthStrAdd(SynthStr):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __str__(self):
        return f"({str(self.left)} + {str(self.right)})"

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.left)}, {repr(self.right)})"

    @classmethod
    def synthesize(cls, 
                   depth: int,
                   input_args: List[SynthArg],
                   output_type: Type[AbstractSynth],
                   int_literals: List[int],
                   int_ops: List[Type[SynthInt]],
                   bool_literals: List[bool],
                   bool_ops: List[Type[SynthBool]],
                   str_literals: List[str],
                   str_ops: List[Type[SynthStr]]):
        if depth <= 1:
            raise RuntimeError("attempting to synthesize SynthStrAdd without enough depth")
        left = SynthStr.synthesize(depth - 1, input_args, output_type, 
                                              int_literals, int_ops,
                                              bool_literals, bool_ops,
                                              str_literals, str_ops)
        right = SynthStr.synthesize(depth - 1, input_args, output_type, 
                                               int_literals, int_ops,
                                               bool_literals, bool_ops,
                                               str_literals, str_ops)
        return SynthStrAdd(left, right)

    def evaluate(self, env):
        return self.left.evaluate(env) + self.right.evaluate(env)

class SynthList(AbstractSynth):
    @classmethod
    def synthesize(cls,
                   depth: int,
                   input_args: List[SynthArg],
                   output_type: Type[AbstractSynth],
                   int_literals: List[int],
                   int_ops: List[Type[SynthInt]],
                   bool_literals: List[bool],
                   bool_ops: List[Type[SynthBool]],
                   str_literals: List[str],
                   str_ops: List[Type[SynthStr]]):
        list_args = [a for a in input_args if a.argtype == SynthList]
        # valid_int_ops = [op for op in int_ops if (op == SynthListConst and int_literals) or (op != SynthIntConst and depth > 1)]
        class_choices: List[Type[SynthList]] = list_args # + valid_int_ops  # type: ignore
        return choice(class_choices).synthesize(depth, input_args, output_type, 
                                                       int_literals, int_ops,
                                                       bool_literals, bool_ops,
                                                       str_literals, str_ops)

def make_func(depth: int,
              input_args: List[SynthArg],
              output_type: Type[AbstractSynth],
              int_literals: List[int],
              int_ops: List[Type[SynthInt]],
              bool_literals: List[bool],
              bool_ops: List[Type[SynthBool]],
              str_literals: List[str],
              str_ops: List[Type[SynthStr]]):
    expr = output_type.synthesize(depth, 
                                  input_args, output_type,
                                  int_literals, int_ops,
                                  bool_literals, bool_ops,
                                  str_literals, str_ops)
    arg_str = ",".join((a.name for a in input_args))
    print(f"lambda {arg_str}: {expr}")
    def inner_func(*args):
        if len(input_args) != len(args):
            raise ValueError("too many or not enough arguments")
        env = {abstract_arg.name: arg for abstract_arg, arg in zip(input_args, args)}
        return expr.evaluate(env)
    return inner_func
        
    
if __name__ == '__main__':
    input_args = [SynthArg("l", SynthList)]#[SynthArg("x", SynthInt), SynthArg("y", SynthStr)]
    output_type = SynthInt
    myfunc = make_func(4, 
                       input_args,
                       output_type,
                       int_literals=list(range(10)),
                       int_ops=[SynthIntConst, SynthIntAdd, SynthListLen],
                       bool_literals=[True, False],
                       bool_ops=[SynthBoolConst, SynthBoolAnd],
                       str_literals=["hello"],
                       str_ops=[SynthStrConst, SynthStrAdd])

    # myintlist = list(range(10))
    mylistoflists = [list(range(3)), list(range(5)), list(range(4))]

    print(list(map(myfunc, mylistoflists)))