(define (domain mars-rover)
  (:requirements :strips :typing)

  (:types rover location rock bay drill)

  (:predicates
    (at-rover ?r - rover ?l - location)
    (at-rock ?x - rock ?l - location)
    (soft ?x - rock)
    (hard ?x - rock)
    (at-drill ?d - drill ?l - location)
    (drill-carried ?d - drill)
    (bay-empty ?b - bay)
    (in-bay ?x - rock ?b - bay)
    (connected ?from - location ?to - location)
  )

  (:action move
    :parameters (?r - rover ?from - location ?to - location)
    :precondition (and
      (at-rover ?r ?from)
      (connected ?from ?to)
    )
    :effect (and
      (at-rover ?r ?to)
      (not (at-rover ?r ?from))
    )
  )

  (:action pick-drill
    :parameters (?r - rover ?d - drill ?l - location)
    :precondition (and
      (at-rover ?r ?l)
      (at-drill ?d ?l)
    )
    :effect (and
      (drill-carried ?d)
      (not (at-drill ?d ?l))
    )
  )

  (:action collect-soft
    :parameters (?r - rover ?x - rock ?l - location ?b - bay)
    :precondition (and
      (at-rover ?r ?l)
      (at-rock ?x ?l)
      (soft ?x)
      (bay-empty ?b)
    )
    :effect (and
      (in-bay ?x ?b)
      (not (at-rock ?x ?l))
      (not (bay-empty ?b))
    )
  )

  (:action collect-hard
    :parameters (?r - rover ?x - rock ?l - location ?b - bay ?d - drill)
    :precondition (and
      (at-rover ?r ?l)
      (at-rock ?x ?l)
      (hard ?x)
      (bay-empty ?b)
      (drill-carried ?d)
    )
    :effect (and
      (in-bay ?x ?b)
      (not (at-rock ?x ?l))
      (not (bay-empty ?b))
    )
  )

  (:action deposit
    :parameters (?r - rover ?x - rock ?b - bay ?l - location)
    :precondition (and
      (at-rover ?r ?l)
      (in-bay ?x ?b)
    )
    :effect (and
      (at-rock ?x ?l)
      (bay-empty ?b)
      (not (in-bay ?x ?b))
    )
  )
)
