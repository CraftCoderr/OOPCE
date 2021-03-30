class(C),
    property(C,P1), property(C,P2), property(C,P3), all_diff([P1,P2,P3]),
    constructor(C,[]),
    constructor(C,PL1), length(PL1,PL1size), PL1size>0,
    destructor(C),
    method_declaration(C,M1,_,_), method_implementation(C,M1,inside,_,_),
    method_declaration(C,M2,_,_), method_implementation(C,M2,outside,_,_)