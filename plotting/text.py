import math
import random
import time
import textwrap

nlwrap = lambda txt,lnsize: "\n".join(textwrap.wrap(txt,lnsize))

def maximizeText(string,width=200,height=100,minsize=8,maxsize=16):
    """
    Try to keep text inside a "box" with a fixed width.
    Returns the text with linebreaks, as well as a recommended font size.
    """
    fontsize = minsize
    calcwidth = lambda string,fontsize: max([len(ln)*fontsize for ln in string.split("\n")])
    linewidth = lambda fontsize: math.floor(width / fontsize)

    cwidth = calcwidth(string,minsize) 
    if cwidth < width:
        while cwidth < width:
            fontsize += 0.1
            cwidth = calcwidth(string,fontsize)
            if fontsize > maxsize:
                fontsize = maxsize
                break
    else:
        string = [string]
        while cwidth > width:
            string = " ".join(string)
            cwidth = calcwidth(string,fontsize)
            string = textwrap.wrap(string,linewidth(fontsize))
            if fontsize < minsize:
                fontsize = minsize
                break
            else:
                fontsize -= 0.1
    return linewidth(fontsize),math.floor(fontsize)

if __name__ == "__main__":
    print(maximizeText("Yes"))
    print(maximizeText("Hello world"))
    print(maximizeText("Hello hellohello world!"))
    print(maximizeText("Hello hellohello wworldworldworldworldworldorld!"))
