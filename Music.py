def music(comp, music_assignment):
    out = []
    for arg in music_assignment.split(","):
        arg = arg.strip()
        if arg.startswith("\""):
            # TODO: Keyword based (e.g queens, 4-runs)
            if arg.lower() == "\"default\"":
                arg = get_default(comp.stage)
            else:
                arg = string_to_test(arg, comp.stage)
        out.append((arg, sum((row.matches(arg) for row in comp))))
    return "\n".join("{} = {!s}".format(arg, n) for arg, n in out)


def get_default(stage):
    # TODO: Stage based defaults
    return "/*/"


def string_to_test(arg, stage):
    arg = arg.strip("\"")
    if "*" in arg or len(arg) == stage:
        # Already right length or expanding to it
        out = "/{}/".format(arg)
    else:
        out = "/*{}/".format(arg)
    return out
