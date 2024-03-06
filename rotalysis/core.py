# core.py in rotalysis folder
import time
import traceback

from rotalysis import CustomException, Pump, RotalysisInput
from rotalysis import UtilityFunction as UF
from utils import streamlit_logger


class Core:
    def __init__(self, input: RotalysisInput, window):
        self.input = input
        self.config_path = input.CONFIG_FILE
        self.task_path = input.TASKLIST_FILE
        self.input_path = input.INPUT_FOLDER
        self.output_path = input.OUTPUT_FOLDER
        self.dftask_list = UF.load_task_list(task_path=self.task_path)
        self.logger = streamlit_logger
        self.success_count = 0
        self.window = window

    def update_tasklist(self, pump: Pump, idx):
        task = self.dftask_list.loc[idx]
        if self.success:
            task.update(
                {
                    "Perform": "N",
                    "Result": "Success",
                    "IT_energy": pump.dfSummary["Impeller"]["Annual Energy Saving"],
                    "IT_ghg_cost": pump.dfEconomics["Impeller"]["GHG Reduction Cost"],
                    "IT_ghg_reduction": pump.dfSummary["Impeller"]["Ghg Reduction"],
                    "IT_ghg_reduction_percent": pump.dfSummary["Impeller"][
                        "Ghg Reduction Percent"
                    ],
                    "VSD_energy": pump.dfSummary["Vsd"]["Annual Energy Saving"],
                    "VSD_ghg_reduction": pump.dfSummary["Vsd"]["Ghg Reduction"],
                    "VSD_ghg_reduction_percent": pump.dfSummary["Vsd"][
                        "Ghg Reduction Percent"
                    ],
                    "VSD_ghg_cost": pump.dfEconomics["VSD"]["GHG Reduction Cost"],
                }
            )

        else:
            self.dftask_list.loc[idx, ["Perform", "Result"]] = ["Y", "Failed"]

    def process_task(self):
        task_list = self.dftask_list.loc[self.dftask_list["Perform"] == "Y"]
        total_tasks = len(task_list)

        self.logger.info(f"\n{'*' * 30}Welcome to Rotalysis{'*' * 30}\n")
        self.logger.info(f"Total tasks to be processed: {total_tasks} \n")

        for i, (idx, row) in enumerate(task_list.iterrows()):
            self.success = False
            self.logger.info(f"Processing task {i+1} of {total_tasks}")
            try:
                site, tag = row["Site"], row["Tag"]
                self.logger.info(f"Searching Excel file for : {site}, {tag}")

                excel_path = UF.get_excel_path(self.input_path, site, tag)
                self.logger.info(f"Found excel path for processing:{excel_path}")

                pump = Pump(config_path=self.config_path, data_path=excel_path)

                pump.process_pump(output_folder=self.output_path, tag=tag, site=site)
                self.success = True
                self.success_count += 1

            except (CustomException, Exception) as e:
                self.logger.error(e)
                print(traceback.format_exc())

            time.sleep(0.1)

            progress = int((i + 1) / total_tasks)
            if self.window:
                self.window.progress(
                    progress, text=f"Processing {i+1} of {total_tasks} tasks"
                )
                (
                    self.logger.info("TASK COMPLETED!")
                    if self.success
                    else self.logger.critical("TASK FAILED!")
                )
                self.update_tasklist(pump, idx) #type: ignore

                self.logger.info("\n" + 50 * "-" + "\n")

        self.logger.info("Please check the output folder for the result.")
        self.logger.info(
            f"Total tasks processed: {self.success_count} out of {total_tasks}"
        )
        UF.write_to_excel(self.task_path, self.dftask_list)
        self.logger.info(f"\n{'*' * 30}Thanks for using Rotalysis{'*' * 30}\n")
