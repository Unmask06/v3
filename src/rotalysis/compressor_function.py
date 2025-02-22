import pandas as pd

from rotalysis import UtilityFunction as uf
from utils import UnitConvertor as uc


class CompressorFunction:
    @staticmethod
    def calculate_compressor_power(
        Qm,
        Ps,
        Pd,
        Ts,
        MW,
        k,
        poly_eff,
        Zs,
        Zd,
        Qm_unit="MMSCFD",
        P_unit="psi",
        Ts_unit="degF",
        gauge=True,
    ):
        """
        Calculate the compressor shaft power.

        Args:
            Qm (MMSCFD) or Mass Flowrate
            Ps (bara): Suction Pressure
            Pd (bara): Discharge Pressure
            Ts (°C): Suction Temperature
            MW (g/mol): Molecular Weight
            k (Cp/Cv - R): Specific Heat Ratio - Real Gas
            polytropic_eff (fraction): Polytropic Efficiency
            Zs (no unit): Suction Compressibility Factor
            Zd (no unit): Discharge Compressibility Factor

        Returns:
            (kW): Compressor shaft power
        """
        # Convert units using UnitConvertor class

        R = 8.314  # J/mol.K
        Ps = uc.convert(Ps, P_unit, "kPa")
        Pd = uc.convert(Pd, P_unit, "kPa")
        if gauge:
            Ps = Ps + 101.325
            Pd = Pd + 101.325
        Ts = uc.convert(Ts, Ts_unit, "K")
        Qm = (
            uc.convert_MMSCFD_to_kg_per_h(Qm, MW) / 3600
            if Qm_unit == "MMSCFD"
            else uc.convert(Qm, Qm_unit, "kg/s")
        )

        adiabatic_exponent = (k - 1) / k

        polytropic_exponent = adiabatic_exponent / poly_eff

        Z_avg = (Zs + Zd) / 2
        Z = (Z_avg ** (1 / k)) * (Zs**adiabatic_exponent)

        polytropic_head = ((Z * (R / MW) * Ts) / polytropic_exponent) * (
            ((Pd / Ps) ** (polytropic_exponent)) - 1
        )
        gas_power = polytropic_head * Qm
        compressor_power = gas_power / poly_eff

        return compressor_power
