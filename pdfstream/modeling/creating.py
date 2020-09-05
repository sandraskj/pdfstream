"""Create a recipe."""
import inspect
import typing as tp

from diffpy.structure import Structure
from pyobjcryst.crystal import Crystal

from .fitfuncs import make_recipe
from .fitobjs import FunConfig, GenConfig, ConConfig, MyParser, MyRecipe

S = tp.Union[Crystal, Structure]


def create(
        name: str,
        data: MyParser,
        arange: tp.Tuple[float, float, float],
        equation: str,
        functions: tp.Dict[str, tp.Callable],
        structures: tp.Dict[str, S],
        ncpu: int = None
) -> MyRecipe:
    """Create a single-contribution recipe without any variables inside.

    Parameters
    ----------
    name :
        The name of the contribution.

    data :
        The parser that contains the information of the

    arange :
        The rmin, rmax, rstep (inclusive).

    equation :
        The equation of the contribution.

    functions :
        The keys are function names in the equation and the values are function objects.

    structures :
        The keys are structure name in the equation and the values are structure object.

    ncpu :
        The number of cpu used in parallel computing. If None, no parallel. Default None.

    Returns
    -------
    recipe :
        A single-contribution recipe without any variables inside.
    """
    genconfigs = [
        GenConfig(
            name=n, structure=s, ncpu=ncpu
        )
        for n, s in structures.items()
    ]
    funconfigs = [
        FunConfig(
            name=n, func=f, argnames=add_suffix(f, n)
        )
        for n, f in functions.items()
    ]
    conconfig = ConConfig(
        name=name, eq=equation, parser=data, fit_range=arange,
        genconfigs=genconfigs, funconfigs=funconfigs
    )
    recipe = make_recipe(conconfig)
    return recipe


def add_suffix(func: tp.Callable, suffix: str) -> tp.List[str]:
    """Add the suffix to the argument names starting at the second the argument. Return the names"""
    args = inspect.getfullargspec(func).args
    return list(
        map(
            lambda arg: '{}_{}'.format(arg, suffix) if arg != "r" else arg,
            args
        )
    )