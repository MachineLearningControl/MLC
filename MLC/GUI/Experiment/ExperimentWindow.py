# -*- coding: utf-8 -*-

import os
import numpy as np
import sys
import time
sys.path.append(os.path.abspath(".") + "/../..")

from MLC.Log.log import get_gui_logger
from MLC.GUI.Autogenerated.autogenerated import Ui_ExperimentWindow
from MLC.GUI.Experiment.ArduinoConfigManager.BoardConfigurationWindow import BoardConfigurationWindow
from MLC.GUI.Experiment.ChartConfiguration import ChartConfiguration
from MLC.GUI.Experiment.MatplotlibCanvas.CostPerIndividualCanvas import CostPerIndividualCanvas
from MLC.GUI.Experiment.QtCharts.QtChartWrapper import QtChartWrapper
from MLC.GUI.Experiment.ExperimentInProgress import ExperimentInProgress
from MLC.GUI.Experiment.GenealogyWindow import GenealogyWindow
from MLC.GUI.Tables.ConfigDictTableModel import ConfigDictTableModel
from MLC.GUI.Tables.ConfigTableModel import ConfigTableModel
from MLC.individual.Individual import Individual
from MLC.mlc_parameters.mlc_parameters import Config
from MLC.Population.Evaluation.EvaluatorFactory import EvaluatorFactory
from MLC.Population.Population import Population
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QInputDialog
from MLC.GUI.Experiment.ArduinoConfigManager.ArduinoBoardManager import ArduinoBoardManager
Config

from MLC.arduino.protocol import ProtocolConfig
from MLC.arduino.connection.serialconnection import SerialConnectionConfig, SerialConnection
from MLC.arduino.connection.base import BaseConnection

logger = get_gui_logger()


