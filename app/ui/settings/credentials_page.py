from PySide6 import QtWidgets, QtCore, QtGui
from ..dayu_widgets.label import MLabel
from ..dayu_widgets.line_edit import MLineEdit
from ..dayu_widgets.check_box import MCheckBox
from ..dayu_widgets.push_button import MPushButton
from ..dayu_widgets.line_tab_widget import MLineTabWidget
from ..dayu_widgets.message import MMessage
from ..dayu_widgets.loading import MLoadingWrapper
from .utils import set_label_width
from modules.translation.models import ModelManager

class PlatformCredentialWidget(QtWidgets.QWidget):
    sig_credentials_changed = QtCore.Signal()

    def __init__(self, platform_display_name, platform_internal_name, parent=None):
        super().__init__(parent)
        self.platform_display_name = platform_display_name
        self.platform_internal_name = platform_internal_name
        self.widgets = {}
        self._init_ui()

    def _init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        
        # Header
        header = MLabel(self.platform_display_name).strong().h2()
        layout.addWidget(header)
        layout.addSpacing(10)

        # Fields based on platform
        if self.platform_internal_name == "Microsoft Azure":
            self._add_azure_fields(layout)
        elif self.platform_internal_name == "Custom":
            self._add_custom_fields(layout)
        elif self.platform_internal_name == "Yandex":
            self._add_yandex_fields(layout)
        elif self.platform_internal_name == "DeeLX":
            self._add_deelx_fields(layout)
        else:
            # Standard LLM platforms (Gemini, GPT, OpenRouter, Claude, Deepseek, DeepL, etc.)
            self._add_standard_llm_fields(layout)
            
        layout.addStretch(1)

    def _add_line_edit(self, layout, label_text, password=False):
        edit = MLineEdit()
        if password:
            edit.setEchoMode(QtWidgets.QLineEdit.Password)
        edit.setFixedWidth(400)
        prefix = MLabel(label_text).border()
        set_label_width(prefix)
        prefix.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        edit.set_prefix_widget(prefix)
        layout.addWidget(edit)
        # Notify when text changes (use lambda to ignore 'text' argument)
        edit.textChanged.connect(lambda: self.sig_credentials_changed.emit())
        return edit

    def _add_standard_llm_fields(self, layout):
        api_key_label = self.tr("API Key")
        if self.platform_internal_name == "DeepL":
            api_key_label = self.tr("Auth Key")
            
        self.api_key_input = self._add_line_edit(layout, api_key_label, password=True)
        self.widgets[f"{self.platform_internal_name}_api_key"] = self.api_key_input
        
        # If it's a platform that supports model fetching
        if self.platform_internal_name in ["Google Gemini", "Open AI GPT", "OpenRouter", "Anthropic Claude", "Deepseek"]:
            layout.addSpacing(15)
            
            fetch_layout = QtWidgets.QHBoxLayout()
            self.fetch_btn = MPushButton(self.tr("Fetch Models")).primary().small()
            self.fetch_btn.clicked.connect(self._fetch_models)
            fetch_layout.addWidget(self.fetch_btn)
            fetch_layout.addStretch(1)
            layout.addLayout(fetch_layout)
            
            layout.addSpacing(5)
            layout.addWidget(MLabel(self.tr("Model List")).secondary())
            
            # Model Search Bar
            self.model_search_input = MLineEdit().search().small()
            self.model_search_input.setPlaceholderText(self.tr("Search models..."))
            self.model_search_input.setFixedWidth(400)
            self.model_search_input.textChanged.connect(self._filter_models)
            layout.addWidget(self.model_search_input)
            
            self.model_list = QtWidgets.QListWidget()
            self.model_list.setFixedHeight(200)
            self.model_list.setFixedWidth(400)
            layout.addWidget(self.model_list)
            self.widgets[f"{self.platform_internal_name}_model_list"] = self.model_list

    def _filter_models(self, text: str):
        if not hasattr(self, 'model_list'):
            return
        for i in range(self.model_list.count()):
            item = self.model_list.item(i)
            # Case-insensitive search
            if text.lower() in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def _add_azure_fields(self, layout):
        layout.addWidget(MLabel(self.tr("OCR")).secondary())
        self.widgets["Microsoft Azure_api_key_ocr"] = self._add_line_edit(layout, self.tr("API Key"), password=True)
        self.widgets["Microsoft Azure_endpoint"] = self._add_line_edit(layout, self.tr("Endpoint URL"))
        
        layout.addSpacing(10)
        layout.addWidget(MLabel(self.tr("Translate")).secondary())
        self.widgets["Microsoft Azure_api_key_translator"] = self._add_line_edit(layout, self.tr("API Key"), password=True)
        self.widgets["Microsoft Azure_region"] = self._add_line_edit(layout, self.tr("Region"))

    def _add_custom_fields(self, layout):
        self.widgets["Custom_api_key"] = self._add_line_edit(layout, self.tr("API Key"), password=True)
        self.widgets["Custom_api_url"] = self._add_line_edit(layout, self.tr("Endpoint URL"))
        self.widgets["Custom_model"] = self._add_line_edit(layout, self.tr("Model"))

    def _add_yandex_fields(self, layout):
        self.widgets["Yandex_api_key"] = self._add_line_edit(layout, self.tr("Secret Key"), password=True)
        self.widgets["Yandex_folder_id"] = self._add_line_edit(layout, self.tr("Folder ID"))

    def _add_deelx_fields(self, layout):
        self.enabled_checkbox = MCheckBox(self.tr("Enabled"))
        layout.addWidget(self.enabled_checkbox)
        self.widgets["DeeLX_self_hosted"] = self.enabled_checkbox
        
        self.url_input = self._add_line_edit(layout, self.tr("URL"))
        self.widgets["DeeLX_url"] = self.url_input
        
        self.url_input.setEnabled(self.enabled_checkbox.isChecked())
        self.enabled_checkbox.toggled.connect(self.url_input.setEnabled)
        self.enabled_checkbox.toggled.connect(lambda: self.sig_credentials_changed.emit())

    def _fetch_models(self):
        api_key = self.api_key_input.text()
        if not api_key and self.platform_internal_name != "OpenRouter":
            MMessage.error(self.tr("Please enter an API Key first"), parent=self, duration=2)
            return

        # Show loading indicator (optional, but good UX)
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText(self.tr("Fetching..."))
        
        # Use a thread for fetching to avoid UI freeze
        class FetchThread(QtCore.QThread):
            finished = QtCore.Signal(list)
            def __init__(self, platform, key):
                super().__init__()
                self.platform = platform
                self.key = key
            def run(self):
                models = []
                if self.platform == "Google Gemini":
                    models = ModelManager.fetch_gemini_models(self.key)
                elif self.platform == "OpenRouter":
                    models = ModelManager.fetch_openrouter_models(self.key)
                elif self.platform == "Open AI GPT":
                    models = ModelManager.fetch_openai_models(self.key)
                elif self.platform == "Anthropic Claude":
                    models = ModelManager.fetch_anthropic_models(self.key)
                elif self.platform == "Deepseek":
                    models = ModelManager.fetch_deepseek_models(self.key)
                self.finished.emit(models)

        self.thread = FetchThread(self.platform_internal_name, api_key)
        self.thread.finished.connect(self._on_models_fetched)
        self.thread.start()

    def _on_models_fetched(self, models):
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText(self.tr("Fetch Models"))
        
        if not models:
            MMessage.warning(self.tr("No models found or error occurred"), parent=self, duration=2)
            return

        self.model_list.clear()
        self.model_list.addItems(models)
        MMessage.success(self.tr(f"Fetched {len(models)} models"), parent=self, duration=2)


