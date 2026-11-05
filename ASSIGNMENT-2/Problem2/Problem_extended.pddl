(define (problem mars-rover-extended)
  (:domain mars-rover)
  (:objects
    Curiosity - rover
    Base SiteA SiteB SiteC SiteD SiteE SiteF - location
    Rock1 Rock2 Rock3 Rock4 Rock5 Rock6 Rock7 - rock
    Bay1 Bay2 - bay
    Drill1 - drill
  )
  (:init
    (at-rover Curiosity Base)
    (at-drill Drill1 SiteE)
    (bay-empty Bay1)
    (bay-empty Bay2)

    (soft Rock1)
    (soft Rock2)
    (hard Rock3)
    (soft Rock4)
    (hard Rock5)
    (soft Rock6)
    (hard Rock7)
    (at-rock Rock1 SiteA)
    (at-rock Rock2 SiteB)
    (at-rock Rock3 SiteC)
    (at-rock Rock4 SiteD)
    (at-rock Rock5 SiteF)
    (at-rock Rock6 SiteE)
    (at-rock Rock7 SiteF)

    (connected Base SiteA)
    (connected SiteA Base)
    ; Base <-> SiteB is closed by the dust storm.
    (connected SiteA SiteC)
    (connected SiteC SiteA)
    (connected SiteB SiteD)
    (connected SiteD SiteB)
    (connected SiteC SiteE)
    (connected SiteE SiteC)
    (connected SiteD SiteE)
    (connected SiteE SiteD)
    (connected SiteE SiteF)
    (connected SiteF SiteE)
    (connected SiteC SiteD)
  )
  (:goal (and
    (at-rock Rock1 Base)
    (at-rock Rock2 Base)
    (at-rock Rock3 Base)
    (at-rock Rock4 Base)
    (at-rock Rock5 Base)
    (at-rock Rock6 Base)
    (at-rock Rock7 Base)
    (bay-empty Bay1)
    (bay-empty Bay2)
    (at-rover Curiosity Base)
  ))
)
