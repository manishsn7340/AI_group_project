% Problem 3: Royal Archive access verification using resolution refutation.
% Run with: swipl -q -s royal_archive_access.pl

:- initialization(main, main).

% -----------------------------------------------------------------------------
% Step 1: Predicate-logic representation
% Predicates: archivist/1, verifies/2, trusted/1, access/2,
%             permitted_inspect/2, inspects/2, hidden_mark/1,
%             stored/2, sealed/1.
% Constants: mira, scroll_7, royal_archive.
% Variables: X ranges over persons, R ranges over records; both are
%            universally quantified and are Prolog variables below.

step1_formula(1,
    forall([X,R], implies(and(archivist(X), verifies(X,R)), trusted(X)))).
step1_formula(2,
    forall([X,R], implies(and(trusted(X), access(X,R), sealed(R)),
                          permitted_inspect(X,R)))).
step1_formula(3,
    forall([X,R], implies(and(inspects(X,R), hidden_mark(R)), verifies(X,R)))).
step1_formula(4,
    forall([R], implies(stored(R,royal_archive), sealed(R)))).
step1_formula(5, stored(scroll_7,royal_archive)).
step1_formula(6, access(mira,scroll_7)).
step1_formula(7, and(inspects(mira,scroll_7), hidden_mark(scroll_7))).
step1_formula(8, archivist(mira)).

% -----------------------------------------------------------------------------
% Step 2: Negation of the goal

step2_negated_goal(neg(trusted(mira))).

% -----------------------------------------------------------------------------
% Step 3: Implication removal
% A -> B becomes neg(A) v B.  The conjunction in each antecedent is
% distributed into the corresponding negative literals in the clauses.

step3_implication_removed(1,
    or(neg(archivist(X)), neg(verifies(X,_R)), trusted(X))).
step3_implication_removed(2,
    or(neg(trusted(X)), neg(access(X,R)), neg(sealed(R)),
       permitted_inspect(X,R))).
step3_implication_removed(3,
    or(neg(inspects(X,R)), neg(hidden_mark(R)), verifies(X,R))).
step3_implication_removed(4,
    or(neg(stored(R,royal_archive)), sealed(R))).

% -----------------------------------------------------------------------------
% Step 4: Negation movement
% There are no nested negations in this knowledge base.  The negated atoms
% produced in Step 3 are therefore already in negation-normal form.

step4_negation_moved(1,
    or(neg(archivist(X)), neg(verifies(X,_R)), trusted(X))).
step4_negation_moved(2,
    or(neg(trusted(X)), neg(access(X,R)), neg(sealed(R)),
       permitted_inspect(X,R))).
step4_negation_moved(3,
    or(neg(inspects(X,R)), neg(hidden_mark(R)), verifies(X,R))).
step4_negation_moved(4,
    or(neg(stored(R,royal_archive)), sealed(R))).

% -----------------------------------------------------------------------------
% Step 5: Standardization apart
% Variables in distinct rules are renamed independently when the clauses are
% used.  clause_cnf/2 below creates a fresh Prolog copy on every call.

step5_standardized(1,
    or(neg(archivist(X1)), neg(verifies(X1,_R1)), trusted(X1))).
step5_standardized(2,
    or(neg(trusted(X2)), neg(access(X2,R2)), neg(sealed(R2)),
       permitted_inspect(X2,R2))).
step5_standardized(3,
    or(neg(inspects(X3,R3)), neg(hidden_mark(R3)), verifies(X3,R3))).
step5_standardized(4,
    or(neg(stored(R4,royal_archive)), sealed(R4))).

% -----------------------------------------------------------------------------
% Step 6: Skolemization
% No formula contains an existentially quantified variable, so no Skolem
% function or Skolem constant is required.

step6_skolemized(no_existential_quantifiers,
    no_skolem_terms_introduced).

% -----------------------------------------------------------------------------
% Step 7: CNF clauses
% A clause is a list of literals.  The facts become unit clauses and the
% negated goal is also included as a unit clause.

clause_cnf(c1_trusted_rule,
    [neg(archivist(X)), neg(verifies(X,_R)), trusted(X)]).
clause_cnf(c2_permitted_rule,
    [neg(trusted(X)), neg(access(X,R)), neg(sealed(R)),
     permitted_inspect(X,R)]).
clause_cnf(c3_verifies_rule,
    [neg(inspects(X,R)), neg(hidden_mark(R)), verifies(X,R)]).
clause_cnf(c4_sealed_rule,
    [neg(stored(R,royal_archive)), sealed(R)]).
clause_cnf(c5_stored_fact, [stored(scroll_7,royal_archive)]).
clause_cnf(c6_access_fact, [access(mira,scroll_7)]).
clause_cnf(c7_inspects_fact, [inspects(mira,scroll_7)]).
clause_cnf(c8_hidden_mark_fact, [hidden_mark(scroll_7)]).
clause_cnf(c9_archivist_fact, [archivist(mira)]).
clause_cnf(c10_negated_goal, [neg(trusted(mira))]).

% -----------------------------------------------------------------------------
% Step 8: Resolution implementation and execution

complementary(A, neg(B)) :- A = B.
complementary(neg(A), B) :- A = B.

% Resolve one complementary pair of literals.  copy_term standardizes the two
% selected clauses apart before unification.
resolve_clauses(C1, C2, Resolvent) :-
    copy_term(C1-C2, C1Copy-C2Copy),
    select(L1, C1Copy, Rest1),
    select(L2, C2Copy, Rest2),
    complementary(L1, L2),
    append(Rest1, Rest2, Combined),
    sort(Combined, Resolvent),
    !.

