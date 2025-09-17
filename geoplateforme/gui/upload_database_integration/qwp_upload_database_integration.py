# standard
import os
from functools import partial
from typing import List, Optional

# PyQGIS
from qgis.core import (
    QgsApplication,
    QgsProcessingAlgorithm,
    QgsProcessingAlgRunnerTask,
    QgsProcessingContext,
    QgsProcessingFeedback,
)
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QByteArray, QSize, QTimer
from qgis.PyQt.QtGui import QIcon, QMovie, QPixmap
from qgis.PyQt.QtWidgets import QHeaderView, QWizardPage

from geoplateforme.__about__ import DIR_PLUGIN_ROOT
from geoplateforme.api.check import CheckExecution
from geoplateforme.api.custom_exceptions import (
    ReadStoredDataException,
    UnavailableProcessingException,
)
from geoplateforme.api.processing import Execution, ProcessingRequestManager
from geoplateforme.api.stored_data import StoredDataRequestManager, StoredDataStatus
from geoplateforme.gui.mdl_execution_list import ExecutionListModel
from geoplateforme.gui.upload_database_integration.qwp_vector_db_edition import (
    VectorDbEditionPageWizard,
)
from geoplateforme.processing import GeoplateformeProvider
from geoplateforme.processing.generation.upload_database_integration import (
    UploadDatabaseIntegrationAlgorithm,
)
from geoplateforme.processing.utils import tags_to_qgs_parameter_matrix_string
from geoplateforme.toolbelt import PlgLogger
from geoplateforme.toolbelt.preferences import PlgOptionsManager


