"""
rotalysis.pump.curve_generator
This module contains the class PumpCurveGenerator, which generates pump and system curves.
"""

from typing import Callable, Tuple

import numpy as np
from scipy.optimize import curve_fit, fsolve


def get_quadratic_equation(a: float, b: float, c: float) -> Callable[[float], float]:
    """
    Returns a quadratic equation in the form of a lambda function.

    Parameters:
    a (float): The coefficient of x^2.
    b (float): The coefficient of x.
    c (float): The constant term.

    Returns:
    Callable[[float], float]: A lambda function representing the quadratic equation.
    """
    return lambda x: (a * x**2) + (b * x) + c


def get_head_from_curve(
    flow: float,
    a: float,
    b: float = 0,
    noflow_head: float = 0,
) -> float:
    """
    Calculates the head value from a pump curve.

    Parameters:
    - flow (float): The flow rate at which to calculate the head.
    - a (float): The coefficient of the quadratic equation.
    - b (float, optional): The linear coefficient of the quadratic equation. Defaults to 0.
    - noflow_head (float, optional): The head value when there is no flow. Defaults to 0.

    Returns:
    - float: The calculated head value.

    """
    return get_quadratic_equation(a, b, noflow_head)(flow)


def solve_coefficient(
    flow: float, head: float, initial_guess: float, b: float = 0, noflow_head: float = 0
) -> float:
    """
    Solve for the coefficient 'a' in the head curve equation.

    Parameters:
    - flow: The flow rate.
    - head: The desired head value.
    - initial_guess: The initial guess for the coefficient.
    - b: Coefficient 'b' in the head curve equation, if applicable.
    - noflow_head: The head value when there is no flow.

    Returns:
    - The solution for the coefficient 'a'.
    """
    equation = lambda a: get_head_from_curve(flow, a, b, noflow_head) - head  # type: ignore
    solution = fsolve(equation, x0=initial_guess)
    return solution[0]


def get_headcurve_coeff_from_twopoint(rated_flow, rated_head) -> Tuple:
    """
    Calculates the coefficients of the head curve equation from two points.
    Assumes a quadratic equation with b = 0

    Parameters:
    - rated_flow (float): The rated flow rate.
    - rated_head (float): The rated head value.

    Returns:
    - Tuple: The coefficients of the head curve equation.
    """
    shutoff_head = rated_head * 1.3
    a = solve_coefficient(
        rated_flow, rated_head, initial_guess=1, b=0, noflow_head=shutoff_head
    )

    return (a, 0, shutoff_head)


def get_headcurve_coeff_from_multipoint(flow, head) -> Tuple:
    """
    Fits a quadratic polynomial to the provided flow and head data.
    Used to generate the pump curve and system curve.

    Parameters:
    flow (list or np.array): The flow rate data points.
    head (list or np.array): The corresponding head data points.

    Returns:
    tuple: Coefficients (a, b, c) of the fitted polynomial head = a*flow^2 + b*flow + c.

    Raises:
    ValueError: If the length of flow and head arrays do not match or are empty.
    """
    flow = np.asarray(flow)
    head = np.asarray(head)

    if len(flow) != len(head):
        raise ValueError("Flow and head arrays must be of the same length.")

    if len(flow) == 0:
        raise ValueError("Flow and head arrays must not be empty.")

    if flow[0] == 0:

        constant = head[0]
        equation = lambda Q, a, b: get_quadratic_equation(a, b, constant)(Q)
        popt, _ = curve_fit(equation, flow, head)  # pylint: disable=E0632
        return (popt[0], popt[1], constant)

    equation = lambda Q, a, b, c: get_quadratic_equation(a, b, c)(Q)
    popt, _ = curve_fit(equation, flow, head)  # pylint: disable=E0632
    return tuple(popt)