print_clause(Clause) :-
    copy_term(Clause, Printable),
    numbervars(Printable, 0, _),
    format('~q~n', [Printable]).

resolution_step(Label, Clause1, Clause2, Resolvent) :-
    resolve_clauses(Clause1, Clause2, Resolvent),
    format('~n~w~n  Clause 1: ', [Label]),
    print_clause(Clause1),
    write('  Clause 2: '),
    print_clause(Clause2),
    write('  Resolvent: '),
    print_clause(Resolvent).

run_refutation :-
    clause_cnf(c3_verifies_rule, C3),
    clause_cnf(c7_inspects_fact, C7),
    resolution_step('R1: c3 + c7', C3, C7, R1),

    clause_cnf(c8_hidden_mark_fact, C8),
    resolution_step('R2: R1 + c8', R1, C8, R2),

    clause_cnf(c1_trusted_rule, C1),
    clause_cnf(c9_archivist_fact, C9),
    resolution_step('R3: c1 + c9', C1, C9, R3),

    resolution_step('R4: R3 + R2', R3, R2, R4),

    clause_cnf(c10_negated_goal, C10),
    resolution_step('R5: R4 + c10', R4, C10, EmptyClause),
    EmptyClause = [],
    writeln('\nEmpty clause [] derived: contradiction reached.'),
    writeln('Therefore trusted(mira) follows from the knowledge base.').

% -----------------------------------------------------------------------------
% Step 9: General resolution search (independent check)
% The trace above follows a hand-chosen derivation.  The procedure below does
% not use it: it saturates the clause set with every possible resolvent,
% round by round, until the empty clause appears, and then prints only the
% clauses that the proof actually uses.  Clause c(Id, Literals, Parents).

variant_member(Clause, Clauses) :-
    member(c(_, Other, _), Clauses),
    Clause =@= Other,
    !.

resolve_pair(C1, C2, Resolvent) :-
    copy_term(C1-C2, C1Copy-C2Copy),
    select(L1, C1Copy, Rest1),
    select(L2, C2Copy, Rest2),
    complementary(L1, L2),
    append(Rest1, Rest2, Combined),
    sort(Combined, Resolvent).

new_resolvents(Clauses, Fresh) :-
    findall(r(R, I-J),
            ( member(c(I, C1, _), Clauses),
              member(c(J, C2, _), Clauses),
              I < J,
              resolve_pair(C1, C2, R) ),
            Raw),
    length(Clauses, N),
    add_fresh(Raw, Clauses, N, [], Fresh).

add_fresh([], _, _, Acc, Fresh) :- reverse(Acc, Fresh).
add_fresh([r(R, Parents)|Rest], Known, N, Acc, Fresh) :-
    append(Known, Acc, Seen),
    (   variant_member(R, Seen)
    ->  add_fresh(Rest, Known, N, Acc, Fresh)
    ;   length(Acc, K),
        NewId is N + K + 1,
        add_fresh(Rest, Known, N, [c(NewId, R, Parents)|Acc], Fresh)
    ).

saturate(Clauses, _, Clauses) :-
    member(c(_, [], _), Clauses),
    !.
saturate(Clauses, Round, Final) :-
    Round < 10,
    new_resolvents(Clauses, Fresh),
    Fresh \== [],
    append(Clauses, Fresh, Bigger),
    Next is Round + 1,
    saturate(Bigger, Next, Final).

used_clauses(Id, Clauses, Used) :-
    member(c(Id, _, Parents), Clauses),
    (   Parents = I-J
    ->  used_clauses(I, Clauses, UI),
        used_clauses(J, Clauses, UJ),
        append(UI, UJ, Both),
        append(Both, [Id], Raw),
        list_to_set(Raw, Used)
    ;   Used = [Id]
    ).

general_refutation :-
    findall(C, clause_cnf(_, C), Cs),
    findall(c(I, C, given), nth1(I, Cs, C), Initial),
    saturate(Initial, 0, Final),
    member(c(EmptyId, [], _), Final),
    used_clauses(EmptyId, Final, Used),
    writeln('\nStep 9: general resolution search (no hand-chosen order)'),
    forall(member(Id, Used),
           ( member(c(Id, Lits, Origin), Final),
             (   Origin = given
             ->  format('  [~w] ', [Id]), print_clause(Lits),
                 format('      (given clause)~n')
             ;   Origin = P-Q,
                 format('  [~w] ', [Id]), print_clause(Lits),
                 format('      (resolvent of [~w] and [~w])~n', [P, Q])
             ) )),
    writeln('Empty clause [] derived by the general search as well.').

print_stage(Label, Goal) :-
    format('~n~w: ', [Label]),
    Goal,
    !.

print_all_stages :-
    writeln('ROYAL ARCHIVE RESOLUTION REFUTATION'),
    writeln('Step 1: predicate-logic formulas'),
    forall(step1_formula(N,F), (format('  F~w = ',[N]), print_clause([F]))),
    write('Step 2: negated goal = '), step2_negated_goal(G), print_clause([G]),
    writeln('Step 3: implication removal'),
    forall(step3_implication_removed(N,F), (format('  R~w = ',[N]), print_clause([F]))),
    writeln('Step 4: negation movement: no changes beyond negation-normal form.'),
    writeln('Step 5: variables standardized apart in each rule.'),
    writeln('Step 6: no existential variables; no Skolem terms.'),
    writeln('Step 7: CNF clauses used in the refutation:'),
    forall(clause_cnf(Name,C), (write('  '), write(Name), write(' = '), print_clause(C))).

main :-
    print_all_stages,
    run_refutation,
    general_refutation.
