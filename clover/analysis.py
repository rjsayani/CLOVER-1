#!/usr/bin/python3
########################################################################################
# analysis.py - In-built analysis module for CLOVER.                                   #
#                                                                                      #
# Authors: Phil Sandwell, Ben Winchester                                               #
# Copyright: Phil Sandwell, 2021                                                       #
# Date created: 13/07/2021                                                             #
# License: Open source                                                                 #
########################################################################################
"""
analysis.py - The analysis module for CLOVER.

In order to best check and validate the results produced by CLOVER simulations and
optimisations, an in-built analysis module is provied which generates plots and figures
corresponding to the sugetsed analysis within the user guide.

"""

import dataclasses
import os

from typing import Dict, Optional

import numpy as np
import pandas as pd
import seaborn as sns

import matplotlib.pyplot as plt
from tqdm import tqdm

from .__utils__ import CUT_OFF_TIME, DemandType, KeyResults

__all__ = (
    "get_key_results",
    "plot_outputs",
)


# Colour map:
#   The preferred sns colourmap to use.
COLOUR_MAP = "Blues"

# Hours per year:
#   The number of hours in a year, used for reshaping arrays.
HOURS_PER_YEAR = 8760

# Plot resolution:
#   The resolution, in dpi, to use for plotting figures.
PLOT_RESOLUTION = 600


def get_key_results(
    grid_input_profile: pd.DataFrame,
    num_years: int,
    simulation_results: pd.DataFrame,
    total_solar_output: pd.DataFrame,
) -> KeyResults:
    """
    Computes the key results of the simulation.

        Inputs:
        - grid_input_profile:
            The relevant grid input profile for the simulation that was run.
        - num_years:
            The number of years for which the simulation was run.
        - simulation_results:
            The results of the simulation.
        - total_solar_output:
            The total solar power produced by the PV installation.

    Outputs:
        - key_results:
            The key results of the simulation, wrapped in a :class:`KeyResults`
            instance.

    """

    key_results = KeyResults()

    # Compute the solar-generation results.
    total_solar_generation: float = np.round(np.sum(total_solar_output))
    key_results.cumulative_pv_generation = float(total_solar_generation)
    key_results.average_pv_generation = float(
        round(total_solar_generation / (20 * 365))
    )

    # Compute the grid results.
    key_results.grid_daily_hours = np.sum(grid_input_profile, axis=0)

    # Compute the simulation related averages and sums.
    key_results.average_daily_diesel_energy_supplied = simulation_results[
        "Diesel energy (kWh)"
    ].sum() / (365 * num_years)

    key_results.average_daily_dumped_energy = simulation_results[
        "Dumped energy (kWh)"
    ].sum() / (365 * num_years)

    key_results.average_daily_energy_consumption = simulation_results[
        "Total energy used (kWh)"
    ].sum() / (365 * num_years)

    key_results.average_daily_grid_energy_supplied = simulation_results[
        "Grid energy (kWh)"
    ].sum() / (365 * num_years)

    key_results.average_daily_renewables_energy_supplied = simulation_results[
        "Renewables energy supplied (kWh)"
    ].sum() / (365 * num_years)

    key_results.average_daily_renewables_energy_used = simulation_results[
        "Renewables energy used (kWh)"
    ].sum() / (365 * num_years)

    key_results.average_daily_stored_energy_supplied = simulation_results[
        "Storage energy supplied (kWh)"
    ].sum() / (365 * num_years)

    key_results.average_daily_unmet_energy = simulation_results[
        "Unmet energy (kWh)"
    ].sum() / (365 * num_years)

    key_results.diesel_times = round(simulation_results["Diesel times"].mean(), 3)
    key_results.blackouts = round(simulation_results["Blackouts"].mean(), 3)

    return key_results