class UploadDatabaseIntegrationPageWizard(QWizardPage):
    def __init__(self, qwp_vector_db_edition: VectorDbEditionPageWizard, parent=None):
        """
        QWizardPage to define create upload to geoplateforme platform

        Args:
            parent: parent QObject
        """

        super().__init__(parent)
        self.setTitle(self.tr("Génération de la base de données vectorielle en cours."))
        self.log = PlgLogger().log
        self.qwp_vector_db_edition = qwp_vector_db_edition

        uic.loadUi(
            os.path.join(
                os.path.dirname(__file__), "qwp_upload_database_integration.ui"
            ),
            self,
        )

        self.tbw_errors.setVisible(False)

        # Task ID and feedback for upload creation
        self.feedback = QgsProcessingFeedback()

        # Processing results
        self.processing_failed = False
        self.created_upload_id = qwp_vector_db_edition.upload_id
        self.upload_check_execution_list: List[CheckExecution] = []
        self.created_stored_data_id = ""

        # Timer for upload check after upload creation
        self.loading_movie = QMovie(
            str(DIR_PLUGIN_ROOT / "resources" / "images" / "loading.gif"),
            QByteArray(),
            self,
        )
        self.vector_db_check_timer = QTimer(self)
        self.vector_db_check_timer.timeout.connect(self.check_vector_db_status)

        # Model for executions display
        self.mdl_execution_list = ExecutionListModel(self)
        self.tableview_execution_list.setModel(self.mdl_execution_list)
        self.tableview_execution_list.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )

    def initializePage(self) -> None:
        """
        Initialize page before show.

        """
        self.tbw_errors.setVisible(False)

        # Processing results
        self.processing_failed = False
        self.created_upload_id = ""
        self.upload_check_execution_list = []
        self.created_stored_data_id = ""

        self.mdl_execution_list.clear_executions()
        self._create_vector_db()

    def _create_vector_db(self) -> None:
        """
        Run UploadDatabaseIntegrationAlgorithm with UploadCreatePageWizard parameters

        """
        algo_str = f"{GeoplateformeProvider().id()}:{UploadDatabaseIntegrationAlgorithm().name()}"
        alg = QgsApplication.processingRegistry().algorithmById(algo_str)
        params = {
            UploadDatabaseIntegrationAlgorithm.STORED_DATA_NAME: self.qwp_vector_db_edition.get_name(),
            UploadDatabaseIntegrationAlgorithm.DATASTORE: self.qwp_vector_db_edition.datastore_id,
            UploadDatabaseIntegrationAlgorithm.UPLOAD: self.qwp_vector_db_edition.upload_id,
            UploadDatabaseIntegrationAlgorithm.TAGS: tags_to_qgs_parameter_matrix_string(
                {"datasheet_name": self.qwp_vector_db_edition.dataset_name}
            ),
            UploadDatabaseIntegrationAlgorithm.WAIT_FOR_INTEGRATION: False,
        }
        self.lbl_step_icon.setMovie(self.loading_movie)
        self.loading_movie.start()

        self._run_alg(
            alg,
            params,
            self.feedback,
            self._vector_db_creation_finished,
        )

        # Run timer for upload check
        self.vector_db_check_timer.start(
            int(PlgOptionsManager.get_plg_settings().status_check_sleep * 1000.0)
        )

    def _vector_db_creation_finished(self, context, successful, results):
        """
        Callback executed when UploadDatabaseIntegrationAlgorithm is finished

        Args:
            context:  algorithm context
            successful: algorithm success
            results: algorithm results
        """
        if successful:
            self.created_stored_data_id = results[
                UploadDatabaseIntegrationAlgorithm.CREATED_STORED_DATA_ID
            ]
            self.setTitle(
                self.tr(
                    "Génération de la base de données vectorielle en cours.\nVous pouvez fermer la fenêtre pendant la génération."
                )
            )
            self.check_vector_db_status()
            # Emit completeChanged to update finish button
            self.completeChanged.emit()
        else:
            self._report_processing_error(
                self.tr("Vector database creation"),
                self.feedback.textLog(),
            )

    def check_vector_db_status(self):
        """
        Check vector db status

        """
        self.mdl_execution_list.clear_executions()

        execution = self._check_stored_data_creation()
        if execution:
            self.mdl_execution_list.set_execution_list([execution])

    def _check_stored_data_creation(self) -> Optional[Execution]:
        """
        Check if stored data creation is done and return processing execution
        If stored data is generated, stop check timer

        Returns: [Execution] database integration processing execution

        """
        execution = None
        if self.created_stored_data_id:
            try:
                stored_data_manager = StoredDataRequestManager()
                processing_manager = ProcessingRequestManager()
                datastore_id = self.qwp_vector_db_edition.datastore_id
                stored_data = stored_data_manager.get_stored_data(
                    datastore_id=datastore_id,
                    stored_data_id=self.created_stored_data_id,
                )

                if (
                    stored_data.tags is not None
                    and "proc_int_id" in stored_data.tags.keys()
                ):
                    execution = processing_manager.get_execution(
                        datastore_id=datastore_id,
                        exec_id=stored_data.tags["proc_int_id"],
                    )
                # Stop timer if stored_data generated
                status = stored_data.status
                if status == StoredDataStatus.GENERATED:
                    self.setTitle(
                        self.tr(
                            "La base de données vectorielle a été générée dans l'entrepôt."
                        )
                    )
                    pixmap = QPixmap(
                        str(
                            DIR_PLUGIN_ROOT
                            / "resources"
                            / "images"
                            / "icons"
                            / "Done.svg"
                        )
                    )
                    self.lbl_step_icon.setMovie(QMovie())
                    self.lbl_step_icon.setPixmap(pixmap)
                    self.vector_db_check_timer.stop()

            except (
                UnavailableProcessingException,
                ReadStoredDataException,
            ) as exc:
                self._report_processing_error(
                    self.tr("Stored database integration check"), str(exc)
                )
        return execution

    def validatePage(self) -> bool:
        """
        Validate current page content : return True

        Returns: True if upload and vector db was created, False otherwise

        """
        result = self.isComplete()

        if result:
            self.vector_db_check_timer.stop()

        return result

    def isComplete(self) -> bool:
        """
        Check if QWizardPage is complete for next/finish button enable.
        Here we check that upload was created.

        Returns: True if upload was created, False otherwise

        """
        result = True
        if not self.created_stored_data_id and not self.processing_failed:
            result = False

        return result

    def _stop_timer_and_display_error(self, error: str) -> None:
        self.vector_db_check_timer.stop()
        self.setTitle(error)
        self.loading_movie.stop()
        self.lbl_step_icon.setMovie(QMovie())
        self.lbl_step_icon.setPixmap(
            QIcon(QgsApplication.iconPath("mIconWarning.svg")).pixmap(QSize(32, 32))
        )
        self.completeChanged.emit()

    def _report_processing_error(self, processing: str, error: str) -> None:
        """
        Report processing error by displaying error in text browser

        Args:
            error:
        """
        self.processing_failed = True
        self.tbw_errors.setVisible(True)
        self.tbw_errors.setText(error)
        self._stop_timer_and_display_error(
            self.tr("{0} failed. Check report for more details.").format(processing)
        )

    @staticmethod
    def _run_alg(
        alg: QgsProcessingAlgorithm,
        params: dict,
        feedback: QgsProcessingFeedback,
        executed_callback,
    ) -> int:
        """
        Run a QgsProcessingAlgorithm and connect execution callback

        Args:
            alg: QgsProcessingAlgorithm to run
            params: QgsProcessingAlgorithm params
            feedback: QgsProcessingFeedback
            executed_callback: executed callback after algorithm execution

        Returns: created QgsTask

        """
        context = QgsProcessingContext()
        task = QgsProcessingAlgRunnerTask(alg, params, context, feedback)
        task.executed.connect(partial(executed_callback, context))
        return QgsApplication.taskManager().addTask(task)