class ExperimentWindow(QMainWindow):
    experiment_finished = pyqtSignal([bool])

    MAX_GENERATIONS = 30

    def __init__(self, mlc_local,
                 experiment_name,
                 experiment_closed_signal,
                 parent=None):
        QMainWindow.__init__(self, parent)
        self._autogenerated_object = Ui_ExperimentWindow()
        self._autogenerated_object.setupUi(self)

        # Experiment tab parameters
        self._current_gen = 0

        # Open the experiment
        self._mlc_local = mlc_local
        self._experiment_name = experiment_name
        self.setWindowTitle("Experiment {0}".format(self._experiment_name))

        self._mlc_local.open_experiment(self._experiment_name)
        self._load_experiment_config()
        self._update_individuals_per_generation_list()
        self._update_experiment_info()
        self._update_individuals_figure()

        # Disable save_config_button until some change is made
        self._autogenerated_object.save_config_button.setDisabled(True)

        # Connect the function that updates the graphics of the Window when the
        # experiment evaluation finished
        self.experiment_finished.connect(self._update_experiment)

        # Store the experiment in progress to close it at the end of the evaluation
        self._progress_dialog = None

        # Signal to be emitted when the experiment is closed
        self._experiment_closed_signal = experiment_closed_signal

        # Experiment in progress chart configuration
        self._chart_conf = ChartConfiguration(self._autogenerated_object)
        self._chart_conf.init()

        # Arduino board configurations
        # FIXME Board configuration must come from the experiment DB
        self._board_config = ProtocolConfig(None)
        self._serial_conn = SerialConnectionConfig('/dev/ttyACM0')

    def closeEvent(self, event):
        logger.debug('[EXPERIMENT {0}] [CLOSE_DIALOG] - Executing overriden closeEvent function'.format(self._experiment_name))
        self._ask_if_experiment_config_must_be_saved()
        # Close the experiment
        self._mlc_local.close_experiment(self._experiment_name)
        self._experiment_closed_signal.emit(self._experiment_name)

    def on_start_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] [START_BUTTON] - Executing on_start_button_clicked function'.format(self._experiment_name))
        from_gen = int(self._autogenerated_object.from_gen_combo.currentText())
        to_gen = int(self._autogenerated_object.to_gen_combo.currentText())

        logger.info('[EXPERIMENT {0}] [START_BUTTON] - Proceed to execute experiment from Generation '
                    'N°{1} to Generation N°{2}'.format(self._experiment_name, from_gen, to_gen))

        progress_dialog = ExperimentInProgress(mlc_local=self._mlc_local,
                                               experiment_name=self._experiment_name,
                                               to_gen=to_gen,
                                               from_gen=from_gen,
                                               chart_params=self._chart_conf.chart_params(),
                                               parent_signal=self.experiment_finished)

        progress_dialog.start()
        self._progress_dialog = progress_dialog

    def on_prev_gen_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] [PREV_GEN_BUTTON] - Executing on_prev_gen_button_clicked function'.format(self._experiment_name))
        experiment_info = self._mlc_local.get_experiment_info(self._experiment_name)
        number_of_gens = experiment_info["generations"]

        if self._current_gen > 1:
            self._current_gen -= 1
            self._update_experiment_info()
            self._update_individuals_figure()

    def on_next_gen_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] [NEXT_GEN_BUTTON] - Executing on_next_gen_button_clicked function'.format(self._experiment_name))
        experiment_info = self._mlc_local.get_experiment_info(self._experiment_name)
        number_of_gens = experiment_info["generations"]

        if self._current_gen < number_of_gens:
            self._current_gen += 1
            self._update_experiment_info()
            self._update_individuals_figure()

    def on_test_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] [TEST_BUTTON] - Executing on_test_button_clicked function'
                     .format(self._experiment_name))

        test_indiv_edit = self._autogenerated_object.test_indiv_edit
        if test_indiv_edit.text() == "":
            logger.warn('[EXPERIMENT {0}] [TEST_BUTTON] - The individual value cannot be an empty string'
                        .format(self._experiment_name))
            QMessageBox.information(self, "Test Individual",
                                    "The individual value cannot be an empty string.", QMessageBox.Ok)
            return

        # Calculate individual cost
        try:

            individual = Individual.generate(config=Config.get_instance(),
                                             rhs_value=test_indiv_edit.text())
            callback = EvaluatorFactory.get_callback()
            cost = callback.cost(individual)
            test_label_result = self._autogenerated_object.test_label_result
            test_label_result.setText(str(cost))
        except Exception, err:
            logger.error('[EXPERIMENT {0}] [TEST_BUTTON] - Error while evaluation individual. '
                         'Check the expression to be correct. Error {1}'
                         .format(self._experiment_name, err))
            QMessageBox.critical(self, "Test Individual",
                                 "Error while evaluation individual. Check the expression to be correct",
                                 QMessageBox.Ok)

    def on_log_check_clicked(self):
        logger.debug('[EXPERIMENT {0}] [LOG_CHECK_CLICKED] - Executing on_log_check_clicked function'
                     .format(self._experiment_name))
        self._update_individuals_figure()

    def on_show_all_check_clicked(self):
        logger.debug('[EXPERIMENT {0}] [SHOW_ALL_CHECK_CLICKED] - Executing on_show_all_check_clicked function'
                     .format(self._experiment_name))
        self._update_individuals_figure()

    def on_dimension_check_clicked(self):
        logger.debug('[EXPERIMENT {0}] [DIMENSION_CHECK_CLICKED] - Executing on_dimension_check_clicked function'
                     .format(self._experiment_name))
        # TODO: Don't know what the 3D graphic option should do yet...

    def on_save_config_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] [SAVE_CONFIG_BUTTON_CLICKED] - Executing on_save_config_button_clicked function'
                     .format(self._experiment_name))
        self._persist_experiment_config()

    def on_tab_changed(self, tab_index):
        logger.debug('[EXPERIMENT {0}] [TAB_CHANGED] - Executing on_tab_changed function'
                     .format(self._experiment_name))
        self._ask_if_experiment_config_must_be_saved()

    def on_import_config_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] [IMPORT_CONFIG_BUTTON_CLICKED] - Executing on_import_config_button_clicked function'
                     .format(self._experiment_name))

    def on_export_config_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] [EXPORT_CONFIG_BUTTON_CLICKED] - Executing on_export_config_button_clicked function'
                     .format(self._experiment_name))

    def on_ev_edit_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] [EV_EDIT_BUTTON_CLICKED] - Executing on_ev_edit_button_clicked function'
                     .format(self._experiment_name))

        ev_function = self._experiment_config["EVALUATOR"]["evaluation_function"] + ".py"
        ev_path_list = [self._mlc_local.get_working_dir(), self._experiment_name, "Evaluation", ev_function]
        # Use the splat operator to dearrange the list
        ev_path = os.path.join(*ev_path_list)

        if os.path.isfile(ev_path):
            logger.debug('[EXPERIMENT {0}] [EV_EDIT_BUTTON_CLICKED] - Proceed to open file: {0}'
                         .format(ev_path))
            # Check if file exists
            QDesktopServices.openUrl(QUrl(ev_path))
        else:
            QMessageBox.critical(self, "Edit Evaluation Script",
                                 "Evaluation file doesn't exists. Check that file {0} exists"
                                 .format(ev_path, ev_path),
                                 QMessageBox.Ok)

    def on_preev_edit_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] [PREEV_EDIT_BUTTON_CLICKED] - Executing on_preev_edit_button_clicked function'
                     .format(self._experiment_name))

        preev_activated = self._experiment_config["EVALUATOR"]["preevaluation"]
        if preev_activated.lower() != "true" and preev_activated != "1":
            QMessageBox.information(self, "Edit Preevaluation Script", "Preevaluation is not activated. "
                                    "Activate it in order to edit the preevaluation function",
                                    QMessageBox.Ok)
            return

        preev_function = self._experiment_config["EVALUATOR"]["preev_function"] + ".py"
        preev_path_list = [self._mlc_local.get_working_dir(), self._experiment_name, "Preevaluation", preev_function]
        # Use the splat operator to dearrange the list
        preev_path = os.path.join(*preev_path_list)

        if os.path.isfile(preev_path):
            logger.debug('[EXPERIMENT {0}] [PREEV_EDIT_BUTTON_CLICKED] - Proceed to open file: {0}'
                         .format(preev_path))
            # Check if file exists
            QDesktopServices.openUrl(QUrl(preev_path))
        else:
            QMessageBox.critical(self, "Edit Preevaluation Script",
                                 "Preevaluation file doesn't exists. Check that file {0} exists"
                                 .format(preev_path),
                                 QMessageBox.Ok)

    def on_gen_count_combo_changed(self, generation):
        logger.debug('[EXPERIMENT {0}] [GEN_COUNT_COMBO_CHANGED] - Executing on_gen_count_combo_changed function'
                     .format(self._experiment_name))
        if self._current_gen == int(generation):
            return

        self._current_gen = int(generation)
        self._update_experiment_info()
        self._update_individuals_figure()

    def on_chart_config_changed(self, value_changed):
        logger.debug('[EXPERIMENT {0}] [CHART_CONFIG_CHANGED] - Executing on_chart_config_changed function'
                     .format(self._experiment_name))
        self._chart_conf.update_chart()

    def on_best_indiv_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] [BEST_INDIV_BUTTON] - Executing on_best_indiv_button_clicked function')
        self._mlc_local.show_best(self._experiment_name, self._current_gen)

    def on_convergence_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] [CONVERGENCE_BUTTON] - Executing on_convergence_button_clicked function')

    def on_genealogy_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] [GENEALOGY_BUTTON] - Executing on_genealogy_button_clicked function')

        # Ask the user which Individual he would like to have displayed
        indivs_per_gen = Config.get_instance().getint("POPULATION", "size")
        individuals_list = [str(x) for x in xrange(1, indivs_per_gen + 1)]

        indiv = QInputDialog.getItem(self, "Individual Genealogy",
                                     "Select the individual you would like to display",
                                     individuals_list, 0, False)

        if indiv[1] == True:
            dialog = GenealogyWindow(parent=self,
                                     mlc_local=self._mlc_local,
                                     generation=self._current_gen,
                                     individual=int(indiv[0]),
                                     experiment_name=self._experiment_name)
            dialog.show()

    def on_board_config_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] [BOARD_CONFIG_BUTTON] - Executing on_board_config_button_clicked function')
        #FIXME Connection config name should not be related with "serial" 
        valid_connection = False
        board_config_window = ArduinoBoardManager(protocol_config=self._board_config, serial_config=self._serial_conn, 
                                                  close_handler=self.on_board_config_button_clicked, parent_win=self)
        board_config_window.start()

    def _config_table_edited(self, left, right):
        config_table = self._autogenerated_object.config_table
        table_model = config_table.model()

        # Get section, parameter and value of the parameter modified
        parameter = table_model.get_data(left.row(), 0)
        section = table_model.get_data(left.row(), 1)
        value = table_model.get_data(left.row(), 2)

        # Modify the experiment config in memory, not the one in the project
        self._experiment_config[section][parameter] = value
        logger.debug('[EXPERIMENT {0}] [CONFIG TABLE] - Parameter ({1}, {2}) edited. New Value: {3}'
                     .format(self._experiment_name, section, parameter, value))
        self._autogenerated_object.save_config_button.setDisabled(False)

    def _get_db_view_stored_value(self, model_index, table_model, indiv_id):
        indiv_data = self._mlc_local.get_individual(self._experiment_name, indiv_id)
        old_value = None

        if model_index.column() == 4:
            # Cost modified
            old_value = indiv_data.get_cost_history()[self._current_gen][0][0]
        elif model_index.column() == 5:
            # Value modified
            old_value = indiv_data.get_value()
        return old_value

    def _db_view_edited(self, left, right):
        db_view = self._autogenerated_object.db_view
        table_model = db_view.model()

        response = QMessageBox.information(self, "Editing Experiment DB",
                                           "Do you really want to change value?",
                                           QMessageBox.No | QMessageBox.Yes,
                                           QMessageBox.No)

        indiv_id = int(table_model.get_data(left.row(), 1))
        if response == QMessageBox.No:
            # Get the value stored in the database
            old_value = self._get_db_view_stored_value(model_index=left,
                                                       table_model=table_model,
                                                       indiv_id=indiv_id)
            logger.info('[EXPERIMENT {0}] [DB_VIEW_EDITED] - '
                        'Edition was canceled. Cell({1}, {2}) - Old value: {3}'
                        .format(self._experiment_name, left.row(),
                                left.column(), old_value))
            table_model.set_data(left.row(), left.column(), str(old_value))
        else:
            value = table_model.get_data(left.row(), left.column())

            if left.column() == 4:
                try:
                    float(value)
                except ValueError:
                    logger.info("[EXPERIMENT {0}] [DB_VIEW_EDITED] - "
                                "Cost inserted is not valid. Individual won't be updated)")
                    QMessageBox.critical(self, "Invalid cost",
                                         "Cost inserted is not valid. Individual won't be updated ")
                    old_value = self._get_db_view_stored_value(model_index=left,
                                                               table_model=table_model,
                                                               indiv_id=indiv_id)
                    table_model.set_data(left.row(), left.column(), str(old_value))
                    return

                logger.info('[EXPERIMENT {0}] [DB_VIEW_EDITED] - '
                            'Updating database. Cell ({1}, {2}) - Value: {3}'
                            .format(self._experiment_name, left.row(),
                                    left.column(), value))
                self._mlc_local.update_individual_cost(experiment_name=self._experiment_name,
                                                       indiv_id=indiv_id,
                                                       new_cost=float(value),
                                                       new_ev_time=time.time(),
                                                       generation=self._current_gen)
                self._update_individuals_figure()
                QMessageBox.information(self, "Experiment updated",
                                        "Individual was succesfully updated")
            elif left.column() == 5:
                # TODO
                pass

    def _update_individuals_per_generation_list(self):
        # Clean up ye olde list
        self._individuals_per_generation = []

        experiment_info = self._mlc_local.get_experiment_info(self._experiment_name)
        number_of_gens = experiment_info["generations"]
        indivs_per_gen = experiment_info["individuals_per_generation"]

        if number_of_gens == 0:
            # Disable Experiment tab buttons
            self._autogenerated_object.left_menu_frame.setDisabled(True)
            self._autogenerated_object.right_menu_frame.setDisabled(True)
            return
        else:
            self._autogenerated_object.left_menu_frame.setDisabled(False)
            self._autogenerated_object.right_menu_frame.setDisabled(False)

        # Complete the list
        individuals = self._mlc_local.get_individuals(self._experiment_name)
        for index in xrange(1, number_of_gens + 1):
            gens_list = []

            generation = self._mlc_local.get_generation(self._experiment_name, index)
            pop_individuals = generation.get_individuals()
            costs = generation.get_costs()
            gen_methods = generation.get_gen_methods()

            for pop_index in xrange(1, indivs_per_gen + 1):
                indiv_index = pop_individuals[pop_index - 1]
                indiv_cost = str(costs[pop_index - 1])
                indiv_value = individuals[indiv_index].get_value()
                indiv_appearences = individuals[indiv_index].get_appearances()

                indiv_gen_method = Population.gen_method_description(gen_methods[pop_index - 1])
                gens_list.append([pop_index, indiv_index, indiv_gen_method,
                                  indiv_appearences, indiv_cost, indiv_value])

            self._individuals_per_generation.append(gens_list)

    def _load_experiment_config(self):
        header = ['Parameter', 'Section', 'Value']
        editable_columns = [2]

        self._experiment_config = self._mlc_local.get_experiment_configuration(self._experiment_name)
        table_model = ConfigDictTableModel("CONFIG TABLE", self._experiment_config, header, self)

        config_table = self._autogenerated_object.config_table
        config_table.setModel(table_model)
        config_table.resizeColumnsToContents()
        config_table.setSortingEnabled(True)
        config_table.setEditTriggers(QAbstractItemView.DoubleClicked)
        table_model.set_editable_columns(editable_columns)
        table_model.set_data_changed_callback(self._config_table_edited)
        table_model.sort_by_col(1)

    def _update_experiment_info(self):
        # Fill the comboboxes
        experiment_info = self._mlc_local.get_experiment_info(self._experiment_name)
        from_gen_combo = self._autogenerated_object.from_gen_combo
        to_gen_combo = self._autogenerated_object.to_gen_combo
        gen_count_combo = self._autogenerated_object.gen_count_combo

        from_gen_combo.clear()
        to_gen_combo.clear()
        gen_count_combo.clear()

        number_of_gens = experiment_info["generations"]
        if number_of_gens == 0:
            from_gen_combo.addItems([str(1)])
            to_gen_combo.addItems([str(x) for x in xrange(2, ExperimentWindow.MAX_GENERATIONS)])
        else:
            # FIXME: Think what to do in the border case of number_of_gens == MAX_GENERATIONS
            from_gen_combo.addItems([str(x) for x in xrange(1, number_of_gens + 1)])
            to_gen_combo.addItems([str(x) for x in xrange(number_of_gens + 1, ExperimentWindow.MAX_GENERATIONS)])

        # Fill the db_view
        gen_count_group = self._autogenerated_object.gen_count_group
        if number_of_gens != 0:
            if self._current_gen == 0:
                self._current_gen = 1

            header = ['Population Index', 'Individual Index', 'Gen Method', 'Appearences', 'Cost', 'Value']
            # TODO: Add support for value edition
            # editable_columns = [4, 5]
            editable_columns = [4]

            table_model = ConfigTableModel("DB TABLE", self._individuals_per_generation[self._current_gen - 1],
                                           header, self)
            db_view = self._autogenerated_object.db_view
            db_view.setModel(table_model)
            db_view.resizeColumnsToContents()
            db_view.setSortingEnabled(True)
            table_model.set_editable_columns(editable_columns)
            table_model.set_data_changed_callback(self._db_view_edited)
            table_model.sort_by_col(0)

            # Refresh the gen_count_label
            gen_count_group.setTitle("Generation: {0}/{1}".format(self._current_gen, number_of_gens))

            # Refresh the gen_count_combo
            gen_count_combo.addItems(str(x) for x in xrange(1, number_of_gens + 1))
            gen_count_combo.setCurrentIndex(self._current_gen - 1)
        else:
            self._current_gen = 0
            gen_count_group.setTitle("Generation: 0/0")

    def _update_individuals_figure(self):
        if self._current_gen != 0:
            chart_layout = self._autogenerated_object.chart_layout

            # Matplotlib graphs
            # indiv_canvas = CostPerIndividualCanvas(indiv_graph_frame, width=5, height=4, dpi=85)
            # indiv_canvas.set_costs(current_generation.get_costs())
            # indiv_canvas.set_xlabel('Individuals')
            # indiv_canvas.set_ylabel('Costs')
            # indiv_canvas.set_title('Cost Per Individual')
            # indiv_canvas.compute_initial_figure(self._autogenerated_object.log_check.isChecked())

            # Draw current generation
            current_generation = self._mlc_local.get_generation(self._experiment_name, self._current_gen)
            costs = current_generation.get_costs()
            samples = np.linspace(1, len(costs), len(costs), dtype=int)
            indiv_chart = QtChartWrapper()
            indiv_chart.set_title('Cost Per Individual')
            ylog = self._autogenerated_object.log_check.isChecked()
            indiv_chart.set_xaxis(log=False, label="Individuals",
                                  label_format='%i', tick_count=10)
            indiv_chart.set_yaxis(log=ylog, label="Costs",
                                  label_format='%g', tick_count=10)
            indiv_chart.add_data(samples, costs, color=Qt.red, line_width=2)

            # Draw all generations only if the show_all button is selected
            if self._autogenerated_object.show_all_check.isChecked():
                experiment_info = self._mlc_local.get_experiment_info(self._experiment_name)
                number_of_gens = experiment_info["generations"]

                for index in xrange(1, number_of_gens + 1):
                    if index == self._current_gen:
                        continue
                    gen = self._mlc_local.get_generation(self._experiment_name, index)
                    costs = gen.get_costs()
                    indiv_chart.add_data(samples, costs, color=Qt.blue, line_width=1)

            indiv_canvas = indiv_chart.get_widget()

            # Remove all previous widgets before rendering again
            for i in reversed(range(chart_layout.count())):
                chart_layout.itemAt(i).widget().setParent(None)
            # Add the Indiv Canvas
            chart_layout.addWidget(indiv_canvas)

    def _persist_experiment_config(self):
        try:
            self._mlc_local.set_experiment_configuration(self._experiment_name, self._experiment_config)
        except:
            exc_type, value, traceback = sys.exc_info()
            logger.error('[EXPERIMENT {0}] [PERSIST_CONFIG] - Error while persisting experiment config file. '
                         'Type: {0} - Value: {1} - Traceback: {2}'
                         .format(self._experiment_name, exc_type, value, traceback))
            return
        self._autogenerated_object.save_config_button.setDisabled(True)

    def _ask_if_experiment_config_must_be_saved(self):
        """
        First, ask if the experiment need to be saved. If not, retrieve the
        previous configuration
        """
        if self._autogenerated_object.save_config_button.isEnabled():
            response = QMessageBox.question(self, "Save Experiment Config",
                                            "Experiment config has changed. Do you want to persist the changes made?",
                                            QMessageBox.Yes | QMessageBox.No,
                                            QMessageBox.Yes)
            if response == QMessageBox.Yes:
                self._persist_experiment_config()
            else:
                self._load_experiment_config()

            self._autogenerated_object.save_config_button.setDisabled(True)

    def _update_experiment(self, cancelled):
        self._progress_dialog.close_window()
        if not cancelled:
            QMessageBox.information(self, 'Experiment {0}'.format(self._experiment_name),
                                    'Experiment was succesfully executed.', QMessageBox.Ok)
        else:
            QMessageBox.information(self, 'Experiment {0}'.format(self._experiment_name),
                                    'Experiment was cancelled by the user.', QMessageBox.Ok)

        self._update_individuals_per_generation_list()
        self._update_experiment_info()
        self._update_individuals_figure()

    def _store_board_configuration(self, board_config, serial_conn):
        # Pass the parameter as a list to mock PyQt fixed data types
        logger.debug('[EXPERIMENT {0}] [BOARD_CONFIG] - '
                     'Board has been configured'
                     .format(self._experiment_name))

        self._board_config = board_config[0]
        self._serial_conn = serial_conn[0]

        # Init the arduino singleton
        try:
            self._board_config = self._board_config._replace(connection = SerialConnection(**self._serial_conn._asdict()))
            #ArduinoInterfaceSingleton.get_instance(protocol_setup=self._board_config,
            #                                       conn_setup=self._serial_conn)
        except Exception, err:
            logger.debug('[EXPERIMENT {0}] [BOARD_CONFIG] - '
                         'Serial port could not be initialized. Error Msg: {1}'
                         .format(self._experiment_name, err))
            selection = QMessageBox.critical(self, "Connection failure",
                             "The current connection setup failed during initialization. Do you want to change this configuration? \
                             (Choosing \"no\" means that the board will not be usable in the experiment)"
                             .format(preev_path),
                             QMessageBox.Yes | No, QMessageBox.Yes)
            if selection == QMessageBox.Yes:
                #self.on_board_config_button_clicked()
                print "FUCK"
            else:
                #FIXME: If the pin setups aren't empty then the protocol init will fail
                self._board_config = self._board_config._replace(connection = BaseConnection())

