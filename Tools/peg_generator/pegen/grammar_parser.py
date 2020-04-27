#!/usr/bin/env python3.8
# @generated by pegen from pegen/metagrammar.gram

import ast
import sys
import tokenize

from typing import Any, Optional

from pegen.parser import memoize, memoize_left_rec, logger, Parser
from ast import literal_eval

from pegen.grammar import (
    Alt,
    Cut,
    Gather,
    Group,
    Item,
    Lookahead,
    LookaheadOrCut,
    MetaTuple,
    MetaList,
    NameLeaf,
    NamedItem,
    NamedItemList,
    NegativeLookahead,
    Opt,
    Plain,
    PositiveLookahead,
    Repeat0,
    Repeat1,
    Rhs,
    Rule,
    RuleList,
    RuleName,
    Grammar,
    StringLeaf,
)

class GeneratedParser(Parser):

    @memoize
    def start(self) -> Optional[Grammar]:
        # start: grammar $
        mark = self.mark()
        cut = False
        grammar = self.grammar()
        if grammar:
            endmarker = self.expect('ENDMARKER')
            if endmarker:
                return grammar
        self.reset(mark)
        if cut: return None
        return None

    @memoize
    def grammar(self) -> Optional[Grammar]:
        # grammar: metas rules | rules
        mark = self.mark()
        cut = False
        metas = self.metas()
        if metas:
            rules = self.rules()
            if rules:
                return Grammar ( rules , metas )
        self.reset(mark)
        if cut: return None
        cut = False
        rules = self.rules()
        if rules:
            return Grammar ( rules , [ ] )
        self.reset(mark)
        if cut: return None
        return None

    @memoize
    def metas(self) -> Optional[MetaList]:
        # metas: meta metas | meta
        mark = self.mark()
        cut = False
        meta = self.meta()
        if meta:
            metas = self.metas()
            if metas:
                return [ meta ] + metas
        self.reset(mark)
        if cut: return None
        cut = False
        meta = self.meta()
        if meta:
            return [ meta ]
        self.reset(mark)
        if cut: return None
        return None

    @memoize
    def meta(self) -> Optional[MetaTuple]:
        # meta: "@" NAME NEWLINE | "@" NAME NAME NEWLINE | "@" NAME STRING NEWLINE
        mark = self.mark()
        cut = False
        literal = self.expect("@")
        if literal:
            name = self.name()
            if name:
                newline = self.expect('NEWLINE')
                if newline:
                    return ( name . string , None )
        self.reset(mark)
        if cut: return None
        cut = False
        literal = self.expect("@")
        if literal:
            a = self.name()
            if a:
                b = self.name()
                if b:
                    newline = self.expect('NEWLINE')
                    if newline:
                        return ( a . string , b . string )
        self.reset(mark)
        if cut: return None
        cut = False
        literal = self.expect("@")
        if literal:
            name = self.name()
            if name:
                string = self.string()
                if string:
                    newline = self.expect('NEWLINE')
                    if newline:
                        return ( name . string , literal_eval ( string . string ) )
        self.reset(mark)
        if cut: return None
        return None

    @memoize
    def rules(self) -> Optional[RuleList]:
        # rules: rule rules | rule
        mark = self.mark()
        cut = False
        rule = self.rule()
        if rule:
            rules = self.rules()
            if rules:
                return [ rule ] + rules
        self.reset(mark)
        if cut: return None
        cut = False
        rule = self.rule()
        if rule:
            return [ rule ]
        self.reset(mark)
        if cut: return None
        return None

    @memoize
    def rule(self) -> Optional[Rule]:
        # rule: rulename memoflag? ":" alts NEWLINE INDENT more_alts DEDENT | rulename memoflag? ":" NEWLINE INDENT more_alts DEDENT | rulename memoflag? ":" alts NEWLINE
        mark = self.mark()
        cut = False
        rulename = self.rulename()
        if rulename:
            opt = self.memoflag(),
            if opt:
                literal = self.expect(":")
                if literal:
                    alts = self.alts()
                    if alts:
                        newline = self.expect('NEWLINE')
                        if newline:
                            indent = self.expect('INDENT')
                            if indent:
                                more_alts = self.more_alts()
                                if more_alts:
                                    dedent = self.expect('DEDENT')
                                    if dedent:
                                        return Rule ( rulename [ 0 ] , rulename [ 1 ] , Rhs ( alts . alts + more_alts . alts ) , memo = opt )
        self.reset(mark)
        if cut: return None
        cut = False
        rulename = self.rulename()
        if rulename:
            opt = self.memoflag(),
            if opt:
                literal = self.expect(":")
                if literal:
                    newline = self.expect('NEWLINE')
                    if newline:
                        indent = self.expect('INDENT')
                        if indent:
                            more_alts = self.more_alts()
                            if more_alts:
                                dedent = self.expect('DEDENT')
                                if dedent:
                                    return Rule ( rulename [ 0 ] , rulename [ 1 ] , more_alts , memo = opt )
        self.reset(mark)
        if cut: return None
        cut = False
        rulename = self.rulename()
        if rulename:
            opt = self.memoflag(),
            if opt:
                literal = self.expect(":")
                if literal:
                    alts = self.alts()
                    if alts:
                        newline = self.expect('NEWLINE')
                        if newline:
                            return Rule ( rulename [ 0 ] , rulename [ 1 ] , alts , memo = opt )
        self.reset(mark)
        if cut: return None
        return None

    @memoize
    def rulename(self) -> Optional[RuleName]:
        # rulename: NAME '[' NAME '*' ']' | NAME '[' NAME ']' | NAME
        mark = self.mark()
        cut = False
        name = self.name()
        if name:
            literal = self.expect('[')
            if literal:
                type = self.name()
                if type:
                    literal_1 = self.expect('*')
                    if literal_1:
                        literal_2 = self.expect(']')
                        if literal_2:
                            return ( name . string , type . string + "*" )
        self.reset(mark)
        if cut: return None
        cut = False
        name = self.name()
        if name:
            literal = self.expect('[')
            if literal:
                type = self.name()
                if type:
                    literal_1 = self.expect(']')
                    if literal_1:
                        return ( name . string , type . string )
        self.reset(mark)
        if cut: return None
        cut = False
        name = self.name()
        if name:
            return ( name . string , None )
        self.reset(mark)
        if cut: return None
        return None

    @memoize
    def memoflag(self) -> Optional[str]:
        # memoflag: '(' 'memo' ')'
        mark = self.mark()
        cut = False
        literal = self.expect('(')
        if literal:
            literal_1 = self.expect('memo')
            if literal_1:
                literal_2 = self.expect(')')
                if literal_2:
                    return "memo"
        self.reset(mark)
        if cut: return None
        return None

    @memoize
    def alts(self) -> Optional[Rhs]:
        # alts: alt "|" alts | alt
        mark = self.mark()
        cut = False
        alt = self.alt()
        if alt:
            literal = self.expect("|")
            if literal:
                alts = self.alts()
                if alts:
                    return Rhs ( [ alt ] + alts . alts )
        self.reset(mark)
        if cut: return None
        cut = False
        alt = self.alt()
        if alt:
            return Rhs ( [ alt ] )
        self.reset(mark)
        if cut: return None
        return None

    @memoize
    def more_alts(self) -> Optional[Rhs]:
        # more_alts: "|" alts NEWLINE more_alts | "|" alts NEWLINE
        mark = self.mark()
        cut = False
        literal = self.expect("|")
        if literal:
            alts = self.alts()
            if alts:
                newline = self.expect('NEWLINE')
                if newline:
                    more_alts = self.more_alts()
                    if more_alts:
                        return Rhs ( alts . alts + more_alts . alts )
        self.reset(mark)
        if cut: return None
        cut = False
        literal = self.expect("|")
        if literal:
            alts = self.alts()
            if alts:
                newline = self.expect('NEWLINE')
                if newline:
                    return Rhs ( alts . alts )
        self.reset(mark)
        if cut: return None
        return None

    @memoize
    def alt(self) -> Optional[Alt]:
        # alt: items '$' action | items '$' | items action | items
        mark = self.mark()
        cut = False
        items = self.items()
        if items:
            literal = self.expect('$')
            if literal:
                action = self.action()
                if action:
                    return Alt ( items + [ NamedItem ( None , NameLeaf ( 'ENDMARKER' ) ) ] , action = action )
        self.reset(mark)
        if cut: return None
        cut = False
        items = self.items()
        if items:
            literal = self.expect('$')
            if literal:
                return Alt ( items + [ NamedItem ( None , NameLeaf ( 'ENDMARKER' ) ) ] , action = None )
        self.reset(mark)
        if cut: return None
        cut = False
        items = self.items()
        if items:
            action = self.action()
            if action:
                return Alt ( items , action = action )
        self.reset(mark)
        if cut: return None
        cut = False
        items = self.items()
        if items:
            return Alt ( items , action = None )
        self.reset(mark)
        if cut: return None
        return None

    @memoize
    def items(self) -> Optional[NamedItemList]:
        # items: named_item items | named_item
        mark = self.mark()
        cut = False
        named_item = self.named_item()
        if named_item:
            items = self.items()
            if items:
                return [ named_item ] + items
        self.reset(mark)
        if cut: return None
        cut = False
        named_item = self.named_item()
        if named_item:
            return [ named_item ]
        self.reset(mark)
        if cut: return None
        return None

    @memoize
    def named_item(self) -> Optional[NamedItem]:
        # named_item: NAME '=' ~ item | item | lookahead
        mark = self.mark()
        cut = False
        name = self.name()
        if name:
            literal = self.expect('=')
            if literal:
                cut = True
                if cut:
                    item = self.item()
                    if item:
                        return NamedItem ( name . string , item )
        self.reset(mark)
        if cut: return None
        cut = False
        item = self.item()
        if item:
            return NamedItem ( None , item )
        self.reset(mark)
        if cut: return None
        cut = False
        it = self.lookahead()
        if it:
            return NamedItem ( None , it )
        self.reset(mark)
        if cut: return None
        return None

    @memoize
    def lookahead(self) -> Optional[LookaheadOrCut]:
        # lookahead: '&' ~ atom | '!' ~ atom | '~'
        mark = self.mark()
        cut = False
        literal = self.expect('&')
        if literal:
            cut = True
            if cut:
                atom = self.atom()
                if atom:
                    return PositiveLookahead ( atom )
        self.reset(mark)
        if cut: return None
        cut = False
        literal = self.expect('!')
        if literal:
            cut = True
            if cut:
                atom = self.atom()
                if atom:
                    return NegativeLookahead ( atom )
        self.reset(mark)
        if cut: return None
        cut = False
        literal = self.expect('~')
        if literal:
            return Cut ( )
        self.reset(mark)
        if cut: return None
        return None

    @memoize
    def item(self) -> Optional[Item]:
        # item: '[' ~ alts ']' | atom '?' | atom '*' | atom '+' | atom '.' atom '+' | atom
        mark = self.mark()
        cut = False
        literal = self.expect('[')
        if literal:
            cut = True
            if cut:
                alts = self.alts()
                if alts:
                    literal_1 = self.expect(']')
                    if literal_1:
                        return Opt ( alts )
        self.reset(mark)
        if cut: return None
        cut = False
        atom = self.atom()
        if atom:
            literal = self.expect('?')
            if literal:
                return Opt ( atom )
        self.reset(mark)
        if cut: return None
        cut = False
        atom = self.atom()
        if atom:
            literal = self.expect('*')
            if literal:
                return Repeat0 ( atom )
        self.reset(mark)
        if cut: return None
        cut = False
        atom = self.atom()
        if atom:
            literal = self.expect('+')
            if literal:
                return Repeat1 ( atom )
        self.reset(mark)
        if cut: return None
        cut = False
        sep = self.atom()
        if sep:
            literal = self.expect('.')
            if literal:
                node = self.atom()
                if node:
                    literal_1 = self.expect('+')
                    if literal_1:
                        return Gather ( sep , node )
        self.reset(mark)
        if cut: return None
        cut = False
        atom = self.atom()
        if atom:
            return atom
        self.reset(mark)
        if cut: return None
        return None

    @memoize
    def atom(self) -> Optional[Plain]:
        # atom: '(' ~ alts ')' | NAME | STRING
        mark = self.mark()
        cut = False
        literal = self.expect('(')
        if literal:
            cut = True
            if cut:
                alts = self.alts()
                if alts:
                    literal_1 = self.expect(')')
                    if literal_1:
                        return Group ( alts )
        self.reset(mark)
        if cut: return None
        cut = False
        name = self.name()
        if name:
            return NameLeaf ( name . string )
        self.reset(mark)
        if cut: return None
        cut = False
        string = self.string()
        if string:
            return StringLeaf ( string . string )
        self.reset(mark)
        if cut: return None
        return None

    @memoize
    def action(self) -> Optional[str]:
        # action: "{" ~ target_atoms "}"
        mark = self.mark()
        cut = False
        literal = self.expect("{")
        if literal:
            cut = True
            if cut:
                target_atoms = self.target_atoms()
                if target_atoms:
                    literal_1 = self.expect("}")
                    if literal_1:
                        return target_atoms
        self.reset(mark)
        if cut: return None
        return None

    @memoize
    def target_atoms(self) -> Optional[str]:
        # target_atoms: target_atom target_atoms | target_atom
        mark = self.mark()
        cut = False
        target_atom = self.target_atom()
        if target_atom:
            target_atoms = self.target_atoms()
            if target_atoms:
                return target_atom + " " + target_atoms
        self.reset(mark)
        if cut: return None
        cut = False
        target_atom = self.target_atom()
        if target_atom:
            return target_atom
        self.reset(mark)
        if cut: return None
        return None

    @memoize
    def target_atom(self) -> Optional[str]:
        # target_atom: "{" ~ target_atoms "}" | NAME | NUMBER | STRING | "?" | ":" | !"}" OP
        mark = self.mark()
        cut = False
        literal = self.expect("{")
        if literal:
            cut = True
            if cut:
                target_atoms = self.target_atoms()
                if target_atoms:
                    literal_1 = self.expect("}")
                    if literal_1:
                        return "{" + target_atoms + "}"
        self.reset(mark)
        if cut: return None
        cut = False
        name = self.name()
        if name:
            return name . string
        self.reset(mark)
        if cut: return None
        cut = False
        number = self.number()
        if number:
            return number . string
        self.reset(mark)
        if cut: return None
        cut = False
        string = self.string()
        if string:
            return string . string
        self.reset(mark)
        if cut: return None
        cut = False
        literal = self.expect("?")
        if literal:
            return "?"
        self.reset(mark)
        if cut: return None
        cut = False
        literal = self.expect(":")
        if literal:
            return ":"
        self.reset(mark)
        if cut: return None
        cut = False
        if self.negative_lookahead(self.expect, "}"):
            op = self.op()
            if op:
                return op . string
        self.reset(mark)
        if cut: return None
        return None


if __name__ == '__main__':
    from pegen.parser import simple_parser_main
    simple_parser_main(GeneratedParser)
