"""Qt widgets for the Text-to-Image tab."""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from PyQt6 import QtCore, QtGui, QtWidgets

from ..api_client import GeneratedImage, StableDiffusionClient, StableDiffusionAPIError
from ..models import GenerationRequest
from .widgets import NoWheelComboBox, NoWheelDoubleSpinBox, NoWheelSpinBox


class GenerationWorker(QtCore.QObject):
    """Worker object that performs a text-to-image request in a separate thread."""

    finished = QtCore.pyqtSignal(list)
    error = QtCore.pyqtSignal(str)

    def __init__(self, client: StableDiffusionClient, request: GenerationRequest) -> None:
        super().__init__()
        self._client = client
        self._request = request

    @QtCore.pyqtSlot()
    def run(self) -> None:
        try:
            images = self._client.text_to_image(self._request.to_payload())
        except Exception as exc:  # pragma: no cover - GUI runtime errors
            self.error.emit(str(exc))
        else:
            self.finished.emit(images)


class TextToImageWidget(QtWidgets.QWidget):
    """Tab that allows triggering txt2img generations."""

    def __init__(self, client: StableDiffusionClient, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.client = client
        self._thread: Optional[QtCore.QThread] = None
        self._worker: Optional[GenerationWorker] = None

        self._build_ui()
        self._connect_signals()
        self._load_initial_metadata()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        self.form_widget = QtWidgets.QWidget()
        form_layout = QtWidgets.QFormLayout(self.form_widget)
        form_layout.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        form_layout.setSpacing(8)

        self.prompt_edit = QtWidgets.QPlainTextEdit()
        self.prompt_edit.setPlaceholderText("Enter your prompt here...")
        self.prompt_edit.setFixedHeight(100)

        self.negative_prompt_edit = QtWidgets.QPlainTextEdit()
        self.negative_prompt_edit.setPlaceholderText("Negative prompt")
        self.negative_prompt_edit.setFixedHeight(80)

        self.checkpoint_combo = NoWheelComboBox()
        self.vae_combo = NoWheelComboBox()
        self.text_encoder_combo = NoWheelComboBox()
        self.sampler_combo = NoWheelComboBox()
        self.scheduler_combo = NoWheelComboBox()

        self.steps_spin = NoWheelSpinBox()
        self.steps_spin.setRange(1, 200)
        self.steps_spin.setValue(20)

        self.clip_skip_spin = NoWheelSpinBox()
        self.clip_skip_spin.setRange(0, 12)
        self.clip_skip_spin.setSpecialValueText("Default")
        self.clip_skip_spin.setValue(0)

        self.cfg_scale_spin = NoWheelDoubleSpinBox()
        self.cfg_scale_spin.setRange(1.0, 30.0)
        self.cfg_scale_spin.setSingleStep(0.5)
        self.cfg_scale_spin.setValue(7.0)

        self.width_spin = NoWheelSpinBox()
        self.width_spin.setRange(64, 2048)
        self.width_spin.setSingleStep(64)
        self.width_spin.setValue(512)

        self.height_spin = NoWheelSpinBox()
        self.height_spin.setRange(64, 2048)
        self.height_spin.setSingleStep(64)
        self.height_spin.setValue(512)

        self.batch_size_spin = NoWheelSpinBox()
        self.batch_size_spin.setRange(1, 8)
        self.batch_size_spin.setValue(1)

        self.batch_count_spin = NoWheelSpinBox()
        self.batch_count_spin.setRange(1, 16)
        self.batch_count_spin.setValue(1)

        self.seed_spin = NoWheelSpinBox()
        self.seed_spin.setRange(-1, 2_147_483_647)
        self.seed_spin.setSpecialValueText("Random")
        self.seed_spin.setValue(-1)

        self.gpu_weight_spin = NoWheelSpinBox()
        self.gpu_weight_spin.setRange(0, 32_768)
        self.gpu_weight_spin.setSpecialValueText("Auto")
        self.gpu_weight_spin.setValue(0)

        form_layout.addRow("Prompt", self.prompt_edit)
        form_layout.addRow("Negative", self.negative_prompt_edit)
        form_layout.addRow("Checkpoint", self.checkpoint_combo)
        form_layout.addRow("VAE", self.vae_combo)
        form_layout.addRow("Text Encoder", self.text_encoder_combo)
        form_layout.addRow("Sampler", self.sampler_combo)
        form_layout.addRow("Scheduler", self.scheduler_combo)
        form_layout.addRow("Sampling Steps", self.steps_spin)
        form_layout.addRow("CFG Scale", self.cfg_scale_spin)
        form_layout.addRow("Clip Skip", self.clip_skip_spin)
        form_layout.addRow("Width", self.width_spin)
        form_layout.addRow("Height", self.height_spin)
        form_layout.addRow("Batch Size", self.batch_size_spin)
        form_layout.addRow("Batch Count", self.batch_count_spin)
        form_layout.addRow("Seed", self.seed_spin)
        form_layout.addRow("GPU Weights (MB)", self.gpu_weight_spin)

        self.generate_button = QtWidgets.QPushButton("Generate")
        self.generate_button.setObjectName("generateButton")
        self.generate_button.setMinimumHeight(40)

        form_layout.addRow(self.generate_button)

        layout.addWidget(self.form_widget, stretch=1)

        # Preview panel --------------------------------------------------
        preview_layout = QtWidgets.QVBoxLayout()
        preview_layout.setSpacing(12)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.preview_label = QtWidgets.QLabel("Image preview will appear here")
        self.preview_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(320, 320)
        self.preview_label.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.preview_label.setStyleSheet("background-color: #101010; color: #cccccc; border-radius: 8px;")
        self.preview_label.setWordWrap(True)

        self.info_box = QtWidgets.QTextEdit()
        self.info_box.setReadOnly(True)
        self.info_box.setFixedHeight(120)

        preview_layout.addWidget(self.progress_bar)
        preview_layout.addWidget(self.preview_label, stretch=1)
        preview_layout.addWidget(self.info_box)

        layout.addLayout(preview_layout, stretch=1)

        self.status_label = QtWidgets.QLabel()
        self.status_label.setObjectName("statusLabel")
        preview_layout.addWidget(self.status_label)

        self.progress_timer = QtCore.QTimer(self)
        self.progress_timer.setInterval(1000)

    # ------------------------------------------------------------------
    def _connect_signals(self) -> None:
        self.generate_button.clicked.connect(self._on_generate_clicked)
        self.progress_timer.timeout.connect(self._refresh_progress)

    # ------------------------------------------------------------------
    def _load_initial_metadata(self) -> None:
        errors: list[str] = []

        def fetch_list(name: str, callback: Callable[[], list[str]]) -> list[str]:
            try:
                return callback()
            except StableDiffusionAPIError as api_error:
                errors.append(f"{name}: {api_error}")
            except Exception as generic_error:  # pragma: no cover - runtime
                errors.append(f"{name}: {generic_error}")
            return []

        checkpoints = fetch_list("Checkpoints", self.client.list_checkpoints)
        vaes = fetch_list("VAEs", self.client.list_vaes)
        encoders = fetch_list("Text encoders", self.client.list_text_encoders)
        samplers = fetch_list("Samplers", self.client.list_samplers)
        schedulers = fetch_list("Schedulers", self.client.list_schedulers)

        options: Dict[str, Any] = {}
        try:
            options = self.client.get_options()
        except StableDiffusionAPIError as api_error:
            errors.append(f"Options: {api_error}")
        except Exception as generic_error:  # pragma: no cover - runtime
            errors.append(f"Options: {generic_error}")

        def populate(combo: QtWidgets.QComboBox, values: list[str]) -> None:
            combo.clear()
            combo.addItem("Auto", userData=None)
            for value in values:
                combo.addItem(value, userData=value)

        populate(self.checkpoint_combo, checkpoints)
        populate(self.vae_combo, vaes)
        populate(self.text_encoder_combo, encoders)
        populate(self.sampler_combo, samplers)
        populate(self.scheduler_combo, schedulers)

        if errors:
            QtWidgets.QMessageBox.warning(
                self,
                "Metadata issues",
                "\n".join(errors),
            )
            self.status_label.setText("Metadata loaded with warnings.")
        else:
            self.status_label.setText("Metadata loaded.")

        self._apply_initial_options(options)

    def _apply_initial_options(self, options: Dict[str, Any]) -> None:
        if not options:
            return

        self._select_combo_value(self.checkpoint_combo, options.get("sd_model_checkpoint"))
        self._select_combo_value(self.vae_combo, options.get("sd_vae"))
        self._select_combo_value(self.text_encoder_combo, options.get("sd_text_encoder"))
        sampler_value = options.get("sampler_name")
        if isinstance(sampler_value, str):
            self._select_combo_value(self.sampler_combo, sampler_value)
        else:
            sampler_index = options.get("sampler_index")
            if isinstance(sampler_index, int):
                self._select_combo_by_index(self.sampler_combo, sampler_index)
        self._select_combo_value(self.scheduler_combo, options.get("scheduler"))

        clip_skip = options.get("CLIP_stop_at_last_layers")
        if isinstance(clip_skip, int) and clip_skip >= 0:
            self.clip_skip_spin.setValue(clip_skip)

        gpu_limit = options.get("gpu_weights_limit_mb")
        if isinstance(gpu_limit, int) and gpu_limit >= 0:
            self.gpu_weight_spin.setValue(gpu_limit)

        int_settings = {
            "steps": self.steps_spin,
            "width": self.width_spin,
            "height": self.height_spin,
            "batch_size": self.batch_size_spin,
            "n_iter": self.batch_count_spin,
            "seed": self.seed_spin,
        }
        for key, widget in int_settings.items():
            value = options.get(key)
            if isinstance(value, int) and value >= widget.minimum():
                widget.setValue(value)

        cfg_scale = options.get("cfg_scale")
        if isinstance(cfg_scale, (int, float)):
            self.cfg_scale_spin.setValue(float(cfg_scale))

    # ------------------------------------------------------------------
    def _build_request(self) -> GenerationRequest:
        request = GenerationRequest(
            prompt=self.prompt_edit.toPlainText().strip(),
            negative_prompt=self.negative_prompt_edit.toPlainText().strip(),
            steps=self.steps_spin.value(),
            sampler=self._selected_value(self.sampler_combo) or "Euler a",
            scheduler=self._selected_value(self.scheduler_combo),
            cfg_scale=self.cfg_scale_spin.value(),
            width=self.width_spin.value(),
            height=self.height_spin.value(),
            batch_size=self.batch_size_spin.value(),
            batch_count=self.batch_count_spin.value(),
            seed=self.seed_spin.value(),
            clip_skip=self.clip_skip_spin.value() or None,
            checkpoint=self._selected_value(self.checkpoint_combo),
            vae=self._selected_value(self.vae_combo),
            text_encoder=self._selected_value(self.text_encoder_combo),
            gpu_weights_mb=self.gpu_weight_spin.value() or None,
        )
        return request

    def _selected_value(self, combo: QtWidgets.QComboBox) -> Optional[str]:
        value = combo.currentData()
        if value is None or value == "":
            return None
        return value

    def _select_combo_value(self, combo: QtWidgets.QComboBox, value: Any) -> None:
        if value in (None, ""):
            return
        if not isinstance(value, str):
            value = str(value)
        match_flags = QtCore.Qt.MatchFlag.MatchFixedString
        index = combo.findData(value)
        if index < 0:
            index = combo.findText(value, match_flags)
        if index < 0:
            lower_value = value.lower()
            for row in range(combo.count()):
                data = combo.itemData(row)
                text = combo.itemText(row)
                if isinstance(data, str) and data.lower() == lower_value:
                    index = row
                    break
                if text.lower() == lower_value:
                    index = row
                    break
        if index < 0:
            combo.addItem(value, userData=value)
            index = combo.count() - 1
        combo.setCurrentIndex(index)

    def _select_combo_by_index(self, combo: QtWidgets.QComboBox, index: int) -> None:
        if index < 0:
            return
        # Account for the "Auto" entry we prepend to every combo box
        adjusted_index = index + 1 if combo.count() > 0 else index
        if 0 <= adjusted_index < combo.count():
            combo.setCurrentIndex(adjusted_index)

    # ------------------------------------------------------------------
    def _on_generate_clicked(self) -> None:
        if self._thread is not None and self._thread.isRunning():
            QtWidgets.QMessageBox.information(
                self,
                "Generation in progress",
                "Please wait for the current generation to finish before starting a new one.",
            )
            return

        request = self._build_request()
        if not request.prompt:
            QtWidgets.QMessageBox.information(self, "Missing prompt", "Please enter a prompt to generate.")
            return

        self.generate_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.info_box.clear()
        self.status_label.setText("Generating...")

        self._thread = QtCore.QThread(self)
        worker = GenerationWorker(self.client, request)
        self._worker = worker
        worker.moveToThread(self._thread)
        self._thread.started.connect(worker.run)
        worker.finished.connect(self._on_generation_finished)
        worker.finished.connect(self._thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.error.connect(self._on_generation_error)
        worker.error.connect(self._thread.quit)
        worker.error.connect(worker.deleteLater)
        self._thread.finished.connect(self._on_thread_finished)

        self._thread.start()
        self.progress_timer.start()

    # ------------------------------------------------------------------
    @QtCore.pyqtSlot(list)
    def _on_generation_finished(self, images: list[GeneratedImage]) -> None:
        self.progress_timer.stop()
        self.generate_button.setEnabled(True)
        self.status_label.setText("Generation finished.")
        self.progress_bar.setValue(100)

        if not images:
            self.info_box.setPlainText("No images returned by the API.")
            return

        image = images[0]
        qimage = QtGui.QImage.fromData(image.data)
        pixmap = QtGui.QPixmap.fromImage(qimage)
        scaled = pixmap.scaled(
            self.preview_label.size(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)

        info_lines = [f"Seed: {image.seed}"]
        for key, value in sorted(image.info.items() if isinstance(image.info, dict) else []):
            info_lines.append(f"{key}: {value}")
        self.info_box.setPlainText("\n".join(info_lines))

    @QtCore.pyqtSlot(str)
    def _on_generation_error(self, message: str) -> None:
        self.progress_timer.stop()
        self.generate_button.setEnabled(True)
        self.status_label.setText("Generation failed.")
        QtWidgets.QMessageBox.critical(self, "Generation error", message)

    @QtCore.pyqtSlot()
    def _on_thread_finished(self) -> None:
        thread = self._thread
        self._worker = None
        self._thread = None
        if thread is None:
            return
        if thread.isRunning():  # pragma: no cover - safety guard
            thread.wait()
        thread.deleteLater()

    # ------------------------------------------------------------------
    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:  # pragma: no cover - UI only
        super().resizeEvent(event)
        if not self.preview_label.pixmap():
            return
        pixmap = self.preview_label.pixmap()
        scaled = pixmap.scaled(
            self.preview_label.size(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)

    # ------------------------------------------------------------------
    def _refresh_progress(self) -> None:
        try:
            progress = self.client.get_progress()
        except Exception as error:  # pragma: no cover - runtime
            self.status_label.setText(f"Progress error: {error}")
            return

        if not progress:
            return
        pct_value = progress.get("progress")
        if isinstance(pct_value, (int, float)):
            percent = max(0, min(100, int(pct_value * 100)))
            self.progress_bar.setValue(percent)
            status = f"Progress: {percent:.0f}%"
        else:
            status = "Processing..."

        eta = progress.get("eta_relative")
        if isinstance(eta, (int, float)) and eta >= 0:
            if isinstance(pct_value, (int, float)):
                status = f"Progress: {pct_value * 100:.1f}% - ETA {eta:.1f}s"
            else:
                status = f"ETA {eta:.1f}s"

        self.status_label.setText(status)