class CredentialsPage(QtWidgets.QWidget):
    def __init__(self, services: list[str], value_mappings: dict[str, str], parent=None):
        super().__init__(parent)
        self.services = services
        self.value_mappings = value_mappings
        self.credential_widgets = {} # Flat dictionary for backward compatibility
        self.platform_widgets = {}

        # main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # Save Keys Checkbox
        self.save_keys_checkbox = MCheckBox(self.tr("Save Keys"))
        main_layout.addWidget(self.save_keys_checkbox)
        main_layout.addSpacing(10)

        # Provider Search Bar
        self.provider_search_bar = MLineEdit().search().small()
        self.provider_search_bar.setPlaceholderText(self.tr("Search providers..."))
        self.provider_search_bar.textChanged.connect(self._filter_providers)
        main_layout.addWidget(self.provider_search_bar)
        main_layout.addSpacing(10)

        # Stacked Widget
        self.stacked_widget = QtWidgets.QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # Grid Page (Page 0)
        self.grid_page = QtWidgets.QWidget()
        self.grid_layout = QtWidgets.QGridLayout(self.grid_page)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(15)
        self.stacked_widget.addWidget(self.grid_page)

        self.provider_buttons = []
        row = 0
        col = 0
        max_cols = 3

        for i, service_label in enumerate(self.services):
            internal_name = self.value_mappings.get(service_label, service_label)
            
            # Create Card/Button for Grid
            btn = MPushButton(text=service_label)
            btn.setFixedSize(160, 60) # Large button acting like a card
            # Capture the index for the closure
            btn.clicked.connect(lambda checked=False, idx=i+1: self.stacked_widget.setCurrentIndex(idx))
            
            self.provider_buttons.append((service_label, btn))
            self.grid_layout.addWidget(btn, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
            
            platform_widget = PlatformCredentialWidget(service_label, internal_name)
            platform_widget.sig_credentials_changed.connect(self.update_status_indicators)
            
            # Add Back Button
            back_btn = MPushButton(text=self.tr("← Back to Providers")).small()
            back_btn.setFixedWidth(150)
            back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
            platform_widget.layout().insertWidget(0, back_btn)
            platform_widget.layout().insertSpacing(1, 10)
            
            self.stacked_widget.addWidget(platform_widget)
            self.platform_widgets[internal_name] = platform_widget
            
            # Merge widgets into the flat dictionary for SettingsPage to access
            self.credential_widgets.update(platform_widget.widgets)

        # Add vertical stretch to push the grid to the top
        self.grid_layout.setRowStretch(row + 1, 1)
        # Add horizontal stretch to the last column to push things left
        self.grid_layout.setColumnStretch(max_cols, 1)

        # Initial update of indicators
        self.update_status_indicators()

    def _filter_providers(self, text: str):
        # Clear current grid items (without deleting widgets)
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.takeAt(i)
            # We don't need to do anything with 'item' as the widgets are still owned by grid_page
            
        row = 0
        col = 0
        max_cols = 3
        
        for label, btn in self.provider_buttons:
            if text.lower() in label.lower():
                btn.show()
                self.grid_layout.addWidget(btn, row, col)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            else:
                btn.hide()
        
        # Re-apply stretch
        self.grid_layout.setRowStretch(row + 1, 1)
        for r in range(row + 1):
            self.grid_layout.setRowStretch(r, 0)

    def update_status_indicators(self):
        for label, btn in self.provider_buttons:
            internal_name = self.value_mappings.get(label, label)
            widget = self.platform_widgets.get(internal_name)
            if not widget: continue
            
            is_configured = False
            # Check primary API key or custom fields
            if internal_name == "Microsoft Azure":
                ocr_key = widget.widgets.get("Microsoft Azure_api_key_ocr")
                tr_key = widget.widgets.get("Microsoft Azure_api_key_translator")
                if (ocr_key and ocr_key.text().strip()) or (tr_key and tr_key.text().strip()):
                    is_configured = True
            elif internal_name == "DeeLX":
                url = widget.widgets.get("DeeLX_url")
                if url and url.text().strip():
                    is_configured = True
            elif internal_name == "Custom":
                url = widget.widgets.get("Custom_api_url")
                if url and url.text().strip():
                    is_configured = True
            else:
                key_input = widget.widgets.get(f"{internal_name}_api_key")
                if key_input and hasattr(key_input, 'text') and key_input.text().strip():
                    is_configured = True
            
            prefix = "🟢 " if is_configured else ""
            # Remove existing prefix if any
            clean_label = label.replace("🟢 ", "")
            btn.setText(f"{prefix}{clean_label}")