def plot_outputs(
    grid_input_profile: pd.DataFrame,
    grid_profile: pd.DataFrame,
    initial_clean_water_hourly_loads: Optional[Dict[str, pd.DataFrame]],
    initial_electric_hourly_loads: Dict[str, pd.DataFrame],
    num_years: int,
    output_directory: str,
    simulation_name: str,
    simulation_number: int,
    simulation_output: pd.DataFrame,
    total_clean_water_load: pd.DataFrame,
    total_electric_load: pd.DataFrame,
    total_solar_output: pd.DataFrame,
) -> None:
    """
    Plots all the outputs given below.

    NOTE: To add an output to be plotted, simply add to this function.

    Inputs:
        - grid_input_profile:
            The relevant grid input profile for the simulation that was run.
        - grid_profile:
            The relevant grid profile for the simulation that was run.
        - initial_clean_water_hourly_loads:
            The initial clean water hourly load for each device for the initial period
            of the simulation run.
        - initial_electric_hourly_loads:
            The hourly load profiles of each device for the initial period of the
            simulation run.
        - num_years:
            The number of years for which the simulation was run.
        - output_directory:
            The directory into which to save the output information.
        - simulation_name:
            The filename used when saving the simulation.
        - simulation_number:
            The number of the simulation being run.
        - simulation_output:
            The output of the simulation carried out.
        - total_clean_water_load:
            The total clean water load placed on the system.
        - total_electric_load:
            The total electric load placed on the system.
        - total_solar_output:
            The total solar power produced by the PV installation.

    """

    # Create an output directory for the various plots to be saved in.
    figures_directory = os.path.join(
        output_directory, simulation_name, f"simulation_{simulation_number}_plots"
    )
    os.makedirs(os.path.join(output_directory, simulation_name), exist_ok=True)
    os.makedirs(figures_directory, exist_ok=True)

    with tqdm(
        total=21 if initial_clean_water_hourly_loads is not None else 10,
        desc="plots",
        leave=False,
        unit="plot",
    ) as pbar:
        # Plot the first year of solar generation as a heatmap.
        rehaped_data = np.reshape(
            total_solar_output.iloc[0:HOURS_PER_YEAR].values, (365, 24)
        )
        heatmap = sns.heatmap(
            rehaped_data,
            vmin=0,
            vmax=1,
            cmap=COLOUR_MAP,
            cbar_kws={"label": "Power output / kW"},
        )
        heatmap.set(
            xticks=range(0, 24, 2),
            xticklabels=range(0, 24, 2),
            yticks=range(0, 365, 30),
            yticklabels=range(0, 365, 30),
            xlabel="Hour of day",
            ylabel="Day of year",
            title="Output per kWp of solar capacity",
        )
        plt.xticks(rotation=0)
        plt.tight_layout()
        plt.savefig(
            os.path.join(figures_directory, "solar_output_hetamap.png"),
            transparent=True,
        )
        plt.close()
        pbar.update(1)

        # Plot the yearly power generated by the solar system.
        solar_daily_sums = pd.DataFrame(np.sum(rehaped_data, axis=1))
        plt.plot(range(365), solar_daily_sums[0])
        plt.xticks(range(0, 365, 30))
        plt.yticks(range(0, 9, 2))
        plt.xlabel("Day of year")
        plt.ylabel("Energy generation / kWh per day")
        plt.title("Daily energy generation of 1 kWp of solar capacity")
        plt.savefig(
            os.path.join(figures_directory, "solar_output_yearly.png"), transparent=True
        )
        plt.close()
        pbar.update(1)

        # Plot the grid availablity profile.
        rehaped_data = np.reshape(grid_profile.iloc[0:HOURS_PER_YEAR].values, (365, 24))
        heatmap = sns.heatmap(rehaped_data, vmin=0, vmax=1, cmap="Greys_r", cbar=False)
        heatmap.set(
            xticks=range(0, 24, 2),
            xticklabels=range(0, 24, 2),
            yticks=range(0, 365, 30),
            yticklabels=range(0, 365, 30),
            xlabel="Hour of day",
            ylabel="Day of year",
            title="Grid availability of the selected profile.",
        )
        plt.xticks(rotation=0)
        plt.tight_layout()
        plt.savefig(
            os.path.join(figures_directory, "grid_availability_heatmap.png"),
            transparent=True,
        )
        plt.close()
        pbar.update(1)

        # Plot the input vs. randomised grid avialability profiles.
        plt.plot(range(24), grid_input_profile, color="k", label="Input")
        plt.plot(range(24), np.mean(rehaped_data, axis=0), color="r", label="Output")
        plt.legend()
        plt.xticks(range(0, 24, 2))
        plt.yticks(np.arange(0, 1.1, 0.2))
        plt.xlabel("Hour of day")
        plt.ylabel("Probability")
        plt.title("Probability of grid electricity being available")
        plt.savefig(
            os.path.join(
                figures_directory, "grid_availability_randomisation_comparison.png"
            ),
            transparent=True,
        )
        plt.close()
        pbar.update(1)

        # Plot the initial electric load of each device.
        for device, load in initial_electric_hourly_loads.items():
            plt.plot(range(CUT_OFF_TIME), load, label=device)
            plt.xticks(range(0, CUT_OFF_TIME - 1, min(6, CUT_OFF_TIME - 1)))
            plt.xlabel("Hour of simulation")
            plt.ylabel("Device load / W")
            plt.title("Electric load demand of each device")
            plt.tight_layout()
        plt.legend()
        plt.savefig(
            os.path.join(figures_directory, "electric_device_loads.png"),
            transparent=True,
        )
        plt.close()
        pbar.update(1)

        # Plot the electric load breakdown by load type.
        plt.plot(
            range(CUT_OFF_TIME),
            total_electric_load[0:CUT_OFF_TIME][DemandType.DOMESTIC.value],
            label=DemandType.DOMESTIC.value,
        )
        plt.plot(
            range(CUT_OFF_TIME),
            total_electric_load[0:CUT_OFF_TIME][DemandType.COMMERCIAL.value],
            label=DemandType.COMMERCIAL.value,
        )
        plt.plot(
            range(CUT_OFF_TIME),
            total_electric_load[0:CUT_OFF_TIME][DemandType.PUBLIC.value],
            label=DemandType.PUBLIC.value,
        )
        plt.plot(
            range(CUT_OFF_TIME),
            np.sum(total_electric_load[0:CUT_OFF_TIME], axis=1),
            "--",
            label="total",
        )
        plt.legend(loc="upper right")
        plt.xticks(list(range(0, CUT_OFF_TIME - 1, min(4, CUT_OFF_TIME - 1))))
        plt.xlabel("Hour of simulation")
        plt.ylabel("Electric power demand / kW")
        plt.title(f"Load profile of the community for the first {CUT_OFF_TIME} hours")
        plt.savefig(
            os.path.join(figures_directory, "electric_demands.png"),
            transparent=True,
        )
        plt.close()
        pbar.update(1)

        # Plot the annual variation of the electricity demand.
        _, axis = plt.subplots(1, 2, figsize=(8, 4))
        domestic_demand = np.sum(
            np.reshape(
                total_electric_load[0:HOURS_PER_YEAR][DemandType.DOMESTIC.value].values,
                (365, 24),
            ),
            axis=1,
        )
        commercial_demand = np.sum(
            np.reshape(
                total_electric_load[0:HOURS_PER_YEAR][
                    DemandType.COMMERCIAL.value
                ].values,
                (365, 24),
            ),
            axis=1,
        )
        public_demand = np.sum(
            np.reshape(
                total_electric_load[0:HOURS_PER_YEAR][DemandType.PUBLIC.value].values,
                (365, 24),
            ),
            axis=1,
        )
        total_demand = np.sum(
            np.reshape(
                np.sum(total_electric_load[0:HOURS_PER_YEAR].values, axis=1),
                (365, 24),
            ),
            axis=1,
        )
        axis[0].plot(
            range(365),
            pd.DataFrame(domestic_demand).rolling(5).mean(),
            label="Domestic",
            color="blue",
        )
        axis[0].plot(
            range(365),
            pd.DataFrame(commercial_demand).rolling(5).mean(),
            label="Commercial",
            color="orange",
        )
        axis[0].plot(
            range(365),
            pd.DataFrame(public_demand).rolling(5).mean(),
            label="Public",
            color="green",
        )
        axis[0].plot(range(365), domestic_demand, alpha=0.5, color="blue")
        axis[0].plot(range(365), commercial_demand, alpha=0.5, color="orange")
        axis[0].plot(range(365), public_demand, alpha=0.5, color="green")
        axis[0].legend(loc="best")
        axis[0].set(
            xticks=(range(0, 366, 60)),
            yticks=range(0, 26, 5),
            xlabel="Day of simulation period",
            ylabel="Load / kWh/day",
            title="Energy demand of each load type",
        )
        axis[1].plot(
            range(365),
            pd.DataFrame(total_demand).rolling(5).mean(),
            "--",
            label="Total",
            color="red",
        )
        axis[1].plot(range(365), total_demand, "--", alpha=0.5, color="red")
        axis[1].legend(loc="best")
        axis[1].set(
            xticks=(range(0, 366, 60)),
            yticks=range(15, 41, 5),
            xlabel="Day of simulation period",
            ylabel="Load / kWh/day",
            title="Total community energy demand",
        )
        plt.tight_layout()
        plt.savefig(
            os.path.join(figures_directory, "electric_demand_annual_variation.png"),
            transparent=True,
        )
        plt.close()
        pbar.update(1)

        # Plot the demand growth over the simulation period.
        domestic_demand = np.sum(
            np.reshape(
                0.001
                * total_electric_load[0 : num_years * HOURS_PER_YEAR][
                    DemandType.DOMESTIC.value
                ].values,
                (num_years, HOURS_PER_YEAR),
            ),
            axis=1,
        )
        commercial_demand = np.sum(
            np.reshape(
                0.001
                * total_electric_load[0 : num_years * HOURS_PER_YEAR][
                    DemandType.COMMERCIAL.value
                ].values,
                (num_years, HOURS_PER_YEAR),
            ),
            axis=1,
        )
        public_demand = np.sum(
            np.reshape(
                0.001
                * total_electric_load[0 : num_years * HOURS_PER_YEAR][
                    DemandType.PUBLIC.value
                ].values,
                (num_years, HOURS_PER_YEAR),
            ),
            axis=1,
        )
        total_demand = np.sum(
            0.001
            * np.reshape(
                np.sum(
                    total_electric_load[0 : num_years * HOURS_PER_YEAR].values, axis=1
                ),
                (num_years, HOURS_PER_YEAR),
            ),
            axis=1,
        )
        plt.plot(
            range(num_years),
            domestic_demand,
            label=DemandType.DOMESTIC.value,
            color="blue",
        )
        plt.plot(
            range(num_years),
            commercial_demand,
            label=DemandType.COMMERCIAL.value,
            color="orange",
        )
        plt.plot(
            range(num_years),
            public_demand,
            label=DemandType.PUBLIC.value,
            color="green",
        )
        plt.plot(range(num_years), total_demand, "--", label="total", color="red")
        plt.legend(loc="upper left")
        plt.xticks(range(0, num_years, 2 if num_years > 2 else 1))
        plt.xlabel("Year of investigation period")
        plt.ylabel("Energy demand / MWh/year")
        plt.title("Load growth of the community")
        plt.savefig(
            os.path.join(figures_directory, "electric_load_growth.png"),
            transparent=True,
        )
        plt.close()
        pbar.update(1)

        total_used = np.mean(
            np.reshape(
                simulation_output[0:HOURS_PER_YEAR]["Total energy used (kWh)"].values,
                (365, 24),
            ),
            axis=0,
        )
        diesel_energy = np.mean(
            np.reshape(
                simulation_output[0:HOURS_PER_YEAR]["Diesel energy (kWh)"].values,
                (365, 24),
            ),
            axis=0,
        )
        dumped = np.mean(
            np.reshape(
                simulation_output[0:HOURS_PER_YEAR]["Dumped energy (kWh)"].values,
                (365, 24),
            ),
            axis=0,
        )
        grid_energy = np.mean(
            np.reshape(
                simulation_output[0:HOURS_PER_YEAR]["Grid energy (kWh)"].values,
                (365, 24),
            ),
            axis=0,
        )
        renewable_energy = np.mean(
            np.reshape(
                simulation_output[0:HOURS_PER_YEAR][
                    "Renewables energy used (kWh)"
                ].values,
                (365, 24),
            ),
            axis=0,
        )
        renewables_supplied = np.mean(
            np.reshape(
                simulation_output[0:HOURS_PER_YEAR][
                    "Renewables energy supplied (kWh)"
                ].values,
                (365, 24),
            ),
            axis=0,
        )
        storage_energy = np.mean(
            np.reshape(
                simulation_output[0:HOURS_PER_YEAR][
                    "Storage energy supplied (kWh)"
                ].values,
                (365, 24),
            ),
            axis=0,
        )
        unmet_energy = np.mean(
            np.reshape(
                simulation_output[0:HOURS_PER_YEAR]["Unmet energy (kWh)"].values,
                (365, 24),
            ),
            axis=0,
        )

        plt.plot(total_used, "--", label="Total used")
        plt.plot(renewable_energy, label="Solar used directly")
        plt.plot(storage_energy, label="Storage")
        plt.plot(grid_energy, label="Grid")
        plt.plot(diesel_energy, label="Diesel")
        plt.plot(unmet_energy, label="Unmet")
        plt.plot(renewables_supplied, label="Solar generated")
        plt.plot(dumped, label="Dumped")
        plt.legend()
        plt.xlim(0, 23)
        plt.xticks(range(0, 24, 1))
        plt.xlabel("Hour of day")
        plt.ylabel("Average energy / kWh/hour")
        plt.title("Energy supply and demand on an average day")
        plt.savefig(
            os.path.join(figures_directory, "electricity_use_on_average_day.png"),
            transparent=True,
        )
        plt.close()
        pbar.update(1)

        blackouts = np.mean(
            np.reshape(
                simulation_output[0:HOURS_PER_YEAR]["Blackouts"].values,
                (365, 24),
            ),
            axis=0,
        )
        storage_energy = np.mean(
            np.reshape(
                simulation_output[0:HOURS_PER_YEAR][
                    "Storage energy supplied (kWh)"
                ].values
                > 0,
                (365, 24),
            ),
            axis=0,
        )
        solar_usage = np.mean(
            np.reshape(
                simulation_output[0:HOURS_PER_YEAR][
                    "Renewables energy used (kWh)"
                ].values,
                (365, 24),
            ),
            axis=0,
        )
        diesel_times = np.mean(
            np.reshape(
                simulation_output[0:HOURS_PER_YEAR]["Diesel times"].values,
                (365, 24),
            ),
            axis=0,
        )

        plt.plot(blackouts, label="Blackouts")
        plt.plot(solar_usage, label="Solar")
        plt.plot(storage_energy, label="Storage")
        plt.plot(grid_energy, label="Grid")
        plt.plot(diesel_times, label="Diesel")
        plt.legend()
        plt.xlim(0, 23)
        plt.xticks(range(0, 24, 1))
        plt.ylim(0, 1)
        plt.yticks(np.arange(0, 1.1, 0.25))
        plt.xlabel("Hour of day")
        plt.ylabel("Probability")
        plt.title("Energy availability on an average day")
        plt.savefig(
            os.path.join(
                figures_directory, "electricity_avilability_on_average_day.png"
            ),
            transparent=True,
        )
        plt.close()
        pbar.update(1)

        # Plot the seasonal variation in electricity supply sources.
        grid_energy = np.reshape(
            simulation_output[0:HOURS_PER_YEAR]["Grid energy (kWh)"].values,
            (365, 24),
        )
        storage_energy = np.reshape(
            simulation_output[0:HOURS_PER_YEAR]["Storage energy supplied (kWh)"].values,
            (365, 24),
        )
        renewable_energy = np.reshape(
            simulation_output[0:HOURS_PER_YEAR]["Renewables energy used (kWh)"].values,
            (365, 24),
        )
        diesel_energy = np.reshape(
            simulation_output[0:HOURS_PER_YEAR]["Diesel times"].values,
            (365, 24),
        )

        fig, ([ax1, ax2], [ax3, ax4]) = plt.subplots(2, 2)  # ,sharex=True, sharey=True)
        sns.heatmap(
            renewable_energy, vmin=0.0, vmax=4.0, cmap="Reds", cbar=True, ax=ax1
        )
        ax1.set(
            xticks=range(0, 25, 6),
            xticklabels=range(0, 25, 6),
            yticks=range(0, 365, 60),
            yticklabels=range(0, 365, 60),
            xlabel="Hour of day",
            ylabel="Day of year",
            title="Solar",
        )
        sns.heatmap(
            storage_energy, vmin=0.0, vmax=4.0, cmap="Greens", cbar=True, ax=ax2
        )
        ax2.set(
            xticks=range(0, 25, 6),
            xticklabels=range(0, 25, 6),
            yticks=range(0, 365, 60),
            yticklabels=range(0, 365, 60),
            xlabel="Hour of day",
            ylabel="Day of year",
            title="Storage",
        )
        sns.heatmap(grid_energy, vmin=0.0, vmax=4.0, cmap="Blues", cbar=True, ax=ax3)
        ax3.set(
            xticks=range(0, 25, 6),
            xticklabels=range(0, 25, 6),
            yticks=range(0, 365, 60),
            yticklabels=range(0, 365, 60),
            xlabel="Hour of day",
            ylabel="Day of year",
            title="Grid",
        )
        sns.heatmap(diesel_energy, vmin=0.0, vmax=4.0, cmap="Greys", cbar=True, ax=ax4)
        ax4.set(
            xticks=range(0, 25, 6),
            xticklabels=range(0, 25, 6),
            yticks=range(0, 365, 60),
            yticklabels=range(0, 365, 60),
            xlabel="Hour of day",
            ylabel="Day of year",
            title="Diesel",
        )
        plt.tight_layout()
        fig.suptitle("Electricity from different sources (kWh)")
        fig.subplots_adjust(top=0.87)
        plt.xticks(rotation=0)
        plt.savefig(
            os.path.join(
                figures_directory, "seasonal_electricity_supply_variations.png"
            ),
            transparent=True,
        )
        plt.close()
        pbar.update(1)

        total_used = simulation_output.iloc[0:24]["Total energy used (kWh)"]
        renewable_energy = simulation_output.iloc[0:24]["Renewables energy used (kWh)"]
        storage_energy = simulation_output.iloc[0:24]["Storage energy supplied (kWh)"]
        grid_energy = simulation_output.iloc[0:24]["Grid energy (kWh)"]
        diesel_energy = simulation_output.iloc[0:24]["Diesel energy (kWh)"]
        dumped_energy = simulation_output.iloc[0:24]["Dumped energy (kWh)"]
        unmet_energy = simulation_output.iloc[0:24]["Unmet energy (kWh)"]
        renewables_supplied = simulation_output.iloc[0:24][
            "Renewables energy supplied (kWh)"
        ]

        plt.plot(total_used, "--", label="Total used")
        plt.plot(renewable_energy, label="Solar used directly")
        plt.plot(storage_energy, label="Storage")
        plt.plot(grid_energy, label="Grid")
        plt.plot(diesel_energy, label="Diesel")
        plt.plot(dumped_energy, label="Dumped")
        plt.plot(unmet_energy, label="Unmet")
        plt.plot(renewables_supplied, label="Solar generated")
        plt.legend()
        plt.xlim(0, 23)
        plt.xticks(range(0, 24, 1))
        plt.xlabel("Hour of day")
        plt.ylabel("Average energy / kWh/hour")
        plt.title("Energy supply and demand on the frist day")
        plt.savefig(
            os.path.join(figures_directory, "electricity_use_on_first_day.png"),
            transparent=True,
        )
        plt.close()
        pbar.update(1)

        # Plot the initial clean-water load of each device.
        if initial_clean_water_hourly_loads is not None:
            for device, load in initial_clean_water_hourly_loads.items():
                plt.plot(range(CUT_OFF_TIME), load, label=device)
                # labels.append(device)
                plt.xticks(range(0, CUT_OFF_TIME - 1, min(6, CUT_OFF_TIME - 2)))
                plt.xlabel("Hour of simulation")
                plt.ylabel("Device load / litres/hour")
                plt.title("Clean water demand of each device")
                plt.tight_layout()
            plt.legend()
            plt.savefig(
                os.path.join(figures_directory, "clean_water_device_loads.png"),
                transparent=True,
            )
            plt.close()
            pbar.update(1)

            # Plot the electric load breakdown by load type.
            plt.plot(
                range(CUT_OFF_TIME),
                total_clean_water_load[0:CUT_OFF_TIME][DemandType.DOMESTIC.value],
                label=DemandType.DOMESTIC.value,
            )
            plt.plot(
                range(CUT_OFF_TIME),
                total_clean_water_load[0:CUT_OFF_TIME][DemandType.COMMERCIAL.value],
                label=DemandType.COMMERCIAL.value,
            )
            plt.plot(
                range(CUT_OFF_TIME),
                total_clean_water_load[0:CUT_OFF_TIME][DemandType.PUBLIC.value],
                label=DemandType.PUBLIC.value,
            )
            plt.plot(
                range(CUT_OFF_TIME),
                np.sum(total_clean_water_load[0:CUT_OFF_TIME], axis=1),
                "--",
                label="total",
            )
            plt.legend(loc="upper right")
            plt.xticks(list(range(0, CUT_OFF_TIME - 1, min(4, CUT_OFF_TIME - 2))))
            plt.xlabel("Hour of simulation")
            plt.ylabel("Clean water demand / litres/hour")
            plt.title(
                f"Clean-water load profile of the community for the first {CUT_OFF_TIME} hours"
            )
            plt.savefig(
                os.path.join(figures_directory, "clean_water_demands.png"),
                transparent=True,
            )
            plt.close()
            pbar.update(1)

            # Plot the annual variation of the electricity demand.
            _, axis = plt.subplots(1, 2, figsize=(8, 4))
            domestic_demand = np.sum(
                np.reshape(
                    total_clean_water_load[0:HOURS_PER_YEAR][
                        DemandType.DOMESTIC.value
                    ].values,
                    (365, 24),
                ),
                axis=1,
            )
            commercial_demand = np.sum(
                np.reshape(
                    total_clean_water_load[0:HOURS_PER_YEAR][
                        DemandType.COMMERCIAL.value
                    ].values,
                    (365, 24),
                ),
                axis=1,
            )
            public_demand = np.sum(
                np.reshape(
                    total_clean_water_load[0:HOURS_PER_YEAR][
                        DemandType.PUBLIC.value
                    ].values,
                    (365, 24),
                ),
                axis=1,
            )
            total_demand = np.sum(
                np.reshape(
                    np.sum(total_clean_water_load[0:HOURS_PER_YEAR].values, axis=1),
                    (365, 24),
                ),
                axis=1,
            )
            axis[0].plot(
                range(365),
                pd.DataFrame(domestic_demand).rolling(5).mean(),
                label="Domestic",
                color="blue",
            )
            axis[0].plot(
                range(365),
                pd.DataFrame(commercial_demand).rolling(5).mean(),
                label="Commercial",
                color="orange",
            )
            axis[0].plot(
                range(365),
                pd.DataFrame(public_demand).rolling(5).mean(),
                label="Public",
                color="green",
            )
            axis[0].plot(range(365), domestic_demand, alpha=0.5, color="blue")
            axis[0].plot(range(365), commercial_demand, alpha=0.5, color="orange")
            axis[0].plot(range(365), public_demand, alpha=0.5, color="green")
            axis[0].legend(loc="best")
            axis[0].set(
                xticks=(range(0, 366, 60)),
                xlabel="Day of simulation period",
                ylabel="Load / litres/hour",
                title="Clean-water demand of each load type",
            )
            axis[1].plot(
                range(365),
                pd.DataFrame(total_demand).rolling(5).mean(),
                "--",
                label="Total",
                color="red",
            )
            axis[1].plot(range(365), total_demand, "--", alpha=0.5, color="red")
            axis[1].legend(loc="best")
            axis[1].set(
                xticks=(range(0, 366, 60)),
                xlabel="Day of simulation period",
                ylabel="Load / litres/hour",
                title="Clean-water demand of each load type",
            )
            plt.tight_layout()
            plt.savefig(
                os.path.join(
                    figures_directory, "clean_water_demand_annual_variation.png"
                ),
                transparent=True,
            )
            plt.close()
            pbar.update(1)

            # Plot the clean-water demand load growth.
            # Plot the demand growth over the simulation period.
            domestic_demand = np.sum(
                np.reshape(
                    0.001
                    * total_clean_water_load[0 : num_years * HOURS_PER_YEAR][
                        DemandType.DOMESTIC.value
                    ].values,
                    (num_years, HOURS_PER_YEAR),
                ),
                axis=1,
            )
            commercial_demand = np.sum(
                np.reshape(
                    0.001
                    * total_clean_water_load[0 : num_years * HOURS_PER_YEAR][
                        DemandType.COMMERCIAL.value
                    ].values,
                    (num_years, HOURS_PER_YEAR),
                ),
                axis=1,
            )
            public_demand = np.sum(
                np.reshape(
                    0.001
                    * total_clean_water_load[0 : num_years * HOURS_PER_YEAR][
                        DemandType.PUBLIC.value
                    ].values,
                    (num_years, HOURS_PER_YEAR),
                ),
                axis=1,
            )
            total_demand = np.sum(
                np.reshape(
                    np.sum(
                        0.001
                        * total_clean_water_load[0 : num_years * HOURS_PER_YEAR].values,
                        axis=1,
                    ),
                    (num_years, HOURS_PER_YEAR),
                ),
                axis=1,
            )
            plt.plot(
                range(num_years),
                domestic_demand,
                label=DemandType.DOMESTIC.value,
                color="blue",
            )
            plt.plot(
                range(num_years),
                commercial_demand,
                label=DemandType.COMMERCIAL.value,
                color="orange",
            )
            plt.plot(
                range(num_years),
                public_demand,
                label=DemandType.PUBLIC.value,
                color="green",
            )
            plt.plot(range(num_years), total_demand, "--", label="total", color="red")
            plt.legend(loc="upper left")
            plt.xticks(range(0, num_years, 2 if num_years > 2 else 1))
            plt.xlabel("Year of investigation period")
            plt.ylabel("Clean-water demand / Cubic meters/year")
            plt.title("Load growth of the community")
            plt.savefig(
                os.path.join(figures_directory, "clean_water_load_growth.png"),
                transparent=True,
            )
            plt.close()
            pbar.update(1)

            total_supplied = np.mean(
                np.reshape(
                    simulation_output[0:HOURS_PER_YEAR][
                        "Total clean water supplied (l)"
                    ].values,
                    (365, 24),
                ),
                axis=0,
            )
            total_used = np.mean(
                np.reshape(
                    simulation_output[0:HOURS_PER_YEAR][
                        "Total clean water consumed (l)"
                    ].values,
                    (365, 24),
                ),
                axis=0,
            )
            backup_clean_water = np.mean(
                np.reshape(
                    simulation_output[0:HOURS_PER_YEAR][
                        "Clean water supplied via backup desalination (l)"
                    ].values,
                    (365, 24),
                ),
                axis=0,
            )
            excess_power_clean_water = np.mean(
                np.reshape(
                    simulation_output[0:HOURS_PER_YEAR][
                        "Clean water supplied using excess minigrid energy (l)"
                    ].values,
                    (365, 24),
                ),
                axis=0,
            )
            renewable_clean_water = np.mean(
                np.reshape(
                    simulation_output[0:HOURS_PER_YEAR][
                        "Renewable clean water used directly (l)"
                    ].values,
                    (365, 24),
                ),
                axis=0,
            )
            storage_clean_water = np.mean(
                np.reshape(
                    simulation_output[0:HOURS_PER_YEAR][
                        "Clean water supplied via tank storage (l)"
                    ].values,
                    (365, 24),
                ),
                axis=0,
            )
            tank_storage = np.mean(
                np.reshape(
                    simulation_output[0:HOURS_PER_YEAR][
                        "Water held in storage tanks (l)"
                    ].values,
                    (365, 24),
                ),
                axis=0,
            )
            total_clean_water_load = np.mean(
                np.reshape(
                    simulation_output[0:HOURS_PER_YEAR][
                        "Total clean water demand (l)"
                    ].values,
                    (365, 24),
                ),
                axis=0,
            )
            unmet_clean_water = np.mean(
                np.reshape(
                    simulation_output[0:HOURS_PER_YEAR][
                        "Unmet clean water demand (l)"
                    ].values,
                    (365, 24),
                ),
                axis=0,
            )

            plt.plot(total_used, "--", label="Total used", zorder=1)
            plt.plot(backup_clean_water, label="Backup desalination", zorder=2)
            plt.plot(
                excess_power_clean_water, label="Excess power desalination", zorder=3
            )
            plt.plot(renewable_clean_water, label="PV-D direct supply", zorder=4)
            plt.plot(storage_clean_water, label="Storage", zorder=5)
            plt.plot(tank_storage, "--", label="Water held in tanks", zorder=6)
            plt.plot(unmet_clean_water, label="Unmet", zorder=7)
            plt.plot(total_clean_water_load, "--", label="Total load", zorder=8)
            plt.plot(total_supplied, "--", label="Total supplied", zorder=9)
            plt.legend()
            plt.xlim(0, 23)
            plt.xticks(range(0, 24, 1))
            plt.xlabel("Hour of day")
            plt.ylabel("Clean-water usage / litres/hour")
            plt.title("Water supply and demand on an average day")
            plt.savefig(
                os.path.join(figures_directory, "clean_water_use_on_average_day.png"),
                transparent=True,
            )
            plt.close()
            pbar.update(1)

            backup = simulation_output.iloc[0:24][
                "Clean water supplied via backup desalination (l)"
            ]
            excess = simulation_output.iloc[0:24][
                "Clean water supplied using excess minigrid energy (l)"
            ]
            renewable = simulation_output.iloc[0:24][
                "Renewable clean water used directly (l)"
            ]
            storage = simulation_output.iloc[0:24][
                "Clean water supplied via tank storage (l)"
            ]
            tank_storage = simulation_output.iloc[0:24][
                "Water held in storage tanks (l)"
            ]
            total_load = simulation_output.iloc[0:24]["Total clean water demand (l)"]
            total_used = simulation_output.iloc[0:24]["Total clean water supplied (l)"]
            unmet_clean_water = simulation_output.iloc[0:24][
                "Unmet clean water demand (l)"
            ]

            plt.plot(total_used, "--", label="Total used", zorder=1)
            plt.plot(backup, label="Backup desalination", zorder=2)
            plt.plot(excess, label="Excess minigrid power", zorder=3)
            plt.plot(renewable, label="PV-D output", zorder=4)
            plt.plot(storage, label="Storage", zorder=5)
            plt.plot(tank_storage, "--", label="Water held in tanks", zorder=6)
            plt.plot(unmet_clean_water, label="Unmet", zorder=7)
            plt.plot(total_load, "--", label="Total load", zorder=8)
            plt.legend()
            plt.xlim(0, 23)
            plt.xticks(range(0, 24, 1))
            plt.xlabel("Hour of day")
            plt.ylabel("Clean-water usage / litres/hour")
            plt.title("Water supply and demand on the first day")
            plt.savefig(
                os.path.join(figures_directory, "clean_water_use_on_first_day.png"),
                transparent=True,
            )
            plt.close()
            pbar.update(1)

            backup = simulation_output.iloc[0:48][
                "Clean water supplied via backup desalination (l)"
            ]
            excess = simulation_output.iloc[0:48][
                "Clean water supplied using excess minigrid energy (l)"
            ]
            renewable = simulation_output.iloc[0:48][
                "Renewable clean water used directly (l)"
            ]
            storage = simulation_output.iloc[0:48][
                "Clean water supplied via tank storage (l)"
            ]
            tank_storage = simulation_output.iloc[0:48][
                "Water held in storage tanks (l)"
            ]
            total_load = simulation_output.iloc[0:48]["Total clean water demand (l)"]
            total_used = simulation_output.iloc[0:48]["Total clean water supplied (l)"]
            unmet_clean_water = simulation_output.iloc[0:48][
                "Unmet clean water demand (l)"
            ]

            plt.plot(total_used, "--", label="Total used", zorder=1)
            plt.plot(backup, label="Backup desalination", zorder=2)
            plt.plot(excess, label="Excess minigrid power", zorder=3)
            plt.plot(renewable, label="PV-D output", zorder=4)
            plt.plot(storage, label="Storage", zorder=5)
            plt.plot(tank_storage, "--", label="Water held in tanks", zorder=6)
            plt.plot(unmet_clean_water, label="Unmet", zorder=7)
            plt.plot(total_load, "--", label="Total load", zorder=8)
            plt.legend()
            plt.xlim(0, 47)
            plt.xticks(range(0, 48, 1))
            plt.xlabel("Hour of day")
            plt.ylabel("Clean-water usage / litres/hour")
            plt.title("Water supply and demand in the first 48 hours")
            plt.savefig(
                os.path.join(
                    figures_directory, "clean_water_use_in_first_48_hours.png"
                ),
                transparent=True,
            )
            plt.close()
            pbar.update(1)

            # blackouts = np.mean(
            #     np.reshape(
            #         simulation_output[0:HOURS_PER_YEAR][
            #             "Water supply blackouts"
            #         ].values,
            #         (365, 24),
            #     ),
            #     axis=0,
            # )
            # direct_electric_supply = np.mean(
            #     np.reshape(
            #         simulation_output[0:HOURS_PER_YEAR][
            #             "Water supplied by direct electricity (l)"
            #         ].values
            #         > 0,
            #         (365, 24),
            #     ),
            #     axis=0,
            # )

            # plt.plot(blackouts, label="Blackouts")
            # plt.plot(direct_electric_supply, label="Direct electric")
            # plt.legend()
            # plt.xlim(0, 23)
            # plt.xticks(range(0, 24, 1))
            # plt.ylim(0, 1)
            # plt.yticks(np.arange(0, 1.1, 0.25))
            # plt.xlabel("Hour of day")
            # plt.ylabel("Probability")
            # plt.title("Clean-water availability on an average day")
            # plt.savefig(
            #     os.path.join(
            #         figures_directory, "clean_water_avilability_on_average_day.png"
            #     ),
            #     transparent=True,
            # )
            # plt.close()
            # pbar.update(1)

            clean_water_power_supplied = np.mean(
                np.reshape(
                    simulation_output[0:HOURS_PER_YEAR][
                        "Power consumed providing clean water (kWh)"
                    ].values,
                    (365, 24),
                ),
                axis=0,
            )
            dumped_power = np.mean(
                np.reshape(
                    simulation_output[0:HOURS_PER_YEAR]["Dumped energy (kWh)"].values,
                    (365, 24),
                ),
                axis=0,
            )
            electric_power_supplied = np.mean(
                np.reshape(
                    simulation_output[0:HOURS_PER_YEAR][
                        "Power consumed providing electricity (kWh)"
                    ].values,
                    (365, 24),
                ),
                axis=0,
            )
            surplus_power_consumed = np.mean(
                np.reshape(
                    simulation_output[0:HOURS_PER_YEAR][
                        "Excess power consumed desalinating clean water (kWh)"
                    ].values,
                    (365, 24),
                ),
                axis=0,
            )
            total_power_supplied = np.mean(
                np.reshape(
                    simulation_output[0:HOURS_PER_YEAR][
                        "Total energy used (kWh)"
                    ].values,
                    (365, 24),
                ),
                axis=0,
            )

            plt.plot(clean_water_power_supplied, label="Clean-water via conversion")
            plt.plot(dumped_power, label="Unused dumped energy")
            plt.plot(electric_power_supplied, label="Electric devices")
            plt.plot(
                surplus_power_consumed,
                label="Clean water via dumped energy",
            )
            plt.plot(total_power_supplied, "--", label="Total load")
            plt.legend()
            plt.xlim(0, 23)
            plt.xticks(range(0, 24, 1))
            plt.xlabel("Hour of day")
            plt.ylabel("Use by device type.")
            plt.title("Electriciy use by supply/device type on an average day")
            plt.savefig(
                os.path.join(figures_directory, "electricity_use_by_supply_type.png"),
                transparent=True,
            )
            plt.close()
            pbar.update(1)

            # Plot the seasonal variation in clean-water supply sources.
            backup_water = np.reshape(
                simulation_output[0:HOURS_PER_YEAR][
                    "Clean water supplied via backup desalination (l)"
                ].values
                / 1000,
                (365, 24),
            )
            excess_pv_water = np.reshape(
                simulation_output[0:HOURS_PER_YEAR][
                    "Clean water supplied using excess minigrid energy (l)"
                ].values
                / 1000,
                (365, 24),
            )
            storage_water = np.reshape(
                simulation_output[0:HOURS_PER_YEAR][
                    "Clean water supplied via tank storage (l)"
                ].values
                / 1000,
                (365, 24),
            )
            renewable_energy = np.reshape(
                simulation_output[0:HOURS_PER_YEAR][
                    "Renewable clean water used directly (l)"
                ].values
                / 1000,
                (365, 24),
            )
            unmet_water = np.reshape(
                simulation_output[0:HOURS_PER_YEAR][
                    "Unmet clean water demand (l)"
                ].values
                / 1000,
                (365, 24),
            )

            fig, ([ax1, ax2, unused_ax], [ax3, ax4, ax5]) = plt.subplots(
                2, 3
            )  # ,sharex=True, sharey=True)
            unused_ax.set_visible(False)
            sns.heatmap(
                excess_pv_water,
                vmin=0.0,
                vmax=excess_pv_water.max(),
                cmap="Reds",
                cbar=True,
                ax=ax1,
            )
            ax1.set(
                xticks=range(0, 25, 6),
                xticklabels=range(0, 25, 6),
                yticks=range(0, 365, 60),
                yticklabels=range(0, 365, 60),
                xlabel="Hour of day",
                ylabel="Day of year",
                title="Excess PV",
            )
            sns.heatmap(
                storage_water,
                vmin=0.0,
                vmax=storage_water.max(),
                cmap="Greens",
                cbar=True,
                ax=ax2,
            )
            ax2.set(
                xticks=range(0, 25, 6),
                xticklabels=range(0, 25, 6),
                yticks=range(0, 365, 60),
                yticklabels=range(0, 365, 60),
                xlabel="Hour of day",
                ylabel="Day of year",
                title="Storage",
            )
            sns.heatmap(
                renewable_energy,
                vmin=0.0,
                vmax=renewable_energy.max(),
                cmap="Blues",
                cbar=True,
                ax=ax3,
            )
            ax3.set(
                xticks=range(0, 25, 6),
                xticklabels=range(0, 25, 6),
                yticks=range(0, 365, 60),
                yticklabels=range(0, 365, 60),
                xlabel="Hour of day",
                ylabel="Day of year",
                title="PV-D/T",
            )
            sns.heatmap(
                backup_water,
                vmin=0.0,
                vmax=backup_water.max(),
                cmap="Oranges",
                cbar=True,
                ax=ax4,
            )
            ax4.set(
                xticks=range(0, 25, 6),
                xticklabels=range(0, 25, 6),
                yticks=range(0, 365, 60),
                yticklabels=range(0, 365, 60),
                xlabel="Hour of day",
                ylabel="Day of year",
                title="Backup",
            )
            sns.heatmap(
                unmet_water,
                vmin=0.0,
                vmax=unmet_water.max(),
                cmap="Greys",
                cbar=True,
                ax=ax5,
            )
            ax5.set(
                xticks=range(0, 25, 6),
                xticklabels=range(0, 25, 6),
                yticks=range(0, 365, 60),
                yticklabels=range(0, 365, 60),
                xlabel="Hour of day",
                ylabel="Day of year",
                title="Unmet",
            )

            # Adjust the positioning of the plots
            # ax4.set_position([0.24, 0.125, 0.228, 0.343])
            # ax5.set_position([0.55, 0.125, 0.228, 0.343])

            plt.tight_layout()
            fig.suptitle("Water from different sources (tonnes)")
            fig.subplots_adjust(top=0.87)
            plt.xticks(rotation=0)
            plt.savefig(
                os.path.join(figures_directory, "seasonal_water_supply_variations.png"),
                transparent=True,
            )
            plt.close()
            pbar.update(1)
