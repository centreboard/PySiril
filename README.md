# PySiril
A python implementation of siril

run as python PySiril.py [-h] [-c] [-I] [-B [BELLS]] [-n [EXTENTS]] [-r [ROUNDS]]
                  [-P [PROVE]] [-M [METHOD]] [-b [BOB]] [-s [SINGLE]]
                  [infile] [outfile]
                  
Where -h brings up help. Infile and outfile specify files to read siril from and output the results to. They default to stdin and stdout respectively and get be explicitly set to be so by using -

MicroSiril is a language for proving compositions for Change Ringing, which was expanded upon by Gsiril. This project is an implementation written in Python that extends Gsiril constructs of pattern matching, dynamic assignment and repeat blocks to include dynamic patttern matching (based on storing specified parts of current row,) formatting the current row output (e.g. omit printing the treble) and extended assignment, where a variable assigns to itself (e.g. currrent_line = current_line, "- \" for a storing a set of string to be printed later. These concepts can be seen in the "SAB 5129 Grandsire Cater.siril" file.

Broadly speaking siril is a series of assignments that eventually resolve as either place notation that advances the composition or a string that is printed. For documentation on Gsiril see http://www.ex-parrot.com/~richard/gsiril/

PySiril also includes new builtin "notextent" which is executed when (for a n extents) a composition:
a) has no row repeated more then n times (else "conflict" and maybe "false" are executed)
b) ends in rounds ("notround")
c) some rows appear fewer than n-1 times (else "true") 

There are also additional statements/optional arguments:

Calling Positions
or the flag -c

This executes siril for the standard calling positions Home (H), Wrong (W), Middle (M) and Before based on the position of the tenor. It is likely to only work for standard use case of lead end placenotation being length 1 and middle not being making an n-2 bob.
The current implementation is where method can be assigned by the method statement or just set it to the place notation for the lead with p, b and s being the lead end place notation.

    H = repeat(method, {/*{tenor}?/: b, break; p})
    sH = repeat(method, {/*{tenor}?/: s, break; p})
    pH = repeat(method, {/*{tenor}?/: p, break; p})
    W = repeat(method, {/*{tenor}/: b, break; p})
    sW = repeat(method, {/*{tenor}/: s, break; p})
    M = repeat(method, {/*{tenor}???/: b, break; p})
    sM = repeat(method, {{/*{tenor}???/: s, break; p})
    B = repeat(method, {/1{tenor}*/: b, break; p})

method <Method Title> ["<short>"]
or the optional argument -M <Method Title> to the command line

This looks up the given <method title>, adding the stage name based on the number of bells if it is omitted from the title, and generates pysiril code based either on the given <short> name or the first two letters of the title if no short form is given. Specifically the siril is of the form (substituting {short}, {notation} and {le}:

    lh =
    finish = lh, (lh = ), finish //means lh affects exactly once at finish
    method = lh, {short}_pn, {short}_lh
    print_p =
    print_b = "- @"
    print_s = "s @"
    print_method = print_{short}
    print_{short} = "{short} \\"
    {short} = (method = lh, {short}_pn, {short}_lh, (print_method = print_{short})), method
    {short}_pn = {notation}
    {short}_lh = (p = (lh = {short}_p), {short}_full_lead), (b = (lh = {short}_b), {short}_full_lead),
                 (s = (lh = {short}_s), {short}_full_lead), (lh={short}_p)
    {short}_full_lead = (p = lh, {short}_pn, (lh = {short}_p)), (b = lh, {short}_pn, (lh = {short}_b)),
                        (s = lh, {short}_pn, (lh = {short}_s))
    {short}_p = {le}, print_p
    {short}_b = bob, print_b
    {short}_s = single, print_s
                

Assign bob and single to desired place notation, e.g. bob = +4; single = +234 or by running with the -b and -s flags sets them to these defaults if no place notation is specified after (i.e. -b+6 will use a 6ths place bob)

The result of this siril is that after calling 6 bells; method Plain Bob "PB"; bob=+4; you can run

    prove 2(PB, b, 3(PB, p), PB, b)
    prove 2(PB, b, 3(method, p), method, b)    
    prove 2(PB, b, 3(PB), PB, b)
    prove 2(PB, b, 3p, PB, b)
    prove 2(PB, b, 3p, b)
    prove PB, 2(b, 3p, b)
for the same result. I.e. after the first call to a method p, b and single all work to execute a plain/bobbed/singled lead, while calling another short form or method results in a plain lead. method is set to the last short form called.

To change the output reassign print_p, print_b and print_s after the call to method.
To print the current method each lead reassign

    {short}_p = {short}_p, print_method
    {short}_b = {short}_b, print_method
    {short}_s = {short}_s, print_method

For different methods with different bobs add a dynamic assignment to the short method name
E.g for Belfast with 4ths place bobs, Glasgow with 6ths place

    8 bells
    method Belfast Surprise "F" 
    method Glasgow Surprise "G"
    F = F, (bob = +4) 
    G = G, (bob = +6)
    prove F, b, G, b
