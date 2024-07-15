import re
from analyzer import StackItem, StackEffect, Instruction, Uop, PseudoInstruction
from dataclasses import dataclass
from cwriter import CWriter
from typing import Iterator

UNUSED = {"unused"}


def maybe_parenthesize(sym: str) -> str:
    """Add parentheses around a string if it contains an operator
       and is not already parenthesized.

    An exception is made for '*' which is common and harmless
    in the context where the symbolic size is used.
    """
    if sym.startswith("(") and sym.endswith(")"):
        return sym
    if re.match(r"^[\s\w*]+$", sym):
        return sym
    else:
        return f"({sym})"


def var_size(var: StackItem) -> str:
    if var.condition:
        # Special case simplifications
        if var.condition == "0":
            return "0"
        elif var.condition == "1":
            return var.size
        elif var.condition == "oparg & 1" and var.size == "1":
            return f"({var.condition})"
        else:
            return f"(({var.condition}) ? {var.size} : 0)"
    else:
        return var.size


@dataclass
class StackOffset:
    "The stack offset of the virtual base of the stack from the physical stack pointer"

    popped: list[str]
    pushed: list[str]

    @staticmethod
    def empty() -> "StackOffset":
        return StackOffset([], [])

    def pop(self, item: StackItem) -> None:
        self.popped.append(var_size(item))

    def push(self, item: StackItem) -> None:
        self.pushed.append(var_size(item))

    def __sub__(self, other: "StackOffset") -> "StackOffset":
        return StackOffset(self.popped + other.pushed, self.pushed + other.popped)

    def __neg__(self) -> "StackOffset":
        return StackOffset(self.pushed, self.popped)

    def simplify(self) -> None:
        "Remove matching values from both the popped and pushed list"
        if not self.popped or not self.pushed:
            return
        # Sort the list so the lexically largest element is last.
        popped = sorted(self.popped)
        pushed = sorted(self.pushed)
        self.popped = []
        self.pushed = []
        while popped and pushed:
            pop = popped.pop()
            push = pushed.pop()
            if pop == push:
                pass
            elif pop > push:
                # if pop > push, there can be no element in pushed matching pop.
                self.popped.append(pop)
                pushed.append(push)
            else:
                self.pushed.append(push)
                popped.append(pop)
        self.popped.extend(popped)
        self.pushed.extend(pushed)

    def to_c(self) -> str:
        self.simplify()
        int_offset = 0
        symbol_offset = ""
        for item in self.popped:
            try:
                int_offset -= int(item)
            except ValueError:
                symbol_offset += f" - {maybe_parenthesize(item)}"
        for item in self.pushed:
            try:
                int_offset += int(item)
            except ValueError:
                symbol_offset += f" + {maybe_parenthesize(item)}"
        if symbol_offset and not int_offset:
            res = symbol_offset
        else:
            res = f"{int_offset}{symbol_offset}"
        if res.startswith(" + "):
            res = res[3:]
        if res.startswith(" - "):
            res = "-" + res[3:]
        return res

    def clear(self) -> None:
        self.popped = []
        self.pushed = []


class StackError(Exception):
    pass


class Stack:
    def __init__(self) -> None:
        self.top_offset = StackOffset.empty()
        self.base_offset = StackOffset.empty()
        self.peek_offset = StackOffset.empty()
        self.variables: list[StackItem] = []
        self.defined: set[str] = set()

    def pop(self, var: StackItem, extract_bits: bool = False) -> str:
        self.top_offset.pop(var)
        if not var.peek:
            self.peek_offset.pop(var)
        indirect = "&" if var.is_array() else ""
        if self.variables:
            popped = self.variables.pop()
            if popped.size != var.size:
                raise StackError(
                    f"Size mismatch when popping '{popped.name}' from stack to assign to {var.name}. "
                    f"Expected {var.size} got {popped.size}"
                )
            if popped.name == var.name:
                var.cached = popped.cached
                return ""
            elif popped.name in UNUSED:
                self.defined.add(var.name)
                return (
                    f"{var.name} = {indirect}stack_pointer[{self.top_offset.to_c()}];\n"
                )
            elif var.name in UNUSED:
                if popped.cached:
                    raise StackError(f"Value is declared unused, but is already cached by prior operation")
                return ""
            else:
                self.defined.add(var.name)
                assert popped.cached
                var.cached = True
                return f"{var.name} = {popped.name};\n"
        self.base_offset.pop(var)
        if var.name in UNUSED:
            return ""
        else:
            self.defined.add(var.name)
        cast = f"({var.type})" if (not indirect and var.type) else ""
        bits = ".bits" if cast and not extract_bits else ""
        assign = (
            f"{var.name} = {cast}{indirect}stack_pointer[{self.base_offset.to_c()}]{bits};"
        )
        if var.condition:
            if var.condition == "1":
                return f"{assign}\n"
            elif var.condition == "0":
                return ""
            else:
                return f"if ({var.condition}) {{ {assign} }}\n"
        return f"{assign}\n"

    def push(self, var: StackItem) -> str:
        self.variables.append(var)
        if var.is_array() and var.name not in self.defined and var.name not in UNUSED:
            c_offset = self.top_offset.to_c()
            self.top_offset.push(var)
            self.defined.add(var.name)
            return f"{var.name} = &stack_pointer[{c_offset}];\n"
        else:
            self.top_offset.push(var)
            if var.name not in UNUSED:
                var.cached = True
            return ""

    def flush(self, out: CWriter, cast_type: str = "uintptr_t", extract_bits: bool = False) -> None:
        out.start_line()
        for var in self.variables:
            if not var.peek:
                cast = f"({cast_type})" if var.type else ""
                bits = ".bits" if cast and not extract_bits else ""
                if var.name not in UNUSED and not var.is_array():
                    if var.condition:
                        if var.condition == "0":
                            continue
                        elif var.condition != "1":
                            out.emit(f"if ({var.condition}) ")
                    out.emit(
                        f"stack_pointer[{self.base_offset.to_c()}]{bits} = {cast}{var.name};\n"
                    )
            self.base_offset.push(var)
        if self.base_offset.to_c() != self.top_offset.to_c():
            print("base", self.base_offset.to_c(), "top", self.top_offset.to_c())
            assert False
        number = self.base_offset.to_c()
        if number != "0":
            out.emit(f"stack_pointer += {number};\n")
            out.emit("assert(WITHIN_STACK_BOUNDS());\n")
        self.variables = []
        self.base_offset.clear()
        self.top_offset.clear()
        self.peek_offset.clear()
        out.start_line()

    def as_comment(self) -> str:
        return f"/* Variables: {[v.name for v in self.variables]}. Base offset: {self.base_offset.to_c()}. Top offset: {self.top_offset.to_c()} */"


def get_stack_effect(inst: Instruction | PseudoInstruction) -> Stack:
    stack = Stack()
    def stacks(inst : Instruction | PseudoInstruction) -> Iterator[StackEffect]:
        if isinstance(inst, Instruction):
            for uop in inst.parts:
                if isinstance(uop, Uop):
                    yield uop.stack
        else:
            assert isinstance(inst, PseudoInstruction)
            yield inst.stack

    for s in stacks(inst):
        for var in reversed(s.inputs):
            stack.pop(var)
        for var in s.outputs:
            stack.push(var)
    return stack
