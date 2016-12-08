from SirilParser import parse
from SirilProver import prove


def run(siril, case_sensitive=True):
    prove(*parse(siril, case_sensitive)[:2])

if __name__ == '__main__':
    test_input_1 = r"""

        6 bells
        Cm = &-3-4-2-3-4-5
        p = Cm, +2, {/16*/: "  @"}
        b = Cm, +4, "- @"
        comp = 2(2p,b,p,b)
        prove comp
        """
    test_input_2 = r"""
        6 bells;
        b = +4;
        Cm = &-3-4-2-3-4-5, (p = +2);
        Pr = &-3-4-2-3-4-5, (p = +6);
        comp =  3(Cm,b,Cm,p,Pr,p,Pr,p,Cm,p,Cm,b,Cm,p,Pr,p,Pr,p,Cm,b);
        prove comp
        """
    test_input_3 = r"""
        6 bells;
        lh = "\";

        start  = "  @ \";
        finish = lh, "\n";

        p2lh = +2,   "  @ \";
        p6lh = +6,   "  @ \";
        blh  = +4,   "- @ \";

        lh2 = (p = lh=p2lh), (b = lh=blh), (lh=p2lh);
        lh6 = (p = lh=p6lh), (b = lh=blh), (lh=p6lh);

        Cm = lh, &-3-4-2-3-4-5, lh2, "Cm"; // Cambridge
        Pr = lh, &-3-4-2-3-4-5, lh6, "Pr"; // Primrose

        prove 3( Cm,b,Cm,Pr,Pr,Cm,Cm,b,Cm,Pr,Pr,Cm,b );
        """
    test_input_4 = r"""
        6 bells;

        m = &-3-4-2-3-4-5;

        p = +2, "  @";
        b = +4, "- @";

        W = repeat( m, {/*6/:  b, break; p} )
        H = repeat( m, {/*6?/: b, break; p} )

        finish = repeat(m, p, {/123456/: break})

        prove 3(W,H,W)
        """
    test_false_1 = r"""
        8 bells
        2 extents
        everyrow = "@"
        abort = "HI there"
        conflict=
        prove 10(&xxx,+x)"""
    test_dixons = """
        // 720 Dixon's Bob Minor.   Comp. A.E.Holroyd.

        6 bells;

        lead = repeat( +x, { /1*/: break; /[24]*/: +14; +16 } );

        p = lead, +12,   "  @";
        b = lead, +14,   "- @";
        s = lead, +1234, "s @";

        prove 4p,s,4p,b,4p,p,4p,b,
              4p,b,4p,b,4p,s,4p,b,
              4p,b,4p,b,4p,p,4p,b"""

    test_magic = r"""
        // 720 Spliced Treble Dodging Minor.   Comp. P.A.B.Saddleton.

        6 bells;

        printlh = over,under,"\n  @ \", over;
        printhl = under, " @ \";

        mid1 = +-2-; // p.n. when treble is dodging 3-4 up
        mid2 = +-2-; // p.n. when treble is dodging 3-4 down

        // Overworks
        A = +4.5-3.2,   (over="A\"), printlh, +3-5.4,  mid1;  // George Orwell
        B = +4-34-2,    (over="B\"), printlh, +-34-4,  mid1;  // Westminster
        C = +4.3-3.2,   (over="C\"), printlh, +3-3.4,  mid1;  // London
        D = +4.3-34.2,  (over="D\"), printlh, +34-3.4, mid1;  // Carlisle
        E = +4-3-2,     (over="E\"), printlh, +-3-4,   mid1;  // Cambridge

        // Underworks
        a = +3-34-5,    (under="a\"),printhl, +-34-3,  mid2;  // S2 (aka Rhyl)
        b = +3.4-4.5,   (under="b\"),printhl, +4-4.3,  mid2;  // Chelsea
        c = +3.2-4.5,   (under="c\"),printhl, +4-2.3,  mid2;  // Kelso
        d = +3.4-34.5,  (under="d\"),printhl, +34-4.3, mid2;  // Beverley
        e = +3-4-5,     (under="e\"),printhl, +-4-3,   mid2;  // Cambridge

        // Opening half-lead -- start midway through a D overwork
        firstsection = "  @ D\", +34-3.4

        // Which bells pivot for which over/underworks?
        above = { /2*/: D; /3*/: C; /4*/: E; /5*/: B; /6*/: A; };
        below = { /*2/: e; /*3/: c; /*4/: d; /*5/: b; /*6/: a; };

        // Tidy up and exit when rounds occurs
        rounds = over,under,"", break;

        prove firstsection, mid1, repeat (below, above);"""

    test_input_5 = r"""
        8 bells
        B=repeat(Sup,{/18*/:b,break;p})
        M=repeat(Sup,{/*8???/:b,break;p})
        sM=repeat(Sup,{/*8???/:s,break;p})
        sW=repeat(Sup,{/*8/:s,break;p})
        sH =repeat(Sup,{/*8?/:s,break;p})
        end=repeat({/12345678/:break;Sup,p})
        s=+234,"s @"
        b=+4,"- @"
        p=+2
        Sup=&x36x4x5x36x4x5x36x7
        snap = " (12536478)",+x4x5x36x4x5x36x7x36x5x4x36x5x4x36x2

        prove snap, 2(sM, M), sW, sH, B, sW, B, end"""
    test_input_6 = r"""

        12 bells


        peal=+x3x34,b,p,p,p,p,p,mwh,h,h,w,mh,h,wh,h,h



        big=lead,+18
        smwh=p,p,p,p,s,b,p,p,p,p,b
        swh=p,p,p,p,p,s,p,p,p,p,b
        msh=p,p,p,p,b,p,p,p,p,p,s
        mswsh=p,p,p,p,b,s,p,p,p,p,s
        mswh=p,p,p,p,b,s,p,p,p,p,b
        mwh=p,p,p,p,b,b,p,p,p,p,b
        mh=p,p,p,p,b,p,p,p,p,p,b
        h=10p,b
        sh=10p,s
        wh=p,p,p,p,p,b,p,p,p,p,b
        sw=p,p,p,p,p,s,p,p,p,p,p
        wsh=p,p,p,p,p,b,p,p,p,p,s
        mw=p,p,p,p,b,b,p,p,p,p,p
        mwsh=p,p,p,p,b,b,p,p,p,p,s
        w=p,p,p,p,p,b,p,p,p,p,p
        msw=p,p,p,p,b,s,p,p,p,p,p
        swsh=p,p,p,p,p,s,p,p,p,p,s
        smsw=p,p,p,p,s,s,p,p,p,p,p
        smswh=p,p,p,p,s,s,p,p,p,p,b
        smswsh=p,p,p,p,s,s,p,p,p,p,s
        sm=p,p,p,p,s,p,p,p,p,p,p
        smw=p,p,p,p,s,b,p,p,p,p,p
        smwsh=p,p,p,p,s,b,p,p,p,p,s
        smsh=p,p,p,p,s,p,p,p,p,p,s
        smh=p,p,p,p,s,p,p,p,p,p,b
        m=p,p,p,p,b,p,p,p,p,p,p


        p=lead,+12,"@...Plain"
        b=lead,+14,"@......BoB"
        s=lead,+1234,"@......Single"
        x=lead,+18
        T=lead,+12345678



        lead=Yorkshire




        yorkstart=&-4-5-6-27-38-49-50-6-7-8-E,+3-2
        hlbys=&-3-4-5-6-27-38-49-50-6-7-8-9,+234
        hlsyb=&-3-4-5-6-27-38-49-50-6-7-8-90Et,+4
        hlbyp=&-3-4-5-6-27-38-49-50-6-7-8-9,+2
        hlsyp=&-3-4-5-6-27-38-49-50-6-7-8-90Et,+2
        hlbyb=&-3-4-5-6-27-38-49-50-6-7-8-9,+4
        hlsys=&-3-4-5-6-27-38-49-50-6-7-8-90Et,+234
        Yorkshire=&-3-4-5-6-27-38-49-50-6-7-8-E
        Pudsey=&-5-6-27-38-49-50-6-7-8-9-0-E
        cambridge=&x3x4x25x36x47x58x69x70x8x9x0xE
        ALBANIAN=&x3x4x5x6x7x8x29x30x4x5x6xE
        lINCOLNSHIRE=&x3x4x5x6x7x8x9x0x8x9x70xE
        sWINDON=&x3x4x5x6x7x8x9x0x6x7x58xE
        quedgeley=&x3x4x5x6x27x38x49x50x6x7x890xE
        eveshamabbey=&x3x4x5x6x27x38x49x50x6x7x8.56.E

        hlscp=&x3x4x25x36x47x58x69x70x8x9x0x90E,+2
        hlscb=&x3x4x25x36x47x58x69x70x8x9x0x90E,+4
        hlscs=&x3x4x25x36x47x58x69x70x8x9x0x90E,+234

        Cambend=+x3



        music="7890ET","default","?234567","12345","1234567","?654321","7654321","1234","4321","3456","2345","4567","34567",
        "7654","76543","6543","5432","?1234","?4321","?3456","?2345","?4567","?34567","?76543","?7654","?6543","?5432",
        "te0987654321","65432","?65432","23456","23465","?23456","?23465", "?658790ET","?568790ET","1324567890ET",
        "1243567890ET","2134567890ET","1234576890ET","1234657890ET","1234568790ET","1235467890ET","1235467890ET",
        "1627384950ET","1234567809ET","?560987ET","?650987ET","90ET","567890ET","TE098765","TE098756","657890","756890ET",
        "765890ET","467890ET","647890ET","?756890ET","?765890ET","?876590ET", "?8756","?24680ET","?74680ET","?34680","568790"
        //everyrow="@"
        //conflict="""

    test_41 = r"""
        6 bells
        7 extents

        peal = "  @ \",2(No, Ne, Ad, Wsb, Adb, Wsb, Wkb, Wm, Lf, Bm, Wmb, Ab, Wk, Ab, Ro, Rob, St, Bc, Stb, Wk), (No, Ne, Ws,
        Wsb, Adb, Wsb, Wkb, Wm, Lf, Bm, Wmb, Ab, Wk, Ab, Ro, Rob, St, Bc, Stb, Wk), (Clb, Wo, Wh, Nwb, Cl, Ch, Clb, Nbb, Mo,
        Sa), 2(Clb, Wo, Wh, Nwb, Cl, Ch, Clb, Nbb, Ct, Sa), (Chb, Nb, Mu, Nw, Sab, 2Nbb, Mu, Clb), 2(Chb, Nb, Mu, Ak, Sab, 2Nbb,
         Mu, Clb), 3(Ip, Bo, Ip, Cmb, Yo, Cm, Du, Dub, Hu, Pr, Nf, Nfb, Dub, Bv, Bk, Bkb, He, Su, Sub, Yob), 2(Lo, Ke, Lob, Li,
         Cob, Lo, Ke, Lob, Lib, Cu, Lib), (We, Ke, Web, Co, Cob, We, Ke, Web, Lib, Cu, Lib),""
        @ = [1:]
        Cm=Cambridge,+2,"Cm \"
        Cmb=Cambridge,+4,"Cm","- @ \"
        Pr=Cambridge,+1,"Pr \"
        Ip=Ipswich,+2,"Ip \"
        Nf=Ipswich,+1,"Nf \"
        Nfb=Ipswich,+4,"Nf","- @ \"
        Bo=Bourne,+2,"Bo \"
        Hu=Bourne,+1,"Hu \"
        Bv=Beverley,+2,"Bv \"
        Bk=Beverley,+1,"Bk \"
        Bkb=Beverley,+4,"Bk","- @ \"
        Su=Surfleet,+2,"Su \"
        Sub=Surfleet,+4,"Su","- @ \"
        He=Surfleet,+1,"He \"
        Yo=York,+2,"Yo \"
        Yob=York,+4,"Yo","- @ \"
        Du=Durham,+2,"Du \"
        Dub=Durham,+4,"Du","- @ \"

        Ne=Netherseale,+2,"Ne \"
        Ab=Netherseale,+1,"Ab \"
        Lf=Rossendale,+2,"Lf \"
        Ro=Rossendale,+1,"Ro \"
        Rob=Rossendale,+4,"Ro","- @ \"
        Wm=Wearmouth,+2,"Wm \"
        Wmb=Wearmouth,+4,"Wm","- @ \"
        St=Wearmouth,+1,"St \"
        Stb=Wearmouth,+4,"St","- @ \"
        Ws=Westminster,+2,"Ws \"
        Wsb=Westminster,+4,"Ws","- @ \"
        Ad=Allendale,+2,"Ad \"
        Adb=Allendale,+4,"Ad","- @ \"
        Bm=Bamborough,+2,"Bm \"
        Bc=Bamborough,+1,"Bc \"
        No=Norwich,+1,"No \"
        Wk=Warkworth,+1,"Wk \"
        Wkb=Warkworth,+4,"Wk","- @ \"

        Lo=London,+2,"Lo \"
        Lob=London,+4,"Lo","- @ \"
        We=Wells,+2,"We \"
        Web=Wells,+4,"We","- @ \"
        Li=Lincoln,+2,"Li \"
        Lib=Lincoln,+4,"Li","- @ \"
        Co=Coldstream,+2,"Co \"
        Cob=Coldstream,+4,"Co","- @ \"
        Cu=Cunecastre,+2,"Cu \"
        Ke=Kelso,+2,"Ke \"

        Cl=Carlisle,+2,"Cl \"
        Clb=Carlisle,+4,"Cl","- @ \"
        Nb=Northumberland,+2,"Nb \"
        Nbb=Northumberland,+4,"Nb","- @ \"
        Wh=Northumberland,+1,"Wh \"
        Ch=Chester,+2,"Ch \"
        Chb=Chester,+4,"Ch","- @ \"
        Mu=Munden,+2,"Mu \"
        Ak=Alnwick,+2,"Ak \"
        Ct=Alnwick,+1,"Ct \"
        Nw=Newcastle,+2,"Nw \"
        Nwb=Newcastle,+4,"Nw","- @ \"
        Mo=Newcastle,+1,"Mo \"
        Sa=Sandiacre,+2,"Sa \"
        Sab=Sandiacre,+4,"Sa","- @ \"
        Wo=Sandiacre,+1,"Wo \"

        Cambridge=&-3-4-2-3-4-5
        Ipswich=&-3-4-2-3-4-1
        Bourne=&-3-4-2-3-34-3
        Beverley=&-3-4-2-3.4-34.5
        Surfleet=&-3-4-2-3.4-2.5
        York=&-3-4-2-3.4-4.3
        Durham=&-3-4-2-3.4-34.1

        Netherseale=&-34-4-2-3-4-3
        Rossendale=&-34-4-2-3.4-4.3
        Wearmouth=&-34-4-2-3.4-34.1
        Westminster=&-34-4-2-3-2-3
        Allendale=&-34-4-2-3.2-2.3
        Bamborough=&-34-4-2-3.2-4.5
        Norwich=&-34-4-2-3-34-1
        Warkworth=&-34-4-2-3.4-2.3

        London=&3-3.4-2-3.4-4.3
        Wells=&3-3.4-2-3.4-34.1
        Lincoln=&3-3.4-2-3-2-3
        Coldstream=&3-3.4-2-3.2-2.3
        Cunecastre=&3-3.4-2-3-4-3
        Kelso=&3-3.4-2-3.2-4.5

        Carlisle=&34-3.4-2-3-4-5
        Northumberland=&34-3.4-2-3-4-1
        Chester=&34-3.4-2-3.4-34.5
        Munden=&34-3.4-2-3.4-2.5
        Alnwick=&34-3.4-2-3.4-4.3
        Newcastle=&34-3.4-2-3.4-34.1
        Sandiacre=&34-3.4-2-3-34-3"""
    test_false_2 = r"""
        16 bells
        c = 16x
        x = &-D
        everyrow = "@"
        """
    test_input_7 = r"""
        8 bells
        compEHM=p,s,4p,s,line,
        4p,b,6p,b,6p,b,p,s,line,
        p,s,4p,b,line,
        b,s,4p,s,line,
        4p,b,6p,b,6p,b,p,s,line,
        p,s,p,b,2p,2b,line,
        2p,b,2p,line,
        s,3p,b,2p,s

        p=Lead,+12,{/*5678/:(@=[1:4]);/*678/:(@=[1:5]);/*78/:(@=[1:6]);/*8/:(@=[1:])}, {/*8/:"  @"}
        b=Lead,+14,"- @"
        s=Lead,+1234,"s @"
        Lead=&x18x18x18x18
        start = (test = @[4:])

        line="--------", {test: "@[4:]"}


        """
    test_input_8 = r"""
        /  5075 Grandsire Caters
        /  Composed by S A Bond
        /  5075 no. 2

        9 bells

        comp=b,2p,b,2p,ln,
        BBlock,
        b,p,2b,p,line,
        BBlock,
        b,3p,s,p,ln,
        b,b,2p,b,line,
        CBlock,
        s,b,s,b,sp,line,
        CBlock,
        s,b,b,2p,line,
        p,p,s,p,p,s,ln,
        s,s,s,b,sp,line,
        p,s,p,b,p,b,ln,
        DBlock,A,
        DBlock,3b,2p,line,3b,fin

        A=2(3b,2p,line)

        BBlock=rule,
        A,s,b,p,b,p,line,A,
        s,3p,b,p,ln,A,
        b,p,s,b,p,line,
        b,3p,b,p,ln,A,
        rule

        CBlock=rule,
        s,p,s,p,b,line,
        b,b,4p,ln,
        A,
        b,p,s,b,p,line,
        rule

        DBlock=rule,
        b,p,b,b,p,line,
        A,
        b,p,b,s,p,line

        start="1 2 3 4 5 6  @[1:]","----------------------"

        p=g,+9.1,"  \"
        b=g,+3.1,"- \"
        s=g,+3.123,"s \"
        sp="  \"
        fin=g,+9,"      (34265879)"
        line="   \", print
        ln=" \", print
        print = {recall5: "@[1:4]"; recall4:"@[1:5]"; recall3:"@[1:6]"; recall2:"@[1:7]"; "@[1:]"}, recall
        start = recall
        recall = (recall5=@[4:]), (recall4=@[5:]), (recall3=@[6:]), (recall2=@[7:])
        rule="----------------------"

        g=+3.1.9.1.9.1.9.1.9.1.9.1.9.1.9.1
    """
    test_input_9 = r"""
        9 bells

        comp=b,p,s,b,p,q,line,
        BBlock,
        s,p,p,s,p,line,
        p,s,s,b,p,line,
        s,b,s,b,sp,line,
        s,s,s,s,sp,line,
        p,p,s,b,b,line,rule,
        s,b,p,p,s,line,
        b,p,p,s,b,line,
        b,s,b,b,sp,line,
        b,p,p,p,s,q,q,line,
        (ToHSCourse=b,p,b,p,p,q,line),(BFinish=AFinish),
        BBlock

        ABlock=rule,3b,2p,line,2b,s,2p,line,2(3b,2p,line),2b,s,2p,line,rule
        AFinish=rule,3b,2p,line,2b,s,2p,line,3b,2p,line,3b,fin
        BFinish=ABlock
        ToHSCourse=b,p,b,b,p,line

        BBlock=ABlock,
        b,s,p,b,sp,line,
        s,p,s,p,b,line,
        b,b,p,p,p,q,line,
        b,b,b,p,p,line,
        b,b,b,p,p,line,
        b,p,s,b,p,line,
        s,s,s,p,p,line,
        p,b,b,b,p,line,
        ABlock,
        ToHSCourse,
        BFinish

        start="@[1:] 1 2 3 4 5",rule, recall
        store = " \"
        p=g,+9.1,(store=store, "  \")
        q=g,+9.1
        b=g,+3.1,(store=store, "- \")
        s=g,+3.123,(store=store, "s \")
        sp= (store =store, "  \")
        fin=g,+9,"     (34265879)"
        //line="  \", print
        line = print, store, (store=" \"),""
        rule="-------------------"
        recall = (recall5=@[4:]), (recall4=@[5:]), (recall3=@[6:]), (recall2=@[7:])
        print = {recall5: "@[1:4]      \"; recall4:"@[1:5]     \"; recall3:"@[1:6]    \"; recall2:"@[1:7]   \"; "@[1:] \"}, recall

        g=+3.1.9.1.9.1.9.1.9.1.9.1.9.1.9.1

        prove comp"""





    # run(test_input_1)
    # run(test_input_2)
    # run(test_input_3)
    # run(test_input_4)
    # run(test_dixons)
    # run(test_magic)
    # run(test_input_5)
    # run(test_false_1)
    # run(test_input_6, case_sensitive=False)
    # run(test_41)
    # run(test_false_2)
    # run(test_input_8)
    run(test_input_9)
